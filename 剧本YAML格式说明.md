# ScriptWeaver 剧本 YAML 格式说明

## 目的

本文档定义了 ScriptWeaver 在人工参与的 AI 改编工作流后生成的 YAML 结构。

该格式专为可编辑的剧本草稿设计。它同时存储最终的剧本正文以及产生该剧本的 AI 辅助决策过程。

## 设计原则

1. **可追溯：** 每个剧本场景均可追溯至原始章节和关键事件。
2. **可交互：** 用户确认内容独立于原始 AI 分析存储。
3. **可编辑：** YAML 可读、可由作者或工具直接修改。
4. **AI 可见：** 格式将 AI 分析、改编规划和修订建议显式化。
5. **面向草稿：** 格式支持早期创意起草阶段，而非最终制作排期。

## 顶层结构

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

## 字段定义

### `schema_version`

类型：string（必填）

含义：标识此 YAML 产物使用的 schema 版本号。

设计理由：后端和未来的 Web UI 需要一种稳定的方式来处理格式变更。

### `metadata`

类型：object（必填）

| 字段 | 类型 | 必填 | 含义 |
| --- | --- | --- | --- |
| `title` | string | 是 | 改编项目标题。 |
| `author` | string | 否 | 原始小说作者。 |
| `adapter` | string | 否 | 人工或 AI 改编者标识。 |
| `target_format` | string | 是 | 目标剧本形式，如 `short_drama`、`film`、`episode`。 |
| `language` | string | 是 | 输出语言，如 `zh-CN`。 |
| `created_at` | string | 否 | ISO 格式的创建时间戳。 |

设计理由：YAML 应能作为独立产物使用，而不仅仅是后端接口的返回内容。

### `source`

类型：object（必填）

| 字段 | 类型 | 必填 | 含义 |
| --- | --- | --- | --- |
| `source_type` | string | 是 | 来源输入类型，通常为 `novel_chapters`。 |
| `chapter_count` | integer | 是 | 原始章节数，至少为 1。 |
| `chapters` | list | 是 | 有序的原始章节元数据。 |

每项 `source.chapters`：

| 字段 | 类型 | 必填 | 含义 |
| --- | --- | --- | --- |
| `index` | integer | 是 | 章节顺序，从 1 开始。 |
| `title` | string | 是 | 章节标题或生成的标签。 |
| `summary` | string | 否 | 可选的 AI 章节摘要。 |

设计理由：来源可追溯性很重要，因为作者需要了解场景和改编决策的出处。

### `ai_analysis`

类型：object（必填）

| 字段 | 类型 | 必填 | 含义 |
| --- | --- | --- | --- |
| `characters` | list | 是 | AI 角色解读。可为空。 |
| `relationships` | list | 是 | AI 推断的角色关系。可为空。 |
| `key_events` | list | 是 | AI 提取的故事事件。可为空。 |
| `conflicts` | list | 是 | AI 推断的戏剧冲突。可为空。 |
| `themes` | list | 是 | AI 推断的主题表述。可为空。 |
| `candidate_scenes` | list | 是 | AI 建议的具有场景潜力的素材。可为空。 |
| `uncertainties` | list | 是 | 需要作者确认的问题。可为空。 |

全部七个字段都是必填的，即使其值为空列表。这用于区分"已完成分析但无发现"与"省略或未完成的分析阶段"。

每项 `characters`：

| 字段 | 类型 | 必填 | 含义 |
| --- | --- | --- | --- |
| `id` | string | 是 | 稳定的角色标识符。 |
| `name` | string | 是 | 角色名或 AI 生成的标签。 |
| `role` | string | 是 | 戏剧角色，如 `protagonist`（主角）或 `supporting`（配角）。 |
| `description` | string | 是 | AI 对角色的解读。 |
| `goal` | string | 是 | 角色尝试达成的目标。 |
| `motivation` | string | 是 | 角色追求目标的动机。 |

设计理由：角色分析必须展示解读，而不仅仅是提取姓名。目标和动机直接影响冲突、场景目的和后续改编决策。

每项 `relationships`：

| 字段 | 类型 | 必填 | 含义 |
| --- | --- | --- | --- |
| `id` | string | 是 | 稳定的关系标识符。 |
| `source_character_id` | string | 是 | 第一个关联的角色 ID。 |
| `target_character_id` | string | 是 | 第二个关联的角色 ID。 |
| `description` | string | 是 | 关系的性质与张力。 |
| `source_chapter_indexes` | list | 是 | 支持此解读的原始章节索引。可为空。 |

