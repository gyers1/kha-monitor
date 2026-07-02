from __future__ import annotations

import json
import sqlite3
import sys
from collections import Counter
from importlib import util
from pathlib import Path


def _relevance_module():
    module_path = Path(__file__).resolve().parents[1] / "application" / "relevance.py"
    spec = util.spec_from_file_location("kha_relevance_for_audit", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load relevance module")
    module = util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _row_to_sample(row: sqlite3.Row, score: int, matched: list[str]) -> dict[str, str | int | list[str]]:
    return {
        "id": int(row["id"]),
        "date": str(row["date_key"]),
        "site": str(row["site_name"]),
        "category": str(row["category"]),
        "title": str(row["title"]),
        "score": score,
        "matched": matched,
    }


def _load_scorer():
    config_path = Path(__file__).resolve().parents[1] / "config" / "relevance.json"
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    return _relevance_module().RelevanceScorer(raw)


def _usage() -> str:
    return "usage: python tools/audit_relevance_db.py <monitoring.db> [sample_limit]"


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(_usage())
        return 2

    db_path = Path(argv[1])
    sample_limit = int(argv[2]) if len(argv) > 2 else 20
    scorer = _load_scorer()

    with sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        rows = list(
            connection.execute(
                "select a.id, a.title, a.date_key, s.name site_name, s.category "
                "from articles a join sites s on s.id = a.site_id",
            ),
        )

    core_samples: list[dict[str, str | int | list[str]]] = []
    by_category: Counter[str] = Counter()
    by_site: Counter[str] = Counter()
    core_count = 0

    for row in rows:
        result = scorer.score(str(row["title"]), str(row["category"]), str(row["site_name"]))
        if not result.is_core:
            continue
        core_count += 1
        by_category[str(row["category"])] += 1
        by_site[str(row["site_name"])] += 1
        if len(core_samples) < sample_limit:
            core_samples.append(_row_to_sample(row, result.score, result.matched))

    print(
        json.dumps(
            {
                "total_articles": len(rows),
                "core_articles": core_count,
                "core_by_category": dict(by_category.most_common()),
                "core_by_site": dict(by_site.most_common(20)),
                "core_samples": core_samples,
            },
            ensure_ascii=False,
            indent=2,
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
