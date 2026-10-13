# encoding: utf-8

###########################################################################################################
#
#   Type Korean CJJ
#
#   Glyphs 3 plugin: a typing mode for the Edit View (Text tool) that inserts positional
#   Hangul jamo glyphs — Choseong / Jungseong / Jongseong — instead of compatibility jamo.
#
#   Edit → Type Hangul Jamo (⌃R) cycles: Off (normal typing) → Choseong → Jongseong → Off
#   Vowels always insert Jungseong. Compound vowels / finals combine when typed within 0.4 s.
#
#   Copyright 2026 HyunJun Lee
#   Apache License 2.0
#
###########################################################################################################

from __future__ import division, print_function, unicode_literals
import os
import sys
import traceback
import objc
from GlyphsApp import Glyphs, EDIT_MENU
from GlyphsApp.plugins import GeneralPlugin
from AppKit import (
	NSMenuItem, NSOnState, NSOffState, NSEvent, NSBeep,
	NSKeyDownMask, NSLeftMouseDownMask, NSLeftMouseDown,
	NSControlKeyMask, NSShiftKeyMask, NSCommandKeyMask, NSAlternateKeyMask,
)
from Foundation import NSMakeRange, NSNotFound

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jamo_logic  # noqa: E402

OFF = "off"
MODES = (OFF, jamo_logic.CHO, jamo_logic.JONG)


def log(message):
	# print() shows up in Window → Macro Panel (logToConsole only goes to Console.app)
	print("TypeKoreanCJJ: %s" % message)


class TypeKoreanCJJ(GeneralPlugin):

	@objc.python_method
	def settings(self):
		self.name = Glyphs.localize({
			"en": "Type Hangul Jamo",
			"ko": "한글 초·중·종성 입력",
		})
		self.modeNames = {
			OFF: Glyphs.localize({"en": "Off (normal typing)", "ko": "꺼짐 (기본 타이핑)"}),
			jamo_logic.CHO: Glyphs.localize({"en": "Choseong", "ko": "초성"}),
			jamo_logic.JONG: Glyphs.localize({"en": "Jongseong", "ko": "종성"}),
		}

	@objc.python_method
	def start(self):
		self.mode = OFF
		self.monitor = None
		self.resetCombine()
		try:
			menuItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
				self.name,
				self.cycleMode_,
				"r"
			)
			menuItem.setKeyEquivalentModifierMask_(NSControlKeyMask)
			menuItem.setTarget_(self)
			Glyphs.menu[EDIT_MENU].append(menuItem)
			self.menuItem = menuItem
		except Exception:
			log(traceback.format_exc())

	# ------------------------------------------------------------------ menu

	def cycleMode_(self, sender):
		try:
			self.mode = MODES[(MODES.index(self.mode) + 1) % len(MODES)]
			if self.mode == OFF:
				self.stopMonitor()
			else:
				self.startMonitor()
			self.resetCombine()
			Glyphs.showNotification(self.name, self.modeNames[self.mode])
		except Exception:
			log(traceback.format_exc())

	def validateMenuItem_(self, menuItem):
		try:
			if self.mode == OFF:
				menuItem.setTitle_(self.name)
				menuItem.setState_(NSOffState)
			else:
				menuItem.setTitle_("%s: %s" % (self.name, self.modeNames[self.mode]))
				menuItem.setState_(NSOnState)
		except Exception:
			pass
		return True

	# ------------------------------------------------------------------ key handling

	@objc.python_method
	def startMonitor(self):
		if self.monitor is None:
			self.monitor = NSEvent.addLocalMonitorForEventsMatchingMask_handler_(
				NSKeyDownMask | NSLeftMouseDownMask,
				self.handleEvent
			)

	@objc.python_method
	def stopMonitor(self):
		if self.monitor is not None:
			NSEvent.removeMonitor_(self.monitor)
			self.monitor = None

	@objc.python_method
	def resetCombine(self):
		self.previous = None
		self.previousTime = None

	@objc.python_method
	def handleEvent(self, event):
		if event.type() == NSLeftMouseDown:
			# a click may move the cursor: never combine across it
			self.resetCombine()
			return event
		return self.handleKeyDown(event)

	@objc.python_method
	def handleKeyDown(self, event):
		isJamoKey = False
		try:
			if self.mode == OFF:
				return event
			if event.modifierFlags() & (NSCommandKeyMask | NSControlKeyMask | NSAlternateKeyMask):
				return event
			tab = self.activeTextTab(event)
			if tab is None:
				return event

			isJamoKey = event.keyCode() in jamo_logic.KEYCODE_JAMO
			now = event.timestamp()
			previous = self.previous if jamo_logic.withinCombineWindow(self.previousTime, now) else None

			shift = bool(event.modifierFlags() & NSShiftKeyMask)
			result = jamo_logic.resolve(event.keyCode(), shift, self.mode, previous)
			if result is None:
				self.resetCombine()
				return event

			kind, role, jamo, cp = result
			if kind == jamo_logic.REJECT:
				self.resetCombine()
				NSBeep()
				return None

			font = Glyphs.font
			glyph = self.glyphForCodepoint(font, cp)
			if glyph is None:
				self.resetCombine()
				NSBeep()
				log("no glyph for U+%04X (%s, %s)" % (cp, jamo, role))
				return None

			self.insert(tab, font, glyph, cp, replace=(kind == jamo_logic.REPLACE))
			self.previous = (role, jamo)
			self.previousTime = now
			return None
		except Exception:
			log(traceback.format_exc())
			self.resetCombine()
			if isJamoKey:
				# never let a jamo key fall through to the input method while the mode is on
				NSBeep()
				return None
			return event

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
	def insert(self, tab, font, glyph, cp, replace=False):
		"""Type the jamo the same way a key press would, replacing the previous character when combining."""
		if "%04X" % cp not in (glyph.unicodes or []):
			# glyph found by name only: the character would not map to it, so place the layer directly
			self.insertLayer(tab, font, glyph, replace)
			return

		graphicView = tab.graphicView()
		cursor = graphicView.selectedRange().location
		if replace and cursor > 0:
			replacement = NSMakeRange(cursor - 1, 1)
		else:
			replacement = NSMakeRange(NSNotFound, 0)  # current selection

		if graphicView.respondsToSelector_("insertText:replacementRange:"):
			graphicView.insertText_replacementRange_(chr(cp), replacement)
		else:
			if replacement.location != NSNotFound:
				graphicView.setSelectedRange_(replacement)
			graphicView.insertText_(chr(cp))

	@objc.python_method
	def insertLayer(self, tab, font, glyph, replace):
		layer = glyph.layers[font.selectedFontMaster.id]
		layers = list(tab.layers)
		cursor = tab.layersCursor
		if replace and cursor > 0:
			layers[cursor - 1] = layer
			newCursor = cursor
		else:
			layers.insert(cursor, layer)
			newCursor = cursor + 1
		tab.layers = layers
		tab.layersCursor = newCursor

	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged."""
		return __file__
