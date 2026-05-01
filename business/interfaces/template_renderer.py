"""
TemplateRenderer port — contract for template engines.

Keeps Jinja (or any other engine) out of business logic. The orchestrator
asks for a rendered string by name + context; how it's rendered is the
adapter's concern.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Mapping


class TemplateRenderer(ABC):
    @abstractmethod
    def render(self, template_name: str, context: Mapping[str, object]) -> str: ...
