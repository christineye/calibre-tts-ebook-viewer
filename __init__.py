#!/usr/bin/env python
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__copyright__ = '2016, github.com/christineye'
__docformat__ = 'restructuredtext en'

# The class that all Interface Action plugin wrappers must inherit from
from calibre.customize import InterfaceActionBase
from calibre.customize import ViewerPlugin

from PyQt5.Qt import QStandardItem, QStandardItemModel
import os
import json

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.Qt import (
        QApplication, QWidget, QIcon, QAction,
        QPushButton,
        QDockWidget, QVBoxLayout, pyqtSlot,
        QWebPage,
        )

        
import types
import re

from calibre_plugins.tts_ebook_viewer.tts_typelib import constants


class Responder(QtCore.QObject):
    @pyqtSlot(str)
    def readText(self, text):
        
        document = self.parent()
        ebookViewer = document.parent().manager
        ebookViewer.tts_speaker.readText(text)

    @pyqtSlot(result=bool)
    def loadNextPage(self):
        document = self.parent()
        ebookViewer = document.parent().manager
        return ebookViewer.tts_speaker.loadNextPage()
        
    @pyqtSlot()
    def playOrPause(self):
        document = self.parent()
        ebookViewer = document.parent().manager
        return ebookViewer.tts_speaker.playOrPause() 
        
    @pyqtSlot()
    def toggleSelectMode(self):
        document = self.parent()
        ebookViewer = document.parent().manager
        return ebookViewer.tts_speaker.toggleSelectMode()
        
    @pyqtSlot()
    def stop(self):
        document = self.parent()
        ebookViewer = document.parent().manager
        return ebookViewer.tts_speaker.stop()

