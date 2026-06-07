"""Tests for screenplay draft domain validation."""

from dataclasses import replace

import pytest

from scriptweaver.domain.models import (
    AdaptationPlan,
    Beat,
    SceneHeading,
    ScenePlan,
    ScreenplayDraft,
    ScreenplayScene,
)
from scriptweaver.domain.screenplay_validation import (
    ScreenplayValidationError,
    validate_screenplay,
)


def make_valid_plan() -> AdaptationPlan:
    return AdaptationPlan(
        target_format="short_drama",
        structure="2 scenes",
        scenes=[
            ScenePlan(
                id="scene_001",
                scene_order=1,
                title="开场",
                dramatic_purpose="建立悬念",
                character_ids=["char_001"],
                source_chapter_indexes=[1],
            ),
            ScenePlan(
                id="scene_002",
                scene_order=2,
                title="冲突升级",
                dramatic_purpose="深化矛盾",
                character_ids=["char_001", "char_002"],
                source_chapter_indexes=[2],
            ),
        ],
    )


def make_valid_draft() -> ScreenplayDraft:
    return ScreenplayDraft(
        scenes=[
            ScreenplayScene(
                id="scene_001",
                heading=SceneHeading(
                    location="茶馆", time="夜", interior_exterior="INT",
                ),
                source_chapter_indexes=[1],
                character_ids=["char_001"],
                beats=[
                    Beat(type="action", text="林照拆开密信。"),
                    Beat(
                        type="dialogue",
                        text="这不是父亲的笔迹。",
                        character_id="char_001",
                    ),
                ],
            ),
            ScreenplayScene(
                id="scene_002",
                heading=SceneHeading(
                    location="巷口", time="夜", interior_exterior="EXT",
                ),
                source_chapter_indexes=[2],
                character_ids=["char_001", "char_002"],
                beats=[
                    Beat(type="action", text="沈微拦住林照。"),
                    Beat(
                        type="dialogue",
                        text="你不能公开。",
                        character_id="char_002",
                    ),
                ],
            ),
        ],
        revision_notes=["审查节奏。"],
    )


# ── Valid draft ─────────────────────────────────────────────────────


def test_validate_screenplay_accepts_valid_draft():
    validate_screenplay(make_valid_draft(), make_valid_plan())


# ── Scene ID uniqueness ─────────────────────────────────────────────


def test_rejects_duplicate_scene_id():
    draft = make_valid_draft()
    scenes = list(draft.scenes)
    scenes[1] = replace(scenes[1], id="scene_001")
    draft = replace(draft, scenes=scenes)

    with pytest.raises(ScreenplayValidationError,
                       match="Duplicate screenplay scene id"):
        validate_screenplay(draft, make_valid_plan())


# ── Scene exists in plan ────────────────────────────────────────────


def test_rejects_scene_not_in_plan():
    draft = make_valid_draft()
    scenes = list(draft.scenes)
    scenes[0] = replace(scenes[0], id="scene_nonexistent")
    draft = replace(draft, scenes=scenes)

    with pytest.raises(ScreenplayValidationError,
                       match="not found in plan"):
        validate_screenplay(draft, make_valid_plan())


# ── Each plan scene appears exactly once ────────────────────────────


def test_rejects_missing_plan_scene():
    draft = make_valid_draft()
    draft = replace(draft, scenes=[draft.scenes[0]])

    with pytest.raises(ScreenplayValidationError,
                       match="Missing plan scenes"):
        validate_screenplay(draft, make_valid_plan())


def test_rejects_extra_scene_not_in_plan():
    plan = make_valid_plan()
    draft = make_valid_draft()
    extra = ScreenplayScene(
        id="scene_003",
        heading=SceneHeading(
            location="X", time="Y", interior_exterior="INT",
        ),
        beats=[Beat(type="action", text="extra")],
    )
    draft = replace(draft, scenes=list(draft.scenes) + [extra])

    with pytest.raises(ScreenplayValidationError,
                       match="not found in plan"):
        validate_screenplay(draft, plan)


# ── Scene order matches plan ────────────────────────────────────────


def test_rejects_wrong_scene_order():
    draft = make_valid_draft()
    scenes = list(draft.scenes)
    draft = replace(draft, scenes=[scenes[1], scenes[0]])

    with pytest.raises(ScreenplayValidationError,
                       match="not match plan order"):
        validate_screenplay(draft, make_valid_plan())


# ── Heading validation ──────────────────────────────────────────────


