from scriptweaver.domain.models import (
    AdaptationDecision,
    AdaptationJob,
    AdaptationPlan,
    AIAnalysis,
    CandidateScene,
    Chapter,
    Character,
    CharacterRelationship,
    Conflict,
    KeyEvent,
    PlanReviewQuestion,
    ScenePlan,
    ScreenplayDraft,
    Theme,
    Uncertainty,
    UncertaintyOption,
    UncertaintyResolution,
    UserConfirmations,
)
from scriptweaver.domain.workflow import AdaptationState


def test_adaptation_job_defaults_to_created_state():
    job = AdaptationJob(id="job_001")

    assert job.id == "job_001"
    assert job.state == AdaptationState.CREATED
    assert job.chapters == []
    assert job.ai_analysis is None
    assert job.confirmed_analysis is None


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
        "options": [],
        "allow_custom_answer": True,
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
        confirmed_analysis=AIAnalysis(
            key_events=[
                KeyEvent(
                    id="confirmed_event_001",
                    summary="用户确认密信必须保留。",
                    character_ids=["char_001"],
                    source_chapter_indexes=[1],
                )
            ]
        ),
        user_confirmations=UserConfirmations(
            accepted_character_ids=["char_001"],
            required_plot_points=["密信必须保留"],
            uncertainty_resolutions=[
                UncertaintyResolution(
                    uncertainty_id="uncertainty_001",
                    custom_answer="沈微只知道密信存在。",
                )
            ],
            notes="强化不信任。",
        ),
        adaptation_plan=AdaptationPlan(
            target_format="short_drama",
            structure="three_scene_sequence",
            scenes=[
                ScenePlan(
                    id="scene_plan_001",
                    scene_order=1,
                    title="密信出现",
                    dramatic_purpose="建立调查目标。",
                    character_ids=["char_001"],
                    source_chapter_indexes=[1],
                    retained_event_ids=["confirmed_event_001"],
                    source_candidate_scene_ids=["candidate_scene_001"],
                )
            ],
            review_questions=[
                PlanReviewQuestion(
                    id="question_plan_001",
                    question="是否保留三场结构？",
                    context="答案会影响整体节奏。",
                    related_scene_ids=["scene_plan_001"],
                )
            ],
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
                    "options": [],
                    "allow_custom_answer": True,
                    "source_chapter_indexes": [1, 2],
                }
            ],
        },
        "confirmed_analysis": {
            "characters": [],
            "relationships": [],
            "key_events": [
                {
                    "id": "confirmed_event_001",
                    "summary": "用户确认密信必须保留。",
                    "character_ids": ["char_001"],
                    "source_chapter_indexes": [1],
                }
            ],
            "conflicts": [],
            "themes": [],
            "candidate_scenes": [],
            "uncertainties": [],
        },
        "user_confirmations": {
            "accepted_character_ids": ["char_001"],
            "required_plot_points": ["密信必须保留"],
            "uncertainty_resolutions": [
                {
                    "uncertainty_id": "uncertainty_001",
                    "selected_option_id": None,
                    "custom_answer": "沈微只知道密信存在。",
                }
            ],
            "notes": "强化不信任。",
        },
        "adaptation_plan": {
            "target_format": "short_drama",
            "structure": "three_scene_sequence",
            "scenes": [
                {
                    "id": "scene_plan_001",
                    "scene_order": 1,
                    "title": "密信出现",
                    "dramatic_purpose": "建立调查目标。",
                    "character_ids": ["char_001"],
                    "source_chapter_indexes": [1],
                    "retained_event_ids": ["confirmed_event_001"],
                    "source_candidate_scene_ids": ["candidate_scene_001"],
                    "compression_choices": [],
                    "merge_choices": [],
                    "rewrite_choices": [],
                    "review_questions": [],
                }
            ],
            "review_questions": [
                {
                    "id": "question_plan_001",
                    "question": "是否保留三场结构？",
                    "context": "答案会影响整体节奏。",
                    "related_scene_ids": ["scene_plan_001"],
                }
            ],
        },
        "screenplay_draft": {
            "scene_ids": ["scene_001", "scene_002", "scene_003"],
            "revision_notes": ["沈微动机需要作者确认。"],
        },
    }