class TTSSpeaker:
    
    def __init__(self, ui):
        self.isPlaying = False
        self.evaljs = None
        self.spVoice = None
        self.currentPosition = None
        self.ebookViewer = ui
        self.canResume = False
        self.selectMode = False
        self.toggleSelectModeButton = None
        
    def playOrPause(self):
        if not self.isPlaying:
            if self.canResume:
                self.isPlaying = True
                self.spVoice.Resume()
            else:
                self.initializeSpeech()
                self.readStartingAtPage()
        else:
            self.pause()
    
    def pause(self):
        if self.spVoice:
            self.isPlaying = False
            self.spVoice.Pause()
            self.canResume = True
    
    
    def toggleSelectMode(self):
        if not self.selectMode:
            self.stop()
            self.selectMode = True
            self.toggleSelectModeButton.setChecked(self.selectMode)

            self.evaljs('''
                $("p").addClass("tts_selectMode");
                $("p").click(function() 
                {
                    $(this).addClass("tts_reading")
                    tts_speaker.readText($(this).text())
                });
            ''')
            
        else:
            self.disableSelectMode()
            
            
    def disableSelectMode(self):
        self.selectMode = False
        self.toggleSelectModeButton.setChecked(self.selectMode)
        
        
        self.evaljs('''
            $('.tts_selectMode').removeClass("tts_selectMode");
            $("p").unbind('click')
        ''')
            
    def stop(self):
    
        
        self.canResume = False
        self.isPlaying = False
        if self.spVoice:
            self.spVoice.Pause()
            self.spVoice = None
            
            self.evaljs('''
            $currentReading = $(".tts_reading").removeClass("tts_reading")
            ''')
            
    def readText(self, text):
        import win32com.client
        
        self.initializeSpeech()
        
        self.spVoice.Speak(text, win32com.client.constants.SVSFlagsAsync)
        self.isPlaying = True
        self.disableSelectMode()
            
            
        
    def loadNextPage(self):
        if self.ebookViewer.current_index < len(self.ebookViewer.iterator.spine) - 1:
            print ("TTS: Loading next document")
            self.ebookViewer.next_document()
            return True
        
        else:
            print ("TTS: Could not load next page; stopping")
            self.isPlaying = False
            return False
        
    def initializeSpeech(self):

        if not self.spVoice:
            import win32com.client, weakref
            
            self.spVoice = win32com.client.Dispatch("SAPI.SpVoice")
            
            from calibre_plugins.tts_ebook_viewer.config import prefs
            
            if prefs['voice']:
                voice = None
                voices = self.spVoice.GetVoices("", "")
            
                for i in range(voices.Count):
                    if voices.Item(i).GetDescription() == prefs['voice']:
                        voice = voices.Item(i)
                        break
                        
                if voice:
                    self.spVoice.Voice = voice
                else:
                    prefs['voice'] = None
            
            self.spVoice.Rate = prefs['rate']
            self.spVoice.Volume = prefs['volume']
            
            
            self.spVoice.EventInterests = win32com.client.constants.SPEI_END_INPUT_STREAM
            self._advise = win32com.client.WithEvents(self.spVoice, SAPI5DriverEventSink)
            
            self._advise.setDriver(self)
        
    def readStartingAtPage(self):
        if self.evaljs:
            self.evaljs('''
 
            $currentReading = $(".tts_reading")
            if ($currentReading.length < 1)
            { 
                $currentReading = getFirstParagraphInView()
            }
            else
            {
                $currentReading = $currentReading[0]
            }
            
            tts_speaker.readText($currentReading.text());
            ''')
    
    
    def OnWord(self, stream, pos, char, length):
        pass

    def OnEndStream(self, stream, pos):
        self.canResume = False
        self.evaljs('''
            $currentReading = $(".tts_reading:first")
            $currentReading.removeClass("tts_reading")
            
            var nextVisible = $($currentReading.nextAll(":visible"))
            
            if (nextVisible.length > 0)
            {
                for (var j = 0; j< nextVisible.length; j++)
                {
                    var thisElement = $(nextVisible[j]);
                    if (isReadable(thisElement))
                    {
                        thisElement.addClass("tts_reading")
                        break;
                    }
                    else
                    {
                        var child = getNextReadableChild(thisElement);
                        if (child.length > 0)
                        {
                            $(child[0]).addClass("tts_reading");
                            break;
                        }
                    }
                }
            }
            else
            {
                // Look for a cousin element if no sibling
                
                $parents = $currentReading.parentsUntil("body")
                for (var i = 0; i < $parents.length; i++)
                {
                    if ($($parents[i]).next().length > 0)
                    {
                        var aunt = $($parents[i]).next();
                        
                        if (isReadable(aunt))
                        {
                            aunt.addClass("tts_reading")
                            break;
                        }
                        else
                        {
                            var readableChild = getNextReadableChild(aunt);
                            if (readableChild.length > 0)
                            {
                                $(readableChild[0]).addClass("tts_reading")
                                break;
                            }
                        }
                        break;
                    }
                }
                
                
            }

            $currentReading = $(".tts_reading:first")
            
            if ($currentReading.length > 0)
            {
                
                if (window.paged_display != null && window.paged_display.in_paged_mode)
                {

                    $currentReading.each(function(index, element)
                    {
                        var br = element.getBoundingClientRect()
                        var pos = calibre_utils.viewport_to_document(br.left, br.top, element.ownerDocument)
                        
                        window.paged_display.scroll_to_xpos(pos[0] + 10)
                    })
                    
                }
                else
                {
                    if (($currentReading.position().top + $currentReading.height() > $(window).scrollTop() + window.innerHeight ) ||
                        $currentReading.position().top < $(window).scrollTop())
                    {
                        $.scrollTo($currentReading)
                    }
                }
                
                
            }
            
            
        ''')
        
        if self.isPlaying:
            self.evaljs('''
            
            if ($currentReading.length > 0)
                {
                    tts_speaker.readText($currentReading.text());
                }
            else
            {
                // Couldn't find a next element, attempt to load next document
                
                tts_speaker.loadNextPage()
            }
            ''')
        else:
             self.evaljs('''
            if ($currentReading.length == 0)
            {
                // Couldn't find a next element, attempt to load next document
                
                tts_speaker.loadNextPage()
            }
            ''')
    
    