设计理由：关系是独立的分析条目，作者可以在不重复角色对象内关系数据的情况下确认或编辑它们。

每项 `key_events`：

| 字段 | 类型 | 必填 | 含义 |
| --- | --- | --- | --- |
| `id` | string | 是 | 稳定的事件标识符。 |
| `summary` | string | 是 | 事件摘要。 |
| `character_ids` | list | 是 | 涉及该事件的角色 ID。可为空。 |
| `source_chapter_indexes` | list | 是 | 包含该事件的原始章节索引。可为空。 |

设计理由：稳定的事件 ID 让用户确认和改编计划能够标识哪些情节点必须保留。

每项 `conflicts`：

| 字段 | 类型 | 必填 | 含义 |
| --- | --- | --- | --- |
| `id` | string | 是 | 稳定的冲突标识符。 |
| `description` | string | 是 | 对立的欲望或力量。 |
| `stakes` | string | 是 | 冲突未解决的后果。 |
| `character_ids` | list | 是 | 涉及该冲突的角色 ID。可为空。 |
| `source_chapter_indexes` | list | 是 | 支持此解读的原始章节索引。可为空。 |

设计理由：将"赌注"与冲突描述分离，使冲突的戏剧重要性变得明确且可审查。

每项 `themes`：

| 字段 | 类型 | 必填 | 含义 |
| --- | --- | --- | --- |
| `id` | string | 是 | 稳定的主题标识符。 |
| `statement` | string | 是 | AI 推断的主题表述。 |
| `source_chapter_indexes` | list | 是 | 支持此主题的原始章节索引。可为空。 |

设计理由：主题是显式的分析条目，作者可以在之后决定改编应保留或强调哪些主题。

每项 `candidate_scenes`：

| 字段 | 类型 | 必填 | 含义 |
| --- | --- | --- | --- |
| `id` | string | 是 | 稳定的候选场景标识符。 |
| `title` | string | 是 | 人类可读的候选标题。 |
| `summary` | string | 是 | 该候选所代表的原始素材。 |
| `dramatic_purpose` | string | 是 | 为什么这段素材适合作为场景。 |
| `location` | string | 是 | AI 推断的地点或显式的不确定标记。 |
| `time_hint` | string | 是 | AI 推断的时间提示或显式的不确定标记。 |
| `character_ids` | list | 是 | 可能涉及的角色 ID。可为空。 |
| `source_chapter_indexes` | list | 是 | 该候选所代表的原始章节索引。可为空。 |

设计理由：候选场景识别具有戏剧潜力的素材。它们是建议，而非有序的最终剧本场景或已确认的改编决策。

每项 `uncertainties`：

| 字段 | 类型 | 必填 | 含义 |
| --- | --- | --- | --- |
| `id` | string | 是 | 稳定的不确定性标识符。 |
| `question` | string | 是 | 需要作者确认的问题。 |
| `context` | string | 是 | 答案对改编的影响说明。 |
| `source_chapter_indexes` | list | 是 | 与该问题相关的原始章节索引。可为空。 |
| `options` | list | 否 | 2-4 个预设选项供作者选择。可为空。 |
| `allow_custom_answer` | boolean | 否 | 作者是否可以提供自由回答。默认为 true。 |

每项 `uncertainties.options`：

| 字段 | 类型 | 必填 | 含义 |
| --- | --- | --- | --- |
| `id` | string | 是 | 稳定的选项标识符。 |
| `label` | string | 是 | 简短选项标签。 |
| `description` | string | 是 | 选择该选项的含义。 |
| `impact` | string | 是 | 该选择如何影响改编。 |

设计理由：不确定性保持可见，避免 AI 悄悄将模糊解读转变为创作事实。选项和自定义回答支持逐个问题确认的工作流程。

`ai_analysis` 的字段名与后端 `AIAnalysis.to_dict()` 的输出完全一致，保持 YAML 可读的同时避免额外的导出映射层。

### `confirmed_analysis`

类型：object（必填）

结构：

`confirmed_analysis` 遵循上述完整的 `ai_analysis` 结构，包含相同的七个必填列表并使用相同的条目字段：

- `characters`
- `relationships`
- `key_events`
- `conflicts`
- `themes`
- `candidate_scenes`
- `uncertainties`

全部七个列表必须存在，但其中任意或全部均可为空。七个空列表意味着作者拒绝了所有 AI 的结论。

