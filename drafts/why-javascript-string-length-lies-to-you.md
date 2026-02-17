---
title: Why JavaScript String Length Lies to You
published: false
description: Understanding code points, code units, and grapheme clusters — and why naive string truncation can corrupt your text.
tags: [javascript, unicode, strings, frontend]
---

If you've ever truncated a string in JavaScript and ended up with garbled characters or broken emoji, you've encountered one of the language's most subtle gotchas: JavaScript strings don't work the way most developers assume they do.

Consider this innocent-looking truncation function:

```javascript
function truncate(str, maxLength) {
  return str.slice(0, maxLength);
}
```

This works fine for basic ASCII text. But pass it a string containing emoji — `"Hello 👋 world"` — and slice at the wrong position, and you might end up with a corrupted character that displays as `�` or breaks downstream systems entirely.

To understand why, we need to distinguish between three concepts: _code points_, _code units_, and _grapheme clusters_. JavaScript's most familiar string APIs — `.length`, indexing, `.slice()` — operate on code units, but developers often expect them to correspond to the visual units they see on screen. They frequently don't: what appears as a single character might be stored as two, four, or even more code units internally. A code point within the Basic Multilingual Plane fits in one code unit, but code points outside it — including most emoji — require two, and a single visual character like a flag can itself comprise multiple code points.

## How Text Is Represented in Unicode

### Code Points

A _code point_ is Unicode's abstract representation of a character. The Unicode Standard assigns a unique number — ranging from 0 to 0x10FFFF — to every character, symbol, and control sequence. The letter "A" is code point U+0041. The emoji "😀" is code point U+1F600. The regional indicator symbol for "G" is code point U+1F1EC.

Code points are the logical unit of text. When we think about "characters" in human terms, we're usually thinking at the grapheme cluster level — what we perceive as a single visual character — though a grapheme cluster can consist of multiple code points, as we'll see shortly.

### Code Units

A _code unit_ is the physical unit of storage in a particular encoding scheme. Different encodings use different code unit sizes: UTF-8 uses 8-bit code units, UTF-32 uses 32-bit code units, and UTF-16 — the encoding JavaScript uses internally — uses 16-bit code units.

Here's where the complexity begins. The Unicode codespace extends to 0x10FFFF (over 1.1 million possible code points), but a 16-bit code unit can only represent values from 0 to 0xFFFF (65,536 values). This means UTF-16 cannot represent every code point with a single code unit.

Unicode solves this by dividing the codespace into two regions:

