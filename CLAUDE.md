# Technical Articles Knowledge Base

## Purpose

This repository contains technical articles intended for publication on platforms such as dev.to. It serves as a personal knowledge base to consolidate and expand technical understanding relevant to a Software Engineering career.

## Framing

Evaluate articles from the perspective of what a senior, experienced Software Engineer would want to hear when asking deep technical questions in an interview. The standard is not "technically not wrong" but "demonstrates genuine understanding". Challenge every assumption. Meticulously scrutinize the text for technical accuracy, ambiguity, and outdated assumptions or statements, as if your Principal Software Engineer boss was going to evaluate it looking for any excuse to fire you.

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

### Mandatory Pre-Publication Verification

**Before any article is marked ready for publication, perform these verification steps:**

1. **Recency check** — For any technology, framework, or library discussed:
   - Search the web for "[technology] latest version [current year]" and "[technology] breaking changes"
   - Check the official changelog or release notes for major version changes in the past 18 months
   - If a major version was released recently, verify that all claims reflect the current architecture

2. **Comparative claims require current data** — When comparing frameworks, libraries, or approaches:
   - Every quantitative claim (bundle size, performance, etc.) must cite a specific version
   - Search for "[framework A] vs [framework B] [current year]" to check for recent architectural shifts
   - Cross-reference with each project's official documentation, not blog posts or tutorials (which may be outdated)

3. **Architecture descriptions decay fastest** — Statements about _how_ something works internally (not just _what_ it does) are high-risk for obsolescence:
   - "X uses virtual DOM" / "Y compiles to vanilla JS" / "Z uses signals" — these can change between major versions
   - Always verify against official documentation dated within the past 12 months
   - If the technology has had a major version release, assume the architecture may have changed and verify

4. **Red-flag patterns** — These claims require immediate verification:
   - "smallest runtime" / "fastest" / "most efficient" — comparative superlatives change constantly
   - Bundle size numbers — re-verify against current bundlephobia.com or official docs and only if the bundle size adds anything meaningful to the discussion, but avoid discussing absolute numbers because they can change frequently over time
   - "No runtime" / "zero overhead" — often marketing claims that have caveats
   - Descriptions of internal mechanisms (reactivity models, rendering strategies, compilation approaches)

5. **Version pinning** — Every framework comparison must:
   - State the specific versions being compared in the article body (not just "as of 2026")
   - Acknowledge that the comparison reflects a point in time
   - For rapidly evolving tools (frontend frameworks especially), include a note about when to re-verify

**Verification failures are publication blockers.** If current authoritative sources cannot be found to confirm a claim, the claim must be removed, qualified with uncertainty, or the article held until verification is possible.

### High-Risk Domains

Some technology areas change so rapidly that extra caution is required:

**Frontend frameworks (React, Vue, Svelte, SolidJS, etc.)**

- Major architectural shifts happen between versions (e.g., Svelte 5 adopted signals, changing its fundamental reactivity model)
- Bundle sizes, performance characteristics, and "how it works" descriptions can become outdated within months
- Always check for major version releases in the past 18 months before publishing

**AI/ML libraries and services**

- APIs, model capabilities, and best practices evolve weekly
- Pricing, rate limits, and availability change without notice
- Prefer linking to official documentation over stating specifics

**Cloud services and DevOps tools**

- Features, pricing, and recommended patterns change frequently
- Regional availability and compliance certifications vary
- Version-lock all CLI commands and API references

**Language features and runtime behavior**

- New language versions add features that change best practices
- Runtime performance characteristics vary by version
- Explicitly state which language/runtime version applies

When writing about these domains, the default assumption should be that your knowledge is potentially outdated. Verify everything.

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

1. **Factual accuracy** — Are all technical claims correct?
2. **Currency** — Has anything changed since this information was written? (See Mandatory Pre-Publication Verification)
3. **Precision** — Is there any ambiguous language?
4. **Completeness** — Are assumptions stated? Are edge cases acknowledged?
5. **Scope** — Does the article try to cover too much? Should parts become separate articles?

Provide feedback in four categories:

- **Errors** — Incorrect statements that must be fixed
- **Outdated** — Claims that may have been true but need re-verification against current sources
- **Imprecisions** — Ambiguous or misleading language
- **Topics** — Concepts that warrant their own article

**For any article comparing technologies or describing implementation details, the reviewer must perform independent web searches to verify claims against current official sources.** Do not rely solely on reading the article — actively search for contradicting information.

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
- Keep paragraphs focused on a single idea
- Explain _why_, not just _what_

#### Sentence Length and Flow

Prefer longer, flowing prose that combines related ideas into single sentences. Short sentences and fragments are fine for emphasis or to drive a point across, but they shouldn't be the default.

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
- **Straight quotes everywhere** — avoid curly quotes, use " and ' (straight quotes) everywhere.
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

1. **Propose** — Describe the topic and intended audience
2. **Outline** — Structure the article before writing
3. **Draft** — Write with placeholders for uncertain sections
4. **Review** — Rigorous check for correctness and precision
5. **Verify** — Execute Mandatory Pre-Publication Verification (web searches, official docs, version checks). This step is non-negotiable for any article discussing technologies, frameworks, or comparative claims.
6. **Refine** — Address all flagged issues from Review and Verify
7. **Publish** — Final version with all links resolved and verification complete
