"""Copy model artifacts into the backend service for a Vercel build."""

import shutil
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent


def stage(name: str) -> None:
    source = REPO / name
    target = BACKEND / name
    if not source.is_dir():
        raise SystemExit(f"Missing {source}")
    if source.resolve() == target.resolve():
        return
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)


if __name__ == "__main__":
    stage("ml")
    stage("datasets")
