#-*- coding:utf-8 -*-
#
# Copyright (C) 2018 sthoo <sth201807@gmail.com>
#
# Support: Report an issue at https://github.com/sth2018/ImportVideo/issues
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version; http://www.gnu.org/copyleft/gpl.html.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import json
import glob
import os
import re
import shutil
import string
import sys
import time

from collections import deque
from subprocess import call
from subprocess import check_output
from subprocess import Popen

import subprocess
import os.path

import anki
import aqt
import aqt.models
from aqt import mw
from aqt.qt import *
from aqt.studydeck import StudyDeck
from anki.hooks import addHook, remHook, runHook

from .base import Dialog
from .common import *
from ..video import Model, VideoWorker, FLD_NAMES
from ..utils.misc import *
from ..config import CONFIG
from ..lang import _


__all__ = ['Importor']


# Use `bytes` for byte strings and `unicode` for unicode strings (str in Py3).
if sys.version_info[0] <= 2:
    try:
        bytes
    except NameError:
        bytes = str
elif sys.version_info[0] >= 3:
    unicode = str


class Importor(Dialog):
    
    def __init__(self, parent, title=u'Import'):
        super(Importor, self).__init__(parent, title)
        self.model = Model()
        self.model.model = get_model_byId(mw.col.models, CONFIG.mid)
        self.worker = None
        self.audio_streams = []
        self._options = list()
        self.initUI()
        
    def initUI(self):
        vbox = QVBoxLayout()
        # UI
        vbox.addWidget(self.createFilesGroup())
        vbox.addWidget(self.createOutputGroup())
        vbox.addLayout(self.createOptionsGroup())
        vbox.addLayout(self.createBottomGroup())
        # events
        self.videoButton.clicked.connect(self.showVideoFileDialog)
        self.audioIdComboBox.currentIndexChanged.connect(self.setAudioId)
        self.subsEngButton.clicked.connect(self.showSubsEnFileDialog)
        self.subsRusButton.clicked.connect(self.showSubsCnFileDialog)
        self.deckComboBox.editTextChanged.connect(self.setDeckName)
        self.previewButton.clicked.connect(self.preview)
        self.startButton.clicked.connect(self.start)
        self.aboutButton.clicked.connect(self.about)
        # changes
        self.widthSpinBox.valueChanged.connect(self.setVideoWidth)
        self.heightSpinBox.valueChanged.connect(self.setVideoHeight)
        self.videoEdit.textChanged.connect(self.changeVideoFile)
        self.subsEngEdit.textChanged.connect(self.changeEnSubs)
        self.subsRusEdit.textChanged.connect(self.changeCnSubs)
        # hooks
        addHook('currentModelChanged', self.onModelChange)
        self.onModelChange()
        # size
        vbox.addStretch(1)
        self.setLayout(vbox)
        self.resize(640, 10)

    def closeEvent(self, event):
        # save settings
        CONFIG.save()
        remHook('currentModelChanged', self.onModelChange)
        self.modelChooser.cleanup()
        self.deckChooser.cleanup()
        self.cancelProgressDialog()
        super(Importor, self).closeEvent(event)

    def showVideoFileDialog(self):
        #fname = unicode(QFileDialog.getOpenFileName(directory = CONFIG.directory, filter = "Video Files (*.avi *.mkv *.mp4 *.ts);;All files (*.*)"))
        ret = QFileDialog.getOpenFileName(
            self,
            caption = u"Select Video File", 
            directory = CONFIG.directory,
            filter = "Video Files (*.avi *.mkv *.mp4 *.ts);;All files (*.*)"
        )
        if ret:
            fname = unicode(ret[0])
            self.videoEdit.setText(os.path.realpath(fname))
            CONFIG.directory = os.path.dirname(fname)

    def showSubsEnFileDialog(self):
        ret = QFileDialog.getOpenFileName(
            self,
            caption = u"Select Subtitles", 
            directory = CONFIG.directory, 
            filter = "Subtitle Files (*.srt)"
        )
        if ret:
            fname = unicode(ret[0])
            self.subsEngEdit.setText(os.path.realpath(fname))
            CONFIG.directory = os.path.dirname(fname)

    def showSubsCnFileDialog(self):
        ret = QFileDialog.getOpenFileName(
            self,
            caption = u"Select Subtitles", 
            directory = CONFIG.directory, 
            filter = "Subtitle Files (*.srt)"
        )
        if ret:
            fname = unicode(ret[0])
            self.subsRusEdit.setText(os.path.realpath(fname))
            CONFIG.directory = os.path.dirname(fname)
    
    def onModelChange(self):
        self.model.model = mw.col.models.current()
        CONFIG.mid = self.model.model['id']
        self.buildOutputFldsLayout()

    def showErrorDialog(self, message):
        QMessageBox.critical(self, self._title, message)

    def showDirAlreadyExistsDialog(self, dir):
        reply = QMessageBox.question(
            self, 
            self._title,
            "Folder '" + dir + "' already exists. Do you want to overwrite it?", 
            QMessageBox.Yes|QMessageBox.No, 
            QMessageBox.No
        )
        return reply == QMessageBox.Yes
        
    def tryToSetEngAudio(self):
        eng_id = len(self.audio_streams) - 1
        for cur_id in range(len(self.audio_streams)):
            if self.audio_streams[cur_id].find("[eng]") != -1:
                eng_id = cur_id
                break
        self.audioIdComboBox.setCurrentIndex(eng_id)

    def setAudioId(self):
        self.model.audio_id = self.audioIdComboBox.currentIndex()

    def getAudioStreams(self, video_file):
        self.audio_streams = []
        if not os.path.isfile(video_file):
            print("Video file not found")
            return

        try:
            output = check_output([
                "ffprobe", 
                "-v", 
                "quiet", 
                "-print_format", "json", 
                "-show_format", 
                "-show_streams", 
                "-select_streams", 
                "a", 
                video_file], 
                **subprocess_args(False)
            )
        except OSError as ex:
            self.model.audio_id = 0
            print("Can't find ffprobe", ex)
            return

        json_data = json.loads(output)
        streams = json_data["streams"]

        for idx,audio in enumerate(streams):
            title = ""
            language = "???"
            if "tags" in audio:
                tags = audio["tags"]
                if "language" in tags:
                    language = tags["language"]
            if len(title) != 0:
                stream = "%i: %s [%s]" % (idx, title, language)
            else:
                stream = "%i: [%s]" % (idx, language)
            self.audio_streams.append(stream)

    def changeAudioStreams(self):
        self.audioIdComboBox.clear()
        self.getAudioStreams(self.model.video_file)
        self.audioIdComboBox.addItems(self.audio_streams)
        self.tryToSetEngAudio()

    def changeSubtitles(self):
        self.model.en_srt = guess_srt_file(self.model.video_file, ["*eng*.srt", "*en*.srt", ".srt"], "")
        self.subsEngEdit.setText(self.model.en_srt)
        self.model.cn_srt = guess_srt_file(self.model.video_file, ["*cns*.srt", "*cn*.srt"], "")
        self.subsRusEdit.setText(self.model.cn_srt)

    def changeVideoFile(self):
        self.model.video_file = unicode(self.videoEdit.text()).strip()
        self.model.input_directory = os.path.dirname(self.model.video_file)
        CONFIG.directory = self.model.input_directory

        if not os.path.isfile(self.model.video_file):
            return

        self.changeAudioStreams()
        self.changeSubtitles()

    def changeEnSubs(self):
        self.model.en_srt = unicode(self.subsEngEdit.text()).strip()

    def changeCnSubs(self):
        self.model.cn_srt = unicode(self.subsRusEdit.text()).strip()

    def setVideoWidth(self):
        CONFIG.update({'video_width': self.widthSpinBox.value()})

    def setVideoHeight(self):
        CONFIG.update({'video_height': self.heightSpinBox.value()})

    def setDeckName(self):
        self.model.deck_name = unicode(self.deckComboBox.currentText()).strip()
    
    def about(self):
        from .common import show_about_dialog
        show_about_dialog(self)

    def validateSubtitles(self):
        if len(self.model.en_srt) == 0:
            self.showErrorDialog("Add Subtitles 01.")
            return False

        if not os.path.isfile(self.model.en_srt):
            print("Subtitles 01 didn't exist.")
            return False

        if len(self.model.cn_srt) != 0:
            if not os.path.isfile(self.model.cn_srt):
                print("Subtitles 02 didn't exist.")
                return False

        return True

    def preview(self):
        # save settings
        CONFIG.save()
        if not self.validateSubtitles():
            return

        # subtitles
        self.model.create_subtitles()

        if not self.model.is_subtitles_created:
            self.showErrorDialog("Check log.txt")
            return

        # show info dialog
        message = u"Subtitles 01: %s\nSubtitles 02: %s" % (self.model.num_en_subs, self.model.num_cn_subs)
        QMessageBox.information(self, "Preview", message)

        self.changeEnSubs()
        self.changeCnSubs()

    def start(self):
        self.model.jobs = []
        self.model.ffmpeg_split_timestamps = []
        self.startSingleMode()

    def startSingleMode(self):
        self.model.batch_mode = False

        if not self.validateSubtitles():
            return

        # subtitles
        self.model.create_subtitles()

        if not self.model.is_subtitles_created:
            self.showErrorDialog("Check log.txt")
            return

        # tsv file
        if len(self.model.deck_name) == 0:
            self.showErrorDialog("Deck's name can't be empty.")
            return

        self.updateDeckComboBox()

        # save settings
        CONFIG.save()

        # check
        if len(self.model.video_file) == 0:
            self.showErrorDialog("Video file name can't be empty.")
            return

        if not os.path.isfile(self.model.video_file):
            self.showErrorDialog("Video file didn't exist.")
            return

        try:
            call(["ffmpeg", "-version"], **subprocess_args())
        except OSError as ex: 
            print("Can't find ffmpeg", ex)
            self.showErrorDialog("Can't find ffmpeg.")
            return
        
        # video & audio files
        self.convertVideo()

    def setProgress(self, progress):
        self.progressDialog.setValue(progress)

    def setProgressText(self, text):
        self.progressDialog.setLabelText(text)

    def finishNote(self, flds):
        '''
        ss = flds[len(flds)-1]
        notes = [id for id, in mw.col.db.execute("select id from notes where mid = ?", self.model.model['id'])]
        for id in notes:
            n = anki.notes.Note(mw.col, id=id)
            if (n.fields[0] == self.model.deck_name) and (ss in n.fields[1]):
                note = n
                break
            if n.fields[1] == flds[0]:
                note = n
                break
        '''
        note = None
        isnew = False
        if note is None:
            note = anki.notes.Note(mw.col, self.model.model)
            isnew = True
        note.model()['did'] = self.deckChooser.selectedId()
        for i,m in enumerate(CONFIG.flds_map):
            if not m['ignore'] and i < len(note.fields):
                note.fields[i] = flds[m['new_fld_ord']]
        note.tags = mw.col.tags.canonify(
            mw.col.tags.split(self.model.deck_name)
        )
        if isnew:
            mw.col.addNote(note)
            mw.col.autosave()
        else:
            note.flush()

    def finishProgressDialog(self, time_diff):
        self.progressDialog.done(0)
        minutes = int(time_diff / 60)
        seconds = int(time_diff % 60)
        message = "Processing completed in %s minutes %s seconds." % (minutes, seconds)
        QMessageBox.information(self, self._title, message)
        self.worker = None
        self.model.proc = None

    def updateDeckComboBox(self):
        text = unicode(self.deckComboBox.currentText()).strip()
        if self.deckComboBox.findText(text) == -1:
            self.deckComboBox.addItem(text)
            CONFIG.recent_deck_names.append(text)
        else:
            CONFIG.recent_deck_names.remove(text)
            CONFIG.recent_deck_names.append(text)

        self.deckComboBox.clear()
        self.deckComboBox.addItems(CONFIG.recent_deck_names)
        self.deckComboBox.setCurrentIndex(self.deckComboBox.count()-1)

    def cancelProgressDialog(self):
        if self.worker != None:
            self.worker.cancel()
        if self.model.proc != None:
            self.model.proc.terminate()
            time.sleep(1)
        self.worker = None
        self.model.proc = None

    def displayErrorMessage(self, message):
        self.showErrorDialog(message)

    def convertVideo(self):
        self.progressDialog = QProgressDialog(self)

        self.progressDialog.setWindowTitle("Generate Video & Audio Clips")
        self.progressDialog.setCancelButtonText("Cancel")
        self.progressDialog.setMinimumDuration(0)

        progress_bar = QProgressBar(self.progressDialog)
        progress_bar.setAlignment(Qt.AlignCenter)
        self.progressDialog.setBar(progress_bar)

        self.worker = VideoWorker(self.model)
        self.worker.updateProgress.connect(self.setProgress)
        self.worker.updateProgressText.connect(self.setProgressText)
        self.worker.noteFinished.connect(self.finishNote)
        self.worker.jobFinished.connect(self.finishProgressDialog)
        self.worker.errorRaised.connect(self.displayErrorMessage)

        self.progressDialog.canceled.connect(self.cancelProgressDialog)
        self.progressDialog.setFixedSize(400, self.progressDialog.height()+ 15)
        self.progressDialog.setModal(True)

        self.worker.start()
        
    def createFilesGroup(self):
        groupBox = QGroupBox("Files:")

        vbox = QVBoxLayout()

        self.videoButton = QPushButton(_('VIDEO'))
        self.videoEdit = QLineEdit()
        self.audioIdComboBox = QComboBox()

        hbox = QHBoxLayout()
        hbox.addWidget(self.videoButton)
        hbox.addWidget(self.videoEdit)
        hbox.addWidget(self.audioIdComboBox)

        vbox.addLayout(hbox)

        self.subsEngButton = QPushButton(_('SUB01'))
        self.subsEngEdit = QLineEdit()

        hbox = QHBoxLayout()
        hbox.addWidget(self.subsEngButton)
        hbox.addWidget(self.subsEngEdit)

        vbox.addLayout(hbox)

        self.subsRusButton = QPushButton(_('SUB02'))
        self.subsRusEdit = QLineEdit()

        hbox = QHBoxLayout()
        hbox.addWidget(self.subsRusButton)
        hbox.addWidget(self.subsRusEdit)

        vbox.addLayout(hbox)

        groupBox.setLayout(vbox)

        return groupBox

    def createVideoDimensionsGroup(self):
        groupBox = QGroupBox("Video Dimensions:")

        layout = QFormLayout()

        self.widthSpinBox = QSpinBox()
        self.widthSpinBox.setRange(-2, 2048)
        self.widthSpinBox.setSingleStep(2)
        self.widthSpinBox.setValue(CONFIG.video_width)

        hbox = QHBoxLayout()
        hbox.addWidget(self.widthSpinBox)
        hbox.addWidget(QLabel("px"))

        layout.addRow(QLabel("Width:"), hbox)

        self.heightSpinBox = QSpinBox()
        self.heightSpinBox.setRange(-2, 2048)
        self.heightSpinBox.setSingleStep(2)
        self.heightSpinBox.setValue(CONFIG.video_height)

        hbox = QHBoxLayout()
        hbox.addWidget(self.heightSpinBox)
        hbox.addWidget(QLabel("px"))

        layout.addRow(QLabel("Height:"), hbox)

        groupBox.setLayout(layout)

        return groupBox

    def createOptionsGroup(self):
        groupBox = QGroupBox("Options:")

        hbox = QHBoxLayout()
        hbox.addWidget(self.createVideoDimensionsGroup())
        groupBox.setLayout(hbox)
        groupBox.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred
        )

        hbox = QHBoxLayout()
        hbox.addWidget(groupBox)
        
        return hbox

    def createBottomGroup(self):
        groupBox = QGroupBox("Name for deck:")

        self.deckComboBox = QComboBox()
        self.deckComboBox.setEditable(True)
        self.deckComboBox.setMaxCount(5)
        self.deckComboBox.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )
        self.deckComboBox.addItems(CONFIG.recent_deck_names)
        self.deckComboBox.clearEditText()
        self.deckComboBox.setInsertPolicy(QComboBox.NoInsert)
        
        hbox = QHBoxLayout()
        hbox.addWidget(self.deckComboBox)
        groupBox.setLayout(hbox)

        hbox = QHBoxLayout()
        hbox.addWidget(groupBox)

        vbox = QVBoxLayout()
        self.aboutButton = QPushButton(_('ABOUT'))
        self.previewButton = QPushButton("Preview...")
        self.startButton = QPushButton("Go!")
        vbox.addWidget(self.aboutButton)
        vbox.addWidget(self.previewButton)
        vbox.addWidget(self.startButton)
        hbox.addLayout(vbox)

        return hbox

    def createOutputGroup(self):
        groupBox = QGroupBox("Output:")
        vbox = QVBoxLayout()
        # chooser
        modes = QWidget()
        decks = QWidget()
        hbox = QHBoxLayout()
        self.modelChooser = aqt.modelchooser.ModelChooser(mw, modes)
        self.deckChooser = aqt.deckchooser.DeckChooser(mw, decks)
        hbox.addWidget(modes)
        hbox.addWidget(decks)
        vbox.addLayout(hbox)
        # fields mapping
        self.fldsLayout = QGridLayout()
        vbox.addLayout(self.fldsLayout)

        groupBox.setLayout(vbox)
        return groupBox

    def buildOutputFldsLayout(self):
        model = self.model.model
        if model is None:
            return
        # clear layout
        clear_layout(self.fldsLayout)
        del self._options[:]
        # labels
        f = QFont()
        f.setBold(True)
        labels = [u'＃', '', 'FIELDS']
        for i, s in enumerate(labels):
            if s:
                label = QLabel(_(s))
                label.setFont(f)
                label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
                self.fldsLayout.addWidget(label, 0, i)

        # ignore all
        self.ignoreAllCheckBtn = QCheckBox(_('SELECT_ALL'))
        self.ignoreAllCheckBtn.setFont(f)
        self.ignoreAllCheckBtn.setEnabled(True)
        self.ignoreAllCheckBtn.setChecked(True)
        self.fldsLayout.addWidget(self.ignoreAllCheckBtn, 0, 1)
        self.ignoreAllCheckBtn.clicked.connect(self.ignoreAllCheckBtnChanged)

        # fields
        flds_map = CONFIG.flds_map
        for i in range(len(flds_map), len(model['flds'])):
            flds_map.append({
                'ignore': True,
                'new_fld_ord': 0,
            })
        for i, fld in enumerate(model['flds']):
            ord = fld['ord']
            name = fld['name']
            m = flds_map[i]
            self.addFieldLayout(i, fld_name=name, fld_ord=ord, **m)
        
        # update
        self.ignoreAllUpdate()
        CONFIG.flds_map = flds_map

    def addFieldLayout(self, idx, **kwargs):
        """
        add dictionary fields row
        """
        
        fld_name, fld_ord, ignore, new_fld_ord = (
            kwargs.get('fld_name', ''),                                 #笔记类型的字段名
            kwargs.get('fld_ord', ''),                                  #笔记类型的字段编号
            kwargs.get('ignore', True),                                 #忽略标志
            kwargs.get('new_fld_ord', 0),                               #笔记类型的字段编号
        )

        # field label
        fld_label = QLabel(fld_name)
        fld_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        # ignore
        ignore_check_btn = QCheckBox(_("IGNORE"))
        ignore_check_btn.setMinimumSize(60, 0)
        ignore_check_btn.setMaximumSize(60, 25)
        ignore_check_btn.setEnabled(True)
        ignore_check_btn.setChecked(ignore)

        # field combox
        fld_combo = QComboBox()
        fld_combo.setCurrentIndex(0)
        for i, n in enumerate(FLD_NAMES):
            fld_combo.addItem(_(n), userData=i)
            if i == new_fld_ord:
                fld_combo.setCurrentIndex(i)
        fld_combo.setEnabled(not ignore)

        # events
        # ignor
        def ignore_check_changed():
            ignore = ignore_check_btn.isChecked()
            fld_combo.setEnabled(not ignore)
            CONFIG.flds_map[idx]['ignore'] = ignore
        ignore_check_btn.stateChanged.connect(ignore_check_changed)
        ignore_check_btn.clicked.connect(self.ignoreAllUpdate)
        # fld_combo
        def fld_index_changed():
            CONFIG.flds_map[idx]['new_fld_ord'] = fld_combo.currentIndex()
        fld_combo.currentIndexChanged.connect(fld_index_changed)
        # widgets
        self.fldsLayout.addWidget(fld_label, idx + 1, 0)
        self.fldsLayout.addWidget(ignore_check_btn, idx + 1, 1)
        self.fldsLayout.addWidget(fld_combo, idx + 1, 2)
        # list
        self._options.append({
            'model': {'fld_name': fld_name, 'fld_ord': fld_ord},
            'ignore_check_btn': ignore_check_btn, 
            'field_combo': fld_combo, 
        })

    def ignoreAllCheckBtnChanged(self):
        b = self.ignoreAllCheckBtn.isChecked()
        for row in self._options:
            row['ignore_check_btn'].setChecked(b)

    def ignoreAllUpdate(self):
        b = True
        for row in self._options:
            if not row['ignore_check_btn'].isChecked():
                b = False
                break
        self.ignoreAllCheckBtn.setChecked(b)
