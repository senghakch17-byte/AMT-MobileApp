from pathlib import Path
from app.core.config import settings

ANNOUNCEMENT_DIR = Path(settings.UPLOAD_DIR) / "announcements"


def ensure_upload_dirs() -> None:
    ANNOUNCEMENT_DIR.mkdir(parents=True, exist_ok=True)

def delete_image(url: str) -> None:
    # Path(...).name strips any directory part, so a crafted URL cannot escape ANNOUNCEMENT_DIR
    (ANNOUNCEMENT_DIR / Path(url).name).unlink(missing_ok=True)