与补丁或操作日志不同，`confirmed_analysis` 是一份完整的受信任快照。作者可以保留、编辑、删除或新增分析条目。其 ID 无需与原始 `ai_analysis` 的 ID 匹配。

引用规则：

- ID 在每个已确认分析类别内唯一。
- `source_character_id`、`target_character_id` 和 `character_ids` 应引用 `confirmed_analysis.characters`。
- `source_chapter_indexes` 应引用 `source.chapters`。
- 引用无需指向原始 `ai_analysis` 条目。

设计理由：分开存储原始分析和已确认分析，使 AI 的贡献和作者的修改可审查。一份完整的已确认快照让后续阶段只需读取一个受信任的结构，而无需重放接受、拒绝和编辑操作。

### `user_confirmations`

类型：object（必填）

| 字段 | 类型 | 必填 | 含义 |
| --- | --- | --- | --- |
| `accepted_character_ids` | list | 否 | 用户接受的角色。 |
| `required_plot_points` | list | 否 | 最终剧本必须保留的情节点。 |
| `notes` | string | 否 | 自由形式的用户指导意见。 |
| `uncertainty_resolutions` | list | 否 | 对 AI 提出的不确定性的有序回答。 |

每项 `uncertainty_resolutions`：

| 字段 | 类型 | 必填 | 含义 |
| --- | --- | --- | --- |
| `uncertainty_id` | string | 是 | 引用 `ai_analysis.uncertainties` 中的一项不确定性。 |
| `selected_option_id` | string | 否 | 所选选项的 ID。`selected_option_id` 与 `custom_answer` 二者必须有且仅有一个。 |
| `custom_answer` | string | 否 | 自由形式回答。`selected_option_id` 与 `custom_answer` 二者必须有且仅有一个。 |

设计理由：`confirmed_analysis` 存储用户确认的受信任故事分析；`user_confirmations` 存储该分析之外的指导意见，包括必须保留的情节点、风格偏好、自由形式备注以及针对逐个问题确认的有序不确定性解决方案。

### `adaptation_plan`

类型：object（必填）

| 字段 | 类型 | 必填 | 含义 |
| --- | --- | --- | --- |
| `target_format` | string | 是 | 计划生成的目标格式，如 `short_drama`。 |
| `structure` | string | 是 | 计划的剧本结构描述。 |
| `scenes` | list | 是 | 有序的场景计划方案。 |
| `review_questions` | list | 否 | 面向作者的计划级审核问题。 |

每项 `scenes`：

| 字段 | 类型 | 必填 | 含义 |
| --- | --- | --- | --- |
| `id` | string | 是 | 稳定的场景标识符，如 `scene_001`。 |
| `scene_order` | integer | 是 | 计划中的顺序位置，从 1 开始。 |
| `title` | string | 是 | 人类可读的场景标题。 |
| `dramatic_purpose` | string | 是 | 此场景在戏剧上的存在理由。 |
| `character_ids` | list | 是 | 此场景中出现的角色 ID。可为空。 |
| `source_chapter_indexes` | list | 是 | 改编到此场景的原始章节索引。可为空。 |
| `retained_event_ids` | list | 否 | 此场景中保留的原始事件 ID。 |
| `source_candidate_scene_ids` | list | 否 | 此场景所基于的候选场景 ID。 |
| `compression_choices` | list | 否 | 结构化的压缩决策。 |
| `merge_choices` | list | 否 | 结构化的合并决策。 |
| `rewrite_choices` | list | 否 | 结构化的改写决策。 |
| `review_questions` | list | 否 | 场景级审核问题。 |

每项 `compression_choices`、`merge_choices` 或 `rewrite_choices`（AdaptationDecision）：

| 字段 | 类型 | 必填 | 含义 |
| --- | --- | --- | --- |
| `id` | string | 是 | 稳定的决策标识符。 |
| `description` | string | 是 | 决策做了什么。 |
| `reason` | string | 是 | 为什么做出此改编选择。 |
| `source_event_ids` | list | 否 | 受此决策影响的原始事件 ID。 |

每项 `review_questions`（PlanReviewQuestion）：

| 字段 | 类型 | 必填 | 含义 |
| --- | --- | --- | --- |
| `id` | string | 是 | 稳定的问题标识符。 |
| `question` | string | 是 | 向作者提出的问题。 |
| `context` | string | 是 | 此问题为什么重要。 |
| `related_scene_ids` | list | 否 | 与此问题相关的场景 ID。 |

