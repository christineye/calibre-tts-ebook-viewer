#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__copyright__ = '2016, github.com/christineye'
__docformat__ = 'restructuredtext en'

from PyQt5.Qt import QWidget, QVBoxLayout, QLabel, QLineEdit, QComboBox, QIntValidator, QHBoxLayout, QCheckBox

from calibre.utils.config import JSONConfig

# This is where all preferences for this plugin will be stored
# Remember that this name (i.e. plugins/viewer_annotation) is also
# in a global namespace, so make it as unique as possible.
# You should always prefix your config file name with plugins/,
# so as to ensure you dont accidentally clobber a calibre config file
prefs = JSONConfig('plugins/tts_ebook_viewer')

# Set defaults
import os
prefs.defaults['voice'] = None
prefs.defaults['rate'] = 1
prefs.defaults['volume'] = 100

from calibre_plugins.tts_ebook_viewer.hotkeys import keycodes, HotkeyWidget, setHotkeyDefault

setHotkeyDefault(prefs, 'pause', 'space', ctrl=True)
setHotkeyDefault(prefs, 'stop', 'space', ctrl = True, shift=True)
setHotkeyDefault(prefs, 'select', '`')


class ConfigWidget(QWidget):

    def __init__(self):
        QWidget.__init__(self)
        self.l = QVBoxLayout()
        self.setLayout(self.l)

        self.label = QLabel("Voice")
        self.l.addWidget(self.label)

        self.voiceOptions = QComboBox()
        self.l.addWidget(self.voiceOptions)

        self.rateLabel = QLabel("Rate (-10 to 10)")
        self.l.addWidget(self.rateLabel)
        
        self.rateEdit = QLineEdit()
        self.rateEdit.setValidator(QIntValidator(-10, 10))
        self.rateEdit.setText(str(prefs['rate']))

        self.l.addWidget(self.rateEdit)
        
        self.volumeLabel = QLabel("Volume (0 to 100)")
        self.volumeEdit = QLineEdit()
        self.volumeEdit.setValidator(QIntValidator(0, 100))
        self.volumeEdit.setText(str(prefs['volume']))
        self.l.addWidget(self.volumeLabel)
        self.l.addWidget(self.volumeEdit)
        
        import win32com.client
        self.spVoice = win32com.client.Dispatch("SAPI.SpVoice")
        voices = self.spVoice.GetVoices("", "")
        
        for i in range(voices.Count):
            self.voiceOptions.addItem(voices.Item(i).GetDescription())
            
            if voices.Item(i).GetDescription() == prefs['voice']:
                self.voiceOptions.setCurrentIndex(i)
                
        self.pauseHotKey = HotkeyWidget(prefs, "pause", "Enable Pause/Play hotkey" )
        self.l.addWidget(self.pauseHotKey)
        
        self.stopHotKey = HotkeyWidget(prefs, "stop", "Enable Stop hotkey")
        self.l.addWidget(self.stopHotKey)
        
        self.selectHotKey = HotkeyWidget(prefs, "select", "Enable Select Mode hotkey")
        self.l.addWidget(self.selectHotKey)

    def save_settings(self):
        from calibre_plugins.tts_ebook_viewer.hotkeys import keycodes
        
        prefs['voice'] = unicode(self.voiceOptions.currentText())
        prefs['rate'] = int(self.rateEdit.text())
        prefs['volume'] = int(self.volumeEdit.text())
        
        self.pauseHotKey.save_settings(prefs)
        self.stopHotKey.save_settings(prefs)
        self.selectHotKey.save_settings(prefs)