def test_structured_adaptation_plan_models_serialize_to_plain_dicts():
    compression = AdaptationDecision(
        id="decision_compress_001",
        description="将调查准备过程压缩为一次电话交谈。",
        reason="更快进入密信冲突。",
        source_event_ids=["event_001"],
    )
    merge = AdaptationDecision(
        id="decision_merge_001",
        description="合并两次线索发现。",
        reason="避免重复的信息揭示。",
        source_event_ids=["event_002", "event_003"],
    )
    rewrite = AdaptationDecision(
        id="decision_rewrite_001",
        description="让沈微当面阻止林照公开密信。",
        reason="将内心矛盾外化为人物冲突。",
        source_event_ids=["event_004"],
    )
    scene_question = PlanReviewQuestion(
        id="question_scene_001",
        question="沈微是否应在本场承认知情？",
        context="答案会改变本场结尾的悬念。",
        related_scene_ids=["scene_plan_001"],
    )
    scene = ScenePlan(
        id="scene_plan_001",
        scene_order=1,
        title="密信对峙",
        dramatic_purpose="建立调查目标并引爆人物冲突。",
        character_ids=["char_001", "char_002"],
        source_chapter_indexes=[1, 2],
        retained_event_ids=["event_001", "event_004"],
        source_candidate_scene_ids=["candidate_scene_001"],
        compression_choices=[compression],
        merge_choices=[merge],
        rewrite_choices=[rewrite],
        review_questions=[scene_question],
    )
    plan_question = PlanReviewQuestion(
        id="question_plan_001",
        question="前三场是否都应围绕密信展开？",
        context="答案会影响整体节奏和支线占比。",
        related_scene_ids=["scene_plan_001", "scene_plan_002"],
    )
    plan = AdaptationPlan(
        target_format="short_drama",
        structure="three_scene_sequence",
        scenes=[scene],
        review_questions=[plan_question],
    )

    assert compression.to_dict() == {
        "id": "decision_compress_001",
        "description": "将调查准备过程压缩为一次电话交谈。",
        "reason": "更快进入密信冲突。",
        "source_event_ids": ["event_001"],
    }
    assert scene_question.to_dict() == {
        "id": "question_scene_001",
        "question": "沈微是否应在本场承认知情？",
        "context": "答案会改变本场结尾的悬念。",
        "related_scene_ids": ["scene_plan_001"],
    }
    assert scene.to_dict() == {
        "id": "scene_plan_001",
        "scene_order": 1,
        "title": "密信对峙",
        "dramatic_purpose": "建立调查目标并引爆人物冲突。",
        "character_ids": ["char_001", "char_002"],
        "source_chapter_indexes": [1, 2],
        "retained_event_ids": ["event_001", "event_004"],
        "source_candidate_scene_ids": ["candidate_scene_001"],
        "compression_choices": [
            {
                "id": "decision_compress_001",
                "description": "将调查准备过程压缩为一次电话交谈。",
                "reason": "更快进入密信冲突。",
                "source_event_ids": ["event_001"],
            }
        ],
        "merge_choices": [
            {
                "id": "decision_merge_001",
                "description": "合并两次线索发现。",
                "reason": "避免重复的信息揭示。",
                "source_event_ids": ["event_002", "event_003"],
            }
        ],
        "rewrite_choices": [
            {
                "id": "decision_rewrite_001",
                "description": "让沈微当面阻止林照公开密信。",
                "reason": "将内心矛盾外化为人物冲突。",
                "source_event_ids": ["event_004"],
            }
        ],
        "review_questions": [
            {
                "id": "question_scene_001",
                "question": "沈微是否应在本场承认知情？",
                "context": "答案会改变本场结尾的悬念。",
                "related_scene_ids": ["scene_plan_001"],
            }
        ],
    }
    assert plan.to_dict() == {
        "target_format": "short_drama",
        "structure": "three_scene_sequence",
        "scenes": [scene.to_dict()],
        "review_questions": [
            {
                "id": "question_plan_001",
                "question": "前三场是否都应围绕密信展开？",
                "context": "答案会影响整体节奏和支线占比。",
                "related_scene_ids": ["scene_plan_001", "scene_plan_002"],
            }
        ],
    }


def test_structured_adaptation_plan_defaults_are_independent():
    first_decision = AdaptationDecision(
        id="decision_001",
        description="压缩调查过程。",
        reason="控制节奏。",
    )
    second_decision = AdaptationDecision(
        id="decision_002",
        description="重写发现方式。",
        reason="增强冲突。",
    )
    first_question = PlanReviewQuestion(
        id="question_001",
        question="是否保留支线？",
        context="影响整体时长。",
    )
    second_question = PlanReviewQuestion(
        id="question_002",
        question="是否提前揭示真相？",
        context="影响悬念。",
    )
    first_scene = ScenePlan(
        id="scene_plan_001",
        scene_order=1,
        title="密信出现",
        dramatic_purpose="建立目标。",
    )
    second_scene = ScenePlan(
        id="scene_plan_002",
        scene_order=2,
        title="首次追查",
        dramatic_purpose="升级冲突。",
    )
    first_plan = AdaptationPlan(
        target_format="short_drama",
        structure="linear",
    )
    second_plan = AdaptationPlan(
        target_format="short_drama",
        structure="linear",
    )

    first_decision.source_event_ids.append("event_001")
    first_question.related_scene_ids.append("scene_plan_001")
    first_scene.character_ids.append("char_001")
    first_scene.source_chapter_indexes.append(1)
    first_scene.retained_event_ids.append("event_001")
    first_scene.source_candidate_scene_ids.append("candidate_scene_001")
    first_scene.compression_choices.append(first_decision)
    first_scene.merge_choices.append(first_decision)
    first_scene.rewrite_choices.append(first_decision)
    first_scene.review_questions.append(first_question)
    first_plan.scenes.append(first_scene)
    first_plan.review_questions.append(first_question)

    assert second_decision.source_event_ids == []
    assert second_question.related_scene_ids == []
    assert second_scene.character_ids == []
    assert second_scene.source_chapter_indexes == []
    assert second_scene.retained_event_ids == []
    assert second_scene.source_candidate_scene_ids == []
    assert second_scene.compression_choices == []
    assert second_scene.merge_choices == []
    assert second_scene.rewrite_choices == []
    assert second_scene.review_questions == []
    assert second_plan.scenes == []
    assert second_plan.review_questions == []
    assert not hasattr(first_plan, "scene_ids")
    assert "scene_ids" not in first_plan.to_dict()


