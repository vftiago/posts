#!/usr/bin/env python3
"""
Convert curly quotes to straight quotes in Markdown prose.

- Converts \u201c and \u201d to "
- Converts \u2018 and \u2019 to '
- Preserves code blocks (``` ... ```) and inline code (` ... `) as-is
- Preserves YAML front matter (--- ... ---) as-is

Usage:
    straightquotes <file>           # Print converted output to stdout
    straightquotes <file> --inplace # Modify file in place
    straightquotes --check <file>   # Check if file needs conversion (exit 1 if yes)
"""

import sys
import re
from pathlib import Path


def convert_quotes(text: str) -> str:
    """Convert curly quotes to straight quotes, preserving code sections."""
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
    """Convert curly quotes in a prose line, preserving inline code."""
    parts = re.split(r'(`[^`]+`)', line)

    converted_parts = []
    for part in parts:
        if part.startswith('`') and part.endswith('`'):
            converted_parts.append(part)
        else:
            converted_parts.append(straighten_quotes(part))

    return ''.join(converted_parts)


def straighten_quotes(text: str) -> str:
    """Replace all curly quotes with straight equivalents."""
    text = text.replace('\u201c', '"')   # left double
    text = text.replace('\u201d', '"')   # right double
    text = text.replace('\u2018', "'")   # left single
    text = text.replace('\u2019', "'")   # right single
    return text


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    check_mode = '--check' in sys.argv
    inplace = '--inplace' in sys.argv

    file_args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not file_args:
        print("Error: No file specified", file=sys.stderr)
        sys.exit(1)

    filepath = file_args[0]

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
