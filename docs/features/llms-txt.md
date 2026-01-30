# LLMs.txt Support

One of the most **remarkable features** of this documentation server: built-in support for AI assistants!

## What is llms.txt?

[llms.txt](https://llmstxt.org/) is an emerging standard for making documentation easily consumable by Large Language Models (LLMs) like Claude, ChatGPT, and others.

Think of it as a **sitemap for AI assistants** - a standardized way to present your documentation structure so AI can understand and reference it accurately.

---

## Why This Matters

When you ask an AI assistant about your project:

❌ **Without llms.txt**: AI might hallucinate, miss pages, or give outdated info

✅ **With llms.txt**: AI gets accurate, structured access to all your documentation

---

## Automatic Generation

This server provides **two strategies** for llms.txt:

### Strategy 1: Curated (Recommended)

Create a custom `llms.txt` in your docs root:

```markdown
# My Project Documentation

Brief description of your project.

## Getting Started
[Quick Start](quick-start.md)
[Installation](installation.md)

## Core Concepts
[Architecture](architecture.md)
[API Reference](api.md)

## Advanced
[Deployment](deployment.md)
[Troubleshooting](troubleshooting.md)
```

**Benefits:**
- Full control over AI context
- Curated order and grouping
- Custom descriptions
- Priority ranking

### Strategy 2: Auto-Generated (Fallback)

If no `llms.txt` exists, the server automatically generates one from:
1. Your `sidebar.md` (navigation structure)
2. Your `index.md` (homepage content)

**Benefits:**
- Zero configuration
- Always up-to-date
- Follows your navigation

---

## Two Endpoints

### 1. `/llms.txt` - Index

A lightweight index of your documentation:

```bash
curl http://localhost:8080/llms.txt
```

Returns:
```
# Project Documentation

[Page 1](https://yourdomain.com/page1.md)
[Page 2](https://yourdomain.com/page2.md)
...
```

**Features:**
- Relative links → Absolute URLs
- Smart caching
- Follows llms.txt spec

### 2. `/llms-full.txt` - Complete Content

All your documentation in one file:

```bash
curl http://localhost:8080/llms-full.txt
```

Returns:
```
# Index content here

<url>https://yourdomain.com/page1.md</url>
<content>
Full content of page1.md
</content>

<url>https://yourdomain.com/page2.md</url>
<content>
Full content of page2.md
</content>
```

**Use cases:**
- Full context for AI
- Offline documentation
- Complete project dump

---

## Link Transformation

The server automatically transforms relative links to absolute URLs:

**Input (your markdown):**
```markdown
[Getting Started](getting-started.md)
[API](api/endpoints.md)
```

**Output (llms.txt):**
```markdown
[Getting Started](https://yourdomain.com/getting-started.md)
[API](https://yourdomain.com/api/endpoints.md)
```

This ensures AI assistants can fetch the actual content!

---

## Base URL Configuration

Control the base URL for absolute links:

### Auto-Detection (Default)

```bash
# Server detects from request
# Request: http://localhost:8080/llms.txt
# Links: http://localhost:8080/page.md
```

### Manual Configuration

```bash
# Set explicit base URL
BASE_URL=https://docs.myproject.com uv run python -m docs_server

# In Docker
docker run -e BASE_URL=https://docs.myproject.com ...
```

---

## Using with AI Assistants

### Claude (claude.ai)

1. Upload your `/llms-full.txt`
2. Ask questions about your docs
3. Claude has full context!

### ChatGPT

1. Share your `/llms.txt` URL
2. ChatGPT can fetch pages as needed
3. Accurate, up-to-date responses

### Cursor/Copilot

1. Reference your documentation URL
2. Code assistants can look up APIs
3. Better code completion

---

## Example: Curated llms.txt

Here's a well-structured example:

```markdown
# Awesome Project

A revolutionary way to do X, Y, and Z.

## Quick Links
- [Homepage](https://docs.awesome.com/index.md)
- [Quick Start](https://docs.awesome.com/quick-start.md)

## Documentation Structure

### Getting Started
Essential reading for new users:
- [Installation](https://docs.awesome.com/install.md)
- [Configuration](https://docs.awesome.com/config.md)
- [First Steps](https://docs.awesome.com/first-steps.md)

### Core Concepts
Deep dives into how it works:
- [Architecture](https://docs.awesome.com/architecture.md)
- [Data Model](https://docs.awesome.com/data-model.md)
- [API Design](https://docs.awesome.com/api-design.md)

### API Reference
Complete API documentation:
- [REST API](https://docs.awesome.com/api/rest.md)
- [GraphQL API](https://docs.awesome.com/api/graphql.md)
- [Webhooks](https://docs.awesome.com/api/webhooks.md)

### Deployment
Production deployment guides:
- [Docker](https://docs.awesome.com/deploy/docker.md)
- [Kubernetes](https://docs.awesome.com/deploy/k8s.md)
- [Cloud Providers](https://docs.awesome.com/deploy/cloud.md)

## FAQ
- [Common Issues](https://docs.awesome.com/faq.md)
- [Troubleshooting](https://docs.awesome.com/troubleshooting.md)

## Additional Resources
- GitHub: https://github.com/awesome/project
- Discord: https://discord.gg/awesome
- Blog: https://blog.awesome.com
```

---

## Caching

Both endpoints are **intelligently cached**:

- ✅ First request: Generates content (slow)
- ✅ Subsequent requests: Serves from cache (instant)
- ✅ Server restart: Cache cleared, regenerated

No manual cache management needed!

---

## Testing Your llms.txt

### Check Format

```bash
# View in browser
open http://localhost:8080/llms.txt

# Or with curl
curl http://localhost:8080/llms.txt
```

### Validate Links

```bash
# All links should be absolute
curl http://localhost:8080/llms.txt | grep -E '\[.*\]\(http'
```

### Check Full Content

```bash
# See complete documentation
curl http://localhost:8080/llms-full.txt | head -100
```

---

## Best Practices

### DO ✅

- Keep llms.txt focused on essential pages
- Use clear, descriptive titles
- Group related content
- Include direct links (not anchors)
- Update when adding major pages

### DON'T ❌

- Don't list every single page
- Don't use relative links (server handles this)
- Don't duplicate content
- Don't forget descriptions
- Don't ignore the structure

---

## Real-World Impact

**Before llms.txt:**
```
User: "How do I deploy this?"
AI: "I'm not sure, let me guess..." (hallucinates)
```

**After llms.txt:**
```
User: "How do I deploy this?"
AI: "According to your deployment docs at /deploy/docker.md..." (accurate!)
```

---

## Specification Compliance

This server follows the [llms.txt spec](https://llmstxt.org/):

✅ Plain text format  
✅ Markdown structure  
✅ Absolute URLs  
✅ Clear hierarchy  
✅ Complete context option  

---

## Advanced: Custom Generation

Want custom llms.txt logic? Extend the server:

```python
# In llms_service.py
async def generate_llms_txt_content(base_url: str) -> str:
    # Your custom logic here
    # - Filter pages by category
    # - Add custom metadata
    # - Generate from database
    pass
```

---

## What's Next?

- **[Configuration](../configuration.md)** - Environment variables
- **[API Reference](../api/endpoints.md)** - All HTTP endpoints
- **[Examples](../examples/advanced.md)** - See it in action

---

## Resources

- [llmstxt.org](https://llmstxt.org/) - Official specification
- [Example llms.txt files](https://github.com/search?q=llms.txt)
- [AI Documentation Best Practices](https://example.com)

---

<div style="background: #f0f9ff; border-left: 4px solid #3b82f6; padding: 1rem; margin: 1rem 0;">
  <strong>💡 Pro Tip:</strong> Test your llms.txt by asking Claude or ChatGPT questions about your docs. You'll be amazed at how accurate the responses become!
</div>
