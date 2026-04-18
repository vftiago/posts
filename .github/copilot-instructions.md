# Copilot Instructions

## Commands

This repository has no application build pipeline or package manifest. The only executable code lives in `tools/`.

```bash
# Full test suite for the Python tooling
python3 tools/test_smartquotes.py

# Run a single unittest
python3 -m unittest tools.test_smartquotes.TestCurlyQuotesInProse.test_double_quotes

# Check quote/style normalization across all active articles
for f in drafts/*.md published/*.md; do
  python3 tools/straightquotes.py --check "$f"
done

# Check one article file
python3 tools/straightquotes.py --check drafts/what-are-signals.md
```

## High-Level Architecture

- This is a technical-article repository, not an application. The primary artifacts are Markdown articles with YAML front matter.
- `drafts/` is the main working area for active articles. `published/` contains finished or near-finished articles, but the real publication state is the `published:` front matter field, not the directory name alone.
- `topics.md` is the follow-up topic backlog. Drafts use inline `<!-- TOPIC: ... -->` markers for ideas that deserve their own article, and those markers are expected to feed `topics.md` with a source reference.
- `archive/` holds older working material, consolidations, and backups. Prefer `drafts/`, `published/`, `topics.md`, and `tools/` when making current changes.
- `tools/` contains the only code in the repo: quote-conversion utilities and their tests. The scripts deliberately preserve YAML front matter, fenced code blocks, and inline code while changing prose quotes.

## Key Conventions

- Follow the front matter pattern from `CLAUDE.md`: `title`, `published`, `description`, and `tags` are standard; drafts often keep `cover_image` and `published_at` commented until the article is closer to release.
- Use straight quotes in repository Markdown. `tools/straightquotes.py --check <file>` is the relevant content-style validation command for article files.
- Write for a senior-engineer/interview audience: explanations should be mechanistic, explicit about tradeoffs and assumptions, and strong enough to survive follow-up questions.
- Before treating an article as publication-ready, independently verify current technical claims against official sources, especially framework internals, version-sensitive behavior, and comparisons.
- When a section would derail the current article, add a `<!-- TOPIC: ... -->` marker instead of forcing the digression, and keep `topics.md` aligned with that backlog.
- Keep the prose technical and measured: active voice, longer connected paragraphs, minimal rhetorical drama, and clear definitions for overloaded terms.