class SAPI5DriverEventSink(object):
    def __init__(self):
        self._driver = None

    def setDriver(self, driver):
        self._driver = driver

    def OnWord(self, stream, pos, char, length):
        #self._driver._proxy.notify('started-word', location=char, length=length)
        pass

    def OnEndStream(self, stream, pos):
        self._driver.OnEndStream(stream, pos)

class TextToSpeechPlugin(ViewerPlugin):
    '''

    '''
    name                = 'TTS Ebook Viewer'
    description         = 'adds TTS capability to ebook-viewer'
    supported_platforms = ['windows']
    author              = 'Christine Ye'
    version             = (0, 0, 2)
    minimum_calibre_version = (0, 7, 53)



    def customize_ui(self, ui):
        self.ebookViewer = ui
        
        self.tts_speaker = TTSSpeaker(ui)
        self.ebookViewer.tts_speaker = self.tts_speaker

        ui.tool_bar.addSeparator()

        
        self.speak_button = QAction('play / pause', ui)
        ui.tool_bar.addAction(self.speak_button)
        self.speak_button.triggered.connect(self.tts_speaker.playOrPause)
        self.tts_speaker.toolbarButton = self.speak_button
        
        self.select_mode_button = QAction('select mode', ui)
        ui.tool_bar.addAction(self.select_mode_button)
        self.select_mode_button.triggered.connect(self.tts_speaker.toggleSelectMode)
        self.select_mode_button.setCheckable(True)
        self.select_mode_button.setChecked(False)
        self.tts_speaker.toggleSelectModeButton = self.select_mode_button
        
        self.stop_button = QAction('stop', ui)
        ui.tool_bar.addAction(self.stop_button)
        self.stop_button.triggered.connect(self.tts_speaker.stop)
        
  
        # HACK?
        # append a callback to the javaScriptWindowObjectCleared
        # signal receiver. If you don't do this, the `py_annotator`
        # object will be empty (has no python functions callable)
        # from js
        ui.view.document.mainFrame().javaScriptWindowObjectCleared.connect(
                self.add_window_objects)

 
        
        # print ("finished customizing ")

    def add_window_objects(self):
        self.ebookViewer.view.document.mainFrame().addToJavaScriptWindowObject('tts_speaker', Responder(self.ebookViewer.view.document))

    # this function is by far the slowest, and is what causes pauses in the render
    def run_javascript(self, evaljs):
        '''
        this gets called after load_javascript.
        '''
        # inject css

        evaljs('''
            $("<style>.tts_reading {  background-color: yellow !important;} p.tts_selectMode:hover {  background-color: #e7eaa4;  }   </style>").appendTo(document.head)
        ''')

        self.evaljs = evaljs
        self.tts_speaker.evaljs = evaljs
        
        def jsbool(pyBool):
            return unicode(pyBool).lower()
        
        
        from calibre_plugins.tts_ebook_viewer.config import prefs
        if prefs['pause_hotkey_enabled'] or prefs['stop_hotkey_enabled'] or prefs['select_hotkey_enabled']:
            hotkeyjs = '''
                $(document).keydown(function(event)
                {
                    if (%s &&
                        event.ctrlKey == %s &&
                        event.altKey == %s &&
                        event.shiftKey == %s &&
                        event.which == %i)
                    {
                        tts_speaker.playOrPause()
                    }
                    else if (%s &&
                        event.ctrlKey == %s &&
                        event.altKey == %s &&
                        event.shiftKey == %s &&
                        event.which == %i)
                    {
                        tts_speaker.stop()
                    }
                    else if (%s &&
                        event.ctrlKey == %s &&
                        event.altKey == %s &&
                        event.shiftKey == %s &&
                        event.which == %i)
                    {
                        tts_speaker.toggleSelectMode()
                    }
                })
            ''';
            
            hotkeyArgs = []
            for hotkey in ['pause', 'stop', 'select']:
                hotkeyArgs.append(jsbool(prefs[hotkey + '_hotkey_enabled']))
                hotkeyArgs.append(jsbool(prefs[hotkey + '_hotkey_ctrl']))
                hotkeyArgs.append(jsbool(prefs[hotkey + '_hotkey_alt']))
                hotkeyArgs.append(jsbool(prefs[hotkey + '_hotkey_shift']))
                hotkeyArgs.append(prefs[hotkey + '_hotkey_keycode'] )
            
            self.evaljs(hotkeyjs % tuple(hotkeyArgs))
        
        if self.tts_speaker.isPlaying:
            print ("TTS: Start reading automatically")
            evaljs('''
                $currentReading = getFirstParagraphInView().addClass("tts_reading")
                tts_speaker.readText($currentReading.text());
            ''')

    def load_javascript(self, evaljs):
        '''
        from calibre docs:
        This method is called every time a new HTML document is
        loaded in the viewer. Use it to load javascript libraries
        into the viewer.
        '''
        evaljs('''
        
        
        function isReadable(node)
        {
            var hasText = false;
            node
                  .contents()
                    .each(function() {
                        var $this = $(this);
                      if (this.nodeType == 3)
                      {
                          if ($this.text().trim().length > 0)
                          {
                            hasText = true;
                            return false;
                          }
                      }
                });
                
            return hasText;
        }
        
        function getNextReadableChild(body)
        {
        	var readable = null;
            // Find all children that have at least 1 text node child with real text
            return body.find(":visible").each(function()
            {
                if (isReadable($(this)))
                {
                	readable = $(this);
                  return false;
                }
            })
            
            return readable;
        }
        
        function getAllReadableChildren(body)
        {
            // Find all children that have at least 1 text node child with real text
            return body.find(":visible").filter(function()
            {
                return isReadable($(this));
            })
        }
        
        function getFirstParagraphInView()
        {
            $p = getAllReadableChildren($("body"))
                        
            if (window.paged_display != null && window.paged_display.in_paged_mode)
            {
                var columnLeft = window.paged_display.current_column_location()
                
                $p.each(function(index, element)
                {
                    var br = element.getBoundingClientRect()
                    var pos = calibre_utils.viewport_to_document(br.left, br.top, element.ownerDocument)
                    
                    if (pos[0] >= columnLeft && pos[0] < columnLeft +  window.paged_display.page_width)
                    {
                        $currentReading = $(element);
                        $currentReading.addClass("tts_reading")

                        return false;
                    }
                })
            }
            else
            {
                var $window = $(window);

                var docViewTop = $window.scrollTop();
                var docViewBottom = docViewTop + $window.height();


                $p.each(function(index, element)
                {
                    $elem = $(element)
                    
                    var elemTop = $elem.offset().top;
                    var elemBottom = elemTop + $elem.height();

                    if ((elemTop <= docViewBottom) && (elemTop >= docViewTop))
                    {
                        $currentReading = $elem;
                        $currentReading.addClass("tts_reading")
                        
                        
                        return false;
                    }
                })
            }
            
            return $currentReading
        }
        ''')
         


    def is_customizable(self):
        '''
        This method must return True to enable customization via
        Preferences->Plugins
        '''
        return True

    def config_widget(self):
        '''
        Implement this method and :meth:`save_settings` in your plugin to
        use a custom configuration dialog.

        This method, if implemented, must return a QWidget. The widget can have
        an optional method validate() that takes no arguments and is called
        immediately after the user clicks OK. Changes are applied if and only
        if the method returns True.

        If for some reason you cannot perform the configuration at this time,
        return a tuple of two strings (message, details), these will be
        displayed as a warning dialog to the user and the process will be
        aborted.

        The base class implementation of this method raises NotImplementedError
        so by default no user configuration is possible.
        '''
        # It is important to put this import statement here rather than at the
        # top of the module as importing the config class will also cause the
        # GUI libraries to be loaded, which we do not want when using calibre
        # from the command line
        from calibre_plugins.tts_ebook_viewer.config import ConfigWidget
        # print('config config')
        return ConfigWidget()

    def save_settings(self, config_widget):
        '''
        Save the settings specified by the user with config_widget.

        :param config_widget: The widget returned by :meth:`config_widget`.
        '''
        config_widget.save_settings()
