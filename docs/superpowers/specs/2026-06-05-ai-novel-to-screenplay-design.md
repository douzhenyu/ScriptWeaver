# AI Novel To Screenplay Tool Design

## Goal

Build ScriptWeaver as an AI-assisted tool that helps novel authors convert at least three chapters of novel text into an editable structured screenplay draft in YAML format.

The project must be delivered through small pull requests. Each PR implements one feature, keeps the main branch runnable after merge, and includes a clear title, feature description, implementation approach, and testing method.

## Repository Context

The GitHub repository `douzhenyu/ScriptWeaver.git` is currently empty. There is no existing application structure, test framework, or branch history to preserve.

Because the repository is empty, the first functional PR should initialize a minimal runnable project before adding adaptation behavior.

## Delivery Strategy

The feature will be split into multiple small PRs:

1. Initialize a runnable CLI project.
2. Add chapter loading and minimum chapter validation.
3. Document the screenplay YAML Schema.
4. Add a rule-based screenplay YAML draft generator.
5. Add an AI provider interface with a mock provider.
6. Add an OpenAI-compatible provider for real AI generation.
7. Add a minimal Web UI that reuses the CLI/core pipeline.

This sequence keeps each PR narrow and avoids mixing project setup, input parsing, schema design, AI integration, and Web UI work in one change.

## Recommended Technology

Use Python for the first stage.

Reasons:

- Text processing, YAML generation, and CLI tooling are straightforward in Python.
- The core conversion pipeline can be tested without a browser.
- The same core modules can later be called by a Web UI.
- Python keeps the initial repository small and readable for reviewers.

The initial stack should be:

- Python package: `scriptweaver`
- CLI entry point: `python -m scriptweaver`
- Test runner: `pytest`
- YAML library: `PyYAML`

## PR Plan

### PR 1: Initialize ScriptWeaver CLI Project

Title: `Initialize ScriptWeaver CLI project`

Feature description:

- Create a minimal Python CLI project.
- Provide a runnable help command.
- Add test infrastructure.
- Add a README with basic usage.

Implementation approach:

- Create package directory `scriptweaver/`.
- Add `scriptweaver/__main__.py` for CLI execution.
- Use `argparse` for the initial command interface.
- Add `pyproject.toml` with project metadata and dependencies.
- Add a smoke test for the CLI help path.

Testing method:

- Run `python -m scriptweaver --help`.
- Run `pytest`.

### PR 2: Add Chapter Loading And Minimum Chapter Validation

Title: `Add chapter loading and minimum chapter validation`

Feature description:

- Read chapter text files from a directory.
- Sort chapters by filename.
- Reject inputs with fewer than three chapters.
- Return structured chapter objects for later conversion.

Implementation approach:

- Add `scriptweaver/chapters.py`.
- Represent chapters with a small dataclass containing `index`, `title`, `source_path`, and `content`.
- Treat each `.txt` file as one chapter.
- Use deterministic filename ordering.

Testing method:

- Test that two chapters fail validation.
- Test that three chapters pass validation.
- Test that chapter order follows filenames.

### PR 3: Document Screenplay YAML Schema

Title: `Document screenplay YAML schema`

Feature description:

- Add a document defining the screenplay YAML Schema.
- Explain each major field and its constraints.
- Explain why the schema is designed for editable drafts rather than final production scripts.
- Include a complete example.

Implementation approach:

- Add `docs/screenplay-yaml-schema.md`.
- Define top-level sections for `metadata`, `source`, `characters`, `scenes`, and `revision_notes`.
- Keep the schema stable enough for CLI and Web UI reuse.

Testing method:

- Manually review the document for field clarity.
- Parse the example YAML in a test or validation script in a later PR.

### PR 4: Generate Rule-Based Screenplay Draft YAML

Title: `Generate rule-based screenplay draft YAML`

Feature description:

- Convert at least three novel chapters into a structured screenplay YAML draft.
- Produce an initial scene per chapter.
- Extract simple dialogue-like lines and narration/action text using deterministic rules.

Implementation approach:

- Add `scriptweaver/models.py` for screenplay dataclasses.
- Add `scriptweaver/pipeline.py` to convert chapters into screenplay structure.
- Add `scriptweaver/yaml_writer.py` to serialize output.
- Keep this PR independent of external AI APIs so the demo remains reproducible.

Testing method:

- Use three chapter fixtures.
- Verify generated YAML includes `metadata`, `source`, `characters`, `scenes`, and `revision_notes`.
- Verify YAML can be parsed back successfully.

### PR 5: Add AI Provider Interface

