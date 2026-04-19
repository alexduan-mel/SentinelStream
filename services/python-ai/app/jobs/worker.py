"""Backward-compatible entrypoint for company analysis worker.

Prefer using `python -m jobs.company_analysis_worker`.
"""

from .company_analysis_worker import *  # noqa: F401,F403
from .company_analysis_worker import main as _main


if __name__ == "__main__":
    raise SystemExit(_main())
