# encoding: utf-8

###########################################################################################################
#
#   Type Korean CJJ
#
#   Glyphs 3 plugin: a typing mode for the Edit View (Text tool) that inserts positional
#   Hangul jamo glyphs — Choseong / Jungseong / Jongseong — instead of compatibility jamo.
#
#   Edit → Type Hangul Jamo (⌃T)                  toggle the typing mode
#   Edit → Consonants as Jongseong (⌃⇧T)          consonant keys insert Jongseong instead of Choseong
#
#   Copyright 2026 HyunJun Lee
#   Apache License 2.0
#
###########################################################################################################

from __future__ import division, print_function, unicode_literals
import os
import sys
import objc
from GlyphsApp import Glyphs, EDIT_MENU
from GlyphsApp.plugins import GeneralPlugin
from AppKit import (
	NSMenuItem, NSOnState, NSOffState, NSEvent, NSBeep,
	NSKeyDownMask, NSLeftMouseDownMask, NSLeftMouseDown, NSControlKeyMask, NSShiftKeyMask, NSCommandKeyMask, NSAlternateKeyMask,
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jamo_logic  # noqa: E402

CONSONANT_ROLE_KEY = "com.eeanzn.TypeKoreanCJJ.consonantRole"


class TypeKoreanCJJ(GeneralPlugin):

	@objc.python_method
	def settings(self):
		self.name = Glyphs.localize({
			"en": "Type Hangul Jamo",
			"ko": "한글 초·중·종성 입력",
		})
		self.jongName = Glyphs.localize({
			"en": "Consonants as Jongseong",
			"ko": "자음을 종성으로 입력",
		})

	@objc.python_method
	def start(self):
		self.enabled = False
		self.monitor = None
		self.previous = None
		try:
			toggleItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
				self.name,
				self.toggleTyping_,
				"t"
			)
			toggleItem.setKeyEquivalentModifierMask_(NSControlKeyMask)
			toggleItem.setTarget_(self)

			jongItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
				self.jongName,
				self.toggleConsonantRole_,
				"t"
			)
			jongItem.setKeyEquivalentModifierMask_(NSControlKeyMask | NSShiftKeyMask)
			jongItem.setTarget_(self)

			Glyphs.menu[EDIT_MENU].append(toggleItem)
			Glyphs.menu[EDIT_MENU].append(jongItem)
			self.toggleItem = toggleItem
			self.jongItem = jongItem
		except Exception as e:
			self.logToConsole("TypeKoreanCJJ Error: %s" % str(e))

	# ------------------------------------------------------------------ menu

	def toggleTyping_(self, sender):
		try:
			if self.enabled:
				self.stopMonitor()
			else:
				self.startMonitor()
			self.notifyState()
		except Exception as e:
			self.logToConsole("TypeKoreanCJJ toggle error: %s" % str(e))

	def toggleConsonantRole_(self, sender):
		try:
			role = jamo_logic.CHO if self.consonantRole() == jamo_logic.JONG else jamo_logic.JONG
			Glyphs.defaults[CONSONANT_ROLE_KEY] = role
			self.previous = None
			self.notifyState()
		except Exception as e:
			self.logToConsole("TypeKoreanCJJ role error: %s" % str(e))

	def validateMenuItem_(self, menuItem):
		try:
			if menuItem == self.toggleItem:
				menuItem.setState_(NSOnState if self.enabled else NSOffState)
			elif menuItem == self.jongItem:
				isJong = self.consonantRole() == jamo_logic.JONG
				menuItem.setState_(NSOnState if isJong else NSOffState)
		except Exception:
			pass
		return True

	@objc.python_method
	def consonantRole(self):
		role = Glyphs.defaults[CONSONANT_ROLE_KEY]
		return jamo_logic.JONG if role == jamo_logic.JONG else jamo_logic.CHO

	@objc.python_method
	def notifyState(self):
		if not self.enabled:
			state = Glyphs.localize({"en": "Off", "ko": "꺼짐"})
		elif self.consonantRole() == jamo_logic.JONG:
			state = Glyphs.localize({"en": "On — consonants as Jongseong", "ko": "켜짐 — 자음은 종성"})
		else:
			state = Glyphs.localize({"en": "On — consonants as Choseong", "ko": "켜짐 — 자음은 초성"})
		Glyphs.showNotification(self.name, state)

	# ------------------------------------------------------------------ key handling

	@objc.python_method
	def startMonitor(self):
		if self.monitor is None:
			self.monitor = NSEvent.addLocalMonitorForEventsMatchingMask_handler_(
				NSKeyDownMask | NSLeftMouseDownMask,
				self.handleEvent
			)
		self.enabled = True
		self.previous = None

	@objc.python_method
	def stopMonitor(self):
		if self.monitor is not None:
			NSEvent.removeMonitor_(self.monitor)
			self.monitor = None
		self.enabled = False
		self.previous = None

	@objc.python_method
	def handleEvent(self, event):
		if event.type() == NSLeftMouseDown:
			# a click may move the cursor: never combine across it
			self.previous = None
			return event
		return self.handleKeyDown(event)

	@objc.python_method
	def handleKeyDown(self, event):
		try:
			if event.modifierFlags() & (NSCommandKeyMask | NSControlKeyMask | NSAlternateKeyMask):
				return event
			tab = self.activeTextTab(event)
			if tab is None:
				return event

			if self.previous is not None and not self.previousIsBeforeCursor(tab):
				self.previous = None

			shift = bool(event.modifierFlags() & NSShiftKeyMask)
			previous = self.previous[:2] if self.previous is not None else None
			result = jamo_logic.resolve(event.keyCode(), shift, self.consonantRole(), previous)
			if result is None:
				self.previous = None
				return event

			kind, role, jamo, cp = result
			if kind == jamo_logic.REJECT:
				NSBeep()
				return None

			glyph = self.glyphForCodepoint(Glyphs.font, cp)
			if glyph is None:
				NSBeep()
				self.logToConsole("TypeKoreanCJJ: no glyph for U+%04X (%s, %s)" % (cp, jamo, role))
				return None

			self.insertGlyph(tab, glyph, replace=(kind == jamo_logic.REPLACE))
			self.previous = (role, jamo, cp)
			return None
		except Exception as e:
			self.logToConsole("TypeKoreanCJJ key error: %s" % str(e))
			return event

	@objc.python_method
	def previousIsBeforeCursor(self, tab):
		"""True if the glyph right before the cursor is the jamo this plugin inserted last."""
		expected = "%04X" % self.previous[2]
		try:
			cursor = tab.textCursor
			found = tab.layers[cursor - 1].parent.unicode if cursor > 0 else None
		except Exception:
			return True  # can't tell: don't break combining
		if found is not None and found.upper() == expected:
			return True
		self.logToConsole("TypeKoreanCJJ: combine reset, expected U+%s before cursor, found %s" % (expected, found))
		return False

	@objc.python_method
	def activeTextTab(self, event):
		"""The current Edit View tab, only if it is focused and the Text tool is active."""
		font = Glyphs.font
		if font is None or font.tool != "TextTool":
			return None
		tab = font.currentTab
		if tab is None:
			return None
		graphicView = tab.graphicView()
		window = graphicView.window()
		if window is None or event.window() != window or window.firstResponder() != graphicView:
			return None
		return tab

	@objc.python_method
	def glyphForCodepoint(self, font, cp):
		glyph = font.glyphs[chr(cp)]
		if glyph is None:
			info = Glyphs.glyphInfoForUnicode("%04X" % cp)
			if info is not None:
				glyph = font.glyphs[info.name]
		return glyph

	@objc.python_method
	def insertGlyph(self, tab, glyph, replace=False):
		font = Glyphs.font
		layer = glyph.layers[font.selectedFontMaster.id]
		layers = list(tab.layers)
		cursor = tab.textCursor
		if replace and cursor > 0:
			layers[cursor - 1] = layer
			newCursor = cursor
		else:
			del layers[cursor:cursor + tab.textRange]
			layers.insert(cursor, layer)
			newCursor = cursor + 1
		tab.layers = layers
		tab.textRange = 0
		tab.textCursor = newCursor

	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged."""
		return __file__
