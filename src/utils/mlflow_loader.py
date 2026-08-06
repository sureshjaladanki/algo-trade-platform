"""
Utilities for loading MLflow models directly from the SQLite database
when the MLflow client API is incompatible or unavailable due to schema issues.
"""
import pickle
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

import mlflow

from src.horizon.horizon_model import GBMHorizonModel
from src.regime.intraday_model import IntradayHMMRegimeModel

REGIME_EXPERIMENT = "Regime_Pipeline"
HORIZON_EXPERIMENT = "Horizon_Pipeline"


def load_hmm_model(
    *,
    train_period: str | None = None,
    run_id: str | None = None,
    experiment_name: str = REGIME_EXPERIMENT,
) -> tuple[IntradayHMMRegimeModel, str]:
    """
    Load a fitted IntradayHMMRegimeModel logged by `regime_pipeline`.

    Resolution order:
      1. Explicit `--regime-run-id`
      2. Latest FINISHED Regime_Pipeline run whose train_period matches
      3. Latest FINISHED Regime_Pipeline run

    Uses the MLflow tracking API when available; falls back to sqlite + mlruns/
    artifact paths when the tracking DB schema is incompatible with the client.
    """
    resolved_run_id, experiment_id = _resolve_run(
        train_period=train_period,
        run_id=run_id,
        experiment_name=experiment_name,
    )
    pkl_path = _model_pkl_path(experiment_id, resolved_run_id, artifact_subdir="model")
    print(f"Loading HMM from Regime_Pipeline run {resolved_run_id} ({pkl_path})")
    with open(pkl_path, "rb") as f:
        hmm_model = pickle.load(f)

    if not isinstance(hmm_model, IntradayHMMRegimeModel):
        raise TypeError(
            f"Expected IntradayHMMRegimeModel artifact, got {type(hmm_model)!r}"
        )
    if not hmm_model.is_fitted:
        raise ValueError(f"HMM from run {resolved_run_id} is not fitted.")
    return hmm_model, resolved_run_id


def load_horizon_model(
    *,
    direction: str,
    train_period: str | None = None,
    run_id: str | None = None,
    experiment_name: str = HORIZON_EXPERIMENT,
) -> tuple[GBMHorizonModel, str]:
    """
    Load a fitted GBMHorizonModel (long or short) logged by `horizon_pipeline`.

    Artifacts are stored as `model/{direction}/{direction}_model.pkl`.

    Resolution order:
      1. Explicit `--horizon-run-id`
      2. Latest FINISHED Horizon_Pipeline run whose train_period matches
      3. Latest FINISHED Horizon_Pipeline run
    """
    models, resolved_run_id = load_horizon_models(
        directions=[direction],
        train_period=train_period,
        run_id=run_id,
        experiment_name=experiment_name,
    )
    return models[direction], resolved_run_id


def load_horizon_models(
    *,
    directions: list[str] | tuple[str, ...] = ("long", "short"),
    train_period: str | None = None,
    run_id: str | None = None,
    experiment_name: str = HORIZON_EXPERIMENT,
) -> tuple[dict[str, GBMHorizonModel], str]:
    """
    Load one or more Horizon sleeves from a single Horizon_Pipeline run.

    Resolves the MLflow run once, then loads each requested sleeve artifact under
    `model/{direction}/`. Missing sleeves are skipped with a warning; raises if
    none of the requested sleeves are found.

    Returns (models_by_direction, resolved_run_id).
    """
    sleeves = list(directions)
    if not sleeves:
        raise ValueError("directions must be non-empty")
    for direction in sleeves:
        if direction not in ("long", "short"):
            raise ValueError(
                f"direction must be 'long' or 'short', got {direction!r}"
            )

    resolved_run_id, experiment_id = _resolve_run(
        train_period=train_period,
        run_id=run_id,
        experiment_name=experiment_name,
    )

    models: dict[str, GBMHorizonModel] = {}
    for direction in sleeves:
        try:
            models[direction] = _load_horizon_pkl(
                experiment_id, resolved_run_id, direction
            )
        except FileNotFoundError as exc:
            print(f"Warning: No Horizon {direction} model: {exc}")

    if not models:
        raise FileNotFoundError(
            f"No Horizon sleeve artifacts found in run {resolved_run_id} "
            f"for directions={sleeves!r}"
        )
    return models, resolved_run_id


def _load_horizon_pkl(
    experiment_id: str, run_id: str, direction: str
) -> GBMHorizonModel:
    pkl_path = _model_pkl_path(
        experiment_id,
        run_id,
        artifact_subdir=Path("model") / direction,
    )
    print(
        f"Loading Horizon {direction} from Horizon_Pipeline run "
        f"{run_id} ({pkl_path})"
    )
    with open(pkl_path, "rb") as f:
        model = pickle.load(f)

    if not isinstance(model, GBMHorizonModel):
        raise TypeError(f"Expected GBMHorizonModel artifact, got {type(model)!r}")
    if model.direction != direction:
        raise ValueError(
            f"Loaded model direction {model.direction!r} != requested {direction!r}"
        )
    return model


