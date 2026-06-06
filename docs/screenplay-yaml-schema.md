# Screenplay YAML Schema

## Purpose

This document defines the YAML structure produced by ScriptWeaver after a human-in-the-loop AI adaptation workflow.

The schema is designed for an editable screenplay draft. It stores the final script text and the AI-assisted decisions that led to it.

## Design Principles

1. **Traceable:** Each screenplay scene can reference source chapters and key events.
2. **Interactive:** User confirmations are stored separately from raw AI analysis.
3. **Editable:** The YAML is readable and can be modified by authors or tools.
4. **AI-visible:** The schema makes AI analysis, adaptation planning, and revision guidance explicit.
5. **Draft-oriented:** The schema supports early creative drafting rather than final production scheduling.

## Top-Level Structure

```yaml
schema_version: "1.0"
metadata: {}
source: {}
ai_analysis: {}
confirmed_analysis: {}
user_confirmations: {}
adaptation_plan: {}
screenplay: {}
revision_notes: []
```

## Field Definitions

### `schema_version`

Type: string

Required: yes

Meaning:

Identifies the schema version used by this YAML artifact.

Design reason:

The backend and future Web UI need a stable way to handle schema changes.

### `metadata`

Type: object

Required: yes

Fields:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `title` | string | yes | Adaptation project title. |
| `author` | string | no | Original novel author. |
| `adapter` | string | no | Human or AI adapter label. |
| `target_format` | string | yes | Intended script form, such as `short_drama`, `film`, or `episode`. |
| `language` | string | yes | Output language, such as `zh-CN`. |
| `created_at` | string | no | ISO-like creation timestamp. |

Design reason:

The YAML should work as a standalone artifact, not only as a backend response.

### `source`

Type: object

Required: yes

Fields:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `source_type` | string | yes | Source input type, normally `novel_chapters`. |
| `chapter_count` | integer | yes | Number of source chapters. Must be at least 1. |
| `chapters` | list | yes | Ordered source chapter metadata. |

Each `source.chapters` item:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `index` | integer | yes | Chapter order starting from 1. |
| `title` | string | yes | Chapter title or generated label. |
| `summary` | string | no | Optional AI-generated chapter summary. |

Design reason:

Source traceability matters because authors need to know where scenes and adaptation choices came from.

### `ai_analysis`

Type: object

Required: yes

Fields:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `characters` | list | yes | AI character interpretations. May be empty. |
| `relationships` | list | yes | AI-inferred character relationships. May be empty. |
| `key_events` | list | yes | AI-extracted story events. May be empty. |
| `conflicts` | list | yes | AI-inferred dramatic conflicts. May be empty. |
| `themes` | list | yes | AI-inferred thematic statements. May be empty. |
| `candidate_scenes` | list | yes | AI-suggested material with scene potential. May be empty. |
| `uncertainties` | list | yes | Questions that require author confirmation. May be empty. |

All seven fields are required, even when their value is an empty list. This distinguishes a completed analysis with no findings from an omitted or incomplete analysis stage.

Each `characters` item:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `id` | string | yes | Stable character identifier. |
| `name` | string | yes | Character name or AI-generated label. |
| `role` | string | yes | Dramatic role, such as `protagonist` or `supporting`. |
| `description` | string | yes | AI interpretation of the character. |
| `goal` | string | yes | What the character is trying to achieve. |
| `motivation` | string | yes | Why the character pursues the goal. |

Design reason:

Character analysis must expose interpretation, not only extracted names. Goals and motivations directly influence conflict, scene purpose, and later adaptation decisions.

Each `relationships` item:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `id` | string | yes | Stable relationship identifier. |
| `source_character_id` | string | yes | First referenced character ID. |
| `target_character_id` | string | yes | Second referenced character ID. |
| `description` | string | yes | Nature and tension of the relationship. |
| `source_chapter_indexes` | list | yes | Source chapter indexes supporting the interpretation. May be empty. |

Design reason:

Relationships are independent analysis items so authors can confirm or edit them without duplicating relationship data inside both character objects.

