# start

**Description:** Start work on a task or feature following the project workflow

**Prompt:**

I want to start work on a task or feature. Please follow this workflow:

1. **Task Analysis**: Review the task description: {{input}}
   - Summarize what needs to be done
   - Identify acceptance criteria or success conditions
   - Note any ambiguities or dependencies

2. **Branch Creation**: Create a new branch from main:
   - Use format: `feature/<descriptive-name>` or `fix/<descriptive-name>` as appropriate
   - Run: `git checkout -b <branch-name>`
   - Use kebab-case for the descriptive part (e.g., `feature/search-topbar`)

3. **Implementation Planning**: Create a `specs/TODO_<feature-slug>.md` file with:
   - Overview section with task summary
   - **Phased Implementation Checklist** (on top) – break the work into explicit phases, each with checkable items:
     - Phase 1: Foundation (setup, scaffolding, dependencies)
     - Phase 2: Core logic (main implementation)
     - Phase 3: Integration (wiring, routes, templates)
     - Phase 4: Polish (tests, docs, linting)
     - Use `- [ ]` for each item so the checklist is checkable; tick with `- [x]` when done
     - Adapt phase names to the feature; not all features need all phases
   - Success Criteria (underneath phasing)
   - Impact Analysis (underneath success criteria)
   - Key Files to Modify (reference project structure from .cursorrules)

4. **Code Examples & Documentation**:
   - Add an Appendix section at the bottom with relevant code examples
   - Reference similar implementations from the codebase
   - DO NOT implement the code yet

5. **Clarification**: If requirements are unclear, ask numbered questions with your proposed approach

6. **Return control**: Tell the user that the TODO file is ready for review, and they can say "go and implement" when ready to proceed.

Remember:
- Follow project conventions from @.cursorrules (Python 3.13+, FastAPI, uv, pytest, Ruff)
- Phases must be explicit (numbered/headed) with checkable `- [ ]` items under each
- Do NOT implement code until explicitly asked

**Arguments:**
- `input` (string, required): Task or feature description to start work on
