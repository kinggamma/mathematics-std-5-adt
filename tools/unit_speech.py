#!/usr/bin/env python3
"""
Expand metric unit abbreviations (km, kg, mm, mL, ...) to full words for
speech, while leaving the visible text/HTML untouched (item 2 in the
evaluation comments: "all symbols/signs of lengths, mass and volume written
in abbreviation ... the AI should read it in long term").

Only touches a fixed whitelist of length/mass/volume unit abbreviations, and
only where they're unambiguous in this book's context (immediately after a
number, or as a bare column-header token like "km m cm").
"""
import re

# Longest-first so e.g. "dam" matches before "m", "mL" before "L".
UNITS = [
    ("km", "kilometres"),
    ("dam", "decametres"),
    ("dm", "decimetres"),
    ("mm", "millimetres"),
    ("cm", "centimetres"),
    ("kg", "kilograms"),
    ("dag", "decagrams"),
    ("dg", "decigrams"),
    ("mg", "milligrams"),
    ("mL", "millilitres"),
    ("ml", "millilitres"),
    ("L", "litres"),
    ("t", "tonnes"),
    ("m", "metres"),
    ("g", "grams"),
]

_UNIT_RE = "|".join(re.escape(a) for a, _ in sorted(UNITS, key=lambda x: -len(x[0])))
_UNIT_MAP = dict(UNITS)

# A unit token right after a number (optionally with a space), e.g. "3 km", "54cm".
AFTER_NUMBER_RE = re.compile(rf"(?<=[0-9])(\s?)({_UNIT_RE})\b")

# A unit token in a bare "in X and Y" / "X and Y" unit-name list with no numbers,
# e.g. "in cm and mm", "in kg and g".
IN_LIST_RE = re.compile(rf"\b(in|and) ({_UNIT_RE})\b(?! *=)")

# A bare sequence of 2+ unit tokens with nothing else, e.g. "km m cm", "dag dg mg".
HEADER_RE = re.compile(rf"^\s*(?:(?:{_UNIT_RE})[\s,]*){{2,}}\s*$")
HEADER_TOKEN_RE = re.compile(rf"({_UNIT_RE})")


def _plural_ok(word):
    return word


_PLURAL_WORDS = "|".join(sorted({w for w in _UNIT_MAP.values()}, key=len, reverse=True))
_SINGULARIZE_RE = re.compile(rf"(?<![0-9.])\b1 ({_PLURAL_WORDS})\b")


def _singularize(text):
    return _SINGULARIZE_RE.sub(lambda m: f"1 {m.group(1)[:-1]}", text)


def expand_units(text):
    if HEADER_RE.match(text):
        return HEADER_TOKEN_RE.sub(lambda m: _UNIT_MAP[m.group(1)], text)

    def repl(m):
        sep, unit = m.group(1), m.group(2)
        return f"{sep}{_UNIT_MAP[unit]}"

    def repl_list(m):
        word, unit = m.group(1), m.group(2)
        return f"{word} {_UNIT_MAP[unit]}"

    text = AFTER_NUMBER_RE.sub(repl, text)
    text = IN_LIST_RE.sub(repl_list, text)
    return _singularize(text)


if __name__ == "__main__":
    import sys
    print(expand_units(sys.argv[1]))
