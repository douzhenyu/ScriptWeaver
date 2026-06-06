from scriptweaver.domain.models import (
    AdaptationJob,
    AdaptationPlan,
    AIAnalysis,
    CandidateScene,
    Chapter,
    Character,
    CharacterRelationship,
    Conflict,
    KeyEvent,
    ScreenplayDraft,
    Theme,
    Uncertainty,
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


def test_structured_analysis_models_serialize_to_plain_dicts():
    character = Character(
        id="char_001",
        name="林照",
        role="protagonist",
        description="追查父亲旧案的年轻记者。",
        goal="查明密信指向的真相。",
        motivation="证明父亲并未背叛家人。",
    )
    relationship = CharacterRelationship(
        id="relationship_001",
        source_character_id="char_001",
        target_character_id="char_002",
        description="彼此合作，但互相隐瞒关键信息。",
        source_chapter_indexes=[1, 2],
    )
    key_event = KeyEvent(
        id="event_001",
        summary="林照收到父亲留下的密信。",
        character_ids=["char_001"],
        source_chapter_indexes=[1],
    )
    conflict = Conflict(
        id="conflict_001",
        description="林照想公开真相，沈微试图阻止他。",
        stakes="公开真相可能令两人陷入危险。",
        character_ids=["char_001", "char_002"],
        source_chapter_indexes=[1, 2],
    )
    theme = Theme(
        id="theme_001",
        statement="真相需要付出代价。",
        source_chapter_indexes=[1, 2, 3],
    )
    candidate_scene = CandidateScene(
        id="candidate_scene_001",
        title="密信出现",
        summary="林照发现父亲留下的密信。",
        dramatic_purpose="建立调查目标。",
        location="林照家",
        time_hint="夜",
        character_ids=["char_001"],
        source_chapter_indexes=[1],
    )
    uncertainty = Uncertainty(
        id="uncertainty_001",
        question="沈微是否提前知道密信内容？",
        context="答案会影响沈微阻止林照的动机。",
        source_chapter_indexes=[1, 2],
    )

    assert character.to_dict() == {
        "id": "char_001",
        "name": "林照",
        "role": "protagonist",
        "description": "追查父亲旧案的年轻记者。",
        "goal": "查明密信指向的真相。",
        "motivation": "证明父亲并未背叛家人。",
    }
    assert relationship.to_dict() == {
        "id": "relationship_001",
        "source_character_id": "char_001",
        "target_character_id": "char_002",
        "description": "彼此合作，但互相隐瞒关键信息。",
        "source_chapter_indexes": [1, 2],
    }
    assert key_event.to_dict() == {
        "id": "event_001",
        "summary": "林照收到父亲留下的密信。",
        "character_ids": ["char_001"],
        "source_chapter_indexes": [1],
    }
    assert conflict.to_dict() == {
        "id": "conflict_001",
        "description": "林照想公开真相，沈微试图阻止他。",
        "stakes": "公开真相可能令两人陷入危险。",
        "character_ids": ["char_001", "char_002"],
        "source_chapter_indexes": [1, 2],
    }
    assert theme.to_dict() == {
        "id": "theme_001",
        "statement": "真相需要付出代价。",
        "source_chapter_indexes": [1, 2, 3],
    }
    assert candidate_scene.to_dict() == {
        "id": "candidate_scene_001",
        "title": "密信出现",
        "summary": "林照发现父亲留下的密信。",
        "dramatic_purpose": "建立调查目标。",
        "location": "林照家",
        "time_hint": "夜",
        "character_ids": ["char_001"],
        "source_chapter_indexes": [1],
    }
    assert uncertainty.to_dict() == {
        "id": "uncertainty_001",
        "question": "沈微是否提前知道密信内容？",
        "context": "答案会影响沈微阻止林照的动机。",
        "source_chapter_indexes": [1, 2],
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
                Character(
                    id="char_001",
                    name="林照",
                    role="protagonist",
                    description="追查父亲旧案的年轻记者。",
                    goal="查明密信指向的真相。",
                    motivation="证明父亲并未背叛家人。",
                )
            ],
            relationships=[
                CharacterRelationship(
                    id="relationship_001",
                    source_character_id="char_001",
                    target_character_id="char_002",
                    description="彼此合作，但互相隐瞒关键信息。",
                    source_chapter_indexes=[1, 2],
                )
            ],
            key_events=[
                KeyEvent(
                    id="event_001",
                    summary="林照收到密信。",
                    character_ids=["char_001"],
                    source_chapter_indexes=[1],
                )
            ],
            conflicts=[
                Conflict(
                    id="conflict_001",
                    description="林照想公开真相，沈微担心代价。",
                    stakes="两人可能因此陷入危险。",
                    character_ids=["char_001", "char_002"],
                    source_chapter_indexes=[1, 2],
                )
            ],
            themes=[
                Theme(
                    id="theme_001",
                    statement="真相需要付出代价。",
                    source_chapter_indexes=[1, 2, 3],
                )
            ],
            candidate_scenes=[
                CandidateScene(
                    id="candidate_scene_001",
                    title="密信出现",
                    summary="林照发现父亲留下的密信。",
                    dramatic_purpose="建立调查目标。",
                    location="林照家",
                    time_hint="夜",
                    character_ids=["char_001"],
                    source_chapter_indexes=[1],
                )
            ],
            uncertainties=[
                Uncertainty(
                    id="uncertainty_001",
                    question="沈微是否提前知道密信内容？",
                    context="答案会影响沈微的动机。",
                    source_chapter_indexes=[1, 2],
                )
            ],
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
                {
                    "id": "char_001",
                    "name": "林照",
                    "role": "protagonist",
                    "description": "追查父亲旧案的年轻记者。",
                    "goal": "查明密信指向的真相。",
                    "motivation": "证明父亲并未背叛家人。",
                }
            ],
            "relationships": [
                {
                    "id": "relationship_001",
                    "source_character_id": "char_001",
                    "target_character_id": "char_002",
                    "description": "彼此合作，但互相隐瞒关键信息。",
                    "source_chapter_indexes": [1, 2],
                }
            ],
            "key_events": [
                {
                    "id": "event_001",
                    "summary": "林照收到密信。",
                    "character_ids": ["char_001"],
                    "source_chapter_indexes": [1],
                }
            ],
            "conflicts": [
                {
                    "id": "conflict_001",
                    "description": "林照想公开真相，沈微担心代价。",
                    "stakes": "两人可能因此陷入危险。",
                    "character_ids": ["char_001", "char_002"],
                    "source_chapter_indexes": [1, 2],
                }
            ],
            "themes": [
                {
                    "id": "theme_001",
                    "statement": "真相需要付出代价。",
                    "source_chapter_indexes": [1, 2, 3],
                }
            ],
            "candidate_scenes": [
                {
                    "id": "candidate_scene_001",
                    "title": "密信出现",
                    "summary": "林照发现父亲留下的密信。",
                    "dramatic_purpose": "建立调查目标。",
                    "location": "林照家",
                    "time_hint": "夜",
                    "character_ids": ["char_001"],
                    "source_chapter_indexes": [1],
                }
            ],
            "uncertainties": [
                {
                    "id": "uncertainty_001",
                    "question": "沈微是否提前知道密信内容？",
                    "context": "答案会影响沈微的动机。",
                    "source_chapter_indexes": [1, 2],
                }
            ],
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
