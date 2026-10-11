from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from common import extract_json_object
from providers.base import ModelResponseError, aggregate_attempts, attempt_record


def find_codex_executable(configured: str = "codex") -> str | None:
    """Find a PATH installation or the CLI bundled with the newest VS Code extension."""
    direct = Path(configured).expanduser()
    if direct.is_file():
        return str(direct.resolve())
    executable = shutil.which(configured)
    if executable:
        return executable
    if platform.system() != "Windows" or configured != "codex":
        return None
    candidates: list[Path] = []
    for extension_root in (Path.home() / ".vscode" / "extensions", Path.home() / ".vscode-insiders" / "extensions"):
        candidates.extend(
            extension_root.glob("openai.chatgpt-*/bin/windows-x86_64/codex.exe")
        )
    existing = [path for path in candidates if path.is_file()]
    return str(max(existing, key=lambda path: path.stat().st_mtime)) if existing else None


def codex_login_status(executable: str) -> tuple[bool, str]:
    """Require ChatGPT subscription auth and reject usage-based API-key auth."""
    try:
        result = subprocess.run(
            [executable, "login", "status"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"Could not check Codex login: {type(exc).__name__}"
    status = " ".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
    normalized = status.lower()
    is_chatgpt = result.returncode == 0 and "logged in" in normalized and "chatgpt" in normalized
    if "api key" in normalized:
        return False, "Codex is using API-key authentication; sign in with ChatGPT instead"
    return is_chatgpt, status or "Codex is not logged in"


def codex_model_capabilities(executable: str) -> dict[str, dict[str, Any]]:
    """Read the installed CLI's bundled model/effort catalog without making a model call."""
    try:
        result = subprocess.run(
            [executable, "debug", "models", "--bundled"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError(f"Could not read Codex model catalog: {type(exc).__name__}") from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "Codex model catalog failed").strip()
        raise RuntimeError(detail[-2000:])
    try:
        raw_models = json.loads(result.stdout)["models"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise RuntimeError("Codex model catalog was not valid JSON") from exc

    capabilities: dict[str, dict[str, Any]] = {}
    for item in raw_models:
        if not isinstance(item, dict) or not str(item.get("slug", "")).strip():
            continue
        slug = str(item["slug"])
        efforts = tuple(
            str(level["effort"])
            for level in item.get("supported_reasoning_levels", [])
            if isinstance(level, dict) and str(level.get("effort", "")).strip()
        )
        capabilities[slug] = {
            "default_reasoning_effort": str(item.get("default_reasoning_level", "")),
            "supported_reasoning_efforts": efforts,
            "description": str(item.get("description", "")),
        }
    return capabilities


def validate_codex_model_effort(
    executable: str,
    model: str,
    reasoning_effort: str,
) -> dict[str, Any]:
    """Fail before inference if a requested model/effort is absent from the local CLI."""
    capabilities = codex_model_capabilities(executable)
    if model not in capabilities:
        raise ValueError(
            f"Codex model {model!r} is unavailable; local catalog contains "
            f"{sorted(capabilities)}"
        )
    supported = capabilities[model]["supported_reasoning_efforts"]
    if reasoning_effort not in supported:
        raise ValueError(
            f"Reasoning effort {reasoning_effort!r} is unavailable for {model}; "
            f"supported: {list(supported)}"
        )
    return capabilities[model]


def _event_metadata(
    stdout: str,
) -> tuple[str | None, str | None, dict[str, int | None]]:
    """Extract stable identifiers and usage from the CLI JSONL event stream."""
    thread_id: str | None = None
    response_model: str | None = None
    usage: dict[str, int | None] = {
        "input_tokens": None,
        "cached_input_tokens": None,
        "output_tokens": None,
        "reasoning_tokens": None,
        "total_tokens": None,
    }
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "thread.started":
            thread_id = str(event.get("thread_id") or event.get("thread", {}).get("id") or "") or None
        if event.get("type") == "model.rerouted":
            response_model = str(event.get("to_model") or event.get("toModel") or "") or None
        if event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict):
            raw_usage = event["usage"]

            def optional_int(name: str) -> int | None:
                value = raw_usage.get(name)
                return value if isinstance(value, int) else None

            usage = {
                "input_tokens": optional_int("input_tokens"),
                "cached_input_tokens": optional_int("cached_input_tokens"),
                "output_tokens": optional_int("output_tokens"),
                "reasoning_tokens": (
                    optional_int("reasoning_output_tokens")
                    if optional_int("reasoning_output_tokens") is not None
                    else optional_int("reasoning_tokens")
                ),
                "total_tokens": optional_int("total_tokens"),
            }
            if usage["total_tokens"] is None:
                input_tokens = usage["input_tokens"]
                output_tokens = usage["output_tokens"]
                if input_tokens is not None and output_tokens is not None:
                    usage["total_tokens"] = input_tokens + output_tokens
    return thread_id, response_model, usage


class CodexCLIJSONClient:
    """Structured Codex agent calls authenticated by a local ChatGPT subscription."""

    provider = "codex_cli"

    def __init__(self, spec: dict[str, Any], root: Path) -> None:
        del root  # Deliberately do not expose the repository as the Codex working directory.
        executable = find_codex_executable(str(spec.get("executable", "codex")))
        if not executable:
            raise RuntimeError("Codex CLI is not installed or is not on PATH")
        ready, detail = codex_login_status(executable)
        if not ready:
            raise RuntimeError(
                f"ChatGPT-authenticated Codex CLI is required: {detail}. "
                "Run `codex login`, choose ChatGPT sign-in, then retry."
            )
        self.executable = executable
        self.model = str(spec["model"])
        self.reasoning_effort = str(spec.get("reasoning_effort", "medium"))
        self.timeout_seconds = int(spec.get("timeout_seconds", 600))
        self.model_capability = validate_codex_model_effort(
            executable,
            self.model,
            self.reasoning_effort,
        )
        # KNOWN LIMITATION (see claude_paid_analysis.md #10): `codex exec` exposes no
        # temperature or seed parameter, unlike the Vertex client's pinned temperature=0.0.
        # Only `reasoning_effort` is controllable here, so Codex-model rows cannot be assumed
        # deterministic across repeated runs the way Gemini rows can. `_base_metadata` below
        # stamps this on every response row so it is visible in the saved data, not just in docs.

    def json(
        self,
        prompt: str,
        *,
        schema: dict[str, Any],
        schema_name: str,
        retries: int = 3,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        last_error: Exception | None = None
        attempts: list[dict[str, Any]] = []
        for attempt in range(1, retries + 1):
            started = time.perf_counter()
            try:
                with tempfile.TemporaryDirectory(prefix="pubmedqa-codex-") as temp_value:
                    temp_dir = Path(temp_value)
                    schema_path = temp_dir / "response.schema.json"
                    output_path = temp_dir / "final-response.json"
                    schema_path.write_text(json.dumps(schema), encoding="utf-8")
                    command = [
                        self.executable,
                        "exec",
                        "--ephemeral",
                        "--skip-git-repo-check",
                        "--ignore-user-config",
                        "--ignore-rules",
                        "--sandbox",
                        "read-only",
                        "--model",
                        self.model,
                        "--config",
                        f'model_reasoning_effort="{self.reasoning_effort}"',
                        "--config",
                        'approval_policy="never"',
                        "--json",
                        "--output-schema",
                        str(schema_path),
                        "--output-last-message",
                        str(output_path),
                        "-",
                    ]
                    environment = os.environ.copy()
                    # Never let an inherited Platform key turn this into usage-based API access.
                    environment.pop("OPENAI_API_KEY", None)
                    instruction = (
                        "Complete this one evaluation item using only the text in this prompt. "
                        "Do not use tools, files, web search, memory, or outside knowledge. "
                        f"Return only a JSON object conforming to schema {schema_name}.\n\n{prompt}"
                    )
                    result = subprocess.run(
                        command,
                        input=instruction,
                        cwd=temp_dir,
                        env=environment,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        timeout=self.timeout_seconds,
                        check=False,
                    )
                    elapsed = time.perf_counter() - started
                    thread_id, response_model, usage = _event_metadata(result.stdout)
                    if result.returncode != 0:
                        diagnostic_parts = [
                            part.strip()
                            for part in (result.stderr, result.stdout)
                            if part and part.strip()
                        ]
                        detail = "\n".join(diagnostic_parts) or "Codex CLI failed"
                        detail = detail[-6000:]
                        attempts.append(attempt_record(
                            attempt,
                            "cli_error",
                            elapsed,
                            response_id=thread_id,
                            detail=detail,
                            **usage,
                        ))
                        raise RuntimeError(detail)
                    text = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
                    try:
                        payload = extract_json_object(text)
                    except Exception:
                        attempts.append(attempt_record(
                            attempt,
                            "invalid_json",
                            elapsed,
                            response_id=thread_id,
                            detail="Codex final message did not match the expected JSON object.",
                        ))
                        raise
                    attempts.append(attempt_record(
                        attempt,
                        "success",
                        elapsed,
                        response_id=thread_id,
                        **usage,
                    ))
                    return payload, {
                        **self._base_metadata(schema_name),
                        "response_model": response_model or self.model,
                        **aggregate_attempts(attempts),
                        "response_status": "ok",
                        "safety_reason": "",
                        "raw_response": text,
                    }
            except subprocess.TimeoutExpired as exc:
                last_error = exc
                if not attempts or attempts[-1].get("attempt") != attempt:
                    attempts.append(attempt_record(
                        attempt,
                        "timeout",
                        time.perf_counter() - started,
                        detail=f"Exceeded {self.timeout_seconds} seconds",
                    ))
            except Exception as exc:
                last_error = exc
                if not attempts or attempts[-1].get("attempt") != attempt:
                    attempts.append(attempt_record(
                        attempt,
                        "cli_error",
                        time.perf_counter() - started,
                        detail=f"{type(exc).__name__}: {exc}",
                    ))
            if attempt < retries:
                time.sleep(2**attempt)
        metadata = {
            **self._base_metadata(schema_name),
            **aggregate_attempts(attempts),
            "response_status": "error",
            "safety_reason": "",
            "raw_response": "",
        }
        raise ModelResponseError(
            f"Codex CLI request failed after {retries} attempts: {last_error}",
            category="request_failed",
            metadata=metadata,
        ) from last_error

    def _base_metadata(self, schema_name: str) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "requested_model": self.model,
            "response_model": self.model,
            "reasoning_effort": self.reasoning_effort,
            "supported_reasoning_efforts": list(
                getattr(self, "model_capability", {}).get("supported_reasoning_efforts", ())
            ),
            "response_schema": schema_name,
            "structured_output": "codex_exec_output_schema",
            "execution_backend": "codex_cli_on_pipeline_host",
            "host_platform": platform.system().lower(),
            "timing_scope": "end_to_end_codex_cli_wall_clock",
            "pure_model_inference_seconds": None,
            "billing_mode": "chatgpt_subscription",
            "temperature": None,
            "seed": None,
            "determinism_note": "codex_cli exposes no temperature/seed; only reasoning_effort is pinned",
        }