Title: `Add AI provider interface for screenplay adaptation`

Feature description:

- Add an abstraction for AI-assisted adaptation.
- Provide a mock provider that produces deterministic output.
- Let the CLI choose provider mode without requiring an API key.

Implementation approach:

- Add `scriptweaver/ai_provider.py`.
- Define a provider protocol such as `adapt_chapters(chapters)`.
- Keep the rule-based generator as the fallback path.
- Add `--provider mock` or equivalent CLI option.

Testing method:

- Test mock provider output.
- Test CLI generation with mock provider.
- Confirm no network access or API key is needed.

### PR 6: Add OpenAI-Compatible Provider

Title: `Add OpenAI-compatible provider for screenplay generation`

Feature description:

- Use a configured AI API to generate screenplay YAML.
- Validate model output against the expected structure.
- Preserve mock provider as the default test/demo path.

Implementation approach:

- Add an OpenAI-compatible provider using environment variables for endpoint, model, and API key.
- Prompt the model to produce YAML matching the documented schema.
- Parse and validate the YAML output.
- Return clear errors for malformed model responses.

Testing method:

- Unit-test prompt construction and YAML parsing with fixtures.
- Keep external API tests manual or opt-in.
- Verify mock provider tests still pass without credentials.

### PR 7: Add Minimal Web UI

Title: `Add minimal web interface for screenplay generation`

Feature description:

- Provide a browser interface for uploading chapter text.
- Generate screenplay YAML through the existing core pipeline.
- Display generated YAML and allow download.

Implementation approach:

- Add a small Web app only after the CLI/core pipeline is stable.
- Reuse the same chapter loading, provider, pipeline, and YAML writer modules.
- Avoid duplicating conversion logic in frontend code.

Testing method:

- Start the Web server.
- Upload at least three chapter files.
- Verify the page returns valid YAML.
- Keep CLI tests passing.

## Core Architecture

The first stage should separate responsibilities into small modules:

- `scriptweaver/cli.py`: Parse CLI arguments and call the pipeline.
- `scriptweaver/__main__.py`: Allow `python -m scriptweaver`.
- `scriptweaver/chapters.py`: Load and validate chapter input.
- `scriptweaver/models.py`: Define screenplay draft structures.
- `scriptweaver/pipeline.py`: Convert chapters into screenplay drafts.
- `scriptweaver/yaml_writer.py`: Serialize screenplay drafts as YAML.
- `scriptweaver/ai_provider.py`: Define AI provider contracts and implementations.

The CLI and future Web UI should depend on the same core modules. This prevents the Web UI from becoming a second implementation of the adaptation logic.

## YAML Schema Design Goals

The screenplay YAML Schema should optimize for an editable draft:

- Preserve traceability from screenplay scenes back to source chapters.
- Separate dialogue, action, narration, and adaptation notes.
- Represent characters explicitly so authors can refine names, roles, and arcs.
- Keep scene structure readable in plain text.
- Avoid overly strict film-production formatting that would make early drafts harder to edit.

The schema should not try to be a final shooting-script format in the first version. The product goal is to lower the adaptation threshold and produce a useful first draft, not to replace professional script polishing.

## Error Handling

The CLI should return clear errors for:

- Missing input path.
- Fewer than three chapter files.
- Empty chapter files.
- Invalid or unparsable AI YAML output.
- Missing credentials when a real AI provider is explicitly selected.

For reproducible demos, mock and rule-based modes must work without credentials.

## Testing Strategy

Each PR should include tests appropriate to its scope:

- PR 1: CLI smoke test.
- PR 2: Chapter loading and validation tests.
- PR 3: Documentation review; example parsing may be added in PR 4.
- PR 4: YAML generation and parsing tests.
- PR 5: Mock provider tests.
- PR 6: Provider parsing and validation tests, with live API tests kept opt-in.
- PR 7: Web smoke test plus existing CLI/core tests.

The main branch should remain runnable after every merge.

## Open Decisions

These decisions can be deferred without blocking PR 1:

- Whether the Web UI will use FastAPI with server-rendered HTML or a separate frontend framework.
- Which real AI provider will be used first.
- Whether a JSON Schema file should be generated from the YAML Schema documentation.
- Whether multi-file chapters beyond `.txt` should be supported.

## Non-Goals For The First PR

PR 1 should not implement:

- Chapter parsing.
- YAML screenplay generation.
- AI provider calls.
- Web UI.
- Schema validation.

Keeping PR 1 limited to project initialization makes it reviewable and keeps the empty repository runnable immediately after merge.
