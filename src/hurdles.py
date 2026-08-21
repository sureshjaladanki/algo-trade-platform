"""Pre-registered hurdle declarations for Books C, A, and B. No peek."""

from src.harness import Declaration

# Book C is an accounting identity on the household lot ledger, not a statistical
# bet. σ = 0 so MDE = 0. The 25 bps/yr figure is the C1 exit, not an estimate.
BOOK_C = Declaration(
    book_id="C",
    spec_id="C.location-bands-harvest",
    n=1,
    sigma=0.0,
    hypothesized_effect=25.0,
    unit="bps_per_year",
)

# Observation = one 30–45 DTE SPX put-spread cycle of the sleeve.
# σ matches Blueprint §0.3 (20-year option cycle). Hypothesized effect is the
# $580 net/cycle target on a $50k sleeve (20% of a $250k book) = 116 bps of
# sleeve. Book-level dilution is a weighting step after the test, not the
# observation the MDE applies to.
BOOK_A = Declaration(
    book_id="A",
    spec_id="A.spx-put-spread-20-25d-30-45dte",
    n=240,
    sigma=150.0,
    hypothesized_effect=116.0,
    unit="bps_of_sleeve_per_cycle",
)

# Observation = name-event. n = 6,000/yr × 5 yrs, then a 5× date/sector
# clustering haircut as in Blueprint §0.3. Hypothesized effect is the 100 bps
# gross 20-day drift in the economic hypothesis, not the 40 bps kill threshold.
BOOK_B = Declaration(
    book_id="B",
    spec_id="B.pead-numeric-surprise",
    n=30_000,
    sigma=800.0,
    hypothesized_effect=100.0,
    clustering_haircut=5.0,
    unit="bps_per_event",
)

PUBLISHED_BOOKS: tuple[Declaration, ...] = (BOOK_C, BOOK_A, BOOK_B)


def books_clearing_mde_gate() -> tuple[Declaration, ...]:
    return tuple(book for book in PUBLISHED_BOOKS if book.clears_gate)
