#!/usr/bin/env python3
"""Map public genealogy ids to the HTML page that owns them."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from build_people_index import ProjectionError


BRANCH_PAGES = {
    "zimmerman": "zimmerman.html",
    "mundell": "mundell.html",
    "dible": "dible.html",
    "connelly": "connelly.html",
}


def _jsonl_rows(path: Path) -> Iterable[dict]:
    if not path.is_file():
        # Assignment helper, not a validator: fixtures and partial roots may
        # lack whole stores; the core validators own existence contracts.
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if isinstance(row, dict):
                yield row


def split_branches(root: Path) -> frozenset[str]:
    return frozenset(
        branch for branch, page in BRANCH_PAGES.items() if (root / page).is_file()
    )


def _page_for_branch(branch: str, split: frozenset[str]) -> str:
    if branch in split:
        return BRANCH_PAGES[branch]
    return "index.html"


def page_assignments(root: Path, split: Iterable[str] | None = None) -> dict[str, str]:
    active_split = split_branches(root) if split is None else frozenset(split)
    assignments: dict[str, str] = {}

    for row in _jsonl_rows(root / "research" / "people" / "people.jsonl"):
        value = row.get("id")
        branches = row.get("branches")
        if isinstance(value, str) and isinstance(branches, list) and branches:
            branch = branches[0]
            if isinstance(branch, str):
                assignments[value] = _page_for_branch(branch, active_split)

    for row in _jsonl_rows(root / "research" / "people" / "relationships.jsonl"):
        value = row.get("id")
        branches = row.get("branches")
        if (
            row.get("node_type") == "gap"
            and isinstance(value, str)
            and isinstance(branches, list)
            and branches
        ):
            branch = branches[0]
            if isinstance(branch, str):
                assignments[value] = _page_for_branch(branch, active_split)

    for row in _jsonl_rows(root / "research" / "cases" / "cases.jsonl"):
        value = row.get("id")
        branch = row.get("branch")
        if isinstance(value, str) and isinstance(branch, str):
            assignments[value] = _page_for_branch(branch, active_split)

    for row in _jsonl_rows(root / "research" / "sources" / "sources.jsonl"):
        html_id = row.get("html_id")
        if isinstance(html_id, str):
            assignments[html_id] = "index.html"

    return assignments


def href(assignments: dict[str, str], target_id: str, current_page: str) -> str:
    if target_id not in assignments:
        raise ProjectionError(f"unknown page-map target id: {target_id}")
    target_page = assignments[target_id]
    if target_page == current_page:
        return f"#{target_id}"
    return f"{target_page}#{target_id}"
