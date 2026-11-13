"""Build dist/stackwatch.tgz from splunk_app/stackwatch (REQ-6 AC2)."""

import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "splunk_app" / "stackwatch"
OUT = ROOT / "dist" / "stackwatch.tgz"
SKIP = {".DS_Store", "__pycache__", "local", "local.meta"}
REQUIRED = ["default/app.conf", "metadata/default.meta"]


def _clean(info: tarfile.TarInfo) -> tarfile.TarInfo | None:
    if SKIP & set(Path(info.name).parts):
        return None
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    return info


def build(app: Path = APP, out: Path = OUT) -> Path:
    missing = [r for r in REQUIRED if not (app / r).is_file()]
    if missing:
        raise FileNotFoundError(f"app incomplete, missing: {', '.join(missing)}")
    out.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(out, "w:gz") as tar:
        tar.add(app, arcname=app.name, filter=_clean)
    return out


def main() -> None:
    try:
        print(f"built {build()}")
    except FileNotFoundError as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()
