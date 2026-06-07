from __future__ import annotations

from scriptweaver.domain.models import AdaptationPlan, ScreenplayDraft

VALID_INTERIOR_EXTERIOR = {"INT", "EXT", "INT/EXT"}
_IE_NORMALIZE: dict[str, str] = {
    "interior": "INT", "inside": "INT", "内景": "INT", "内": "INT",
    "exterior": "EXT", "outside": "EXT", "外景": "EXT", "外": "EXT",
    "int/ext": "INT/EXT", "int / ext": "INT/EXT",
    "内外景": "INT/EXT", "内外": "INT/EXT",
}
VALID_BEAT_TYPES = {"action", "dialogue", "voiceover", "transition"}


class ScreenplayValidationError(ValueError):
    """Raised when a screenplay draft fails validation."""


def validate_screenplay(
    draft: ScreenplayDraft,
    confirmed_plan: AdaptationPlan,
) -> None:
    """Validate screenplay draft against the confirmed adaptation plan."""
    plan_scene_by_id = {
        scene.id: scene for scene in confirmed_plan.scenes
    }

    # ── Scene coverage ────────────────────────────────────────
    screenplay_scene_ids: set[str] = set()

    for s in draft.scenes:
        if s.id in screenplay_scene_ids:
            raise ScreenplayValidationError(
                f"Duplicate screenplay scene id: {s.id}"
            )
        screenplay_scene_ids.add(s.id)

        if s.id not in plan_scene_by_id:
            raise ScreenplayValidationError(
                f"Screenplay scene '{s.id}' not found in plan"
            )

    plan_scene_ids = set(plan_scene_by_id.keys())
    if screenplay_scene_ids != plan_scene_ids:
        missing = plan_scene_ids - screenplay_scene_ids
        if missing:
            raise ScreenplayValidationError(
                f"Missing plan scenes in screenplay: "
                f"{', '.join(sorted(missing))}"
            )
        extra = screenplay_scene_ids - plan_scene_ids
        if extra:
            raise ScreenplayValidationError(
                f"Extra screenplay scenes not in plan: "
                f"{', '.join(sorted(extra))}"
            )

    # ── Scene order matches plan ──────────────────────────────
    ordered_plan_ids = [
        scene.id for scene in sorted(
            confirmed_plan.scenes,
            key=lambda s: s.scene_order,
        )
    ]
    ordered_screenplay_ids = [s.id for s in draft.scenes]
    if ordered_screenplay_ids != ordered_plan_ids:
        raise ScreenplayValidationError(
            f"Screenplay scene order does not match plan order: "
            f"screenplay={ordered_screenplay_ids} "
            f"vs plan={ordered_plan_ids}"
        )

    # ── Per-scene validation ──────────────────────────────────
    for s in draft.scenes:
        plan_scene = plan_scene_by_id[s.id]

        # Heading
        heading = s.heading
        if not heading.location.strip():
            raise ScreenplayValidationError(
                f"scene {s.id}: heading.location must not be blank"
            )
        if not heading.time.strip():
            raise ScreenplayValidationError(
                f"scene {s.id}: heading.time must not be blank"
            )
        raw_ie = heading.interior_exterior.strip()
        normalized_ie = _IE_NORMALIZE.get(
            raw_ie.lower(), raw_ie.upper()
        )
        if normalized_ie not in VALID_INTERIOR_EXTERIOR:
            raise ScreenplayValidationError(
                f"scene {s.id}: interior_exterior must be one of "
                f"{sorted(VALID_INTERIOR_EXTERIOR)}, "
                f"got: '{heading.interior_exterior}'"
            )

        # Character IDs and chapter indexes must belong to plan scene
        plan_char_ids = set(plan_scene.character_ids)
        for cid in s.character_ids:
            if cid not in plan_char_ids:
                raise ScreenplayValidationError(
                    f"scene {s.id}: character '{cid}' not in plan "
                    f"scene character_ids"
                )
        plan_chapter_indexes = set(plan_scene.source_chapter_indexes)
        for ci in s.source_chapter_indexes:
            if ci not in plan_chapter_indexes:
                raise ScreenplayValidationError(
                    f"scene {s.id}: chapter index {ci} not in plan "
                    f"scene source_chapter_indexes"
                )

        # Beats
        for i, beat in enumerate(s.beats):
            label = f"scene {s.id} beat {i}"

            normalized_type = beat.type.strip().lower()
            if normalized_type not in VALID_BEAT_TYPES:
                raise ScreenplayValidationError(
                    f"{label}: beat type must be one of "
                    f"{sorted(VALID_BEAT_TYPES)}, "
                    f"got: '{beat.type}'"
                )

            if not beat.text.strip():
                raise ScreenplayValidationError(
                    f"{label}: beat text must not be blank"
                )

            if normalized_type in ("dialogue", "voiceover"):
                if not beat.character_id or not beat.character_id.strip():
                    raise ScreenplayValidationError(
                        f"{label}: {normalized_type} beat requires "
                        f"character_id"
                    )
            else:
                if beat.character_id is not None:
                    raise ScreenplayValidationError(
                        f"{label}: {normalized_type} beat must not have "
                        f"character_id"
                    )

    # ── revision_notes ────────────────────────────────────────
    for i, note in enumerate(draft.revision_notes):
        if not note.strip():
            raise ScreenplayValidationError(
                f"revision note {i} must not be blank"
            )
