"""Raw-corpus access: snapshot loading, pair-identity validation, season
iteration.

Ported from nba-analytics (derive_shot_context.validate_game_pair and the
snapshot conventions of pull_play_by_play.py) so this repository is
self-contained; the storage layout is identical, so a corpus copied from
that repo is consumed as-is.

Layout: data/raw/play-by-play/<game-id>/<pull-date>.json paired with
data/raw/box-score/<game-id>/<pull-date>.json, both verbatim endpoint
responses under a {_meta, response} wrapper, append-only.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

PBP_SOURCE = "NBA Stats PlayByPlayV3"
BOX_SOURCE = "NBA Stats BoxScoreTraditionalV3"


class CorpusError(Exception):
    """A raw artifact violating the corpus conventions."""


def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CorpusError(f"cannot read {path}: {exc}") from exc


def _response(snapshot: dict, label: str) -> dict:
    response = snapshot.get("response")
    if not isinstance(response, dict):
        raise CorpusError(f"{label} snapshot has no response object")
    return response


def validate_game_pair(pbp_snapshot: dict, box_snapshot: dict) -> tuple[dict, dict, str]:
    """Validate a raw pair's identity; return (pbp_game, box_game, game_id)."""
    pbp = _response(pbp_snapshot, "play-by-play")
    box = _response(box_snapshot, "box-score")
    pbp_game = pbp.get("game")
    box_game = box.get("boxScoreTraditional")
    if not isinstance(pbp_game, dict) or not isinstance(box_game, dict):
        raise CorpusError("source response missing game/boxScoreTraditional object")

    game_id = str(pbp_game.get("gameId", ""))
    if not game_id or str(box_game.get("gameId", "")) != game_id:
        raise CorpusError("play-by-play and box-score game IDs disagree")

    pbp_meta = pbp_snapshot.get("_meta")
    box_meta = box_snapshot.get("_meta")
    if not isinstance(pbp_meta, dict) or not isinstance(box_meta, dict):
        raise CorpusError("source pair missing wrapper metadata")
    if str(pbp_meta.get("game_id", "")) != game_id:
        raise CorpusError("play-by-play wrapper game ID disagrees with response")
    if str(box_meta.get("game_id", "")) != game_id:
        raise CorpusError("box-score wrapper game ID disagrees with response")
    if pbp_meta.get("source") != PBP_SOURCE or box_meta.get("source") != BOX_SOURCE:
        raise CorpusError("source pair has unexpected endpoint identity")
    pbp_date = str(pbp_meta.get("pull_date", ""))
    box_date = str(box_meta.get("pull_date", ""))
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", pbp_date) or pbp_date != box_date:
        raise CorpusError("play-by-play and box-score pull dates disagree")
    return pbp_game, box_game, game_id


def latest_pair_paths(raw_root: Path, game_id: str) -> tuple[Path, Path] | None:
    """The newest complete snapshot pair for a game, or None; orphans raise."""
    pbp_dir = raw_root / "play-by-play" / game_id
    box_dir = raw_root / "box-score" / game_id
    pbp_files = {p.name: p for p in pbp_dir.glob("*.json")} if pbp_dir.exists() else {}
    box_files = {p.name: p for p in box_dir.glob("*.json")} if box_dir.exists() else {}
    if not pbp_files and not box_files:
        return None
    orphaned = sorted(set(pbp_files) ^ set(box_files))
    if orphaned:
        raise CorpusError(
            f"game {game_id} has orphaned source snapshots: {', '.join(orphaned)}"
        )
    pair_name = sorted(set(pbp_files) & set(box_files))[-1]
    return pbp_files[pair_name], box_files[pair_name]


def season_game_prefix(season: str) -> str:
    """Regular-season game-ID prefix, e.g. '2025-26' -> '00225'."""
    if not re.fullmatch(r"\d{4}-\d{2}", season):
        raise CorpusError(f"invalid season string: {season!r}")
    return "002" + season[2:4]


def season_game_ids_on_disk(raw_root: Path, season: str) -> list[str]:
    """Game IDs in the corpus belonging to a season's regular season."""
    prefix = season_game_prefix(season)
    pbp_root = raw_root / "play-by-play"
    if not pbp_root.exists():
        return []
    return sorted(
        d.name for d in pbp_root.iterdir() if d.is_dir() and d.name.startswith(prefix)
    )
