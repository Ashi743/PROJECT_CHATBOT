"""Central path constants for the application."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
DATABASES_DIR = DATA_DIR / "databases"
CHROMA_DIR = DATA_DIR / "chroma_db"
PLOTS_DIR = DATA_DIR / "plots"

for d in (UPLOADS_DIR, DATABASES_DIR, CHROMA_DIR, PLOTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    print(f"[OK] CHROMA_DIR={CHROMA_DIR}")
    assert CHROMA_DIR.name == "chroma_db"
    assert CHROMA_DIR.parent.name == "data"
