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
| `chapter_count` | integer | yes | Number of source chapters. Must be at least 3. |
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
| `characters` | list | yes | Raw AI character extraction. |
| `relationships` | list | no | Raw AI relationship extraction. |
| `conflicts` | list | yes | Raw AI conflict extraction. |
| `key_events` | list | yes | Raw AI event extraction. |
| `locations` | list | no | Raw AI location extraction. |
| `candidate_scenes` | list | yes | AI-suggested scene candidates. |
| `uncertainties` | list | no | AI-flagged ambiguity or missing context. |

Design reason:

This section makes the AI contribution reviewable instead of hiding it inside the final script.

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

The final script should be based on user-confirmed creative decisions, not raw AI guesses.

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

Adaptation is a planning problem. Recording the plan lets users understand and revise the AI's creative decisions.

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
      goal: "查明父亲失踪真相"
    - id: "char_002"
      name: "沈微"
      role: "ally_with_secret"
      goal: "阻止真相伤害无辜者"
  relationships:
    - from: "char_001"
      to: "char_002"
      type: "allies_with_hidden_conflict"
      description: "两人目标相近，但对公开真相的代价判断不同。"
  conflicts:
    - id: "conflict_001"
      description: "林照想公开真相，沈微担心真相会伤害无辜者。"
  key_events:
    - id: "event_001"
      source_chapter: 1
      summary: "林照收到父亲留下的密信。"
    - id: "event_002"
      source_chapter: 2
      summary: "沈微出现并阻止林照公开密信。"
    - id: "event_003"
      source_chapter: 3
      summary: "林照和沈微发现密信指向旧案。"
  locations:
    - id: "loc_001"
      name: "茶馆"
    - id: "loc_002"
      name: "巷口"
    - id: "loc_003"
      name: "旧档案室"
  candidate_scenes:
    - id: "candidate_scene_001"
      source_chapters: [1]
      location: "茶馆"
      dramatic_purpose: "引出密信和主线悬念。"
    - id: "candidate_scene_002"
      source_chapters: [2]
      location: "巷口"
      dramatic_purpose: "让沈微介入并制造信任危机。"
    - id: "candidate_scene_003"
      source_chapters: [3]
      location: "旧档案室"
      dramatic_purpose: "揭示密信与旧案的关联。"
  uncertainties:
    - "沈微是否提前知道密信内容需要作者确认。"
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
- `metadata`, `source`, `ai_analysis`, `user_confirmations`, `adaptation_plan`, `screenplay`, and `revision_notes` are required top-level sections.
- `source.chapter_count` is at least 3.
- `source.chapters` length matches `source.chapter_count`.
- `screenplay.scenes` is not empty.
- Each scene has a heading and at least one beat.
- Dialogue beats include `character`.
- Scene source chapter references point to existing source chapters.
- `adaptation_plan.scene_breakdown` references align with `screenplay.scenes`.
