#!/usr/bin/env python3
"""
Speech transform for Chapter Seven (item 11 in the evaluation comments):
read "@" as "each" and "shs"/"sh" as "shillings", except where the text is
actually talking ABOUT the "@" symbol itself (defining what it means) —
there it's read as "at" so the sentence still makes sense.
"""
import re

# "@" immediately followed by "shs"/"sh"/a number is the invoice operator
# usage ("2 pairs of socks @ shs 1200") -> "each". Otherwise (discussing the
# symbol itself) -> "at".
AT_OPERATOR_RE = re.compile(r"@(?=\s*(?:shs\b|sh\b|[0-9]))")
AT_SYMBOL_RE = re.compile(r"@")

SHS_RE = re.compile(r"\bshs\b", re.IGNORECASE)
SH_TYPO_RE = re.compile(r"\bsh\b(?=\s*[0-9,])")


def expand_chapter7(text):
    text = AT_OPERATOR_RE.sub("each", text)
    text = AT_SYMBOL_RE.sub("at", text)
    text = SH_TYPO_RE.sub("shillings", text)
    text = SHS_RE.sub("shillings", text)
    return text


if __name__ == "__main__":
    import sys
    print(expand_chapter7(sys.argv[1]))