设计理由：改编是一个规划问题。改编计划必须基于 `confirmed_analysis` 而非原始 `ai_analysis`。结构化的决策（压缩、合并、改写）使 AI 的选择可审查。审核问题支持在场景和计划两个层面进行作者参与的验证。

### `screenplay`

类型：object 或 null（必填；尚未生成时为 null）

| 字段 | 类型 | 必填 | 含义 |
| --- | --- | --- | --- |
| `scenes` | list | 是 | 有序的剧本场景，含场景标题和节拍。 |
| `revision_notes` | list | 是 | AI 生成的修订建议。可为空。 |

每项 `scenes`：

| 字段 | 类型 | 必填 | 含义 |
| --- | --- | --- | --- |
| `id` | string | 是 | 与改编计划匹配的稳定场景标识符。 |
| `heading` | object | 是 | 包含地点、时间和内/外景的场景标题。 |
| `source_chapter_indexes` | list | 是 | 改编到此场景的原始章节索引。可为空。 |
| `character_ids` | list | 是 | 此场景中出现的角色 ID。可为空。 |
| `beats` | list | 是 | 有序的动作、对白、旁白和转场。必须至少包含 4 个节拍。 |

每项 `heading`：

| 字段 | 类型 | 必填 | 含义 |
| --- | --- | --- | --- |
| `location` | string | 是 | 场景地点。 |
| `time` | string | 是 | 时间提示。 |
| `interior_exterior` | string | 是 | `INT`（内景）、`EXT`（外景）或 `INT/EXT`（内外景）。中文值（`内景`、`外景`、`内外景`）在校验时自动标准化。 |

每项 `beats`：

| 字段 | 类型 | 必填 | 含义 |
| --- | --- | --- | --- |
| `type` | string | 是 | 节拍类型：`action`（动作）、`dialogue`（对白）、`voiceover`（旁白）或 `transition`（转场）。 |
| `text` | string | 是 | 节拍内容（动作描述或对白台词）。 |
| `character_id` | string 或 null | 是 | 对白和旁白的角色 ID；动作和转场为 null。 |

设计理由：

- **稳定的场景 ID** 允许场景与改编计划和审核问题进行交叉引用。
- **原始章节索引** 保留对原始小说的可追溯性，使作者可以核实哪些内容被改编。
- **结构化的场景标题**（地点、时间、内/外景）使场景可过滤，并可转换为标准剧本格式。
- **有序的节拍** 将剧本呈现为动作-对白序列，符合剧本写作和制作方式。
- **对白和旁白的 character_id** 通过 ID 引用角色，将角色身份与说出的文本分离，便于配音分配。`dialogue` 和 `voiceover` 类型的节拍必须提供非 null 的 `character_id`；`action` 和 `transition` 类型必须为 null。
- **剧本与 revision_notes 分离** 使作者可以独立审查创作草稿和 AI 反馈。
- **最少 4 个节拍** 防止输出过于单薄或概括化。每个关键时刻和对白交流都应展开为具体的节拍。
- **转场节拍** 允许在单个场景标题内连接时间或空间的变化。

### `revision_notes`

类型：字符串列表（必填）

每项为纯文本修订备注。备注由 AI 在剧本起草过程中生成，提供面向作者的可操作反馈，如连贯性检查、节奏建议或风格建议。

设计理由：AI 生成的草稿应帮助作者持续修改。简单的文本备注避免了修订反馈的过早结构化，保持格式的轻量化和作者友好性。

## 完整示例

