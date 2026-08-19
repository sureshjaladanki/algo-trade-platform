"""Repository data and log locations."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_DIR = REPO_ROOT / "data" / "GOLDEN"
DERIVED_DIR = REPO_ROOT / "data" / "derived"
LOGS_DIR = REPO_ROOT / "logs"
DOCS_ARCHIVE = REPO_ROOT / "docs" / "archive"
DOCS_NEXT = REPO_ROOT / "docs" / "next"

NIFTY_CSV_NAME = "^NSEI.csv"
DAILY_PANEL_PARQUET = DERIVED_DIR / "daily_panel.parquet"
MCWB_RAW_DIR = REPO_ROOT / "data" / "raw" / "mcwb"
MCWB_MONTHLY_PARQUET = DERIVED_DIR / "mcwb_monthly.parquet"
F1B_CHARTER_PATH = DOCS_NEXT / "f1b-charter.md"
F1B_LOG_PATH = LOGS_DIR / "f1b_ranking.txt"
EVENT_POOL_PARQUET = LOGS_DIR / "f0_event_pool.parquet"
F1_CHARTER_PATH = DOCS_NEXT / "f1-charter.md"
F0_MEMO_PATH = DOCS_ARCHIVE / "f0-event-pool.md"
F1_MEMO_PATH = DOCS_ARCHIVE / "f1-effect-exists.md"
F1_LOG_PATH = LOGS_DIR / "f1_effect_exists.txt"
F1A_CHARTER_PATH = DOCS_NEXT / "f1a-charter.md"
F1A_MEMO_PATH = DOCS_ARCHIVE / "f1a-post-announcement.md"
F1B_MEMO_PATH = DOCS_ARCHIVE / "f1b-pre-announcement.md"
F1C_MEMO_PATH = DOCS_ARCHIVE / "f1c-reversal.md"
F1_SERIES_LOG_PATH = LOGS_DIR / "f1_series.txt"
