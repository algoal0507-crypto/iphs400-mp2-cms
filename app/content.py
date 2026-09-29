"""Markdown rendering and HTML sanitization for user-written content.

`_md` is built with html=False, so raw HTML in Markdown source is always
escaped as literal text on render — that is the actual security boundary,
not string-scrubbing. `sanitize_markdown_source` is defense in depth on top
of that: it strips <script>/<style> blocks and on* event attributes from the
stored source with plain regexes rather than an HTML sanitizer, because
running Markdown source through an HTML sanitizer (e.g. nh3.clean) HTML-
entity-encodes ordinary characters like "&" — corrupting the text on every
save/reload round trip instead of just neutralizing danger.
"""
from __future__ import annotations

import re

import nh3
from markdown_it import MarkdownIt

_md = MarkdownIt("commonmark", {"html": False})

_SCRIPT_RE = re.compile(r"<script\b[^>]*>.*?</script\s*>", re.IGNORECASE | re.DOTALL)
_STYLE_RE = re.compile(r"<style\b[^>]*>.*?</style\s*>", re.IGNORECASE | re.DOTALL)
_EVENT_ATTR_RE = re.compile(r"""\son\w+\s*=\s*("[^"]*"|'[^']*'|[^\s>]+)""", re.IGNORECASE)


def sanitize_markdown_source(text: str) -> str:
    text = _SCRIPT_RE.sub("", text)
    text = _STYLE_RE.sub("", text)
    text = _EVENT_ATTR_RE.sub("", text)
    return text


def render_markdown(text: str) -> str:
    return nh3.clean(_md.render(text))