def test_structured_adaptation_plan_models_are_public_domain_exports():
    from scriptweaver.domain import (
        AdaptationDecision as ExportedAdaptationDecision,
        PlanReviewQuestion as ExportedPlanReviewQuestion,
        ScenePlan as ExportedScenePlan,
    )

    assert ExportedAdaptationDecision is AdaptationDecision
    assert ExportedPlanReviewQuestion is PlanReviewQuestion
    assert ExportedScenePlan is ScenePlan


def test_uncertainty_options_and_resolutions_serialize_to_plain_dicts():
    option = UncertaintyOption(
        id="option_001",
        label="提前知情",
        description="沈微一直知道密信内容。",
        impact="强化隐瞒与信任冲突。",
    )
    alternative_option = UncertaintyOption(
        id="option_002",
        label="刚刚得知",
        description="沈微与林照同时得知密信内容。",
        impact="强化共同调查关系。",
    )
    uncertainty = Uncertainty(
        id="uncertainty_001",
        question="沈微是否提前知道密信？",
        context="答案影响人物动机。",
        options=[option, alternative_option],
        allow_custom_answer=True,
        source_chapter_indexes=[1, 2],
    )
    selected_resolution = UncertaintyResolution(
        uncertainty_id="uncertainty_001",
        selected_option_id="option_001",
    )
    custom_resolution = UncertaintyResolution(
        uncertainty_id="uncertainty_002",
        custom_answer="沈微只知道密信存在，不知道内容。",
    )
    confirmations = UserConfirmations(
        uncertainty_resolutions=[
            selected_resolution,
            custom_resolution,
        ]
    )

    assert option.to_dict() == {
        "id": "option_001",
        "label": "提前知情",
        "description": "沈微一直知道密信内容。",
        "impact": "强化隐瞒与信任冲突。",
    }
    assert uncertainty.to_dict() == {
        "id": "uncertainty_001",
        "question": "沈微是否提前知道密信？",
        "context": "答案影响人物动机。",
        "options": [option.to_dict(), alternative_option.to_dict()],
        "allow_custom_answer": True,
        "source_chapter_indexes": [1, 2],
    }
    assert selected_resolution.to_dict() == {
        "uncertainty_id": "uncertainty_001",
        "selected_option_id": "option_001",
        "custom_answer": None,
    }
    assert custom_resolution.to_dict() == {
        "uncertainty_id": "uncertainty_002",
        "selected_option_id": None,
        "custom_answer": "沈微只知道密信存在，不知道内容。",
    }
    assert confirmations.to_dict()["uncertainty_resolutions"] == [
        selected_resolution.to_dict(),
        custom_resolution.to_dict(),
    ]


def test_uncertainty_option_and_resolution_defaults_are_independent():
    first_uncertainty = Uncertainty(
        id="uncertainty_001",
        question="问题一",
        context="上下文一",
    )
    second_uncertainty = Uncertainty(
        id="uncertainty_002",
        question="问题二",
        context="上下文二",
    )
    first_confirmations = UserConfirmations()
    second_confirmations = UserConfirmations()

    first_uncertainty.options.append(
        UncertaintyOption(
            id="option_001",
            label="方案一",
            description="描述一",
            impact="影响一",
        )
    )
    first_confirmations.uncertainty_resolutions.append(
        UncertaintyResolution(
            uncertainty_id="uncertainty_001",
            custom_answer="自定义答案",
        )
    )

    assert second_uncertainty.options == []
    assert second_confirmations.uncertainty_resolutions == []


def test_uncertainty_preserves_existing_positional_argument_order():
    uncertainty = Uncertainty(
        "uncertainty_001",
        "沈微是否提前知道密信？",
        "答案影响人物动机。",
        [1, 2],
    )

    assert uncertainty.source_chapter_indexes == [1, 2]
    assert uncertainty.options == []
    assert uncertainty.allow_custom_answer is True


def test_user_confirmations_preserves_existing_positional_argument_order():
    confirmations = UserConfirmations(
        ["char_001"],
        ["密信必须保留"],
        "强化不信任。",
    )

    assert confirmations.notes == "强化不信任。"
    assert confirmations.uncertainty_resolutions == []


def test_uncertainty_models_are_public_domain_exports():
    from scriptweaver.domain import (
        UncertaintyOption as ExportedUncertaintyOption,
        UncertaintyResolution as ExportedUncertaintyResolution,
    )

    assert ExportedUncertaintyOption is UncertaintyOption
    assert ExportedUncertaintyResolution is UncertaintyResolution