1. **The [Basic Multilingual Plane](<https://en.wikipedia.org/wiki/Plane_(Unicode)#Basic_Multilingual_Plane>) (BMP)** — Code points U+0000 to U+FFFF. These fit in a single 16-bit code unit. This includes most common characters: Latin alphabets, Cyrillic, Greek, Chinese, Japanese, Korean, and many symbols.

2. **Supplementary Planes** — Code points U+10000 to U+10FFFF. These require two 16-bit code units, called a _surrogate pair_. This includes emoji, mathematical symbols, historic scripts, and rare CJK characters.

A surrogate pair consists of a _high surrogate_ (U+D800 to U+DBFF) followed by a _low surrogate_ (U+DC00 to U+DFFF). These ranges are reserved specifically for this purpose — they don't represent any characters on their own.

For example, the emoji "😀" (U+1F600) is encoded in UTF-16 as the surrogate pair `\uD83D\uDE00`.

### Grapheme Clusters

A _grapheme cluster_ is what users perceive as a single visual character. This is defined by Unicode Standard Annex #29 as "the text between grapheme cluster boundaries" — essentially, the smallest unit of text that makes sense to a human reader.

The critical insight is that a grapheme cluster can consist of _multiple code points_. Some examples:

- **Flag emoji** — The 🇬🇧 flag is two code points: Regional Indicator Symbol Letter G (U+1F1EC) followed by Regional Indicator Symbol Letter B (U+1F1E7). When adjacent, they render as a single flag.

- **Skin tone modifiers** — The 👋🏽 waving hand with medium skin tone is two code points: the base emoji (U+1F44B) followed by a skin tone modifier (U+1F3FD).

- **ZWJ sequences** — The 👨‍👩‍👧 family emoji is five code points: man, Zero-Width Joiner, woman, ZWJ, girl. The ZWJ (U+200D) tells rendering systems to combine them into a single glyph.

- **Combining marks** — The character "é" can be represented either as a single precomposed code point (U+00E9) or as two code points: "e" (U+0065) followed by a combining acute accent (U+0301).

## What JavaScript Actually Does

JavaScript strings are sequences of 16-bit code units. The ECMAScript specification is explicit about this: "The String type is the set of all ordered sequences of zero or more 16-bit unsigned integer values."

This design decision has cascading consequences across the entire string API.

### Length Counts Code Units

The `.length` property returns the number of code units, not characters:

```javascript
"hello".length; // 5 — five code units, five code points
"😀".length; // 2 — two code units, one code point
"👨‍👩‍👧".length; // 8 — eight code units, five code points, one grapheme
"🇬🇧".length; // 4 — four code units, two code points, one grapheme
```

### Indexing Returns Code Units

Bracket notation and `.charAt()` return individual code units:

```javascript
"hello"[0]; // "h"
"😀"[0]; // "\uD83D" — the high surrogate, not a valid character
"😀"[1]; // "\uDE00" — the low surrogate, not a valid character
```

### Slice Operates on Code Units

The `.slice()` and `.substring()` methods use code unit indices:

```javascript
"hello".slice(0, 2); // "he" — works as expected
"😀😀".slice(0, 2); // "😀" — accidentally correct (two code units = one emoji)
"😀😀".slice(0, 3); // "😀\uD83D" — corrupted: complete emoji + orphan surrogate
```

That third example is the source of the truncation bug. Slicing at position 3 cuts a surrogate pair in half, producing an invalid sequence that contains an orphan high surrogate.

## Why This Causes Real Bugs

When you naively truncate user-generated content — say, for a preview or database field limit — you risk:

1. **Visual corruption** — Orphan surrogates display as the replacement character (�) or, depending on the font, as empty boxes or nothing at all.

2. **Broken emoji** — A flag like 🇬🇧 sliced in the middle becomes two separate regional indicators that may render as boxed letters or not render at all.

3. **Encoding failures** — Some systems reject strings containing orphan surrogates. Protocol buffers, for instance, require valid UTF-8, and an orphan surrogate cannot be validly encoded in UTF-8.

4. **Character count mismatches** — If your UI shows "12/100 characters" but counts code units while displaying graphemes, users will be confused when some emoji count as 2 or 4 or 8.

## Safe Truncation Strategies

### Code Point-Safe Truncation

If you need to preserve code points (avoiding orphan surrogates), spread the string into an array:

```javascript
function truncateCodePoints(str, maxCodePoints) {
  return [...str].slice(0, maxCodePoints).join("");
}

truncateCodePoints("😀😀😀", 2); // "😀😀" — two code points
```

The spread operator uses the string's `Symbol.iterator`, which iterates by code point rather than code unit. Surrogate pairs are kept together.

However, this still doesn't handle grapheme clusters. Flag emoji and ZWJ sequences will still be split:

```javascript
truncateCodePoints("🇬🇧🇫🇷", 2); // "🇬🇧" — appears correct, but only by luck
truncateCodePoints("🇬🇧🇫🇷", 3); // "🇬🇧🇫" — split the French flag, shows GB flag + unpaired F indicator
truncateCodePoints("👨‍👩‍👧", 3); // "👨‍👩" — split the family, shows man + ZWJ + woman
```

### Grapheme-Safe Truncation

For proper grapheme cluster handling, use `Intl.Segmenter`:

```javascript
function truncateGraphemes(str, maxGraphemes) {
  const segmenter = new Intl.Segmenter("en", { granularity: "grapheme" });
  const segments = [...segmenter.segment(str)];
  return segments
    .slice(0, maxGraphemes)
    .map((s) => s.segment)
    .join("");
}

truncateGraphemes("🇬🇧🇫🇷", 1); // "🇬🇧" — one grapheme cluster
truncateGraphemes("👨‍👩‍👧👨‍👩‍👧", 1); // "👨‍👩‍👧" — one grapheme cluster
truncateGraphemes("Hello 👋🏽", 6); // "Hello " — six graphemes (space is one)
truncateGraphemes("Hello 👋🏽", 7); // "Hello 👋🏽" — seven graphemes
```

`Intl.Segmenter` has been available in all major browsers since April 2024 (Baseline 2024).

### Choosing the Right Approach

The right truncation strategy depends on your constraints:

- **Code unit truncation** (`slice`) — Use when you have strict storage constraints (database column limits, protocol constraints) and can handle the visual artifacts downstream. You'll need to validate that you haven't created orphan surrogates.

- **Code point truncation** (spread + slice) — Use when you need valid Unicode sequences but don't need precise grapheme boundaries. Faster than `Intl.Segmenter` and sufficient for many use cases.

- **Grapheme truncation** (`Intl.Segmenter`) — Use when displaying to users or when character count must match user expectations. This is the only approach that handles all edge cases correctly.

## Key Takeaways

> JavaScript strings are sequences of UTF-16 code units. The `.length` property, indexing, and methods like `.slice()` all operate on code units — not code points or grapheme clusters.

This mismatch between JavaScript's internal representation and human intuition about "characters" is a frequent source of bugs. Any code that assumes `.length` returns the number of visible characters, or that slicing at an arbitrary index produces valid text, is potentially broken for input containing emoji or other characters outside the Basic Multilingual Plane.

The safest approach is to treat strings as opaque sequences when possible, use `[...str]` iteration when you need code point access, and reach for `Intl.Segmenter` when you need to match user-perceived character boundaries.

---

_This article was inspired by [Attio's engineering blog post](https://attio.com/engineering/blog/javascript-string-slice-considered-harmful) about a production bug caused by naive string truncation._
