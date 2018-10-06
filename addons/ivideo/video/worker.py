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


import os
import sys
import time

from subprocess import Popen
from aqt.qt import *
from ..utils.misc import *
from ..config import CONFIG


__all__ = ['VideoWorker']


class VideoWorker(QThread):

    updateProgress = pyqtSignal(int)
    updateProgressText = pyqtSignal(str)
    noteFinished = pyqtSignal(list)
    jobFinished = pyqtSignal(float)
    errorRaised = pyqtSignal(str)

    def __init__(self, model):
        super(VideoWorker, self).__init__()
        self.model = model
        self.canceled = False

    def cancel(self):
      self.canceled = True

    def run(self):
        video_resolution = str(CONFIG.video_width) + ":" + str(CONFIG.video_height)
        time_start = time.time()

        num_files_completed = 0       
        num_files = len(self.model.en_subs)
        
        for i,en_sub in enumerate(self.model.en_subs):
            if self.canceled:
                break
            
            chunk = get_ffmpeg_split_timestamps(self.model.deck_name, en_sub)
            filename = chunk[0]
            ss = chunk[1]
            to = chunk[2]
            t = tsv_time_to_seconds(to) - tsv_time_to_seconds(ss)

            en_str = en_sub[2]
            cn_str = self.model.cn_subs[i][2]

            af_d = 0.25
            af_st = 0
            af_to = t - af_d
            af_params = "afade=t=in:st=%s:d=%s,afade=t=out:st=%s:d=%s" % (af_st, af_d, af_to, af_d)

            # progress
            self.updateProgress.emit((num_files_completed * 1.0 / num_files) * 100)
            self.updateProgressText.emit('[{0}]<br>{1}'.format(ss, en_str))

            # mp4
            vf = '"'
            vf += "scale=" + video_resolution
            vf += '"'
            softsubs_options = ""
            softsubs_map = ""
            mp4 = filename + ".mp4"
            rmfile(mp4)
            if not os.path.exists(mp4):
                cmd = " ".join([
                    "ffmpeg", 
                    "-ss", ss, 
                    "-i", '"' + self.model.video_file + '"', softsubs_options, 
                    "-strict", "-2", 
                    "-loglevel", "quiet", 
                    "-t", str(t), 
                    "-af", af_params, 
                    "-map", "0:v:0", 
                    "-map", "0:a:" + str(self.model.audio_id), softsubs_map, 
                    "-c:v", "libx264", 
                    "-vf", vf, 
                    "-c:a", "aac", 
                    "-ac", "2", 
                    '"' + mp4 + '"'
                ])
                self.model.proc = Popen(cmd.encode(sys.getfilesystemencoding()), shell=True, **subprocess_args())
                self.model.proc.wait()

            if self.canceled:
                break
            
            # jpg
            jpg = filename + ".jpg"
            rmfile(jpg)
            if not os.path.exists(jpg):
                cmd = " ".join([
                    "ffmpeg", 
                    "-ss", ss, 
                    "-i", '"' + self.model.video_file + '"',  
                    "-loglevel", "quiet", 
                    "-r 1 -vframes 1 -an -vcodec mjpeg",
                    '"' + jpg + '"'
                ])
                self.model.proc = Popen(cmd.encode(sys.getfilesystemencoding()), shell=True, **subprocess_args())
                self.model.proc.wait()

            if self.canceled:
                break

            # mp3
            mp3 = filename + ".mp3"
            rmfile(mp3)
            if not os.path.exists(mp3):
                cmd = " ".join([
                    "ffmpeg", "-ss", ss, 
                    "-i", '"' + self.model.video_file + '"', 
                    "-loglevel", "quiet", 
                    "-t", str(t), 
                    "-af", af_params, 
                    "-map", "0:a:" + str(self.model.audio_id), 
                    '"' + mp3 + '"'
                ])
                self.model.proc = Popen(cmd.encode(sys.getfilesystemencoding()), shell=True, **subprocess_args())
                self.model.proc.wait()

            # note
            self.noteFinished.emit([
                chunk[0],
                '<img src="%s.jpg" />' % (chunk[0]),
                '[sound:%s.mp4]' % (chunk[0]),
                '[sound:%s.mp3]' % (chunk[0]),
                en_str, 
                cn_str
            ])
            
            # counter
            num_files_completed += 1

        time_end = time.time()
        time_diff = (time_end - time_start)
 
        if not self.canceled:
            self.updateProgress.emit(100)
            self.jobFinished.emit(time_diff)
