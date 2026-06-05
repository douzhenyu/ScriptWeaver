# AI Adaptation Workflow

## Purpose

ScriptWeaver is a human-in-the-loop AI adaptation workflow for helping novel authors turn three or more novel chapters into an editable screenplay draft.

The AI does not simply reformat prose. It helps the author understand the source material, decide what to preserve or change, and generate a screenplay draft from confirmed creative decisions.

## Workflow Summary

```text
Upload 3+ chapters
  -> AI story analysis
  -> User confirms or edits analysis
  -> AI adaptation planning
  -> User confirms or edits plan
  -> AI screenplay drafting
  -> YAML export for editing
```

## Stage 1: Chapter Intake

Input:

- At least three novel chapters.
- Chapter title or sequence number.
- Chapter body text.

System responsibilities:

- Reject fewer than three chapters.
- Reject empty chapter content.
- Preserve chapter order.
- Preserve source references for later traceability.

Output:

- A normalized chapter list that later AI stages can reference.

## Stage 2: AI Story Analysis

AI responsibilities:

- Identify main characters and supporting characters.
- Infer character goals and relationships.
- Extract key events.
- Identify locations and time cues.
- Identify core conflicts.
- Identify candidate dramatic scenes.
- Flag uncertain or ambiguous points.

User interaction:

- Accept characters that are correct.
- Reject mistaken characters.
- Edit names, roles, goals, and relationships.
- Add missing plot points.
- Mark story elements that must be preserved.
- Add notes about tone, pacing, or intended format.

Why this stage exists:

Novel-to-screenplay adaptation depends on interpretation. The author should be able to correct AI interpretation before the system writes scenes.

## Stage 3: AI Adaptation Planning

AI responsibilities:

- Propose a target screenplay format.
- Break the source material into scenes.
- Assign each scene a dramatic purpose.
- Map scenes back to source chapters and key events.
- Propose compression choices.
- Propose merge choices.
- Propose rewrite choices, such as converting internal monologue into action or dialogue.
- Identify choices that need author review.

User interaction:

- Confirm or edit the target format.
- Add, remove, merge, or reorder proposed scenes.
- Require specific plot points.
- Adjust tone and pacing.
- Confirm which source material can be compressed.

Why this stage exists:

Good adaptation is selective. This stage makes the AI's creative decisions visible before the final screenplay is generated.

## Stage 4: AI Screenplay Drafting

AI responsibilities:

- Generate scene headings.
- Generate action beats.
- Generate dialogue beats.
- Add voice-over or narration only when useful.
- Preserve scene-to-source traceability.
- Generate revision notes for uncertain decisions.

User interaction:

- Review the generated screenplay YAML.
- Edit the YAML directly or through a future UI.
- Use revision notes to decide what needs manual rewriting.

Why this stage exists:

The final output should be a useful first draft, not a final shooting script. The author remains responsible for creative polish.

## Stage 5: AI Revision Support

AI responsibilities:

- Explain what was compressed, merged, rewritten, or left uncertain.
- Identify continuity risks across scenes.
- Suggest where dialogue may need stronger character voice.
- Suggest where scene purpose or conflict may be weak.
- Point the author back to related source chapters or plan decisions.

User interaction:

- Accept revision notes as guidance.
- Ignore notes that do not match the author's intent.
- Edit screenplay YAML directly or request a future regeneration flow.

Why this stage exists:

The generated screenplay is an editable first draft. AI revision support helps the author continue polishing without hiding uncertainty or making final creative decisions automatically.

First-version boundary:

The first backend version only needs to preserve revision notes in the exported YAML. A later version can add explicit revision requests and regenerated scene drafts.

## Workflow States

The backend should eventually represent the workflow with these states:

| State | Meaning | Allowed Next State |
| --- | --- | --- |
| `created` | Adaptation job exists but chapters are incomplete. | `chapters_uploaded` |
| `chapters_uploaded` | At least three valid chapters are available. | `analysis_generated` |
| `analysis_generated` | Raw AI analysis exists. | `analysis_confirmed` |
| `analysis_confirmed` | User-confirmed analysis exists. | `plan_generated` |
| `plan_generated` | AI adaptation plan exists. | `plan_confirmed` |
| `plan_confirmed` | User-confirmed plan exists. | `screenplay_generated` |
| `screenplay_generated` | Final screenplay YAML exists. | export or revise |

Invalid transitions should be rejected. For example, screenplay generation should not run before the adaptation plan is confirmed.

## AI Output Versus User Confirmation

The system must distinguish raw AI output from user-confirmed decisions.

Raw AI output:

- Useful for suggestions.
- Can be incomplete or mistaken.
- Should be editable before it drives later stages.

User-confirmed output:

- Represents creative decisions accepted by the author.
- Should drive adaptation planning and screenplay generation.
- Should be preserved in the final YAML.

## Backend Implications

The future backend should expose operations equivalent to:

- Create adaptation job.
- Upload chapters.
- Run AI analysis.
- Update or confirm analysis.
- Run adaptation planning.
- Update or confirm plan.
- Generate screenplay YAML.
- Export screenplay YAML.

The first backend implementation can use a mock AI provider. The mock provider should still produce realistic analysis, plan, and screenplay structures so the workflow can be demonstrated without external credentials.

## Non-Goals

This workflow does not require the first backend version to include:

- Web UI.
- Persistent database storage.
- Real LLM integration.
- Final shooting-script formatting.
- Video production scheduling.
