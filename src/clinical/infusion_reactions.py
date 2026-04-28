"""Infusion reaction rechallenge rules (US-028).

Pure functions — no DB or Tk imports. All rechallenge policy is read from
the config dict; nothing is hardcoded here.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RechallengeAdvice:
    grade: int
    rechallenge: bool
    rate_pct: Optional[int]
    premed_enhance: bool
    switch_agent_to: Optional[str]
    hard_block: bool
    advisory_text: str


def rechallenge_advice(grade: int, config: dict) -> RechallengeAdvice:
    """Return rechallenge guidance for an infusion reaction of the given grade.

    config may be the full toxicity section dict or the infusion_reactions sub-dict.
    Raises ValueError for grades outside 1–4.
    """
    if not isinstance(grade, int) or not (1 <= grade <= 4):
        raise ValueError(f"severity_grade must be an integer 1–4, got {grade!r}")

    reactions_cfg = config.get('infusion_reactions', config)
    policy = reactions_cfg.get('rechallenge_policy', {})

    entry = policy.get(grade)
    if entry is None:
        raise ValueError(f"No rechallenge_policy entry for grade {grade} in config")

    # entry may be a Pydantic model or a plain dict
    if hasattr(entry, 'rechallenge'):
        rechallenge   = entry.rechallenge
        rate_pct      = entry.rate_pct
        premed        = entry.premed_enhance
        switch_to     = entry.switch_agent_to
        hard_block    = entry.hard_block
    else:
        rechallenge   = entry['rechallenge']
        rate_pct      = entry.get('rate_pct')
        premed        = entry.get('premed_enhance', False)
        switch_to     = entry.get('switch_agent_to')
        hard_block    = entry.get('hard_block', False)

    advisory_text = _build_advisory(grade, rechallenge, rate_pct, premed, switch_to, hard_block)

    return RechallengeAdvice(
        grade=grade,
        rechallenge=rechallenge,
        rate_pct=rate_pct,
        premed_enhance=premed,
        switch_agent_to=switch_to,
        hard_block=hard_block,
        advisory_text=advisory_text,
    )


def _build_advisory(
    grade: int,
    rechallenge: bool,
    rate_pct: Optional[int],
    premed_enhance: bool,
    switch_agent_to: Optional[str],
    hard_block: bool,
) -> str:
    if not rechallenge:
        parts = ["Do not rechallenge with this agent."]
        if switch_agent_to:
            agent = switch_agent_to.replace('_', ' ')
            parts.append(f"Switch to {agent}.")
        if hard_block:
            parts.append("Hard block: this grade prohibits re-exposure (Sprint 8 enforcement).")
        return " ".join(parts)

    parts = []
    if rate_pct is not None:
        parts.append(f"May rechallenge at {rate_pct}% infusion rate.")
    if premed_enhance:
        parts.append("Enhance premedication before rechallenge.")
    return " ".join(parts) if parts else "May rechallenge."
