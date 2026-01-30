# Markdown Features

This server supports **rich Markdown** with powerful extensions. See them all in action!

## Headings

# H1 Heading
## H2 Heading
### H3 Heading
#### H4 Heading
##### H5 Heading
###### H6 Heading

All headings automatically get:
- Unique IDs for linking
- Permalink icons on hover (🔗)
- Table of contents entries

---

## Text Formatting

**Bold text** using `**bold**`

*Italic text* using `*italic*`

***Bold and italic*** using `***both***`

~~Strikethrough~~ using `~~strikethrough~~`

---

## Lists

### Unordered Lists

* Item 1
* Item 2
  * Nested item 2.1
  * Nested item 2.2
* Item 3

### Ordered Lists

1. First item
2. Second item
   1. Nested 2.1
   2. Nested 2.2
3. Third item

### Task Lists

- [x] Completed task
- [x] Another completed task
- [ ] Pending task
- [ ] Another pending task

---

## Code Blocks

### Inline Code

Use `backticks` for inline code like `const x = 5;`

### Syntax Highlighted Blocks

Python example:

```python
def fibonacci(n):
    """Calculate Fibonacci number."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Usage
result = fibonacci(10)
print(f"Fibonacci(10) = {result}")
```

JavaScript example:

```javascript
// Async/await example
async function fetchData(url) {
    try {
        const response = await fetch(url);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error:', error);
    }
}
```

Bash example:

```bash
# Docker deployment
docker build -t my-app .
docker run -p 8080:8080 my-app

# With environment variables
docker run \
  -e DEBUG=true \
  -e PORT=3000 \
  -p 3000:3000 \
  my-app
```

---

## Tables

Tables are fully supported with automatic styling:

| Feature | Supported | Notes |
|---------|-----------|-------|
| Markdown | ✅ Yes | Full CommonMark support |
| Code Highlighting | ✅ Yes | Pygments-powered |
| Tables | ✅ Yes | You're looking at one! |
| Math | ❌ No | Not yet implemented |
| Mermaid | ✅ Yes | Diagrams supported |

### Table with Alignment

| Left Aligned | Center Aligned | Right Aligned |
|:-------------|:--------------:|--------------:|
| Left | Center | Right |
| Text | Text | Text |
| More | More | More |

---

## Links

### Internal Links

Link to other pages: [Quick Setup Guide](../quick-setup.md)

Link to sections: [Back to Code Blocks](#code-blocks)

### External Links

Visit [GitHub](https://github.com) or [Python.org](https://python.org)

External links open in new tabs automatically in the navigation.

---

## Blockquotes

> This is a blockquote.
> It can span multiple lines.
>
> And even multiple paragraphs!

> **Pro Tip**: Blockquotes are great for callouts, tips, and warnings.

---

## Horizontal Rules

Separate content with horizontal rules:

---

Like that one above!

---

## Images

Images are automatically handled:

![Example Image](../assets/example.png)

Images support:
- PNG, JPG, GIF, SVG
- Automatic sizing
- Responsive layout
- Lazy loading

---

## Footnotes

You can add footnotes[^1] to your documentation.

Another footnote[^2] reference.

[^1]: This is the first footnote.
[^2]: This is the second footnote with more text.

---

## Definition Lists

Term 1
:   Definition of term 1

Term 2
:   Definition of term 2
:   Another definition for term 2

---

## Abbreviations

The HTML specification is maintained by the W3C.

*[HTML]: Hyper Text Markup Language
*[W3C]: World Wide Web Consortium

---

## Advanced Features

### Nested Lists with Code

1. First step
   ```python
   print("Step 1")
   ```
2. Second step
   ```python
   print("Step 2")
   ```
3. Third step

### Mixed Content

You can mix **bold**, *italic*, `code`, and [links](#) in tables:

| Feature | Code | Link |
|---------|------|------|
| **Bold** | `code` | [link](#) |
| *Italic* | `more` | [another](#) |

---

## Escaping

Need to show literal markdown? Escape with backslash:

\*\*Not bold\*\*

\`Not code\`

\[Not a link\](url)

---

## Special Characters

The server handles special characters correctly:

- En dash: –
- Em dash: —
- Ellipsis: …
- Quotes: "smart" 'quotes'
- Symbols: © ® ™
- Arrows: → ← ↑ ↓
- Math: ± × ÷ ≠ ≈
- Emojis: 🎉 🚀 ✅ ❌ 💡

---

## What's Not Supported?

Currently not implemented:
- Math equations (LaTeX)
- Embedded videos
- Custom HTML components
- MDX-style components

Everything else from [CommonMark](https://commonmark.org/) and popular extensions is supported!

---

## Next Steps

- **[Navigation Features](navigation.md)** - Learn about sidebar and topbar
- **[LLMs.txt Support](llms-txt.md)** - AI assistant integration
- **[Examples](../examples/advanced.md)** - See real-world examples
