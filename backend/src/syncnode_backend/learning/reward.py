"""
SyncNode — deterministic reward signals for workflow trajectories.

These are NOT neural RL rewards. They are deterministic, configurable scores
used to rank recorded workflow trajectories so the system can prefer strategies
that historically verified successfully. No model or policy is trained or
mutated from these numbers; they only inform (never override) strategy ranking,
and any change to production behaviour still requires explicit human promotion.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RewardConfig:
    verified_success: float = 1.0
    no_retry_bonus: float = 0.2
    retry_penalty: float = -0.2
    recovery_penalty: float = -0.5
    verification_failure: float = -1.0
    policy_violation: float = -2.0
    unsafe_side_effect: float = -3.0


DEFAULT_REWARD = RewardConfig()


def step_reward(
    *,
    verification: str,        # PASS | FAIL | STALE | UNAVAILABLE | None
    retries: int = 0,
    recovered: bool = False,
    policy_violation: bool = False,
    unsafe_side_effect: bool = False,
    config: RewardConfig = DEFAULT_REWARD,
) -> float:
    """Deterministic reward for one executed step."""
    r = 0.0
    if unsafe_side_effect:
        return config.unsafe_side_effect
    if policy_violation:
        return config.policy_violation
    if verification == "PASS":
        r += config.verified_success
        if retries == 0 and not recovered:
            r += config.no_retry_bonus
    elif verification in ("FAIL",):
        r += config.verification_failure
    # STALE / UNAVAILABLE / None: neutral-to-slightly-negative via retries.
    if retries > 0:
        r += config.retry_penalty * retries
    if recovered:
        r += config.recovery_penalty
    return round(r, 3)


def trajectory_reward(step_rewards: list[float]) -> float:
    return round(sum(step_rewards), 3)
