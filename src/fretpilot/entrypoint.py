"""Backward-compatible console entry point.

All command behavior lives in :mod:`fretpilot.cli`; prototype sidecars are part
of the prototype pipeline rather than a command-line post-processing hook.
"""

from fretpilot.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
