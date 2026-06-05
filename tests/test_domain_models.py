from scriptweaver.domain.models import (
    AdaptationJob,
    AdaptationPlan,
    AIAnalysis,
    Chapter,
    Character,
    ScreenplayDraft,
    UserConfirmations,
)
from scriptweaver.domain.workflow import AdaptationState


def test_adaptation_job_defaults_to_created_state():
    job = AdaptationJob(id="job_001")

    assert job.id == "job_001"
    assert job.state == AdaptationState.CREATED
    assert job.chapters == []


def test_chapter_model_serializes_to_plain_dict():
    chapter = Chapter(index=1, title="第一章", content="开场内容")

    assert chapter.to_dict() == {
        "index": 1,
        "title": "第一章",
        "content": "开场内容",
    }


def test_adaptation_job_serializes_nested_workflow_data():
    job = AdaptationJob(
        id="job_001",
        state=AdaptationState.PLAN_CONFIRMED,
        chapters=[
            Chapter(index=1, title="第一章", content="开场内容"),
            Chapter(index=2, title="第二章", content="冲突升级"),
            Chapter(index=3, title="第三章", content="发现线索"),
        ],
        ai_analysis=AIAnalysis(
            characters=[
                Character(id="char_001", name="林照", role="protagonist")
            ],
            conflicts=["林照想公开真相，沈微担心代价。"],
            key_events=["林照收到密信。"],
        ),
        user_confirmations=UserConfirmations(
            accepted_character_ids=["char_001"],
            required_plot_points=["密信必须保留"],
            notes="强化不信任。",
        ),
        adaptation_plan=AdaptationPlan(
            target_format="short_drama",
            structure="three_scene_sequence",
            scene_ids=["scene_001", "scene_002", "scene_003"],
        ),
        screenplay_draft=ScreenplayDraft(
            scene_ids=["scene_001", "scene_002", "scene_003"],
            revision_notes=["沈微动机需要作者确认。"],
        ),
    )

    data = job.to_dict()

    assert data == {
        "id": "job_001",
        "state": "plan_confirmed",
        "chapters": [
            {"index": 1, "title": "第一章", "content": "开场内容"},
            {"index": 2, "title": "第二章", "content": "冲突升级"},
            {"index": 3, "title": "第三章", "content": "发现线索"},
        ],
        "ai_analysis": {
            "characters": [
                {"id": "char_001", "name": "林照", "role": "protagonist"}
            ],
            "conflicts": ["林照想公开真相，沈微担心代价。"],
            "key_events": ["林照收到密信。"],
        },
        "user_confirmations": {
            "accepted_character_ids": ["char_001"],
            "required_plot_points": ["密信必须保留"],
            "notes": "强化不信任。",
        },
        "adaptation_plan": {
            "target_format": "short_drama",
            "structure": "three_scene_sequence",
            "scene_ids": ["scene_001", "scene_002", "scene_003"],
        },
        "screenplay_draft": {
            "scene_ids": ["scene_001", "scene_002", "scene_003"],
            "revision_notes": ["沈微动机需要作者确认。"],
        },
    }
