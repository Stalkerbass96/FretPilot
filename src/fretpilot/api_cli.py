"""Command-line entry point for the local FretPilot API."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

import uvicorn


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the FretPilot local API.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args(argv)
    uvicorn.run(
        "fretpilot.api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
