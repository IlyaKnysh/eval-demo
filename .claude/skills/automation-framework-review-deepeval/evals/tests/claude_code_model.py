"""DeepEval judge model backed by the local Claude Code CLI.

Routes GEval's LLM-as-judge calls through `claude -p` instead of a metered
provider API key, so grading rides on the existing Claude Code session/
subscription. Each call is a fresh, tool-less, non-interactive `claude`
invocation — no file/bash access, no conversation state carried between
calls.

Requires the `claude` CLI on PATH and already authenticated (interactively,
once, via `claude` login) outside of this eval run.
"""

import asyncio
import json
import re
import shutil
import subprocess

from deepeval.models.base_model import DeepEvalBaseLLM

DEFAULT_TIMEOUT_SECONDS = 180
MAX_JSON_RETRIES = 2

# The field spec must live in --system-prompt, not the user prompt: appending
# a raw JSON schema (or even a plain-English field list) to the user prompt
# was observed to make Claude Code answer in prose ~100% of the time despite
# an otherwise-strict system prompt, apparently because the model treats it
# as more conversational content to respond to rather than a format
# constraint. Putting the same field spec in the system prompt instead was
# 100% reliable across repeated trials.
def _json_system_prompt(schema) -> str:
    fields = schema.model_json_schema().get("properties", {})
    field_desc = ", ".join(
        "%s (%s)" % (name, spec.get("type", "any")) for name, spec in fields.items()
    )
    return (
        "You are a strict JSON API used for LLM-as-judge grading. Respond "
        "with ONLY a single valid JSON object with exactly these fields: "
        "%s. Never include markdown, code fences, or any text outside the "
        "JSON object." % field_desc
    )


class ClaudeCodeModel(DeepEvalBaseLLM):
    def __init__(self, model: str = "sonnet", timeout: int = DEFAULT_TIMEOUT_SECONDS):
        self.timeout = timeout
        # On Windows, `claude` resolves to a .cmd shim that subprocess.run
        # won't execute via plain PATH lookup with shell=False; resolving the
        # full path first works on every platform.
        self.cli_path = shutil.which("claude")
        if self.cli_path is None:
            raise RuntimeError(
                "claude CLI not found on PATH. Install/login Claude Code "
                "before running this eval suite."
            )
        super().__init__(model)

    def load_model(self):
        return self

    def _run(self, prompt: str, system_prompt: str = None) -> str:
        # The prompt is piped via stdin rather than passed as a positional
        # argument: a long prompt (a full review document plus grading
        # criteria easily runs several KB) passed as a Windows argv entry was
        # observed to arrive at the model truncated/empty ("no criteria and
        # no output were included"), while the same content piped via stdin
        # arrived intact every time.
        args = [
            self.cli_path,
            "-p",
            "--output-format",
            "text",
            "--tools",
            "",
            "--model",
            self.name,
        ]
        if system_prompt:
            args += ["--system-prompt", system_prompt]
        result = subprocess.run(
            args,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=self.timeout,
            encoding="utf-8",
        )
        if result.returncode != 0:
            raise RuntimeError(
                "claude CLI exited %d: %s" % (result.returncode, result.stderr.strip())
            )
        return result.stdout.strip()

    def generate(self, prompt: str, schema=None) -> str:
        if schema is None:
            return self._run(prompt)

        system_prompt = _json_system_prompt(schema)
        required_fields = list(schema.model_json_schema().get("properties", {}))
        last_output = None
        for _ in range(MAX_JSON_RETRIES + 1):
            text = _strip_code_fence(self._run(prompt, system_prompt=system_prompt))
            if _looks_like_json_object(text, required_fields=required_fields):
                return text
            last_output = text
        return last_output

    async def a_generate(self, prompt: str, schema=None) -> str:
        # generate() blocks on subprocess.run, which would otherwise
        # serialize every metric's CLI call behind the others despite
        # deepeval gathering them "concurrently" (they all fight over the
        # same event loop thread). Running it in a worker thread lets the
        # CLI invocations for a test case's several metrics actually overlap.
        return await asyncio.to_thread(self.generate, prompt, schema=schema)

    def get_model_name(self) -> str:
        return "claude-code-cli:%s" % self.name


def _strip_code_fence(text: str) -> str:
    match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    return match.group(1) if match else text


def _looks_like_json_object(text: str, required_fields=None) -> bool:
    stripped = text.strip()
    if not (stripped.startswith("{") and stripped.endswith("}")):
        return False
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return False
    if not isinstance(parsed, dict):
        return False
    # Syntactically valid JSON that's missing a field the caller's schema
    # requires (e.g. `{"reason": "..."}` with no `score`) used to pass this
    # check and only blow up two frames later, inside deepeval's own
    # extract_json lambda (a bare `d["score"]` with no fallback) — outside
    # this retry loop, so it surfaced as an unrecoverable KeyError instead of
    # a retry. Checking required fields here keeps the retry loop the single
    # place that decides whether a response is usable.
    if required_fields and not all(field in parsed for field in required_fields):
        return False
    return True
