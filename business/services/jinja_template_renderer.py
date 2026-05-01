"""
Concrete TemplateRenderer backed by Jinja2 with HTML autoescape and
StrictUndefined (a missing variable raises rather than silently rendering
an empty string).
"""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from business.interfaces.template_renderer import TemplateRenderer

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_TEMPLATES_DIR = _PROJECT_ROOT / "templates"


class JinjaTemplateRenderer(TemplateRenderer):
    def __init__(self, templates_dir: Path = DEFAULT_TEMPLATES_DIR) -> None:
        self._env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(enabled_extensions=("html", "xml")),
            undefined=StrictUndefined,
            enable_async=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, template_name: str, context: Mapping[str, object]) -> str:
        return self._env.get_template(template_name).render(**context)
