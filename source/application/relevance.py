from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from importlib import import_module
from pathlib import Path

JsonValue = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]

_SPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True, slots=True)
class RelevanceResult:
    score: int
    is_core: bool
    matches: tuple[str, ...] = ()

    @property
    def matched(self) -> list[str]:
        return list(self.matches)

    def as_dict(self) -> dict[str, int | bool | list[str]]:
        return {"score": self.score, "is_core": self.is_core, "matched": self.matched}


def _as_dict(value: JsonValue) -> dict[str, JsonValue]:
    if isinstance(value, dict):
        return value
    return {}


def _as_list(value: JsonValue) -> list[JsonValue]:
    if isinstance(value, list):
        return value
    return []


def _str_list(value: JsonValue) -> list[str]:
    return [item for item in _as_list(value) if isinstance(item, str)]


def _int_value(value: JsonValue, default: int) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default


def _dedupe(items: list[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(item for item in items if item))


def _compact(text: str) -> str:
    return _SPACE_RE.sub("", text)


class RelevanceScorer:
    def __init__(self, config: dict[str, JsonValue]):
        self.threshold = _int_value(config.get("threshold"), 5)
        self._site_score = self._load_site_scores(_as_dict(config.get("source_tiers")))
        self._category_bonus = {
            key: _int_value(value, 0)
            for key, value in _as_dict(config.get("category_bonus")).items()
        }

        weights = _as_dict(config.get("relevance_weights"))
        self._legal_score = _int_value(weights.get("legal"), 5)
        self._policy_score = _int_value(weights.get("policy"), 4)
        self._support_score = _int_value(weights.get("support"), 2)
        self._action_bonus = _int_value(weights.get("action_bonus"), 1)

        keyword_score = _as_dict(config.get("keyword_score"))
        self._legacy_core_score = _int_value(keyword_score.get("core"), 4)
        self._legacy_support_score = _int_value(keyword_score.get("support"), 2)

        penalties = _as_dict(config.get("penalties"))
        self._negative_penalty = _int_value(penalties.get("negative"), -3)
        self._region_penalty = _int_value(penalties.get("region"), -2)
        self._no_topic = _int_value(penalties.get("no_topic"), -99)

        committee = _as_dict(config.get("committee_pass_bonus"))
        self._committee_bonus = _int_value(committee.get("score"), 1)
        self._committee_markers = _str_list(committee.get("markers"))

        criteria = _as_dict(config.get("criteria"))
        self._legal_keywords = _str_list(criteria.get("legal_keywords"))
        self._legal_aliases = {
            key: value
            for key, value in _as_dict(criteria.get("legal_aliases")).items()
            if isinstance(value, str)
        }
        self._policy_keywords = _str_list(criteria.get("policy_keywords"))
        self._support_keywords = _str_list(
            criteria.get("support_keywords") or config.get("support_keywords"),
        )
        self._action_markers = _str_list(criteria.get("action_markers"))
        self._negative_keywords = _str_list(config.get("negative_keywords"))
        self._region_keywords = _str_list(config.get("region_keywords"))
        self._region_exempt = _str_list(config.get("region_exempt_markers"))
        self._negative_exempt = _str_list(criteria.get("negative_exempt_markers"))
        self._context_rules = {
            key: _str_list(value)
            for key, value in _as_dict(criteria.get("context_required")).items()
        }
        self._institution_keywords = _str_list(criteria.get("institution_keywords"))
        self._institution_context = _str_list(criteria.get("institution_context"))
        self._grouped_config = bool(self._legal_keywords or self._policy_keywords)

        self._legacy_core = _str_list(config.get("core_keywords"))
        self._legacy_support = _str_list(config.get("support_keywords"))

    @staticmethod
    def _load_site_scores(tiers: dict[str, JsonValue]) -> dict[str, int]:
        site_scores: dict[str, int] = {}
        for tier in tiers.values():
            tier_map = _as_dict(tier)
            score = _int_value(tier_map.get("score"), 0)
            for name in _str_list(tier_map.get("sites")):
                site_scores[name] = score
        return site_scores

    @staticmethod
    def _any(text: str, words: list[str]) -> bool:
        return any(word and word in text for word in words)

    def _hits(self, title: str, words: list[str]) -> tuple[str, ...]:
        compact_title = _compact(title)
        hits = [
            word
            for word in words
            if word and (word in title or _compact(word) in compact_title)
        ]
        return _dedupe(hits)

    def _legal_hits(self, title: str) -> tuple[str, ...]:
        compact_title = _compact(title)
        hits = list(self._hits(title, self._legal_keywords))
        for alias, canonical in self._legal_aliases.items():
            if alias in title or _compact(alias) in compact_title:
                hits.append(canonical)
        return self._apply_context_rules(title, _dedupe(hits))

    def _policy_hits(self, title: str) -> tuple[str, ...]:
        hits = self._hits(title, self._policy_keywords)
        contextual = self._apply_context_rules(title, hits)
        if not self._any(title, self._institution_keywords):
            return contextual
        if self._any(title, self._institution_context):
            return _dedupe(list(contextual) + list(self._hits(title, self._institution_keywords)))
        return contextual

    def _apply_context_rules(self, title: str, hits: tuple[str, ...]) -> tuple[str, ...]:
        kept: list[str] = []
        for hit in hits:
            contexts = self._context_rules.get(hit, [])
            if not contexts or self._any(title, contexts):
                kept.append(hit)
        return _dedupe(kept)

    def _legacy_score(self, title: str, category: str, site_name: str) -> RelevanceResult:
        matched_core = self._hits(title, self._legacy_core)
        has_support = self._any(title, self._legacy_support)
        if not (matched_core or has_support):
            return RelevanceResult(score=self._no_topic, is_core=False)

        score = self._site_score.get(site_name, 0)
        score += self._category_bonus.get(category, 0)
        score += self._legacy_core_score if matched_core else self._legacy_support_score
        score = self._apply_common_adjustments(score, title, matched_core)
        return RelevanceResult(score=score, is_core=score >= self.threshold, matches=matched_core[:4])

    def _apply_common_adjustments(
        self,
        score: int,
        title: str,
        matched: tuple[str, ...],
    ) -> int:
        if self._any(title, self._committee_markers):
            score += self._committee_bonus
        if self._any(title, self._negative_keywords) and not self._negative_exempt_applies(
            title,
            matched,
        ):
            score += self._negative_penalty
        if self._any(title, self._region_keywords) and not self._region_exempt_applies(title, matched):
            score += self._region_penalty
        return score

    def _negative_exempt_applies(self, title: str, matched: tuple[str, ...]) -> bool:
        return bool(matched) or self._any(title, self._negative_exempt)

    def _region_exempt_applies(self, title: str, matched: tuple[str, ...]) -> bool:
        return bool(matched) or self._any(title, self._region_exempt) or self._any(
            title,
            self._action_markers,
        )

    def score(self, title: str, category: str = "", site_name: str = "") -> RelevanceResult:
        title = title or ""
        if not self._grouped_config:
            return self._legacy_score(title, category, site_name)

        legal_hits = self._legal_hits(title)
        policy_hits = self._policy_hits(title)
        support_hits = self._hits(title, self._support_keywords)
        if not (legal_hits or policy_hits or support_hits):
            return RelevanceResult(score=self._no_topic, is_core=False)

        score = self._site_score.get(site_name, 0) + self._category_bonus.get(category, 0)
        if legal_hits:
            score += self._legal_score
        if policy_hits:
            score += self._policy_score
        elif support_hits:
            score += self._support_score

        action_hits = self._hits(title, self._action_markers)
        topic_hits = _dedupe(list(legal_hits) + list(policy_hits))
        if action_hits and topic_hits:
            score += self._action_bonus

        matched = _dedupe(
            list(topic_hits) + (list(action_hits) if topic_hits else list(support_hits)),
        )[:6]
        score = self._apply_common_adjustments(score, title, topic_hits)
        return RelevanceResult(score=score, is_core=score >= self.threshold, matches=matched)


def _resolve_config_path() -> Path:
    fallback = Path(__file__).resolve().parent.parent
    settings = import_module("config").get_settings()
    return Path(getattr(settings, "resource_dir", fallback)) / "config" / "relevance.json"


@lru_cache(maxsize=1)
def get_scorer() -> RelevanceScorer:
    path = _resolve_config_path()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raw = {}
    config = raw if isinstance(raw, dict) else {}
    return RelevanceScorer(config)
