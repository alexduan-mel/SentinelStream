"""Backward-compatible entrypoint for market analysis worker.

Prefer using `python -m jobs.market_analysis_worker`.
"""

from .market_analysis_worker import *  # noqa: F401,F403
from .market_analysis_worker import main as _main


if __name__ == "__main__":
    raise SystemExit(_main())
