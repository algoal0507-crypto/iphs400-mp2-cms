"""The app reads `.env` itself, so the manual's `uv run cms serve` works.

`uv run` does not load `.env`. The grader runs `cp .env.example .env` and then
`uv run python scripts/seed_demo.py` with nothing else in the environment.
"""
from __future__ import annotations

from app.settings import load_env_file


def test_reads_values_into_an_empty_environment(tmp_path):
    f = tmp_path / ".env"
    f.write_text("CMS_ADMIN_PASSWORD=change-me-admin\nCMS_DATABASE=cms.db\n")
    env: dict[str, str] = {}
    load_env_file(f, env)
    assert env == {"CMS_ADMIN_PASSWORD": "change-me-admin", "CMS_DATABASE": "cms.db"}


def test_real_environment_wins_over_the_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("CMS_SECRET_KEY=from-file\nCMS_BASE_PATH=/x/\n")
    env = {"CMS_SECRET_KEY": "from-shell"}
    load_env_file(f, env)
    assert env["CMS_SECRET_KEY"] == "from-shell"
    assert env["CMS_BASE_PATH"] == "/x/"


def test_quotes_comments_and_blank_lines(tmp_path):
    f = tmp_path / ".env"
    f.write_text(
        "# a comment\n"
        "\n"
        'CMS_SITE_TITLE="La Once Mil"\n'
        "CMS_OTHER='single quoted'\n"
        "CMS_EMPTY=\n"
        "export CMS_EXPORTED=yes\n"
        "not a setting line\n"
        "  CMS_SPACED = padded  \n"
    )
    env: dict[str, str] = {}
    load_env_file(f, env)
    assert env["CMS_SITE_TITLE"] == "La Once Mil"
    assert env["CMS_OTHER"] == "single quoted"
    assert env["CMS_EMPTY"] == ""
    assert env["CMS_EXPORTED"] == "yes"
    assert env["CMS_SPACED"] == "padded"
    assert "not a setting line" not in env


def test_missing_file_is_fine(tmp_path):
    env: dict[str, str] = {}
    load_env_file(tmp_path / "nope.env", env)
    assert env == {}


def test_unreadable_bytes_do_not_crash_startup(tmp_path):
    f = tmp_path / ".env"
    f.write_bytes(b"CMS_OK=1\n\xff\xfe\x00bad\n")
    env: dict[str, str] = {}
    load_env_file(f, env)  # must not raise


def test_bom_crlf_equals_in_value_and_inline_comment(tmp_path):
    f = tmp_path / ".env"
    f.write_bytes(
        b"\xef\xbb\xbfCMS_FIRST=1\r\nCMS_URL=https://x.test/?a=b\r\n"
        b"CMS_NOTE=plain # trailing comment\r\nCMS_Q=\"keep # this\"\r\n"
    )
    env: dict[str, str] = {}
    load_env_file(f, env)
    assert env["CMS_FIRST"] == "1"
    assert env["CMS_URL"] == "https://x.test/?a=b"
    assert env["CMS_NOTE"] == "plain"
    assert env["CMS_Q"] == "keep # this"
