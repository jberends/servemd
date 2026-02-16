# ask

**Description:** Discuss approaches and strategies through structured questioning without implementation

**Prompt:**

I want to discuss and explore a topic/problem/approach without implementing it yet. Let's work through this systematically:

**Theme/Topic:** {{input}}

**Your Role:**

- Ask me unlimited numbered questions to fully understand the problem/approach
- Ask me one numbered question at a time.
- For each question, provide:
  1. **Option A**: First logical answer/approach
  2. **Option B**: Second logical answer/approach (different from A)
  3. **Option C**: An outlier/unconventional approach
  4. **Recommendation**: Clear reasoning on which option to pick and why

**Questioning Process:**

- Start broad, then drill down into specifics
- Build upon previous answers to ask deeper questions
- Reference relevant parts of @.cursorrules and existing codebase patterns
- Consider: architecture, data models, API design, user experience, edge cases, testing, performance
- Continue until the approach is fully defined and all ambiguities are resolved

**Final Summary:**
When questioning is complete, provide:

1. **Decision Summary**: Numbered list of all decisions made
2. **Recommended Approach**: Clear, structured implementation strategy
3. **Key Considerations**: Important points to remember during implementation
4. **Next Steps**: What should happen next (e.g., create TODO file, start implementation)

**Important Guidelines:**

- NO implementation in this mode - only discussion and planning
- Keep options practical and grounded in Django/DRF best practices
- Reference similar implementations from the codebase when relevant
- Respect project conventions from @.cursorrules
- Stay focused on the theme - don't drift to unrelated topics
- If I say "that's clear" or "let's move on", proceed to the next aspect

Let's start exploring this topic together!

**Arguments:**

- `input` (string, required): Theme, problem, topic, or question to discuss and explore