Each `key_events` item:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `id` | string | yes | Stable event identifier. |
| `summary` | string | yes | Event summary. |
| `character_ids` | list | yes | Character IDs involved in the event. May be empty. |
| `source_chapter_indexes` | list | yes | Source chapter indexes containing the event. May be empty. |

Design reason:

Stable event IDs let user confirmations and adaptation plans identify which plot points must be preserved.

Each `conflicts` item:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `id` | string | yes | Stable conflict identifier. |
| `description` | string | yes | Opposing goals or forces. |
| `stakes` | string | yes | Consequences if the conflict is not resolved. |
| `character_ids` | list | yes | Character IDs involved in the conflict. May be empty. |
| `source_chapter_indexes` | list | yes | Source chapter indexes supporting the interpretation. May be empty. |

Design reason:

Separating stakes from the conflict description makes the dramatic importance of a conflict explicit and reviewable.

Each `themes` item:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `id` | string | yes | Stable theme identifier. |
| `statement` | string | yes | AI-inferred thematic statement. |
| `source_chapter_indexes` | list | yes | Source chapter indexes supporting the theme. May be empty. |

Design reason:

Themes are explicit analysis items so authors can later decide which ideas the adaptation should preserve or emphasize.

Each `candidate_scenes` item:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `id` | string | yes | Stable candidate-scene identifier. |
| `title` | string | yes | Human-readable candidate title. |
| `summary` | string | yes | Source material represented by the candidate. |
| `dramatic_purpose` | string | yes | Why this material may work as a scene. |
| `location` | string | yes | AI-inferred location or explicit uncertainty label. |
| `time_hint` | string | yes | AI-inferred time cue or explicit uncertainty label. |
| `character_ids` | list | yes | Character IDs likely involved. May be empty. |
| `source_chapter_indexes` | list | yes | Source chapter indexes represented by the candidate. May be empty. |

Design reason:

Candidate scenes identify material with dramatic potential. They are suggestions, not ordered final screenplay scenes or confirmed adaptation decisions.

Each `uncertainties` item:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `id` | string | yes | Stable uncertainty identifier. |
| `question` | string | yes | Question requiring author confirmation. |
| `context` | string | yes | Why the answer matters to the adaptation. |
| `source_chapter_indexes` | list | yes | Source chapter indexes related to the question. May be empty. |
| `options` | list | no | 2-4 predefined options the author can choose from. May be empty. |
| `allow_custom_answer` | boolean | no | Whether the author may provide a free-form answer. Defaults to true. |

Each `uncertainties.options` item:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `id` | string | yes | Stable option identifier. |
| `label` | string | yes | Short option label. |
| `description` | string | yes | What selecting this option means. |
| `impact` | string | yes | How this choice affects the adaptation. |

Design reason:

Uncertainty remains visible so AI does not silently convert ambiguous interpretations into creative facts. Options and custom answers support a one-question-at-a-time confirmation workflow.

The `ai_analysis` field names exactly match the backend's `AIAnalysis.to_dict()` output. This keeps the YAML readable while avoiding a separate export mapping layer.

### `confirmed_analysis`

Type: object

Required: yes

Structure:

`confirmed_analysis` follows the complete `ai_analysis` structure defined above. It contains the same seven required lists and uses the same item fields:

- `characters`
- `relationships`
- `key_events`
- `conflicts`
- `themes`
- `candidate_scenes`
- `uncertainties`

All seven lists must exist, but any or all of them may be empty. Seven empty lists explicitly mean that the author rejected every AI conclusion.

Unlike a patch or action log, `confirmed_analysis` is a complete trusted snapshot. The author may retain, edit, delete, or add analysis items. Its IDs do not need to match raw `ai_analysis` IDs.

Reference rules:

- IDs are unique within each confirmed-analysis category.
- `source_character_id`, `target_character_id`, and `character_ids` reference `confirmed_analysis.characters`.
- `source_chapter_indexes` reference `source.chapters`.
- References do not need to point to raw `ai_analysis` items.

Design reason:

Keeping raw and confirmed analysis separately makes the AI contribution and author corrections reviewable. A complete confirmed snapshot lets later stages read one trusted structure without replaying accept, reject, and edit operations.

### `user_confirmations`

Type: object

Required: yes

Fields:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `accepted_character_ids` | list | no | Characters accepted by the user. |
| `rejected_character_ids` | list | no | Characters rejected by the user. |
| `edited_conflicts` | list | no | User-edited conflict descriptions. |
| `required_plot_points` | list | no | Plot points the final script must preserve. |
| `style_preferences` | object | no | Tone, pacing, genre, or format preferences. |
| `notes` | string | no | Free-form user guidance. |
| `uncertainty_resolutions` | list | no | Ordered answers to AI-raised uncertainties. |

Each `uncertainty_resolutions` item:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `uncertainty_id` | string | yes | References an uncertainty in `ai_analysis.uncertainties`. |
| `selected_option_id` | string | no | ID of the chosen option. Exactly one of `selected_option_id` or `custom_answer` must be present. |
| `custom_answer` | string | no | Free-form answer. Exactly one of `selected_option_id` or `custom_answer` must be present. |

Design reason:

`confirmed_analysis` stores the user's trusted structured story analysis. `user_confirmations` stores guidance outside that analysis, such as required plot points, style preferences, free-form notes, and ordered uncertainty resolutions for one-question-at-a-time confirmation.

### `adaptation_plan`

Type: object

Required: yes

Fields:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `target_format` | string | yes | Planned output format, such as `short_drama`. |
| `structure` | string | yes | Planned script structure description. |
| `scenes` | list | yes | Ordered proposed scene plan. |
| `review_questions` | list | no | Plan-level review questions for the author. |

Each `scenes` item:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `id` | string | yes | Stable scene identifier, e.g. `scene_001`. |
| `scene_order` | integer | yes | Ordinal position in the plan, starting from 1. |
| `title` | string | yes | Human-readable scene title. |
| `dramatic_purpose` | string | yes | Why this scene exists dramatically. |
| `character_ids` | list | yes | Character IDs appearing in this scene. May be empty. |
| `source_chapter_indexes` | list | yes | Source chapter indexes adapted into this scene. May be empty. |
| `retained_event_ids` | list | no | Source event IDs preserved in this scene. |
| `source_candidate_scene_ids` | list | no | Candidate scene IDs this scene is based on. |
| `compression_choices` | list | no | Structured compression decisions. |
| `merge_choices` | list | no | Structured merge decisions. |
| `rewrite_choices` | list | no | Structured rewrite decisions. |
| `review_questions` | list | no | Scene-level review questions. |

Each `compression_choices`, `merge_choices`, or `rewrite_choices` item (AdaptationDecision):

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `id` | string | yes | Stable decision identifier. |
| `description` | string | yes | What the decision does. |
| `reason` | string | yes | Why this adaptation choice was made. |
| `source_event_ids` | list | no | Source event IDs affected by this decision. |

Each `review_questions` item (PlanReviewQuestion):

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `id` | string | yes | Stable question identifier. |
| `question` | string | yes | Question for the author. |
| `context` | string | yes | Why this question matters. |
| `related_scene_ids` | list | no | Scene IDs relevant to this question. |

Design reason:

Adaptation is a planning problem. The plan must be based on `confirmed_analysis`, not raw `ai_analysis`. Structured decisions (compression, merge, rewrite) make AI choices reviewable. Review questions support author-in-the-loop validation at both scene and plan level.

### `screenplay`

Type: object or null

Required: yes (null if not yet generated)

Fields:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `scene_ids` | list | yes | Ordered scene identifiers from the adaptation plan. |
| `revision_notes` | list | yes | AI-generated revision suggestions. May be empty. |

Design reason:

The screenplay draft stores the scene sequence and revision guidance. Detailed scene content (headings, beats, dialogue) is a future extension. The current structure supports review while keeping the format open for author edits.

### `revision_notes`

Type: list of strings

Required: yes

Each item is a plain-text revision note. Notes are generated by AI during screenplay drafting and provide author-actionable feedback such as continuity checks, pacing suggestions, or style recommendations.