def test_rejects_blank_heading_location():
    draft = make_valid_draft()
    scenes = list(draft.scenes)
    heading = replace(scenes[0].heading, location="")
    scenes[0] = replace(scenes[0], heading=heading)
    draft = replace(draft, scenes=scenes)

    with pytest.raises(ScreenplayValidationError,
                       match="heading.location must not be blank"):
        validate_screenplay(draft, make_valid_plan())


def test_rejects_blank_heading_time():
    draft = make_valid_draft()
    scenes = list(draft.scenes)
    heading = replace(scenes[0].heading, time="")
    scenes[0] = replace(scenes[0], heading=heading)
    draft = replace(draft, scenes=scenes)

    with pytest.raises(ScreenplayValidationError,
                       match="heading.time must not be blank"):
        validate_screenplay(draft, make_valid_plan())


def test_rejects_invalid_interior_exterior():
    draft = make_valid_draft()
    scenes = list(draft.scenes)
    heading = replace(scenes[0].heading, interior_exterior="INDOOR")
    scenes[0] = replace(scenes[0], heading=heading)
    draft = replace(draft, scenes=scenes)

    with pytest.raises(ScreenplayValidationError,
                       match="interior_exterior must be"):
        validate_screenplay(draft, make_valid_plan())


# ── Beat validation ─────────────────────────────────────────────────


def test_rejects_invalid_beat_type():
    draft = make_valid_draft()
    scenes = list(draft.scenes)
    beats = list(scenes[0].beats)
    beats[0] = replace(beats[0], type="narration")
    scenes[0] = replace(scenes[0], beats=beats)
    draft = replace(draft, scenes=scenes)

    with pytest.raises(ScreenplayValidationError,
                       match="beat type must be"):
        validate_screenplay(draft, make_valid_plan())


def test_rejects_blank_beat_text():
    draft = make_valid_draft()
    scenes = list(draft.scenes)
    beats = list(scenes[0].beats)
    beats[0] = replace(beats[0], text="")
    scenes[0] = replace(scenes[0], beats=beats)
    draft = replace(draft, scenes=scenes)

    with pytest.raises(ScreenplayValidationError,
                       match="beat text must not be blank"):
        validate_screenplay(draft, make_valid_plan())


def test_rejects_dialogue_without_character_id():
    draft = make_valid_draft()
    scenes = list(draft.scenes)
    beats = list(scenes[0].beats)
    beats[1] = replace(beats[1], character_id=None)
    scenes[0] = replace(scenes[0], beats=beats)
    draft = replace(draft, scenes=scenes)

    with pytest.raises(ScreenplayValidationError,
                       match="dialogue beat.*requires character_id"):
        validate_screenplay(draft, make_valid_plan())


def test_rejects_non_dialogue_with_character_id():
    draft = make_valid_draft()
    scenes = list(draft.scenes)
    beats = list(scenes[0].beats)
    beats[0] = replace(beats[0], character_id="char_001")
    scenes[0] = replace(scenes[0], beats=beats)
    draft = replace(draft, scenes=scenes)

    with pytest.raises(ScreenplayValidationError,
                       match="action beat.*must not have character_id"):
        validate_screenplay(draft, make_valid_plan())


# ── Beat type: voiceover accepted ──────────────────────────────────


def test_accepts_voiceover_beat_type():
    draft = make_valid_draft()
    scenes = list(draft.scenes)
    beats = list(scenes[0].beats) + [
        Beat(type="voiceover", text="旁白淡出。", character_id="char_001")
    ]
    scenes[0] = replace(scenes[0], beats=beats)
    draft = replace(draft, scenes=scenes)

    validate_screenplay(draft, make_valid_plan())


# ── revision_notes ──────────────────────────────────────────────────


def test_accepts_chinese_interior_exterior():
    """Chinese 内景/外景 must be accepted and normalized."""
    draft = make_valid_draft()
    scenes = list(draft.scenes)
    heading = replace(scenes[0].heading, interior_exterior="外景")
    scenes[0] = replace(scenes[0], heading=heading)
    draft = replace(draft, scenes=scenes)
    validate_screenplay(draft, make_valid_plan())


def test_accepts_lowercase_interior_exterior():
    """Lowercase 'exterior' must be accepted."""
    draft = make_valid_draft()
    scenes = list(draft.scenes)
    heading = replace(scenes[0].heading, interior_exterior="exterior")
    scenes[0] = replace(scenes[0], heading=heading)
    draft = replace(draft, scenes=scenes)
    validate_screenplay(draft, make_valid_plan())


def test_rejects_blank_revision_note():
    draft = make_valid_draft()
    draft = replace(draft, revision_notes=["  "])

    with pytest.raises(ScreenplayValidationError,
                       match="revision note.*must not be blank"):
        validate_screenplay(draft, make_valid_plan())
