"""Download Nifty 1-minute candle data from Kaggle.

Two modes are supported:

* ``--mode stocks``  (default) : per-stock 1-min OHLCV from
  ``debashis74017/stock-market-data-nifty-50-stocks-1-min-data``
  (despite the slug, this dataset contains Nifty 100 stocks).
  Symbols are pulled from ``nifty100_symbols`` in the YAML.

* ``--mode indices`` : VIX + sectoral index 1-min OHLCV from
  ``debashis74017/nifty-50-minute-data``.
  Symbols are the ``vix_symbol``, ``market_symbol``, plus the keys of
  ``sectoral_indices``.

The script reads ``config/market_sectoral_symbols.yml``, downloads the
relevant dataset archive once into a local cache, then extracts only the
matching CSVs into ``data/GOLDEN/<YAML_SYMBOL>.csv``.

Usage
-----
    poetry run python -m src.scripts.download_kaggle_data                       # stocks (default)
    poetry run python -m src.scripts.download_kaggle_data --mode indices        # VIX + sectoral indices
    poetry run python -m src.scripts.download_kaggle_data --skip-existing         # only missing CSVs (default)
    poetry run python -m src.scripts.download_kaggle_data --force-symbols "^CNXMETAL,^CNXENERGY"
    poetry run python -m src.scripts.download_kaggle_data --keep-archive        # retain the zip
    poetry run python -m src.scripts.download_kaggle_data --force               # re-download archive

One-time Kaggle credential setup
--------------------------------
1. ``poetry install`` (``kaggle`` is a declared Poetry dependency)
2. Visit https://www.kaggle.com/settings/account and click
   "Create New API Token".
3. Either set ``KAGGLE_API_TOKEN`` in the repo-root ``.env`` (recommended,
   gitignored) or place the legacy ``kaggle.json`` at:
       Windows : %USERPROFILE%\\.kaggle\\kaggle.json
       macOS/Linux : ~/.kaggle/kaggle.json
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import zipfile
from collections.abc import Callable, Iterable
from pathlib import Path

import yaml

KAGGLE_STOCKS_DATASET = "debashis74017/stock-market-data-nifty-50-stocks-1-min-data"
KAGGLE_INDICES_DATASET = "debashis74017/nifty-50-minute-data"

# YAML key (normalized) -> ordered Kaggle archive filename candidates.
INDEX_ALIASES: dict[str, list[str]] = {
    "INDIAVIX": ["INDIAVIX", "INDIA VIX", "VIX"],
    "NSEI": ["NSEI", "NIFTY 50", "NIFTY50", "NIFTY"],
    "CNXIT": ["CNXIT", "NIFTY IT", "NIFTYIT"],
    "CNXAUTO": ["CNXAUTO", "NIFTY AUTO", "NIFTYAUTO"],
    "CNXENERGY": ["CNXENERGY", "NIFTY ENERGY", "NIFTYENERGY"],
    "CNXFINANCE": [
        "CNXFINANCE", "NIFTY FIN SERVICE", "NIFTY FINANCIAL SERVICES", "NIFTYFIN",
    ],
    "CNXMETAL": ["CNXMETAL", "NIFTY METAL", "NIFTYMETAL"],
    "CNXFMCG": ["CNXFMCG", "NIFTY FMCG", "NIFTYFMCG"],
    "CNXREALTY": ["CNXREALTY", "NIFTY REALTY", "NIFTYREALTY"],
    "NIFTY_OIL_AND_GAS": [
        "NIFTY OIL AND GAS", "NIFTY OIL & GAS", "NIFTY_OIL_AND_GAS",
    ],
    "NIFTYCEMENT": [
        "NIFTYCEMENT", "NIFTY CEMENT", "NIFTY CEMENT & CEMENT PRODUCTS",
        "NIFTY INFRA", "NIFTYINFRA",
    ],
    "CNXPSUBANK": ["CNXPSUBANK", "NIFTY PSU BANK", "NIFTYPSUBANK"],
    "NIFTY_PVT_BANK": [
        "NIFTY PVT BANK", "NIFTY PRIVATE BANK", "NIFTY_PVT_BANK",
    ],
    "CNXPHARMA": ["CNXPHARMA", "NIFTY PHARMA", "NIFTYPHARMA", "NIFTY HEALTHCARE"],
    "NIFTY_IND_DEFENCE": [
        "NIFTY IND DEFENCE", "NIFTY INDIA DEFENCE", "NIFTYINDDEFENCE",
        "NIFTY_IND_DEFENCE",
    ],
}

BACKFILL_PROXY = "NIFTY 50"
BACKFILL_START = "2015-01-09 09:15:00"


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO_ROOT / "config" / "market_sectoral_symbols.yml"
DEFAULT_OUT = REPO_ROOT / "data" / "GOLDEN"
DEFAULT_CACHE = REPO_ROOT / "data" / "_kaggle_cache"
DOTENV_PATH = REPO_ROOT / ".env"


def _load_dotenv() -> None:
    """Load secrets from the repo-root ``.env`` if present."""
    if not DOTENV_PATH.exists():
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        print(
            "Warning: 'python-dotenv' not installed; .env will be ignored. "
            "Install with: poetry install",
            file=sys.stderr,
        )
        return
    load_dotenv(DOTENV_PATH, override=False)


def _check_kaggle_credentials() -> None:
    """Verify any of the supported Kaggle auth mechanisms is configured."""
    kaggle_dir = Path.home() / ".kaggle"
    legacy_json = kaggle_dir / "kaggle.json"
    new_access_token = kaggle_dir / "access_token"
    has_legacy_env = bool(
        os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY")
    )
    has_new_env = bool(os.environ.get("KAGGLE_API_TOKEN"))
    if (
        legacy_json.exists()
        or new_access_token.exists()
        or has_legacy_env
        or has_new_env
    ):
        return
    raise SystemExit(
        "Kaggle API credentials not found. Configure any one of:\n"
        f"  - {legacy_json}                  (legacy username+key kaggle.json)\n"
        f"  - {new_access_token}              (new personal access token file)\n"
        "  - env: KAGGLE_API_TOKEN              (new personal access token)\n"
        "  - env: KAGGLE_USERNAME + KAGGLE_KEY  (legacy)\n\n"
        "Generate a token at https://www.kaggle.com/settings/account."
    )


def load_nifty100_symbols(config_path: Path) -> list[str]:
    """Return the sorted, deduplicated ``nifty100_symbols`` list from the config."""
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    symbols = {sym for sym in (cfg.get("nifty100_symbols") or []) if sym}
    return sorted(symbols)


def load_index_symbols(config_path: Path) -> list[str]:
    """Return VIX, market, and every sectoral index key in the config."""
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    symbols: set[str] = set()
    for key in ("vix_symbol", "regime_symbol", "market_symbol"):
        value = cfg.get(key)
        if value:
            symbols.add(value)
    for key in (cfg.get("sectoral_indices") or {}):
        symbols.add(key)
    return sorted(symbols)


def normalize_symbol(symbol: str) -> str:
    """Strip Yahoo-style decorations (leading ``^``, trailing ``.NS``)."""
    s = symbol.removeprefix("^")
    s = s.removesuffix(".NS")
    return s


_ALNUM_RE = re.compile(r"[^a-z0-9]")
_KNOWN_SUFFIXES = re.compile(
    r"(_with_indicators_?|_minute_data|_minute|_1m|_1min)$",
    re.IGNORECASE,
)
_NON_1MIN_SUFFIX = re.compile(
    r"_(\d+\s*minute|day|week|month|hour)\.csv$",
    re.IGNORECASE,
)


def _alnum_lower(s: str) -> str:
    return _ALNUM_RE.sub("", s.lower())


def is_1min_member(name: str) -> bool:
    """Return True if ``name`` looks like a 1-minute resolution CSV."""
    if not name.lower().endswith(".csv"):
        return False
    return _NON_1MIN_SUFFIX.search(name) is None


def _member_matches_name(member: str, candidate: str) -> bool:
    stem = Path(member).stem
    cleaned = _KNOWN_SUFFIXES.sub("", stem)
    key = _alnum_lower(candidate)
    return _alnum_lower(cleaned) == key or _alnum_lower(stem) == key


def find_member_for_symbol(
    members: Iterable[str],
    symbol: str,
    aliases: dict[str, list[str]] | None = None,
) -> str | None:
    """Locate a CSV in the archive for ``symbol`` using ordered alias matching."""
    candidate_names = list((aliases or {}).get(symbol, [symbol]))
    if symbol not in candidate_names:
        candidate_names = [symbol, *candidate_names]

    for candidate in candidate_names:
        matches = [m for m in members if _member_matches_name(m, candidate)]
        if matches:
            return min(matches, key=lambda x: len(Path(x).stem))
    return None


def download_archive(dataset: str, cache_dir: Path, force: bool = False) -> Path:
    """Download the given Kaggle dataset zip into ``cache_dir``."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    expected_zip = cache_dir / f"{dataset.split('/')[-1]}.zip"
    if expected_zip.exists() and not force:
        print(f"Using cached archive: {expected_zip}")
        return expected_zip

    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError as e:
        raise SystemExit(
            "The 'kaggle' package is not installed. Run: poetry install"
        ) from e

    api = KaggleApi()
    api.authenticate()
    print(f"Downloading {dataset} -> {cache_dir} (this may take a few minutes)...")
    api.dataset_download_files(
        dataset,
        path=str(cache_dir),
        unzip=False,
        quiet=False,
        force=force,
    )
    if not expected_zip.exists():
        zips = sorted(cache_dir.glob("*.zip"))
        if not zips:
            raise SystemExit(f"No archive was downloaded into {cache_dir}")
        expected_zip = zips[0]
    return expected_zip


