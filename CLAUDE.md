# Technical Articles Knowledge Base

## Purpose

This repository contains technical articles intended for publication on platforms such as dev.to. It serves as a personal knowledge base to consolidate and expand technical understanding relevant to a Software Engineering career.

## Framing

Write and evaluate articles from the perspective of what a senior, experienced Software Engineer would want to hear when asking deep technical questions in an interview. The standard is not "technically not wrong" but "demonstrates genuine understanding."

This means:

- Anticipate follow-up questions and address them proactively
- Distinguish between surface-level explanations and mechanistic understanding
- Show awareness of tradeoffs, edge cases, and real-world implications
- Avoid rehearsed-sounding answers that collapse under scrutiny

Some articles will be direct explorations of actual technical interview questions, with real examples and the depth of answer that would satisfy a rigorous interviewer.

## Core Principles

### Technical Correctness

Every claim must be verifiable. When reviewing or writing:

- Verify facts against authoritative sources (official documentation, specifications, RFCs)
- Distinguish between implementation details and specification guarantees
- Note version-specific behavior explicitly (e.g., "As of Python 3.11...")
- Avoid generalizations that break under edge cases

### Language Precision

Ambiguity is the enemy. Apply these standards:

- Define terms on first use if they have multiple interpretations
- Prefer concrete examples over abstract explanations
- Use precise qualifiers: "always" vs "typically" vs "in this context"
- Avoid weasel words: "simply", "just", "obviously", "clearly"
- State assumptions explicitly rather than implying them

### Ambiguity as Opportunity

When a topic requires clarification that would derail the current article:

1. Flag it inline with: `<!-- TOPIC: Brief description of the ambiguity -->`
2. The flagged topic becomes a candidate for a new article
3. Reference the future article with a placeholder link
4. This creates a natural web of interconnected articles

## Review Process

When asked to review an article, check for:

1. **Factual accuracy** - Are all technical claims correct?
2. **Precision** - Is there any ambiguous language?
3. **Completeness** - Are assumptions stated? Are edge cases acknowledged?
4. **Scope** - Does the article try to cover too much? Should parts become separate articles?

Provide feedback in three categories:

- **Errors**: Incorrect statements that must be fixed
- **Imprecisions**: Ambiguous or misleading language
- **Topics**: Concepts that warrant their own article

## Writing Conventions

### File Organization

```
posts/
  drafts/           # Work in progress
  published/        # Final versions
  topics.md         # List of candidate topics from flagged ambiguities
```

### Front Matter

Each article should begin with:

```markdown
---
title: Catchy SEO-friendly Title That Works As A URL Slug
published: false
description: A brief SEO-friendly summary of the article's content.
tags: [tag1, tag2, tag3]
# cover_image: https://direct_url_to_image.jpg
# Use a ratio of 100:42 for best results.
# published_at: 2026-01-25 16:44 +0000
---
```

### Style

#### Voice and Tone

- Use active voice
- Contractions are fine (isn't, you're, it's)
- Short, direct sentences. Fragments for emphasis are acceptable.
- Keep paragraphs focused on a single idea
- Explain _why_, not just _what_

#### Avoiding Dramatic Prose

The tone should be technical and measured, not dramatic or emotional.

**Avoid:**

- Manufactured tension: "You have one hour. The interviewer is watching."
- Imperative commands to the reader: "Resist it." "Stop and think."
- Staccato repetition for artificial emphasis: "X is fast. Y is fast. Z is fast. W is not."
- Colloquial anthropomorphizing: "without the browser caring at all" (prefer precise technical language like "without triggering browser rendering work")
- Framing advice as urgent warnings: "Five minutes here saves twenty minutes later."

**Prefer:**

- Direct statements of fact with reasoning: "Before writing code, it's worth reading each requirement carefully to identify hidden implications." State the advice and why it matters in the same breath.
- Technical explanations over emotional appeals
- Let the content earn emphasis through clarity, not rhetorical devices
- When making a recommendation, state it plainly: "Option 2 is pragmatic for a timed exercise."

#### Punctuation

- **Em dashes** — use them sparsely, always with spaces on both sides, not attached to words (British/web convention for screen readability)
- **Periods and brackets** — when a parenthetical ends a sentence that began outside the brackets, the period goes outside: "This is an example (like this)." Not "(like this.)"
- **Serial comma** — use it (red, white, and blue)
- **Double quotes** for scare quotes around terms being examined: "touching the DOM"

#### Formatting

- **Headings**: Title Case for H2 section headings
- **Emphasis**: Use _italics_ (underscores) for emphasis and introducing terms
- **Bold**: Reserve for list item labels and key terms in definitions
- **Inline code**: Use backticks for code references, function names, technical identifiers
- **Code blocks**: Always specify the language (`javascript, not `)

#### Lists

- **Unordered lists**: For simple enumerations without explanations
- **Ordered lists with labels**: For items that need descriptions, use:
  ```
  1. **Label** — Description continues on the same line.
  ```
  This maintains semantic list structure for accessibility.

#### Blockquotes

Use blockquotes for:

- Claims being examined or refuted
- Rephrased conclusions or key takeaways

#### Code Examples

- Minimal but complete enough to illustrate the point
- Use realistic variable names, not `foo`/`bar` unless demonstrating syntax
- Specify the correct language identifier

## Workflow

1. **Propose**: Describe the topic and intended audience
2. **Outline**: Structure the article before writing
3. **Draft**: Write with placeholders for uncertain sections
4. **Review**: Rigorous check for correctness and precision
5. **Refine**: Address all flagged issues
6. **Publish**: Final version with all links resolved