```yaml
schema_version: "1.0"
metadata:
  title: "未命名改编"
  author: "原作者"
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
  required_plot_points: ["密信必须保留"]
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
  scenes:
    - id: "scene_001"
      heading:
        location: "茶馆"
        time: "夜"
        interior_exterior: "INT"
      source_chapter_indexes: [1]
      character_ids: ["char_001"]
      beats:
        - type: "action"
          text: "林照拆开父亲留下的密信，手指微微发抖。"
          character_id: null
        - type: "dialogue"
          text: "这不是父亲的笔迹。"
          character_id: "char_001"
        - type: "voiceover"
          text: "二十年前，他用这种纸给我写过信。"
          character_id: "char_001"
        - type: "action"
          text: "林照将信纸举到灯下，辨认褪色的字迹。"
          character_id: null
    - id: "scene_002"
      heading:
        location: "巷口"
        time: "夜"
        interior_exterior: "EXT"
      source_chapter_indexes: [2]
      character_ids: ["char_001", "char_002"]
      beats:
        - type: "action"
          text: "沈微从暗处走出，一把拦住林照的去路。"
          character_id: null
        - type: "dialogue"
          text: "你不能公开这封信。"
          character_id: "char_002"
        - type: "dialogue"
          text: "你知道这封信？为什么瞒着我？"
          character_id: "char_001"
        - type: "action"
          text: "沈微沉默片刻，目光扫过巷口的监控摄像头。"
          character_id: null
        - type: "dialogue"
          text: "先跟我走，这里不安全。"
          character_id: "char_002"
    - id: "scene_003"
      heading:
        location: "旧档案室"
        time: "凌晨"
        interior_exterior: "INT"
      source_chapter_indexes: [3]
      character_ids: ["char_001", "char_002"]
      beats:
        - type: "action"
          text: "两人翻找积灰的旧档案，手电筒光束扫过发黄的文件夹。"
          character_id: null
        - type: "dialogue"
          text: "原来父亲一直在查这个案子。"
          character_id: "char_001"
        - type: "action"
          text: "沈微抽出一份标有\"绝密\"的卷宗，手指停在日期一栏。"
          character_id: null
        - type: "dialogue"
          text: "二十年前的悬案……当天值班记录被人撕掉了。"
          character_id: "char_002"
        - type: "transition"
          text: "天光微亮，两人仍在档案室翻阅。"
          character_id: null
  revision_notes:
    - "场景 1 需要导演审查节奏。"
    - "场景 2 对话需要润色。"
    - "scene_003 的旧案线索需要与后续章节证据保持一致。"
revision_notes:
  - "场景 1 需要导演审查节奏。"
  - "场景 2 对话需要润色。"
  - "scene_003 的旧案线索需要与后续章节证据保持一致。"
```

## 校验规则

未来的实现应对以下内容进行校验：

- `schema_version` 必须存在。
- `metadata`、`source`、`ai_analysis`、`confirmed_analysis`、`user_confirmations`、`adaptation_plan`、`screenplay` 和 `revision_notes` 是必填的顶层区块。
- `source.chapter_count` 至少为 1。
- `source.chapters` 长度与 `source.chapter_count` 一致。
- `ai_analysis` 的七个列表字段全部存在，即使列表为空。
- 每条分析条目包含其类别定义的全部字段。
- 分析条目 ID 在各自类别内唯一。
- `source_character_id`、`target_character_id` 和 `character_ids` 应引用已有的 `ai_analysis.characters` ID。
- `source_chapter_indexes` 应引用已有的 `source.chapters` 索引。
- 候选场景是建议项，无需与最终剧本场景匹配或有序。
- `uncertainties` 条目应包含 `options`（2-4 项或空）和 `allow_custom_answer`。
- 不确定性选项 ID 在每个不确定性内唯一。
- `confirmed_analysis` 遵循与 `ai_analysis` 相同的七列表和条目字段规则。
- 已确认分析条目 ID 在各自类别内唯一。
- 已确认的 `source_character_id`、`target_character_id` 和 `character_ids` 应引用 `confirmed_analysis.characters` ID。
- 已确认的 `source_chapter_indexes` 应引用已有的 `source.chapters` 索引。
- `confirmed_analysis` 可包含七个空列表。
- `user_confirmations.uncertainty_resolutions` 条目应引用已有的 `ai_analysis.uncertainties` ID。
- 每个解决方案恰好提供 `selected_option_id` 或 `custom_answer` 之一。
- `adaptation_plan` 基于 `confirmed_analysis`，而非原始 `ai_analysis`。
- `adaptation_plan.scenes` 的场景 ID 和 `scene_order` 值唯一。
- `adaptation_plan.scenes` 引用已有的已确认角色 ID 和原始章节索引。
- `screenplay.scenes` ID 必须存在于 `adaptation_plan.scenes` 中。场景数量必须与计划一致。未生成时可为空。
- `screenplay.scenes` 排序与 `adaptation_plan.scenes`（按 `scene_order`）一致。
- 每个 `screenplay.scene` 必须至少包含 4 个节拍。
- 节拍类型必须为 `action`、`dialogue`、`voiceover`、`transition` 之一。
- `dialogue` 和 `voiceover` 类型的节拍必须提供非 null、非空白的 `character_id`。
- `action` 和 `transition` 类型的节拍必须为 null `character_id`。
- `heading.interior_exterior` 接受 `INT`、`EXT`、`INT/EXT`，并自动标准化中文值（`内景`、`外景`、`内外景`）。
- `revision_notes` 包含纯文本字符串。可为空。