def _resolve_run(
    *,
    train_period: str | None,
    run_id: str | None,
    experiment_name: str,
) -> tuple[str, str]:
    if run_id:
        experiment_id = _experiment_id_for_run(run_id, experiment_name)
        return run_id, experiment_id

    try:
        return _resolve_run_mlflow(train_period, experiment_name)
    except Exception as exc:  # noqa: BLE001
        print(
            f"MLflow client unavailable ({exc}); "
            f"resolving {experiment_name} run via sqlite."
        )
        return _resolve_run_sqlite(train_period, experiment_name)


def _resolve_run_mlflow(
    train_period: str | None, experiment_name: str
) -> tuple[str, str]:
    experiment = mlflow.get_experiment_by_name(experiment_name)
    if experiment is None:
        raise FileNotFoundError(f"MLflow experiment '{experiment_name}' not found.")

    filter_parts = ["attributes.status = 'FINISHED'"]
    if train_period:
        filter_parts.append(f"params.train_period = '{train_period}'")
    runs = mlflow.search_runs(
        experiment_ids=[experiment.experiment_id],
        filter_string=" and ".join(filter_parts),
        order_by=["start_time DESC"],
        max_results=1,
    )
    if (runs is None or runs.empty) and train_period:
        # Fall back to latest finished run when no exact train_period match.
        runs = mlflow.search_runs(
            experiment_ids=[experiment.experiment_id],
            filter_string="attributes.status = 'FINISHED'",
            order_by=["start_time DESC"],
            max_results=1,
        )
    if runs is None or runs.empty:
        raise FileNotFoundError(
            f"No FINISHED runs found in MLflow experiment '{experiment_name}'."
        )
    return str(runs.iloc[0]["run_id"]), str(experiment.experiment_id)


def _resolve_run_sqlite(
    train_period: str | None, experiment_name: str
) -> tuple[str, str]:
    db_path = _mlflow_sqlite_path()
    if db_path is None or not db_path.exists():
        raise FileNotFoundError(
            f"Could not locate mlflow.db to resolve {experiment_name} runs."
        )

    conn = sqlite3.connect(db_path)
    try:
        exp = conn.execute(
            "SELECT experiment_id FROM experiments WHERE name = ?",
            (experiment_name,),
        ).fetchone()
        if exp is None:
            raise FileNotFoundError(f"Experiment '{experiment_name}' not in {db_path}")
        experiment_id = str(exp[0])

        if train_period:
            row = conn.execute(
                """
                SELECT r.run_uuid
                FROM runs r
                JOIN params p ON p.run_uuid = r.run_uuid
                WHERE r.experiment_id = ?
                  AND r.status = 'FINISHED'
                  AND p.key = 'train_period'
                  AND p.value = ?
                ORDER BY r.start_time DESC
                LIMIT 1
                """,
                (experiment_id, train_period),
            ).fetchone()
            if row:
                return str(row[0]), experiment_id

        row = conn.execute(
            """
            SELECT run_uuid
            FROM runs
            WHERE experiment_id = ? AND status = 'FINISHED'
            ORDER BY start_time DESC
            LIMIT 1
            """,
            (experiment_id,),
        ).fetchone()
        if row is None:
            raise FileNotFoundError(
                f"No FINISHED runs in experiment '{experiment_name}'."
            )
        return str(row[0]), experiment_id
    finally:
        conn.close()


def _experiment_id_for_run(run_id: str, experiment_name: str) -> str:
    try:
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment is not None:
            return str(experiment.experiment_id)
    except Exception:  # noqa: BLE001
        pass

    db_path = _mlflow_sqlite_path()
    if db_path is not None and db_path.exists():
        conn = sqlite3.connect(db_path)
        try:
            row = conn.execute(
                "SELECT experiment_id FROM runs WHERE run_uuid = ?",
                (run_id,),
            ).fetchone()
            if row:
                return str(row[0])
        finally:
            conn.close()

    # Conventional local artifact layout used by this repo.
    return "1"


def _model_pkl_path(
    experiment_id: str,
    run_id: str,
    *,
    artifact_subdir: str | Path = "model",
) -> Path:
    artifact_dir = (
        Path("mlruns") / str(experiment_id) / run_id / "artifacts" / Path(artifact_subdir)
    )
    if not artifact_dir.exists():
        raise FileNotFoundError(
            f"No model artifacts for run {run_id} under {artifact_dir}"
        )
    pkls = sorted(artifact_dir.glob("*.pkl"))
    if not pkls:
        raise FileNotFoundError(f"No .pkl model artifact in {artifact_dir}")
    return pkls[0]


def _mlflow_sqlite_path() -> Path | None:
    tracking_uri = mlflow.get_tracking_uri()
    if tracking_uri.startswith("sqlite:"):
        parsed = urlparse(tracking_uri)
        # sqlite:///C:/path or sqlite:///relative.db
        path = parsed.path
        if path.startswith("/") and len(path) > 2 and path[2] == ":":
            path = path[1:]  # strip leading slash before Windows drive
        return Path(path)
    default = Path("mlflow.db")
    return default if default.exists() else None
