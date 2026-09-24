"""
SyncNode — Inference Profiles.

A typed abstraction that binds a *task class* to a concrete set of local-runtime
inference parameters. Model parameters must not be scattered across .env and
call sites; every model call resolves through exactly one profile.

The values here are grounded in measured benchmarks on the target hardware
(NVIDIA RTX 2050, 4GB VRAM, gemma4:e4b Q4_K_M). See docs/INFERENCE_OPTIMIZATION.md
and docs/INFERENCE_BENCHMARK.md for the evidence behind each choice:

  - num_gpu=99 (full offload) fits the model in VRAM at bounded context and is
    ~3.8x faster than Ollama's conservative auto-offload (8 -> 31 tok/s).
  - The gemma4 sliding-window / shared-KV cache is compact, so context up to
    ~32768 still keeps the whole model GPU-resident. Profiles stay well under
    that for headroom.
  - keep_alive keeps the model warm so successive workflow steps skip the
    ~11-19s cold reload (warm reload measured at 0.01s).
  - temperature=0.0 for machine-to-machine (structured / tool / planner) steps
    maximizes schema validity and determinism; the writer uses a little warmth.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TaskClass(str, Enum):
    """The kind of work a model call performs. Drives profile selection."""

    FAST_SIMPLE = "fast_simple"          # short free-text (writer, summaries)
    FAST_STRUCTURED = "fast_structured"  # small structured objects, tool selection
    NORMAL_REASONING = "normal_reasoning"
    PLANNER = "planner"                  # ExecutionPlan / DAG generation
    VISION = "vision"                    # screenshot / image interpretation


class InferenceProfile(BaseModel):
    """A frozen bundle of local-runtime inference parameters for a task class.

    Only parameters actually supported by the installed Ollama runtime are
    represented. Values map to Ollama chat `options` / top-level fields.
    """

    name: str
    task_class: TaskClass

    # Ollama `options`
    num_ctx: int = Field(description="Context window (Ollama num_ctx).")
    num_gpu: Optional[int] = Field(
        default=99,
        description="GPU layers to offload (Ollama num_gpu). None = auto.",
    )
    max_output_tokens: int = Field(description="Ollama num_predict.")
    temperature: float = 0.0
    top_p: Optional[float] = None

    # Top-level chat fields
    keep_alive: str = "30m"
    thinking: bool = False

    # Client-side deadline (seconds) for the whole request.
    timeout_seconds: int = 120

    def request_overrides(self) -> dict:
        """Return the ModelRequest field overrides implied by this profile.

        Use with ``request.model_copy(update=profile.request_overrides())`` so a
        single profile drives every runtime knob for a call.
        """
        return {
            "num_ctx": self.num_ctx,
            "num_gpu": self.num_gpu,
            "keep_alive": self.keep_alive,
            "max_tokens": self.max_output_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "thinking": self.thinking,
        }


# ------------------------------------------------------------------ #
# Default profile set (measured-optimal for RTX 2050 / gemma4:e4b).    #
# ------------------------------------------------------------------ #

_DEFAULT_PROFILES: dict[TaskClass, InferenceProfile] = {
    # Short free-text generation (e.g. writer.generate_paragraph). A little
    # warmth for natural prose; small output budget keeps it snappy.
    TaskClass.FAST_SIMPLE: InferenceProfile(
        name="fast_simple",
        task_class=TaskClass.FAST_SIMPLE,
        num_ctx=4096,
        num_gpu=99,
        max_output_tokens=512,
        temperature=0.4,
        top_p=0.92,
        keep_alive="30m",
        thinking=False,
        timeout_seconds=90,
    ),
    # Small structured decisions / tool selection. Deterministic, compact.
    # num_ctx raised to 8192 so composite multi-step goals (with enricher context
    # + system prompt + schema hint) never overflow the context window.
    TaskClass.FAST_STRUCTURED: InferenceProfile(
        name="fast_structured",
        task_class=TaskClass.FAST_STRUCTURED,
        num_ctx=12288,
        num_gpu=99,
        max_output_tokens=2048,
        temperature=0.0,
        top_p=1.0,
        keep_alive="30m",
        thinking=False,
        timeout_seconds=120,
    ),
    # General reasoning over accumulated context.
    TaskClass.NORMAL_REASONING: InferenceProfile(
        name="normal_reasoning",
        task_class=TaskClass.NORMAL_REASONING,
        num_ctx=8192,
        num_gpu=99,
        max_output_tokens=1024,
        temperature=0.2,
        top_p=0.9,
        keep_alive="30m",
        thinking=False,
        timeout_seconds=120,
    ),
    # ExecutionPlan / DAG generation. Larger context for intent + tool schemas,
    # larger output budget for the plan, deterministic.
    # num_ctx=16384: complex multi-doc+email goals with full system prompt,
    # schema hint, and enriched intent JSON can exceed 8192 tokens. 16384 keeps
    # the model GPU-resident on 4GB VRAM at Q4_K_M (measured stable).
    # max_output_tokens=6144: a 10-step plan with full postconditions, inputs,
    # and retry_policy JSON is ~4000-5000 tokens. 4096 was too tight for goals
    # like "create 3 docs + open Word + compose Gmail + attach + pause".
    TaskClass.PLANNER: InferenceProfile(
        name="planner",
        task_class=TaskClass.PLANNER,
        num_ctx=16384,
        num_gpu=99,
        max_output_tokens=6144,
        temperature=0.0,
        top_p=1.0,
        keep_alive="30m",
        thinking=False,
        timeout_seconds=240,
    ),
    # Vision / screenshot interpretation. Image tokens dominate prompt-eval, so
    # give a bit more context; keep output modest.
    TaskClass.VISION: InferenceProfile(
        name="vision",
        task_class=TaskClass.VISION,
        num_ctx=8192,
        num_gpu=99,
        max_output_tokens=512,
        temperature=0.0,
        top_p=1.0,
        keep_alive="30m",
        thinking=False,
        timeout_seconds=180,
    ),
}


class InferenceProfileRegistry:
    """Resolves a TaskClass to its InferenceProfile.

    Defaults are the measured-optimal set; callers may override individual
    profiles (e.g. from settings) without touching call sites.
    """

    def __init__(self, profiles: Optional[dict[TaskClass, InferenceProfile]] = None) -> None:
        self._profiles = dict(profiles) if profiles else dict(_DEFAULT_PROFILES)

    def get(self, task_class: TaskClass) -> InferenceProfile:
        profile = self._profiles.get(task_class)
        if profile is None:
            # Fail safe to a deterministic, bounded profile rather than the
            # model's huge defaults.
            return _DEFAULT_PROFILES[TaskClass.FAST_STRUCTURED]
        return profile

    def override(self, task_class: TaskClass, profile: InferenceProfile) -> None:
        self._profiles[task_class] = profile

    def all(self) -> dict[TaskClass, InferenceProfile]:
        return dict(self._profiles)


# Module-level default registry.
profile_registry = InferenceProfileRegistry()
