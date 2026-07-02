from __future__ import annotations

import json
import sys
from importlib import util
from pathlib import Path

import pytest


def _relevance_module():
    module_path = Path(__file__).resolve().parents[1] / "application" / "relevance.py"
    spec = util.spec_from_file_location("kha_relevance_for_tests", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load relevance module")
    module = util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _scorer():
    config_path = Path(__file__).resolve().parents[1] / "config" / "relevance.json"
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    return _relevance_module().RelevanceScorer(raw)


@pytest.mark.parametrize(
    ("title", "category", "site_name", "expected_matches"),
    [
        (
            "국토교통부령제1599호(공공주택 특별법 시행규칙 일부개정령)",
            "전자관보",
            "대한민국 관보",
            {"공공주택 특별법", "시행규칙"},
        ),
        (
            "국토교통부공고제2026-830호(「건축물의 분양에 관한 법률 시행령」 일부개정령안 재입법예고)",
            "전자관보",
            "대한민국 관보",
            {"건축물의 분양에 관한 법률", "시행령"},
        ),
        (
            "대통령령제36365호(부동산 거래신고 등에 관한 법률 시행령 일부개정령)",
            "전자관보",
            "대한민국 관보",
            {"부동산 거래신고 등에 관한 법률", "시행령"},
        ),
        (
            "국토교통부공고제2026-323호(주차장법 시행규칙 개정안 입법예고)",
            "전자관보",
            "대한민국 관보",
            {"주차장법", "시행규칙", "입법예고"},
        ),
        (
            "소득세법 시행규칙 일부개정령안 입법예고",
            "입법예고",
            "법제처 입법예고",
            {"소득세법", "시행규칙", "입법예고"},
        ),
    ],
)
def test_core_when_kha_repeated_legal_issue(
    title: str,
    category: str,
    site_name: str,
    expected_matches: set[str],
) -> None:
    result = _scorer().score(title, category, site_name)

    assert result.is_core
    assert expected_matches.issubset(set(result.matched))


@pytest.mark.parametrize(
    ("title", "category", "site_name"),
    [
        ("근로기준법 일부개정법률안(이종배의원 등 10인)", "의안정보", "의안정보시스템"),
        ("HUG, 「제4회 부산혁신도시 오픈캠퍼스」 일경험 수련생 수료식 개최", "보도자료", "HUG 보도자료"),
        ("하천공사 준공고시(반변천 신석지구 하천환경정비사업)", "전자관보", "대한민국 관보"),
        ("국토교통부공고제2026-849호(공동주택가격 정정)", "전자관보", "대한민국 관보"),
        ("도로교통법 일부개정법률안(이재관의원 등 11인)", "의안정보", "의안정보시스템"),
    ],
)
def test_not_core_when_only_generic_or_wrong_domain(
    title: str,
    category: str,
    site_name: str,
) -> None:
    result = _scorer().score(title, category, site_name)

    assert not result.is_core


def test_institution_name_needs_policy_context() -> None:
    scorer = _scorer()

    event_result = scorer.score("HUG, 지역사회 공동기금 전달", "보도자료", "HUG 보도자료")
    issue_result = scorer.score("HUG, PF 보증제도 개선방안 발표", "보도자료", "HUG 보도자료")

    assert not event_result.is_core
    assert issue_result.is_core
    assert {"PF", "보증제도", "HUG"}.issubset(set(issue_result.matched))
