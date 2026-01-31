# go

**Description:** Implement selected phases from a TODO file with context awareness

**Prompt:**

I want to implement specific phases from a TODO file. Please follow this workflow:

**Context Provided:** {{input}}

**Step 1: Identify the TODO File**

- Look for the TODO_KLO-###.md file referenced in the context
- If not explicitly mentioned, check the current branch name to determine the ticket number
- Read the full TODO file using @TODO_KLO-###.md

**Step 2: Re-read All Relevant Files**

- The codebase may have changed outside this chat context
- Re-read all files mentioned in the selected phases before starting implementation
- Verify current state of the code to understand what's already implemented

**Step 3: Validate Selected Phases**

- Review the phases/tasks provided in the context
- Check if any tasks are already ticked `- [x]` - if so, verify they actually exist in the codebase
- If implementation is missing despite being ticked, implement it and keep the tick
- If implementation exists and is correct, leave the tick as-is

**Step 4: Implementation**

- Implement ONLY the phases/tasks provided in the context
- Stay focused and within the boundaries of the selected tasks
- Keep changes small and effective (as per @.cursorrules)
- Tick off boxes `- [x]` in the TODO file as you complete each task

**Step 5: Ask Questions When Unclear**

- If requirements are unclear or ambiguous, STOP and ask for clarification
- Don't guess or over-engineer
- Keep it simple and direct (follow the Zen of Python)
- Reference specific line items from the TODO when asking questions

**Step 6: Report Completion**

- Summarize what was implemented
- List files that were modified
- Highlight any items that need further clarification
- Update the TODO file with all ticked-off items

Remember:

- Respect the TODO file structure and content
- Keep implementation minimal and focused
- Always validate that ticked items correspond to actual working code
- Never commit changes - leave that to the developer
- Follow all conventions from @.cursorrules

**Arguments:**

- `input` (string, required): Selected phases/tasks from the TODO file to implement
