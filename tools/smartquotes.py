#!/usr/bin/env python3
"""
Convert straight quotes to curly quotes in Markdown prose.

- Converts " to " and " in prose
- Converts ' to ' for contractions and possessives
- Preserves straight quotes in:
  - Code blocks (``` ... ```)
  - Inline code (` ... `)
  - YAML front matter (--- ... ---)

Usage:
    smartquotes <file>           # Print converted output to stdout
    smartquotes <file> --inplace # Modify file in place
    smartquotes --check <file>   # Check if file needs conversion (exit 1 if yes)
"""

import sys
import re
from pathlib import Path


def convert_quotes(text: str) -> str:
    """Convert straight quotes to curly quotes, preserving code sections."""
    lines = text.split('\n')
    result = []
    in_code_block = False
    in_front_matter = False
    front_matter_count = 0

    for i, line in enumerate(lines):
        # Track YAML front matter (only at start of file)
        if i == 0 and line == '---':
            in_front_matter = True
            front_matter_count = 1
            result.append(line)
            continue
        elif in_front_matter and line == '---':
            front_matter_count += 1
            if front_matter_count == 2:
                in_front_matter = False
            result.append(line)
            continue

        # Track code blocks
        if line.startswith('```'):
            in_code_block = not in_code_block
            result.append(line)
            continue

        # Skip conversion in code blocks or front matter
        if in_code_block or in_front_matter:
            result.append(line)
            continue

        # Convert prose line, preserving inline code
        result.append(convert_prose_line(line))

    return '\n'.join(result)


def convert_prose_line(line: str) -> str:
    """Convert quotes in a prose line, preserving inline code."""
    # Split by inline code sections
    parts = re.split(r'(`[^`]+`)', line)

    converted_parts = []
    for part in parts:
        if part.startswith('`') and part.endswith('`'):
            # Inline code - preserve as-is
            converted_parts.append(part)
        else:
            # Prose - convert quotes
            converted_parts.append(convert_quotes_in_text(part))

    return ''.join(converted_parts)


def convert_quotes_in_text(text: str) -> str:
    """Convert straight quotes to curly in plain text."""
    # Unicode characters
    LEFT_DOUBLE = '\u201C'   # "
    RIGHT_DOUBLE = '\u201D'  # "
    RIGHT_SINGLE = '\u2019'  # ' (used for apostrophes)

    # Convert double quotes: "text" -> "text"
    text = re.sub(r'"([^"]*)"', LEFT_DOUBLE + r'\1' + RIGHT_DOUBLE, text)

    # Convert apostrophes in contractions: don't, isn't, it's, etc.
    text = re.sub(r"(\w)'(\w)", r'\1' + RIGHT_SINGLE + r'\2', text)

    # Convert 'n' style contractions: rock 'n' roll
    # Must come BEFORE start-of-word pattern to catch both apostrophes
    text = re.sub(r"(^|\s)'(\w)'(\s|$)", r'\1' + RIGHT_SINGLE + r'\2' + RIGHT_SINGLE + r'\3', text)

    # Convert apostrophe at start of word: 'twas, 'tis, 'em
    text = re.sub(r"(^|\s)'(\w)", r'\1' + RIGHT_SINGLE + r'\2', text)

    return text


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    # Parse arguments
    check_mode = '--check' in sys.argv
    inplace = '--inplace' in sys.argv

    # Get file path (skip flags)
    file_args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not file_args:
        print("Error: No file specified", file=sys.stderr)
        sys.exit(1)

    filepath = file_args[0]

    # Handle stdin explicitly
    if filepath == '-' or filepath == '/dev/stdin':
        original = sys.stdin.read()
        filepath = '<stdin>'
    else:
        filepath = Path(filepath)
        if not filepath.exists():
            print(f"Error: File not found: {filepath}", file=sys.stderr)
            sys.exit(1)
        original = filepath.read_text(encoding='utf-8')
    converted = convert_quotes(original)

    if check_mode:
        if original != converted:
            print(f"{filepath}: needs conversion")
            sys.exit(1)
        else:
            print(f"{filepath}: ok")
            sys.exit(0)
    elif inplace:
        if isinstance(filepath, str):
            print("Error: Cannot use --inplace with stdin", file=sys.stderr)
            sys.exit(1)
        filepath.write_text(converted, encoding='utf-8')
        print(f"Converted: {filepath}")
    else:
        print(converted)


if __name__ == '__main__':
    main()
