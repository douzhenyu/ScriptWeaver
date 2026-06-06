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

Design reason:

Uncertainty remains visible so AI does not silently convert ambiguous interpretations into creative facts.

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

Design reason:

`confirmed_analysis` stores the user's trusted structured story analysis. `user_confirmations` stores guidance outside that analysis, such as required plot points, style preferences, and free-form notes.

### `adaptation_plan`

Type: object

Required: yes

Fields:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `target_format` | string | yes | Planned output format. |
| `structure` | string | yes | Planned script structure. |
| `scene_breakdown` | list | yes | Ordered proposed scene plan. |

Each `scene_breakdown` item:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `scene_id` | string | yes | Stable scene identifier. |
| `source_chapters` | list | yes | Source chapter indexes. |
| `purpose` | string | yes | Dramatic purpose of the scene. |
| `retained_events` | list | no | Source event IDs preserved in this scene. |
| `compression_choices` | list | no | Content compressed by AI. |
| `merge_choices` | list | no | Content merged by AI. |
| `rewrite_choices` | list | no | Content transformed from prose to drama. |

Design reason:

Adaptation is a planning problem. The plan must be based on `confirmed_analysis`, not raw `ai_analysis`. Recording the plan lets users understand and revise the AI's creative decisions.

### `screenplay`

Type: object

Required: yes

Fields:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `scenes` | list | yes | Ordered screenplay scenes. |

Each `screenplay.scenes` item:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `id` | string | yes | Scene identifier. |
| `heading` | object | yes | Scene heading. |
| `source_chapters` | list | yes | Source chapter indexes. |
| `characters` | list | no | Character names appearing in the scene. |
| `beats` | list | yes | Action, dialogue, narration, or transition beats. |

Each `heading` object:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `type` | string | yes | `INT`, `EXT`, or another supported scene type. |
| `location` | string | yes | Scene location. |
| `time` | string | yes | Time of day or story time. |

Each `beats` item:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `type` | string | yes | `action`, `dialogue`, `narration`, `transition`, or `note`. |
| `text` | string | yes | Beat text. |
| `character` | string | required for dialogue | Speaking character. |

Design reason:

Scenes and beats make the script editable while preserving enough structure for future UI rendering and validation.

### `revision_notes`

Type: list

Required: yes

Each item:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `type` | string | yes | Note category, such as `author_review`, `continuity`, or `style`. |
| `text` | string | yes | Note content. |
| `related_scene_id` | string | no | Scene related to this note. |

Design reason:

AI-generated drafts should help authors continue revising. Revision notes make uncertainty and suggested improvements visible.

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
adaptation_plan:
  target_format: "short_drama"
  structure: "three_scene_sequence"
  scene_breakdown:
    - scene_id: "scene_001"
      source_chapters: [1]
      purpose: "建立悬念"
      retained_events: ["event_001"]
      compression_choices: ["压缩环境描写"]
      merge_choices: []
      rewrite_choices: ["将心理活动改为动作和停顿"]
    - scene_id: "scene_002"
      source_chapters: [2]
      purpose: "升级冲突"
      retained_events: ["event_002"]
      compression_choices: ["压缩追赶过程"]
      merge_choices: []
      rewrite_choices: ["将解释性叙述改为对峙对白"]
    - scene_id: "scene_003"
      source_chapters: [3]
      purpose: "揭示线索"
      retained_events: ["event_003"]
      compression_choices: ["压缩查找档案过程"]
      merge_choices: ["合并次要线索"]
      rewrite_choices: ["用物证和沉默呈现发现"]
screenplay:
  scenes:
    - id: "scene_001"
      heading:
        type: "INT"
        location: "茶馆"
        time: "夜"
      source_chapters: [1]
      characters: ["林照", "沈微"]
      beats:
        - type: "action"
          text: "雨声敲打窗棂。林照坐在角落，手指反复摩挲茶杯边缘。"
        - type: "dialogue"
          character: "林照"
          text: "你早就知道了，对吗？"
        - type: "action"
          text: "沈微没有回答，只把信推到他面前。"
    - id: "scene_002"
      heading:
        type: "EXT"
        location: "巷口"
        time: "夜"
      source_chapters: [2]
      characters: ["林照", "沈微"]
      beats:
        - type: "action"
          text: "林照冲出茶馆，沈微拦在巷口，雨水顺着伞沿落下。"
        - type: "dialogue"
          character: "沈微"
          text: "现在公开，只会让更多人被拖进去。"
        - type: "dialogue"
          character: "林照"
          text: "所以你要我继续装作什么都不知道？"
    - id: "scene_003"
      heading:
        type: "INT"
        location: "旧档案室"
        time: "凌晨"
      source_chapters: [3]
      characters: ["林照", "沈微"]
      beats:
        - type: "action"
          text: "旧档案室的灯忽明忽暗。林照翻开泛黄卷宗，信纸上的编号与卷宗封条重合。"
        - type: "dialogue"
          character: "沈微"
          text: "这不是失踪案，是有人把它藏成了失踪案。"
        - type: "note"
          text: "此处保留旧案真相的部分信息，为后续章节留悬念。"
revision_notes:
  - type: "author_review"
    text: "沈微是否提前知道密信内容会影响后续人物动机。"
    related_scene_id: "scene_001"
  - type: "continuity"
    text: "scene_003 的旧案线索需要与后续章节证据保持一致。"
    related_scene_id: "scene_003"
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
- Uncertainty questions remain available for user confirmation.
- `confirmed_analysis` follows the same seven-list and item-field rules as `ai_analysis`.
- Confirmed analysis item IDs are unique within their category.
- Confirmed `source_character_id`, `target_character_id`, and `character_ids` reference `confirmed_analysis.characters` IDs.
- Confirmed `source_chapter_indexes` reference existing `source.chapters` indexes.
- `confirmed_analysis` may contain seven empty lists.
- `adaptation_plan` is based on `confirmed_analysis`, not raw `ai_analysis`.
- `screenplay.scenes` is not empty.
- Each scene has a heading and at least one beat.
- Dialogue beats include `character`.
- Scene source chapter references point to existing source chapters.
- `adaptation_plan.scene_breakdown` references align with `screenplay.scenes`.
