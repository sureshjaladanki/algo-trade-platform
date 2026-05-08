"""Download Nifty 1-minute candle data from Kaggle.

Two modes are supported:

* ``--mode stocks``  (default) : per-stock 1-min OHLCV from
  ``debashis74017/stock-market-data-nifty-50-stocks-1-min-data``
  (despite the slug, this dataset contains Nifty 100 stocks).
  Symbols are pulled from ``sectoral_indices.*.trade_symbols`` in the YAML.

* ``--mode indices`` : VIX + sectoral index 1-min OHLCV from
  ``debashis74017/nifty-50-minute-data``.
  Symbols are the ``regime_symbol`` plus the keys of ``sectoral_indices``.

The script reads ``config/nifty_100_sectoral_symbols.yml``, downloads the
relevant dataset archive once into a local cache, then extracts only the
matching CSVs into ``data/GOLDEN/<YAML_SYMBOL>.csv``.

Usage
-----
    python src/scripts/download_kaggle_data.py                       # stocks (default)
    python src/scripts/download_kaggle_data.py --mode indices        # VIX + sectoral indices
    python src/scripts/download_kaggle_data.py --keep-archive        # retain the zip
    python src/scripts/download_kaggle_data.py --force               # re-download

One-time Kaggle credential setup
--------------------------------
1. ``pip install kaggle`` (already in requirements.txt)
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
from pathlib import Path
from typing import Callable, Iterable

import yaml


KAGGLE_STOCKS_DATASET = "debashis74017/stock-market-data-nifty-50-stocks-1-min-data"
KAGGLE_INDICES_DATASET = "debashis74017/nifty-50-minute-data"

# Map from a normalized YAML index symbol to a list of plausible filename stems
# that the Kaggle indices dataset might use. ``_alnum_lower`` is applied to both
# sides during matching, so case and punctuation don't matter here.
INDEX_ALIASES: dict[str, list[str]] = {
    "INDIAVIX": ["INDIAVIX", "INDIA VIX", "VIX"],
    "CNXIT": ["CNXIT", "NIFTY IT", "NIFTYIT"],
    "CNXAUTO": ["CNXAUTO", "NIFTY AUTO", "NIFTYAUTO"],
    "CNXENERGY": ["CNXENERGY", "NIFTY ENERGY", "NIFTYENERGY"],
    "CNXFINANCE": [
        "CNXFINANCE", "NIFTY FIN SERVICE", "NIFTY FINANCIAL SERVICES", "NIFTYFIN",
    ],
    # No 1-min Metal index exists on Kaggle; fall back to NIFTY 50 as a proxy.
    "CNXMETAL": ["CNXMETAL", "NIFTY METAL", "NIFTYMETAL", "NIFTY 50"],
    "CNXFMCG": ["CNXFMCG", "NIFTY FMCG", "NIFTYFMCG"],
    "CNXREALTY": ["CNXREALTY", "NIFTY REALTY", "NIFTYREALTY"],
    # No 1-min Oil & Gas index exists on Kaggle; fall back to NIFTY 50 as a proxy.
    "NIFTY_OIL_AND_GAS": [
        "NIFTY OIL AND GAS", "NIFTY OIL & GAS", "NIFTY_OIL_AND_GAS", "NIFTY 50",
    ],
    "NIFTY_CONSR_DURBL": [
        "NIFTY CONSR DURBL", "NIFTY CONSUMER DURABLES", "NIFTY_CONSR_DURBL",
    ],
    "NIFTYCEMENT": ["NIFTYCEMENT", "NIFTY CEMENT", "NIFTY CEMENT & CEMENT PRODUCTS"],
    # Proxy mappings: dataset doesn't carry these specific indices, so we use
    # the closest available index as a stand-in. The CSV will be saved under
    # the requested YAML symbol's filename so downstream code can keep using
    # the same key without changes.
    "CNXPSUBANK": ["CNXPSUBANK", "NIFTY PSU BANK", "NIFTYPSUBANK", "NIFTY BANK"],
    "NIFTY_PVT_BANK": [
        "NIFTY PVT BANK", "NIFTY PRIVATE BANK", "NIFTY_PVT_BANK", "NIFTY BANK",
    ],
    "CNXPHARMA": ["CNXPHARMA", "NIFTY PHARMA", "NIFTYPHARMA", "NIFTY HEALTHCARE"],
}

# After extraction, splice earlier history from a different archive member into
# certain symbols whose primary source has a short history. The mapping is
# ``output symbol -> source name (looked up the same way as INDEX_ALIASES)``.
# Only rows strictly older than the target's first row are prepended, so the
# operation is idempotent.
INDEX_HISTORY_BACKFILL: dict[str, str] = {
    # NIFTY HEALTHCARE only starts 2022-08-29; backfill 2015-2022 with NIFTY 50.
    "CNXPHARMA": "NIFTY 50",
}


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO_ROOT / "config" / "nifty_100_sectoral_symbols.yml"
DEFAULT_OUT = REPO_ROOT / "data" / "GOLDEN"
DEFAULT_CACHE = REPO_ROOT / "data" / "_kaggle_cache"
DOTENV_PATH = REPO_ROOT / ".env"


def _load_dotenv() -> None:
    """Load secrets from the repo-root ``.env`` if present.

    Existing process env vars take precedence (override=False) so callers can
    still set ``KAGGLE_API_TOKEN`` inline at the shell when needed.
    """
    if not DOTENV_PATH.exists():
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        print(
            "Warning: 'python-dotenv' not installed; .env will be ignored. "
            "Install with: pip install python-dotenv",
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


def load_trade_symbols(config_path: Path) -> list[str]:
    """Return the sorted, deduplicated union of ``trade_symbols`` in the config."""
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    symbols: set[str] = set()
    for entry in (cfg.get("sectoral_indices") or {}).values():
        if not isinstance(entry, dict):
            continue
        for sym in entry.get("trade_symbols") or []:
            symbols.add(sym)
    return sorted(symbols)


def load_index_symbols(config_path: Path) -> list[str]:
    """Return the regime symbol plus every sectoral index key in the config."""
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    symbols: set[str] = set()
    regime = cfg.get("regime_symbol")
    if regime:
        symbols.add(regime)
    for key in (cfg.get("sectoral_indices") or {}).keys():
        symbols.add(key)
    return sorted(symbols)


def normalize_symbol(symbol: str) -> str:
    """Strip Yahoo-style decorations (leading ``^``, trailing ``.NS``)."""
    s = symbol[1:] if symbol.startswith("^") else symbol
    if s.endswith(".NS"):
        s = s[:-3]
    return s


_ALNUM_RE = re.compile(r"[^a-z0-9]")
_KNOWN_SUFFIXES = re.compile(
    r"(_with_indicators_?|_minute_data|_minute|_1m|_1min)$",
    re.IGNORECASE,
)
# Other timeframes present in the multi-resolution indices dataset that we
# must NOT match when 1-min is requested.
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


def find_member_for_symbol(
    members: Iterable[str],
    symbol: str,
    aliases: dict[str, list[str]] | None = None,
) -> str | None:
    """Locate a CSV in the archive that corresponds to ``symbol`` (best-effort).

    Matching is tolerant of the dataset's various naming conventions
    (e.g. ``RELIANCE.csv``, ``RELIANCE_minute.csv``, ``NIFTY IT_minute.csv``)
    and of punctuation differences (``M&M`` vs ``MM``, ``BAJAJ-AUTO`` vs
    ``BAJAJAUTO``, ``CNXIT`` vs ``NIFTY IT``).

    ``aliases`` lets callers register extra candidate names for a symbol; this
    is needed for sectoral indices where the YAML name (``^CNXIT``) differs
    materially from the dataset filename (``NIFTY IT_minute.csv``).
    """
    candidate_names = (aliases or {}).get(symbol, [symbol])
    if symbol not in candidate_names:
        candidate_names = [symbol, *candidate_names]
    target_keys = {_alnum_lower(c) for c in candidate_names}

    matches: list[str] = []
    for m in members:
        if not m.lower().endswith(".csv"):
            continue
        stem = Path(m).stem
        cleaned = _KNOWN_SUFFIXES.sub("", stem)
        if _alnum_lower(cleaned) in target_keys or _alnum_lower(stem) in target_keys:
            matches.append(m)
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
            "The 'kaggle' package is not installed. Run: pip install kaggle"
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


def extract_symbols(
    archive: Path,
    wanted: dict[str, str],
    out_dir: Path,
    aliases: dict[str, list[str]] | None = None,
    member_filter: Callable[[str], bool] | None = None,
) -> tuple[list[tuple[str, str]], list[str]]:
    """Extract the wanted symbols from ``archive`` into ``out_dir``.

    Returns a ``(found, missing)`` tuple where ``found`` is a list of
    ``(symbol, archive_member)`` pairs and ``missing`` is a list of symbols
    that could not be matched to any archive member.

    ``wanted`` maps normalized lookup symbols to the YAML symbol name that
    should be used for the output CSV filename.

    ``member_filter`` (if given) pre-filters archive entries; this is used to
    restrict matching to the 1-minute timeframe when a dataset offers
    multiple resolutions per symbol.
    """
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


def apply_history_backfill(
    archive: Path,
    out_dir: Path,
    backfill_map: dict[str, str],
    output_names: dict[str, str] | None = None,
    aliases: dict[str, list[str]] | None = None,
    member_filter: Callable[[str], bool] | None = None,
) -> list[tuple[str, str, int]]:
    """Prepend earlier-history rows from a proxy member to selected symbols.

    For each ``(target_symbol -> proxy_name)`` entry, finds the proxy CSV in
    ``archive`` (using the same alias/member-filter rules as extraction) and
    splices in every row whose timestamp is *strictly older* than the target
    file's first data row. ``output_names`` maps normalized symbols to the
    actual CSV filenames written by ``extract_symbols``. Headers are required
    to match.

    Returns a list of ``(symbol, source_member, rows_added)`` tuples for the
    backfills that were actually applied. The operation is idempotent.
    """
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
                        f"  [backfill] {output_symbol}: header mismatch with '{source_member}' "
                        f"({src_header!r} vs {target_header!r}); skipped."
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--mode", choices=["stocks", "indices"], default="stocks",
                        help="What to download: 'stocks' (per-stock 1-min) or "
                             "'indices' (VIX + sectoral indices 1-min). "
                             "(default: stocks)")
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
    args = parser.parse_args(argv)

    _load_dotenv()
    _check_kaggle_credentials()

    if not args.config.exists():
        print(f"Config not found: {args.config}", file=sys.stderr)
        return 1

    if args.mode == "stocks":
        dataset = args.dataset or KAGGLE_STOCKS_DATASET
        raw_symbols = load_trade_symbols(args.config)
        aliases = None
        symbol_kind = "trade symbols"
    else:
        dataset = args.dataset or KAGGLE_INDICES_DATASET
        raw_symbols = load_index_symbols(args.config)
        aliases = INDEX_ALIASES
        symbol_kind = "indices"

    if not raw_symbols:
        print(f"No {symbol_kind} found in config.", file=sys.stderr)
        return 1

    print(f"Mode: {args.mode}. Found {len(raw_symbols)} {symbol_kind} in config.")
    norm_to_raw = {normalize_symbol(s): s for s in raw_symbols}

    archive = download_archive(dataset, args.cache, force=args.force)
    found, missing = extract_symbols(
        archive,
        norm_to_raw,
        args.out,
        aliases=aliases,
        member_filter=is_1min_member,
    )

    print()
    print(f"Extracted {len(found)} / {len(norm_to_raw)} {symbol_kind} into {args.out}:")
    for sym, member in found:
        raw = norm_to_raw[sym]
        label = raw if sym == raw else f"{sym} -> {raw}"
        print(f"  {label:<28} <- {member}")

    if missing:
        print()
        print(f"Not found in dataset ({len(missing)}): "
              f"{', '.join(norm_to_raw[s] for s in missing)}")
        print("These may be too new for this dataset version, or named differently.")

    if args.mode == "indices" and INDEX_HISTORY_BACKFILL:
        backfilled = apply_history_backfill(
            archive,
            args.out,
            INDEX_HISTORY_BACKFILL,
            output_names=norm_to_raw,
            aliases=INDEX_ALIASES,
            member_filter=is_1min_member,
        )
        if backfilled:
            print()
            print("Backfilled earlier history from proxy:")
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
