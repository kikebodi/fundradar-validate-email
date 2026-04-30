from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

TEMPLATES_DIR: Path = Path(__file__).resolve().parent.parent.parent / "templates"


def build_template_env(templates_dir: Path = TEMPLATES_DIR) -> Environment:
    return Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(enabled_extensions=("html", "xml")),
        undefined=StrictUndefined,
        enable_async=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )
