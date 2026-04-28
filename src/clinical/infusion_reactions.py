from dataclasses import dataclass


@dataclass
class RechallengeAdvice:
    grade: int
    rechallenge: bool
    rate_pct: int | None
    premed_enhance: bool
    switch_agent_to: str | None
    hard_block: bool
    advisory_text: str


def rechallenge_advice(grade: int, config: dict) -> RechallengeAdvice:
    """Return rechallenge guidance for an infusion reaction grade using config.

    Raises ValueError for grades outside 1–4.
    """
    raise NotImplementedError
