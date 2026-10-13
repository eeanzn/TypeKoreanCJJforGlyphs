# encoding: utf-8
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "TypeKoreanCJJ.glyphsPlugin", "Contents", "Resources"))
import jamo_logic as J  # noqa: E402

KEY = {c: k for k, c in {
	12: "q", 13: "w", 14: "e", 15: "r", 17: "t", 16: "y", 32: "u", 34: "i", 31: "o", 35: "p",
	0: "a", 1: "s", 2: "d", 3: "f", 5: "g", 4: "h", 38: "j", 40: "k", 37: "l",
	6: "z", 7: "x", 8: "c", 9: "v", 11: "b", 45: "n", 46: "m",
}.items()}


def type_keys(keys, role, previous=None):
	"""Simulate typing a key sequence; returns the list of code points left in the text."""
	out = []
	for ch in keys:
		result = J.resolve(KEY[ch.lower()], ch.isupper(), role, previous)
		kind, r, jamo, cp = result
		if kind == J.REJECT:
			previous = None
			continue
		if kind == J.REPLACE:
			out[-1] = cp
		else:
			out.append(cp)
		previous = (r, jamo)
	return out


class TestBlocks(unittest.TestCase):

	def test_block_sizes_and_ranges(self):
		self.assertEqual(len(J.CHO_JAMO), 19)
		self.assertEqual(len(J.JUNG_JAMO), 21)
		self.assertEqual(len(J.JONG_JAMO), 27)
		self.assertEqual(J.codepoint("ㅎ", J.CHO), 0x1112)
		self.assertEqual(J.codepoint("ㅣ", J.JUNG), 0x1175)
		self.assertEqual(J.codepoint("ㅎ", J.JONG), 0x11C2)

	def test_no_jongseong_for_tense_d_b_j(self):
		for jamo in "ㄸㅃㅉ":
			self.assertIsNone(J.codepoint(jamo, J.JONG))

	def test_every_key_mapped_to_a_jamo(self):
		self.assertEqual(len(J.KEYCODE_JAMO), 26)
		for plain, shifted in J.KEYCODE_JAMO.values():
			self.assertIn(plain, J.CHO_JAMO + J.JUNG_JAMO)
			self.assertIn(shifted, J.CHO_JAMO + J.JUNG_JAMO)


class TestResolve(unittest.TestCase):

	def test_non_jamo_key_passes_through(self):
		self.assertIsNone(J.resolve(49, False, J.CHO))  # space
		self.assertIsNone(J.resolve(123, False, J.CHO))  # left arrow

	def test_choseong_mode(self):
		self.assertEqual(type_keys("rk", J.CHO), [0x1100, 0x1161])  # ㄱ ㅏ

	def test_jongseong_mode(self):
		self.assertEqual(type_keys("r", J.JONG), [0x11A8])  # ㄱ

	def test_vowel_always_jungseong(self):
		self.assertEqual(type_keys("k", J.JONG), [0x1161])

	def test_shift_doubles(self):
		self.assertEqual(type_keys("REQTW", J.CHO), [0x1101, 0x1104, 0x1108, 0x110A, 0x110D])
		self.assertEqual(type_keys("OP", J.CHO), [0x1164, 0x1168])  # ㅒ ㅖ
		self.assertEqual(type_keys("A", J.CHO), [0x1106])  # Shift on a plain key = plain jamo

	def test_jongseong_rejects_tense_d_b_j(self):
		for ch in "EQW":
			self.assertEqual(J.resolve(KEY[ch.lower()], True, J.JONG)[0], J.REJECT)
		self.assertEqual(type_keys("RT", J.JONG), [0x11A9, 0x11BB])  # ㄲ ㅆ are fine

	def test_compound_vowels(self):
		cases = {"hk": "ㅘ", "ho": "ㅙ", "hl": "ㅚ", "nj": "ㅝ", "np": "ㅞ", "nl": "ㅟ", "ml": "ㅢ"}
		for keys, expected in cases.items():
			self.assertEqual(type_keys(keys, J.CHO), [J.codepoint(expected, J.JUNG)], keys)

	def test_compound_finals(self):
		cases = {"rt": "ㄳ", "sw": "ㄵ", "sg": "ㄶ", "fr": "ㄺ", "fa": "ㄻ", "fq": "ㄼ",
				 "ft": "ㄽ", "fx": "ㄾ", "fv": "ㄿ", "fg": "ㅀ", "qt": "ㅄ"}
		for keys, expected in cases.items():
			self.assertEqual(type_keys(keys, J.JONG), [J.codepoint(expected, J.JONG)], keys)

	def test_choseong_never_combines(self):
		self.assertEqual(type_keys("rt", J.CHO), [0x1100, 0x1109])

	def test_compound_does_not_chain(self):
		self.assertEqual(type_keys("hkl", J.CHO), [0x116A, 0x1175])  # ㅘ then ㅣ

	def test_no_combine_without_previous(self):
		self.assertEqual(J.resolve(KEY["k"], False, J.CHO, None), (J.INSERT, J.JUNG, "ㅏ", 0x1161))

	def test_no_combine_across_roles(self):
		# previous glyph is a Choseong ㄹ, consonant mode switched to Jongseong: no ㄺ
		self.assertEqual(J.resolve(KEY["r"], False, J.JONG, (J.CHO, "ㄹ"))[0], J.INSERT)


if __name__ == "__main__":
	unittest.main()
