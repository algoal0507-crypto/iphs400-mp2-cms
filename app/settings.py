"""Configuration, read from the environment (never hard-code secrets)."""
from __future__ import annotations

import os
from collections.abc import MutableMapping
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_env_file(path: Path, environ: MutableMapping[str, str] = os.environ) -> None:
    """Copy KEY=VALUE lines from `path` into `environ`, keeping any value already set.

    `uv run` does not read `.env`, so the app does it. A variable that is already
    in the environment (the shell, `--env-file`, a test) wins over the file.
    """
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.removeprefix("export ").partition("=")
        key, value = key.strip(), value.strip()
        if not sep or not key.isidentifier():
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        else:
            value = value.split(" #", 1)[0].rstrip()
        environ.setdefault(key, value)


load_env_file(ROOT / ".env")  # must run before the os.environ reads below
TEMPLATES = ROOT / "templates"
SITE = ROOT / "site"
ASSETS = ROOT / "assets"  # assets/images/web/ is copied into site/images/ by `cms publish`
INSTAGRAM_URL = "https://www.instagram.com/tacoslaoncemil/"

SECRET_KEY = os.environ.get("CMS_SECRET_KEY", "dev-only-not-for-production")
DATABASE_PATH = ROOT / os.environ.get("CMS_DATABASE", "cms.db")  # a relative path means "inside the repo"
SITE_TITLE = os.environ.get("CMS_SITE_TITLE", "My CMS")
# Set this to your Pages URL once you deploy, e.g.
# https://yourname.github.io/iphs400-mp2-cms/
BASE_PATH = os.environ.get("CMS_BASE_PATH", "")
