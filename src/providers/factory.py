from __future__ import annotations

from pathlib import Path
from typing import Any

from providers.base import JSONModelClient


def create_client(spec: dict[str, Any], root: Path) -> JSONModelClient:
    provider = str(spec.get("provider", "")).lower()
    if provider == "codex_cli":
        from providers.codex_cli_client import CodexCLIJSONClient

        return CodexCLIJSONClient(spec, root)
    if provider == "vertex":
        from providers.vertex_client import VertexJSONClient

        return VertexJSONClient(spec, root)
    if provider == "ollama":
        from providers.ollama_client import OllamaJSONClient

        return OllamaJSONClient(spec, root)
    raise ValueError(f"Unsupported provider: {provider!r}")
