"""Production cutover freeze for M0–M6.

Fresh architecture work must not silently swap the live cascade. Until an
explicit M8 ship decision, treat these as locked:

- ``src.precision.session.LONG_TOP_K`` / ``SHORT_TOP_K`` — capacity constants
- ``src.labels.triple_barrier`` floors (60/30 Long, 50/30 Short) and H=6
- ``predict_horizon_gbm`` / ``GBMHorizonModel`` ship path
- ``calculate_horizon_precision_features`` Top-K registry emit

Fresh code lives under ``src.horizon.fresh`` and ``src.labels.fresh_barrier``.
"""

PRODUCTION_CUTOVER_MILESTONE = "M8"
PRODUCTION_FROZEN_UNTIL = "M8 ship / no-ship decision"

FROZEN_SURFACES: tuple[str, ...] = (
    "src.precision.session.LONG_TOP_K",
    "src.precision.session.SHORT_TOP_K",
    "src.labels.triple_barrier.TP_FLOOR_LONG",
    "src.labels.triple_barrier.SL_FLOOR",
    "src.labels.triple_barrier.TP_FLOOR_SHORT",
    "src.utils.eval_common.H_BARS",
    "src.pipelines.horizon_pipeline.predict_horizon_gbm",
    "src.features.horizon_precision.calculate_horizon_precision_features",
)
