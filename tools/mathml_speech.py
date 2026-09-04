#!/usr/bin/env python3
"""
Convert the MathML fragments used in this book's texts.json into natural
spoken English, inserting "over" for fractions instead of just concatenating
numerator and denominator (which is what the TTS pipeline currently does,
since it strips all tags and keeps only the text content).

Only handles the subset of MathML actually used in this book (mrow, mfrac,
msup, mi, mn, mo, mtext, mspace, mpadded, mstyle, mtable/mtr/mtd). Falls back
to concatenating text content (with spaces) for anything unrecognised, so it
never crashes — but callers should sanity-check output before regenerating
audio at scale.
"""
import html
import re
import xml.etree.ElementTree as ET

MO_WORDS = {
    "=": "equals",
    "+": "plus",
    "-": "minus",
    "−": "minus",
    "×": "times",
    "÷": "divided by",
    "·": "times",
    ",": ",",
    ".": ".",
}

MI_WORDS = {
    "π": "pi",
}


def _text(s):
    return (s or "").replace("\xa0", " ").strip()


def _join(parts):
    out = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        out.append(p)
    s = " ".join(out)
    s = re.sub(r"\s+([,.])", r"\1", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def render(node):
    tag = node.tag.split("}")[-1]  # strip namespace if any

    if tag in ("math", "mrow", "mstyle", "mpadded"):
        parts = []
        prev_tag = None  # last *meaningful* (non-whitespace) child tag
        letter_run = []  # buffer of consecutive single-character <mi> text
        for c in node:
            child_tag = c.tag.split("}")[-1]
            is_letter = (
                child_tag == "mi"
                and len(_text(c.text)) == 1
                and _text(c.text).isascii()
                and _text(c.text).isalpha()
            )
            if is_letter:
                letter_run.append(_text(c.text))
                continue
            if letter_run:
                parts.append("".join(letter_run))
                letter_run = []
            rendered = render(c)
            is_whitespace_mtext = child_tag == "mtext" and not _text(c.text)
            if not is_whitespace_mtext:
                if prev_tag == "mn" and child_tag == "mfrac":
                    parts.append("and")
                parts.append(rendered)
                prev_tag = child_tag
        if letter_run:
            parts.append("".join(letter_run))
        return _join(parts)

    if tag == "mfrac":
        children = list(node)
        if len(children) != 2:
            return _join([render(c) for c in children])
        num, den = children
        return f"{render(num)} over {render(den)}"

    if tag == "msup":
        children = list(node)
        if len(children) != 2:
            return _join([render(c) for c in children])
        base, exp = children
        exp_text = render(exp)
        if exp_text.strip() == "2":
            return f"{render(base)} squared"
        if exp_text.strip() == "3":
            return f"{render(base)} cubed"
        return f"{render(base)} to the power {exp_text}"

    if tag == "msub":
        children = list(node)
        if len(children) != 2:
            return _join([render(c) for c in children])
        base, sub = children
        return f"{render(base)} sub {render(sub)}"

    if tag == "mtable":
        rows = []
        for tr in node:
            cells = [render(td) for td in tr]
            rows.append(_join(cells))
        return ", then ".join(r for r in rows if r)

    if tag in ("mtr", "mtd"):
        return _join([render(c) for c in node])

    if tag == "mspace":
        return ""

    if tag == "mi":
        t = _text(node.text)
        return MI_WORDS.get(t, t)

    if tag == "mn":
        return _text(node.text)

    if tag == "mtext":
        return _text(node.text)

    if tag == "mo":
        t = _text(node.text)
        return MO_WORDS.get(t, t)

    # Unknown tag: just render children.
    return _join([render(c) for c in node])


def mathml_to_speech(fragment):
    """fragment: a string containing one <math>...</math> element (already
    HTML-entity-decoded or not; this function decodes entities itself)."""
    decoded = html.unescape(fragment)
    try:
        root = ET.fromstring(decoded)
    except ET.ParseError as e:
        raise ValueError(f"Could not parse MathML: {e}\n{decoded[:300]}")
    return render(root)


def convert_mixed_text(raw):
    """Given a texts.json value that may mix plain text and one or more
    <math>...</math> fragments, return the fully spoken version with fractions
    expanded to 'X over Y'."""
    parts = []
    pos = 0
    for m in re.finditer(r"<math>.*?</math>", raw, re.DOTALL):
        parts.append(raw[pos:m.start()])
        parts.append(mathml_to_speech(m.group(0)))
        pos = m.end()
    parts.append(raw[pos:])
    return _join(parts) if False else "".join(parts).strip()


if __name__ == "__main__":
    import sys
    print(convert_mixed_text(sys.argv[1]))