Design reason:

AI-generated drafts should help authors continue revising. Simple string notes avoid premature structure on revision feedback, keeping the format lightweight and author-friendly.

## Complete Example

```yaml
schema_version: "1.0"
metadata:
  title: "Untitled Adaptation"
  author: "Original Author"
  adapter: "ScriptWeaver AI"
  target_format: "short_drama"
  language: "zh-CN"
  created_at: "2026-06-05T00:00:00Z"
source:
  source_type: "novel_chapters"
  chapter_count: 3
  chapters:
    - index: 1
      title: "第一章"
      summary: "林照收到父亲留下的密信。"
    - index: 2
      title: "第二章"
      summary: "沈微出现并阻止林照公开密信。"
    - index: 3
      title: "第三章"
      summary: "两人发现密信指向旧案。"
ai_analysis:
  characters:
    - id: "char_001"
      name: "林照"
      role: "protagonist"
      description: "执着追查父亲失踪真相的年轻记者。"
      goal: "查明父亲失踪和旧案之间的联系。"
      motivation: "证明父亲并未背叛家人。"
    - id: "char_002"
      name: "沈微"
      role: "supporting"
      description: "掌握旧案线索、但担心真相造成伤害的协助者。"
      goal: "控制调查范围并保护无辜者。"
      motivation: "避免旧案相关人员再次受到伤害。"
  relationships:
    - id: "relationship_001"
      source_character_id: "char_001"
      target_character_id: "char_002"
      description: "两人共同调查，但对是否公开真相存在分歧。"
      source_chapter_indexes: [1, 2, 3]
  key_events:
    - id: "event_001"
      summary: "林照收到父亲留下的密信。"
      character_ids: ["char_001"]
      source_chapter_indexes: [1]
    - id: "event_002"
      summary: "沈微出现并阻止林照公开密信。"
      character_ids: ["char_001", "char_002"]
      source_chapter_indexes: [2]
    - id: "event_003"
      summary: "林照和沈微发现密信指向旧案。"
      character_ids: ["char_001", "char_002"]
      source_chapter_indexes: [3]
  conflicts:
    - id: "conflict_001"
      description: "林照想公开真相，沈微担心真相会伤害无辜者。"
      stakes: "错误选择可能让旧案相关人员再次陷入危险。"
      character_ids: ["char_001", "char_002"]
      source_chapter_indexes: [1, 2, 3]
  themes:
    - id: "theme_001"
      statement: "追求真相需要面对公开真相的代价。"
      source_chapter_indexes: [1, 2, 3]
  candidate_scenes:
    - id: "candidate_scene_001"
      title: "密信出现"
      summary: "林照收到父亲留下的密信。"
      dramatic_purpose: "引出调查目标和主线悬念。"
      location: "茶馆"
      time_hint: "夜"
      character_ids: ["char_001"]
      source_chapter_indexes: [1]
    - id: "candidate_scene_002"
      title: "巷口阻拦"
      summary: "沈微阻止林照公开密信。"
      dramatic_purpose: "让沈微介入并制造信任危机。"
      location: "巷口"
      time_hint: "夜"
      character_ids: ["char_001", "char_002"]
      source_chapter_indexes: [2]
    - id: "candidate_scene_003"
      title: "旧案线索"
      summary: "两人发现密信指向旧案。"
      dramatic_purpose: "揭示密信与旧案的关联。"
      location: "旧档案室"
      time_hint: "凌晨"
      character_ids: ["char_001", "char_002"]
      source_chapter_indexes: [3]
  uncertainties:
    - id: "uncertainty_001"
      question: "沈微是否提前知道密信内容？"
      context: "答案会影响沈微阻止林照的动机和后续冲突。"
      source_chapter_indexes: [1, 2]
      options:
        - id: "option_001"
          label: "提前知情"
          description: "沈微一直知道密信存在。"
          impact: "强化隐瞒与信任冲突。"
        - id: "option_002"
          label: "刚刚得知"
          description: "沈微与林照同时发现密信。"
          impact: "强化共同调查关系。"
      allow_custom_answer: true
confirmed_analysis:
  characters:
    - id: "char_001"
      name: "林照"
      role: "protagonist"
      description: "执着追查父亲失踪真相的年轻记者。"
      goal: "查明父亲失踪和旧案之间的联系。"
      motivation: "确认父亲留下密信的真实意图，并保护仍然在世的家人。"
    - id: "char_002"
      name: "沈微"
      role: "supporting"
      description: "掌握旧案线索、但担心真相造成伤害的协助者。"
      goal: "控制调查范围并保护无辜者。"
      motivation: "避免旧案相关人员再次受到伤害。"
  relationships:
    - id: "relationship_001"
      source_character_id: "char_001"
      target_character_id: "char_002"
      description: "两人共同调查，但对是否公开真相存在分歧。"
      source_chapter_indexes: [1, 2, 3]
  key_events:
    - id: "event_001"
      summary: "林照收到父亲留下的密信。"
      character_ids: ["char_001"]
      source_chapter_indexes: [1]
    - id: "event_002"
      summary: "沈微出现并阻止林照公开密信。"
      character_ids: ["char_001", "char_002"]
      source_chapter_indexes: [2]
    - id: "event_003"
      summary: "林照和沈微发现密信指向旧案。"
      character_ids: ["char_001", "char_002"]
      source_chapter_indexes: [3]
  conflicts:
    - id: "conflict_001"
      description: "林照想公开真相，沈微担心真相会伤害无辜者。"
      stakes: "如果两人无法决定公开范围，旧案受害者和林照的家人都可能再次受到威胁。"
      character_ids: ["char_001", "char_002"]
      source_chapter_indexes: [1, 2, 3]
  themes:
    - id: "theme_001"
      statement: "追求真相需要面对公开真相的代价。"
      source_chapter_indexes: [1, 2, 3]
  candidate_scenes:
    - id: "candidate_scene_001"
      title: "密信出现"
      summary: "林照收到父亲留下的密信。"
      dramatic_purpose: "引出调查目标和主线悬念。"
      location: "茶馆"
      time_hint: "夜"
      character_ids: ["char_001"]
      source_chapter_indexes: [1]
    - id: "candidate_scene_003"
      title: "旧案线索"
      summary: "两人发现密信指向旧案。"
      dramatic_purpose: "揭示密信与旧案的关联。"
      location: "旧档案室"
      time_hint: "凌晨"
      character_ids: ["char_001", "char_002"]
      source_chapter_indexes: [3]
  uncertainties: []
user_confirmations:
  accepted_character_ids: ["char_001", "char_002"]
  rejected_character_ids: []
  edited_conflicts: []
  required_plot_points: ["密信必须保留"]
  style_preferences:
    tone: "悬疑"
    pacing: "紧凑"
  notes: "强化林照和沈微之间的不信任。"
  uncertainty_resolutions:
    - uncertainty_id: "uncertainty_001"
      selected_option_id: "option_001"
adaptation_plan:
  target_format: "short_drama"
  structure: "three_scene_sequence"
  scenes:
    - id: "scene_001"
      scene_order: 1
      title: "密信出现"
      dramatic_purpose: "建立悬念"
      character_ids: ["char_001"]
      source_chapter_indexes: [1]
      retained_event_ids: ["event_001"]
      source_candidate_scene_ids: ["candidate_scene_001"]
      compression_choices:
        - id: "compression_001"
          description: "压缩环境描写为单一场。"
          reason: "短剧需要在有限时间内展现核心冲突。"
          source_event_ids: ["event_001"]
      merge_choices: []
      rewrite_choices:
        - id: "rewrite_001"
          description: "将心理活动改为动作和停顿。"
          reason: "视觉媒介需要用可见动作传达内心冲突。"
          source_event_ids: ["event_001"]
      review_questions:
        - id: "review_001"
          question: "场景 1 的密信改编是否保留了核心冲突？"
          context: "原始章节包含关键悬念信息。"
          related_scene_ids: ["scene_001"]
    - id: "scene_002"
      scene_order: 2
      title: "巷口阻拦"
      dramatic_purpose: "升级冲突"
      character_ids: ["char_001", "char_002"]
      source_chapter_indexes: [2]
      retained_event_ids: ["event_002"]
      source_candidate_scene_ids: ["candidate_scene_002"]
      compression_choices:
        - id: "compression_002"
          description: "压缩追赶过程为对峙场景。"
          reason: "集中冲突，避免冗长追逐。"
          source_event_ids: ["event_002"]
      merge_choices: []
      rewrite_choices:
        - id: "rewrite_002"
          description: "将解释性叙述改为对峙对白。"
          reason: "对白比叙述更适合短剧节奏。"
          source_event_ids: ["event_002"]
      review_questions: []
    - id: "scene_003"
      scene_order: 3
      title: "旧案线索"
      dramatic_purpose: "揭示线索"
      character_ids: ["char_001", "char_002"]
      source_chapter_indexes: [3]
      retained_event_ids: ["event_003"]
      source_candidate_scene_ids: ["candidate_scene_003"]
      compression_choices:
        - id: "compression_003"
          description: "压缩查找档案过程。"
          reason: "过程细节不影响核心冲突。"
          source_event_ids: ["event_003"]
      merge_choices:
        - id: "merge_001"
          description: "合并次要线索到主场景。"
          reason: "避免引入过多角色和地点。"
          source_event_ids: ["event_003"]
      rewrite_choices: []
      review_questions: []
  review_questions:
    - id: "review_overall"
      question: "整体结构是否符合短剧节奏要求？"
      context: "共 3 个章节改编为场景。"
      related_scene_ids: ["scene_001", "scene_002", "scene_003"]
screenplay:
  scene_ids: ["scene_001", "scene_002", "scene_003"]
  revision_notes:
    - "场景 1 需要导演审查节奏。"
    - "场景 2 对话需要润色。"
    - "scene_003 的旧案线索需要与后续章节证据保持一致。"
revision_notes:
  - "场景 1 需要导演审查节奏。"
  - "场景 2 对话需要润色。"
  - "scene_003 的旧案线索需要与后续章节证据保持一致。"
```

