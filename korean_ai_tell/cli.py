"""ai-tell FILE... [--lang ko|en] [--channel NAME] [--baseline FILE]

Prints one line per finding and exits 1 when any finding is BLOCK, so it can run in pre-commit or CI.
Use '-' to read standard input.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .rules import BLOCK, check, lang_of, load_baseline


def _line_of(text: str, match: str) -> int:
    # shortcut: the first occurrence of the matched words, not the exact offset (rules run on stripped prose)
    pos = text.find(match) if match else -1
    return text.count("\n", 0, pos) + 1 if pos >= 0 else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="ai-tell", description="Flag AI tells in Korean (or English) text.")
    ap.add_argument("files", nargs="+", help="text or Markdown files, '-' for stdin")
    ap.add_argument("--lang", choices=["ko", "en"], help="default: detect per file")
    ap.add_argument("--channel", help="length budget to apply (chat, speech, email, linkedin, letter, listing)")
    ap.add_argument("--baseline", help="JSON file that overrides channels, avoid_phrases, short_sentence_words")
    args = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    baseline = load_baseline(args.baseline)
    blocked = False
    for name in args.files:
        text = sys.stdin.read() if name == "-" else Path(name).read_text(encoding="utf-8")
        findings = check(text, args.lang, args.channel, baseline)
        print(f"{name}: lang={args.lang or lang_of(text)} {len(findings)} finding(s)")
        for line, f in sorted(((_line_of(text, f.match), f) for f in findings), key=lambda p: p[0]):
            quoted = f' "{f.match}"' if f.match else ""
            print(f"  {name}:{line}: {f.severity:5} {f.rule_id}{quoted} -> {f.hint}")
        blocked |= any(f.severity == BLOCK for f in findings)
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())
