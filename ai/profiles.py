from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AIProfile:
    economy: float
    military: float
    technology: float
    diplomacy: float
    aggression: float
    debt_caution: float


DEFAULT_PROFILE = AIProfile(0.55, 0.45, 0.35, 0.35, 0.18, 0.62)

PROFILES = {
    "USA": AIProfile(0.85, 0.52, 0.55, 0.90, 0.08, 0.82),
    "Russia": AIProfile(0.42, 0.92, 0.38, 0.26, 0.58, 0.45),
    "China": AIProfile(0.95, 0.62, 0.64, 0.38, 0.18, 0.72),
    "Japan": AIProfile(0.58, 0.36, 0.95, 0.58, 0.06, 0.86),
    "Germany": AIProfile(0.92, 0.35, 0.70, 0.72, 0.05, 0.88),
    "France": AIProfile(0.68, 0.46, 0.62, 0.70, 0.12, 0.78),
    "UK": AIProfile(0.68, 0.50, 0.70, 0.78, 0.10, 0.80),
    "India": AIProfile(0.76, 0.68, 0.45, 0.34, 0.24, 0.62),
    "Turkey": AIProfile(0.50, 0.68, 0.34, 0.36, 0.32, 0.52),
    "Brazil": AIProfile(0.78, 0.32, 0.35, 0.48, 0.08, 0.64),
    "Australia": AIProfile(0.70, 0.42, 0.62, 0.72, 0.06, 0.82),
}


def profile_for(country_name: str) -> AIProfile:
    return PROFILES.get(country_name, DEFAULT_PROFILE)
