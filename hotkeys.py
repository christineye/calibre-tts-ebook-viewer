__license__   = 'GPL v3'
__copyright__ = '2016, github.com/christineye'
__docformat__ = 'restructuredtext en'

from collections import OrderedDict

from PyQt5.Qt import QWidget, QVBoxLayout, QLabel, QLineEdit, QComboBox, QIntValidator, QHBoxLayout, QCheckBox



keycodes = OrderedDict([
    ("backspace", 8),
    ("tab", 9),
    ("enter", 13),
    ("caps lock", 20),
    ("escape", 27),
    ("space", 32),
    ("page up", 33),
    ("page down", 34),
    ("end", 35),
    ("home", 36),
    ("left arrow", 37),
    ("up arrow", 38),
    ("right arrow", 39),
    ("down arrow", 40), 
    ("0", 48),
    ("1", 49),
    ("2", 50),
    ("3", 51),
    ("4", 52),
    ("5", 53),
    ("6", 54),
    ("7", 55),
    ("8", 56),
    ("9", 57),
    ("a", 65),
    ("b", 66),
    ("c", 67),
    ("d", 68),
    ("e", 69),
    ("f", 70),
    ("g", 71),
    ("h", 72),
    ("i", 73),
    ("j", 74),
    ("k", 75),
    ("l", 76),
    ("m", 77),
    ("n", 78),
    ("o", 79),
    ("p", 80),
    ("q", 81),
    ("r", 82),
    ("s", 83),
    ("t", 84),
    ("u", 85),
    ("v", 86),
    ("w", 87),
    ("x", 88),
    ("y", 89),
    ("z", 90), 
    ("numpad 0", 96),
    ("numpad 1", 97),
    ("numpad 2", 98),
    ("numpad 3", 99),
    ("numpad 4", 100),
    ("numpad 5", 101),
    ("numpad 6", 102),
    ("numpad 7", 103),
    ("numpad 8", 104),
    ("numpad 9", 105),
    ("f1", 112),
    ("f2", 113),
    ("f3", 114),
    ("f4", 115),
    ("f5", 116),
    ("f6", 117),
    ("f7", 118),
    ("f8", 119),
    ("f9", 120),
    ("f10", 121),
    ("f11", 122),
    ("f12", 123),
    (";", 186),
    ("=", 187),
    (",", 188),
    (".", 190),
    ("`", 192),
    ("[", 219),
    ("\\", 220),
    ("]", 221),
])

def setHotkeyDefault(prefs, configName, keycode, enabled = True, ctrl = False, alt = False, shift = False):
    prefs.defaults[configName + '_hotkey_enabled'] = enabled
    prefs.defaults[configName + '_hotkey_ctrl'] = ctrl
    prefs.defaults[configName + '_hotkey_alt'] = alt
    prefs.defaults[configName + '_hotkey_shift'] = shift
    prefs.defaults[configName + '_hotkey_keycode'] = keycodes[keycode]


class HotkeyWidget(QWidget):
    def __init__(self, prefs, configName, title):
        QWidget.__init__(self)
        self.l = QVBoxLayout()
        self.setLayout(self.l)
        
        self.configName = configName
    
        self.hotkeyLayout = QHBoxLayout()
        self.l.addLayout(self.hotkeyLayout)
        
        enabledLabel = QLabel(title)
        self.hotkeyLayout.addWidget(enabledLabel)
        
        self.enabledBox = QCheckBox()
        self.hotkeyLayout.addWidget(self.enabledBox)
        self.enabledBox.setChecked(prefs[configName + '_hotkey_enabled'])
        
        hotkeyLayout2 = QHBoxLayout()
        self.l.addLayout(hotkeyLayout2)
        
        ctrlLabel = QLabel("Ctrl")
        self.ctrlBox = QCheckBox()
        self.ctrlBox.setChecked(prefs[configName + '_hotkey_ctrl'])
        
        ctrlLabel.setBuddy(self.ctrlBox)
        hotkeyLayout2.addWidget(ctrlLabel)
        hotkeyLayout2.addWidget(self.ctrlBox)
        
        altLabel = QLabel("Alt")
        self.altBox = QCheckBox()
        self.altBox.setChecked(prefs[configName + '_hotkey_alt'])
        
        altLabel.setBuddy(self.altBox)
        hotkeyLayout2.addWidget(altLabel)
        hotkeyLayout2.addWidget(self.altBox)
        
        shiftLabel = QLabel("Shift")
        self.shiftBox = QCheckBox()
        self.shiftBox.setChecked(prefs[configName + '_hotkey_shift'])
        
        shiftLabel.setBuddy(self.shiftBox)
        hotkeyLayout2.addWidget(shiftLabel)
        hotkeyLayout2.addWidget(self.shiftBox)
        
        self.keycodeBox = QComboBox()
        for key, value in keycodes.iteritems():
            self.keycodeBox.addItem(key, value)
            
        index = self.keycodeBox.findData(prefs[configName + '_hotkey_keycode'])
        if index != -1:
            self.keycodeBox.setCurrentIndex(index)
            
        hotkeyLayout2.addWidget(self.keycodeBox)
        
    def save_settings(self, prefs):
        prefs[self.configName + '_hotkey_enabled'] = self.enabledBox.isChecked()
        prefs[self.configName + '_hotkey_ctrl'] = self.ctrlBox.isChecked()
        prefs[self.configName + '_hotkey_alt'] = self.altBox.isChecked()
        prefs[self.configName + '_hotkey_shift'] = self.shiftBox.isChecked()
        prefs[self.configName + '_hotkey_keycode'] = keycodes[unicode(self.keycodeBox.currentText())]
        