## Validation Expectations

Future implementations should validate:

- `schema_version` exists.
- `metadata`, `source`, `ai_analysis`, `confirmed_analysis`, `user_confirmations`, `adaptation_plan`, `screenplay`, and `revision_notes` are required top-level sections.
- `source.chapter_count` is at least 1.
- `source.chapters` length matches `source.chapter_count`.
- All seven `ai_analysis` list fields exist, even when a list is empty.
- Every analysis item contains all fields defined for its category.
- Analysis item IDs are unique within their category.
- `source_character_id`, `target_character_id`, and `character_ids` reference existing `ai_analysis.characters` IDs.
- `source_chapter_indexes` reference existing `source.chapters` indexes.
- Candidate scenes are suggestions and do not need to match or order final screenplay scenes.
- Uncertainty questions include `options` (2-4 items or empty) and `allow_custom_answer`.
- Uncertainty option IDs are unique within each uncertainty.
- `confirmed_analysis` follows the same seven-list and item-field rules as `ai_analysis`.
- Confirmed analysis item IDs are unique within their category.
- Confirmed `source_character_id`, `target_character_id`, and `character_ids` reference `confirmed_analysis.characters` IDs.
- Confirmed `source_chapter_indexes` reference existing `source.chapters` indexes.
- `confirmed_analysis` may contain seven empty lists.
- `user_confirmations.uncertainty_resolutions` entries reference existing `ai_analysis.uncertainties` IDs.
- Each resolution provides exactly one of `selected_option_id` or `custom_answer`.
- `adaptation_plan` is based on `confirmed_analysis`, not raw `ai_analysis`.
- `adaptation_plan.scenes` scene IDs and `scene_order` values are unique.
- `adaptation_plan.scenes` reference existing confirmed character IDs and source chapter indexes.
- `screenplay.scene_ids` reference `adaptation_plan.scenes` IDs. May be empty if not yet generated.
- `revision_notes` contains plain-text strings. May be empty.