def filter_wanted_symbols(
    norm_to_raw: dict[str, str],
    out_dir: Path,
    *,
    skip_existing: bool,
    force_symbols: set[str],
) -> dict[str, str]:
    """Return the subset of symbols that should be extracted this run."""
    if not skip_existing and not force_symbols:
        return norm_to_raw

    wanted: dict[str, str] = {}
    for norm, raw in norm_to_raw.items():
        if raw in force_symbols:
            wanted[norm] = raw
            continue
        if skip_existing and (out_dir / f"{raw}.csv").exists():
            continue
        wanted[norm] = raw
    return wanted


def extract_symbols(
    archive: Path,
    wanted: dict[str, str],
    out_dir: Path,
    aliases: dict[str, list[str]] | None = None,
    member_filter: Callable[[str], bool] | None = None,
) -> tuple[list[tuple[str, str]], list[str]]:
    """Extract the wanted symbols from ``archive`` into ``out_dir``."""
    out_dir.mkdir(parents=True, exist_ok=True)
    found: list[tuple[str, str]] = []
    missing: list[str] = []
    with zipfile.ZipFile(archive, "r") as zf:
        members = zf.namelist()
        if member_filter is not None:
            members = [m for m in members if member_filter(m)]
        for sym in sorted(wanted):
            member = find_member_for_symbol(members, sym, aliases=aliases)
            if member is None:
                missing.append(sym)
                continue
            target_path = out_dir / f"{wanted[sym]}.csv"
            with zf.open(member) as src, open(target_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
            found.append((sym, member))
    return found, missing


def _first_data_timestamp(csv_path: Path) -> str | None:
    with open(csv_path, "rb") as fh:
        fh.readline()
        first_data = fh.readline()
    if not first_data.strip():
        return None
    return first_data.split(b",", 1)[0].decode("ascii", "replace")


def detect_backfill_targets(
    out_dir: Path,
    output_names: dict[str, str],
    *,
    backfill_start: str = BACKFILL_START,
) -> dict[str, str]:
    """Return symbols whose CSV starts after ``backfill_start``."""
    targets: dict[str, str] = {}
    for norm, raw in output_names.items():
        csv_path = out_dir / f"{raw}.csv"
        if not csv_path.exists():
            continue
        first_dt = _first_data_timestamp(csv_path)
        if first_dt and first_dt > backfill_start:
            targets[norm] = BACKFILL_PROXY
    return targets


def apply_history_backfill(
    archive: Path,
    out_dir: Path,
    backfill_map: dict[str, str],
    output_names: dict[str, str] | None = None,
    aliases: dict[str, list[str]] | None = None,
    member_filter: Callable[[str], bool] | None = None,
) -> list[tuple[str, str, int]]:
    """Prepend earlier-history rows from a proxy member to selected symbols."""
    results: list[tuple[str, str, int]] = []
    if not backfill_map:
        return results

    with zipfile.ZipFile(archive, "r") as zf:
        members = zf.namelist()
        if member_filter is not None:
            members = [m for m in members if member_filter(m)]

        for sym, proxy_name in backfill_map.items():
            output_symbol = (output_names or {}).get(sym, sym)
            target = out_dir / f"{output_symbol}.csv"
            if not target.exists():
                continue

            source_member = find_member_for_symbol(
                members, proxy_name, aliases=aliases
            )
            if source_member is None:
                print(
                    f"  [backfill] {output_symbol}: proxy '{proxy_name}' "
                    "not found in archive; skipped."
                )
                continue

            with open(target, "rb") as fh:
                target_header = fh.readline().rstrip(b"\r\n")
                first_data = fh.readline()
            if not first_data.strip():
                continue
            target_first_dt = first_data.split(b",", 1)[0].decode("ascii", "replace")

            backfill_rows: list[bytes] = []
            with zf.open(source_member) as src:
                src_header = src.readline().rstrip(b"\r\n")
                if src_header != target_header:
                    print(
                        f"  [backfill] {output_symbol}: header mismatch with "
                        f"'{source_member}' ({src_header!r} vs {target_header!r}); skipped."
                    )
                    continue
                for line in src:
                    line_dt = line.split(b",", 1)[0].decode("ascii", "replace")
                    if line_dt >= target_first_dt:
                        break
                    backfill_rows.append(line)

            if not backfill_rows:
                continue

            tmp_path = target.with_suffix(target.suffix + ".tmp")
            with open(target, "rb") as src_fh, open(tmp_path, "wb") as dst_fh:
                dst_fh.write(src_fh.readline())
                dst_fh.writelines(backfill_rows)
                shutil.copyfileobj(src_fh, dst_fh)
            os.replace(tmp_path, target)

            results.append((output_symbol, source_member, len(backfill_rows)))

    return results


def parse_force_symbols(value: str | None) -> set[str]:
    if not value:
        return set()
    return {part.strip() for part in value.split(",") if part.strip()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--mode", choices=["stocks", "indices"], default="stocks",
                        help="What to download: 'stocks' or 'indices' (default: stocks)")
    parser.add_argument("--dataset", type=str, default=None,
                        help="Override the Kaggle dataset slug for the chosen mode")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG,
                        help=f"YAML config with symbols (default: {DEFAULT_CONFIG})")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
                        help=f"Output directory for per-symbol CSVs (default: {DEFAULT_OUT})")
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE,
                        help=f"Where to cache the Kaggle zip (default: {DEFAULT_CACHE})")
    parser.add_argument("--force", action="store_true",
                        help="Re-download the archive even if it is already cached")
    parser.add_argument("--keep-archive", action="store_true",
                        help="Don't delete the cached zip after extraction")
    parser.add_argument("--skip-existing", action="store_true", default=True,
                        help="Skip symbols whose CSV already exists in --out (default: on)")
    parser.add_argument("--no-skip-existing", action="store_false", dest="skip_existing",
                        help="Extract all config symbols, overwriting existing CSVs")
    parser.add_argument("--force-symbols", type=str, default=None,
                        help="Comma-separated YAML symbol names to extract even if present")
    args = parser.parse_args(argv)

    _load_dotenv()
    _check_kaggle_credentials()

    if not args.config.exists():
        print(f"Config not found: {args.config}", file=sys.stderr)
        return 1

    force_symbols = parse_force_symbols(args.force_symbols)

    if args.mode == "stocks":
        dataset = args.dataset or KAGGLE_STOCKS_DATASET
        raw_symbols = load_nifty100_symbols(args.config)
        aliases = None
        symbol_kind = "nifty100 symbols"
    else:
        dataset = args.dataset or KAGGLE_INDICES_DATASET
        raw_symbols = load_index_symbols(args.config)
        aliases = INDEX_ALIASES
        symbol_kind = "indices"

    if not raw_symbols:
        print(f"No {symbol_kind} found in config.", file=sys.stderr)
        return 1

    norm_to_raw = {normalize_symbol(s): s for s in raw_symbols}
    wanted = filter_wanted_symbols(
        norm_to_raw,
        args.out,
        skip_existing=args.skip_existing,
        force_symbols=force_symbols,
    )

    print(f"Mode: {args.mode}. Config has {len(norm_to_raw)} {symbol_kind}; "
          f"extracting {len(wanted)} this run.")
    if not wanted:
        print("Nothing to extract.")
        return 0

    archive = download_archive(dataset, args.cache, force=args.force)
    found, missing = extract_symbols(
        archive,
        wanted,
        args.out,
        aliases=aliases,
        member_filter=is_1min_member,
    )

    print()
    print(f"Extracted {len(found)} / {len(wanted)} {symbol_kind} into {args.out}:")
    for sym, member in found:
        raw = wanted[sym]
        label = raw if sym == raw else f"{sym} -> {raw}"
        print(f"  {label:<28} <- {member}")

    if missing:
        print()
        print(f"Not found in dataset ({len(missing)}): "
              f"{', '.join(wanted[s] for s in missing)}")
        print("These may be too new for this dataset version, or named differently.")

    if args.mode == "indices":
        backfill_map = detect_backfill_targets(
            args.out,
            {sym: wanted[sym] for sym, _ in found},
        )
        if backfill_map:
            backfilled = apply_history_backfill(
                archive,
                args.out,
                backfill_map,
                output_names={sym: wanted[sym] for sym in backfill_map},
                aliases=INDEX_ALIASES,
                member_filter=is_1min_member,
            )
            if backfilled:
                print()
                print("Backfilled earlier history from NIFTY 50:")
                for sym, source, n in backfilled:
                    print(f"  {sym:<14} <- {source}  ({n:,} rows prepended)")

    if not args.keep_archive:
        try:
            archive.unlink()
            print(f"\nDeleted cached archive {archive} (use --keep-archive to retain).")
        except OSError:
            pass

    return 0 if found else 2


if __name__ == "__main__":
    raise SystemExit(main())
