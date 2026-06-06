"""Tests for mock AI providers."""

import pytest

from scriptweaver.ai.mock_provider import MockPlanProvider
from scriptweaver.domain.models import AIAnalysis, Chapter, KeyEvent


def test_mock_plan_more_chapters_than_events():
    """When chapters outnumber events, plan generation must not raise IndexError."""
    provider = MockPlanProvider()
    analysis = AIAnalysis(
        characters=[],
        key_events=[
            KeyEvent(
                id="event_001",
                summary="唯一事件",
                source_chapter_indexes=[1],
            )
        ],
    )
    chapters = [
        Chapter(index=1, title="第一章", content="内容1。"),
        Chapter(index=2, title="第二章", content="内容2。"),
        Chapter(index=3, title="第三章", content="内容3。"),
    ]

    plan = provider.generate_plan(analysis, chapters)

    assert len(plan.scenes) == 3
    # Every scene must have at least one retained event (fallback works)
    for scene in plan.scenes:
        assert len(scene.retained_event_ids) >= 1


def test_mock_plan_scene_count_matches_chapter_count():
    """Each chapter should produce exactly one scene."""
    provider = MockPlanProvider()
    analysis = AIAnalysis()
    chapters = [
        Chapter(index=1, title="第一章", content="内容1。"),
        Chapter(index=2, title="第二章", content="内容2。"),
    ]

    plan = provider.generate_plan(analysis, chapters)

    assert len(plan.scenes) == 2
    assert plan.scenes[0].scene_order == 1
    assert plan.scenes[1].scene_order == 2


def test_mock_plan_empty_events_produces_empty_retained():
    """When confirmed_analysis has no events, retained_event_ids should be empty."""
    provider = MockPlanProvider()
    analysis = AIAnalysis(characters=[], key_events=[])
    chapters = [Chapter(index=1, title="第一章", content="内容1。")]

    plan = provider.generate_plan(analysis, chapters)

    assert len(plan.scenes) == 1
    assert plan.scenes[0].retained_event_ids == []
    assert plan.scenes[0].compression_choices[0].source_event_ids == []
