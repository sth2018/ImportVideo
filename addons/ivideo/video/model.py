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
import os
from ..utils.misc import *
from ..config import CONFIG


__all__ = ['Model', 'FLD_NAMES']

FLD_NAMES = ['FLD_TIMESTAMP', 'FLD_IMAGE', 'FLD_VIDEO', 'FLD_SOUND', 'FLD_SUB01', 'FLD_SUB02']

class Model(object):

    def __init__(self):
        
        self.video_file = ""
        self.audio_id = 0
        self.deck_name = ""
        
        self.en_srt = ""
        self.cn_srt = ""

        self.encodings = ["utf-8", "gb2312", "gbk", "cp1251"]
        self.sub_encoding = None

        self.input_directory = ""
        
        self.proc = None
        self.model = None
        self.deck = None
        self.en_subs = []
        self.cn_subs = []
        self.is_subtitles_created = False

    def convert_to_unicode(self, file_content):
        for enc in self.encodings:
            try:
                content = file_content.decode(enc)
                self.sub_encoding = enc
                return content
            
            except UnicodeDecodeError:
                pass

        self.sub_encoding = None
        return file_content

    def load_subtitle(self, filename, is_ignore_SDH):
        if len(filename) == 0:
            return []

        file_content = open(filename, 'rU').read()
        if file_content[:3]=='\xef\xbb\xbf': # with bom
            file_content = file_content[3:]

        file_content = fix_empty_lines(file_content)
        file_content = self.convert_to_unicode(file_content)
        return read_subtitles(file_content, is_ignore_SDH)

    def create_subtitles(self):
        self.is_subtitles_created = False
        # [(start_time, end_time, subtitle), (...), ...]
        self.en_subs = self.load_subtitle(self.en_srt, CONFIG.is_ignore_sdh_subtitle)
        # [(start_time, end_time, subtitle), (...), ...]
        self.cn_subs = self.load_subtitle(self.cn_srt, CONFIG.is_ignore_sdh_subtitle)
        # sync
        self.cn_subs = sync_subtitles(self.en_subs, self.cn_subs)
        # movie
        if CONFIG.mode == "Movie":
            change_subtitles_ending_time(self.en_subs, None, CONFIG.is_separate_fragments_without_subtitles, CONFIG.time_delta)
            change_subtitles_ending_time(self.cn_subs, None, CONFIG.is_separate_fragments_without_subtitles, CONFIG.time_delta)
        # status
        self.is_subtitles_created = True

    @property
    def num_en_subs(self):
        return len(self.en_subs)
    
    @property
    def num_cn_subs(self):
        return len(self.cn_subs)
