# encoding: utf-8

###########################################################################################################
#
#   Type Korean CJJ — jamo logic
#
#   Pure Python (no Glyphs / AppKit imports) so it can be unit-tested outside Glyphs.
#   Maps physical keys (Dubeolsik layout) to positional Hangul jamo code points:
#   Choseong U+1100–1112, Jungseong U+1161–1175, Jongseong U+11A8–11C2.
#
#   Copyright 2026 HyunJun Lee
#   Apache License 2.0
#
###########################################################################################################

from __future__ import division, print_function, unicode_literals

CHO = "cho"
JUNG = "jung"
JONG = "jong"

# Compatibility jamo in Unicode order of each positional block
CHO_JAMO = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
JUNG_JAMO = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"
JONG_JAMO = "ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ"

CHO_BASE = 0x1100
JUNG_BASE = 0x1161
JONG_BASE = 0x11A8

# macOS virtual key codes (ANSI) → (jamo, jamo with Shift), Dubeolsik layout
KEYCODE_JAMO = {
	12: ("ㅂ", "ㅃ"),  # q
	13: ("ㅈ", "ㅉ"),  # w
	14: ("ㄷ", "ㄸ"),  # e
	15: ("ㄱ", "ㄲ"),  # r
	17: ("ㅅ", "ㅆ"),  # t
	16: ("ㅛ", "ㅛ"),  # y
	32: ("ㅕ", "ㅕ"),  # u
	34: ("ㅑ", "ㅑ"),  # i
	31: ("ㅐ", "ㅒ"),  # o
	35: ("ㅔ", "ㅖ"),  # p
	0: ("ㅁ", "ㅁ"),   # a
	1: ("ㄴ", "ㄴ"),   # s
	2: ("ㅇ", "ㅇ"),   # d
	3: ("ㄹ", "ㄹ"),   # f
	5: ("ㅎ", "ㅎ"),   # g
	4: ("ㅗ", "ㅗ"),   # h
	38: ("ㅓ", "ㅓ"),  # j
	40: ("ㅏ", "ㅏ"),  # k
	37: ("ㅣ", "ㅣ"),  # l
	6: ("ㅋ", "ㅋ"),   # z
	7: ("ㅌ", "ㅌ"),   # x
	8: ("ㅊ", "ㅊ"),   # c
	9: ("ㅍ", "ㅍ"),   # v
	11: ("ㅠ", "ㅠ"),  # b
	45: ("ㅜ", "ㅜ"),  # n
	46: ("ㅡ", "ㅡ"),  # m
}

VOWEL_COMBOS = {
	("ㅗ", "ㅏ"): "ㅘ",
	("ㅗ", "ㅐ"): "ㅙ",
	("ㅗ", "ㅣ"): "ㅚ",
	("ㅜ", "ㅓ"): "ㅝ",
	("ㅜ", "ㅔ"): "ㅞ",
	("ㅜ", "ㅣ"): "ㅟ",
	("ㅡ", "ㅣ"): "ㅢ",
}

JONG_COMBOS = {
	("ㄱ", "ㅅ"): "ㄳ",
	("ㄴ", "ㅈ"): "ㄵ",
	("ㄴ", "ㅎ"): "ㄶ",
	("ㄹ", "ㄱ"): "ㄺ",
	("ㄹ", "ㅁ"): "ㄻ",
	("ㄹ", "ㅂ"): "ㄼ",
	("ㄹ", "ㅅ"): "ㄽ",
	("ㄹ", "ㅌ"): "ㄾ",
	("ㄹ", "ㅍ"): "ㄿ",
	("ㄹ", "ㅎ"): "ㅀ",
	("ㅂ", "ㅅ"): "ㅄ",
}

# Result kinds
INSERT = "insert"    # insert a new glyph at the cursor
REPLACE = "replace"  # replace the glyph just before the cursor (compound vowel / final)
REJECT = "reject"    # a jamo key, but no glyph exists for it in this position (beep)


def isVowel(jamo):
	return jamo in JUNG_JAMO


def codepoint(jamo, role):
	"""Positional code point for a compatibility jamo, or None if it has no form in that role."""
	if role == CHO and jamo in CHO_JAMO:
		return CHO_BASE + CHO_JAMO.index(jamo)
	if role == JUNG and jamo in JUNG_JAMO:
		return JUNG_BASE + JUNG_JAMO.index(jamo)
	if role == JONG and jamo in JONG_JAMO:
		return JONG_BASE + JONG_JAMO.index(jamo)
	return None


def resolve(keyCode, shift, consonantRole, previous=None):
	"""
	Decide what a key press should do.

	keyCode:       macOS virtual key code
	shift:         True if Shift is held
	consonantRole: CHO or JONG — where consonant keys go
	previous:      (role, jamo) of the glyph this plugin inserted right before the cursor, or None

	Returns None for keys that are not jamo keys (let the event through),
	otherwise a tuple (kind, role, jamo, codepoint).
	"""
	pair = KEYCODE_JAMO.get(keyCode)
	if pair is None:
		return None
	jamo = pair[1] if shift else pair[0]
	role = JUNG if isVowel(jamo) else consonantRole

	if previous is not None:
		prevRole, prevJamo = previous
		if prevRole == role:
			combos = VOWEL_COMBOS if role == JUNG else JONG_COMBOS if role == JONG else {}
			combined = combos.get((prevJamo, jamo))
			if combined is not None:
				return (REPLACE, role, combined, codepoint(combined, role))

	cp = codepoint(jamo, role)
	if cp is None:
		return (REJECT, role, jamo, None)
	return (INSERT, role, jamo, cp)
