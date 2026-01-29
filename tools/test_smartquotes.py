"""Tests for smartquotes script.

Run with: python3 test_smartquotes.py
Or with pytest if installed: pytest test_smartquotes.py -v
"""

import unittest
import sys
from pathlib import Path

# Import from smartquotes module
sys.path.insert(0, str(Path(__file__).parent))
from smartquotes import convert_quotes

# Unicode constants for readability
LDQ = '\u201c'  # " left double quote
RDQ = '\u201d'  # " right double quote
RSQ = '\u2019'  # ' right single quote (apostrophe)


class TestCurlyQuotesInProse(unittest.TestCase):
    """Straight quotes should become curly in prose."""

    def test_double_quotes(self):
        result = convert_quotes('He said "hello"')
        self.assertEqual(result, f'He said {LDQ}hello{RDQ}')

    def test_multiple_double_quotes(self):
        result = convert_quotes('"one" and "two"')
        self.assertEqual(result, f'{LDQ}one{RDQ} and {LDQ}two{RDQ}')

    def test_apostrophe_contraction(self):
        result = convert_quotes("don't")
        self.assertEqual(result, f"don{RSQ}t")

    def test_multiple_contractions(self):
        result = convert_quotes("it's won't isn't")
        self.assertEqual(result, f"it{RSQ}s won{RSQ}t isn{RSQ}t")

    def test_apostrophe_at_word_start(self):
        result = convert_quotes("'twas the night")
        self.assertEqual(result, f"{RSQ}twas the night")

    def test_apostrophe_em(self):
        result = convert_quotes("give 'em hell")
        self.assertEqual(result, f"give {RSQ}em hell")

    def test_rock_n_roll(self):
        result = convert_quotes("rock 'n' roll")
        self.assertEqual(result, f"rock {RSQ}n{RSQ} roll")

    def test_mixed_quotes_and_apostrophes(self):
        result = convert_quotes('"Don\'t stop," she said.')
        self.assertEqual(result, f'{LDQ}Don{RSQ}t stop,{RDQ} she said.')


class TestStraightQuotesInCode(unittest.TestCase):
    """Straight quotes should be preserved in code."""

    def test_code_block_preserved(self):
        text = '```\nconst x = "hello";\n```'
        self.assertEqual(convert_quotes(text), text)

    def test_code_block_with_language(self):
        text = '```javascript\nconst x = "hello";\nconsole.log("don\'t");\n```'
        self.assertEqual(convert_quotes(text), text)

    def test_inline_code_preserved(self):
        self.assertEqual(convert_quotes('Use `"quotes"` here'), 'Use `"quotes"` here')

    def test_inline_code_with_apostrophe(self):
        self.assertEqual(convert_quotes("Use `don't` here"), "Use `don't` here")

    def test_multiple_inline_code(self):
        text = 'Compare `"a"` with `"b"` in code'
        self.assertEqual(convert_quotes(text), text)


class TestYAMLFrontMatter(unittest.TestCase):
    """Straight quotes should be preserved in YAML front matter."""

    def test_front_matter_preserved(self):
        text = '---\ntitle: "My Article"\n---\n\nContent here.'
        result = convert_quotes(text)
        self.assertIn('title: "My Article"', result)

    def test_front_matter_with_prose_after(self):
        text = '---\ntitle: "Test"\n---\n\nHe said "hello".'
        result = convert_quotes(text)
        self.assertIn('title: "Test"', result)  # front matter unchanged
        self.assertIn(f'He said {LDQ}hello{RDQ}', result)  # prose converted


class TestMixedContent(unittest.TestCase):
    """Lines with both prose and code should be handled correctly."""

    def test_prose_and_inline_code_same_line(self):
        text = 'The "output" is `"raw"` here'
        result = convert_quotes(text)
        self.assertIn(f'{LDQ}output{RDQ}', result)  # prose converted
        self.assertIn('`"raw"`', result)  # code preserved

    def test_prose_before_code_block(self):
        text = 'He said "hi"\n\n```\n"code"\n```\n\nShe said "bye"'
        result = convert_quotes(text)
        self.assertIn(f'He said {LDQ}hi{RDQ}', result)
        self.assertIn('"code"', result)  # straight quotes in code
        self.assertIn(f'She said {LDQ}bye{RDQ}', result)

    def test_contraction_next_to_inline_code(self):
        text = "It's using `it's` syntax"
        result = convert_quotes(text)
        self.assertIn(f"It{RSQ}s", result)  # prose converted
        self.assertIn("`it's`", result)  # code preserved


class TestEdgeCases(unittest.TestCase):
    """Edge cases and boundary conditions."""

    def test_empty_string(self):
        self.assertEqual(convert_quotes(''), '')

    def test_no_quotes(self):
        text = 'Plain text without any quotes'
        self.assertEqual(convert_quotes(text), text)

    def test_already_curly_quotes(self):
        # Already-curly quotes should pass through unchanged
        text = f'Already {LDQ}curly{RDQ} quotes'
        self.assertEqual(convert_quotes(text), text)

    def test_unclosed_code_block(self):
        # Unclosed code block - everything after ``` stays straight
        text = 'Before\n```\n"in code"\nno closing'
        result = convert_quotes(text)
        self.assertIn('"in code"', result)

    def test_nested_backticks_in_code_block(self):
        text = '```\nconst s = `template "literal"`;\n```'
        self.assertEqual(convert_quotes(text), text)

    def test_empty_quotes(self):
        self.assertEqual(convert_quotes('""'), f'{LDQ}{RDQ}')

    def test_possessive(self):
        result = convert_quotes("James's book")
        self.assertEqual(result, f"James{RSQ}s book")


class TestStdinHandling(unittest.TestCase):
    """Test stdin input modes (requires running script as subprocess)."""

    def setUp(self):
        self.script = Path(__file__).parent / "smartquotes.py"

    def run_script(self, args, stdin_text=None):
        """Run the smartquotes script with given args and optional stdin."""
        import subprocess
        result = subprocess.run(
            ["python3", str(self.script)] + args,
            input=stdin_text,
            capture_output=True,
            text=True,
            timeout=5  # Prevent hangs
        )
        return result

    def test_stdin_with_dash(self):
        result = self.run_script(["-"], 'He said "hello"')
        self.assertEqual(result.returncode, 0)
        self.assertIn(LDQ, result.stdout)
        self.assertIn(RDQ, result.stdout)

    def test_stdin_with_dev_stdin(self):
        result = self.run_script(["/dev/stdin"], 'He said "hello"')
        self.assertEqual(result.returncode, 0)
        self.assertIn(LDQ, result.stdout)

    def test_stdin_check_mode_needs_conversion(self):
        result = self.run_script(["--check", "-"], 'straight "quotes"')
        self.assertEqual(result.returncode, 1)
        self.assertIn("needs conversion", result.stdout)

    def test_stdin_check_mode_ok(self):
        result = self.run_script(["--check", "-"], f'curly {LDQ}quotes{RDQ}')
        self.assertEqual(result.returncode, 0)
        self.assertIn("ok", result.stdout)

    def test_inplace_with_stdin_fails(self):
        result = self.run_script(["--inplace", "-"], "some text")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Cannot use --inplace with stdin", result.stderr)


if __name__ == '__main__':
    unittest.main()
