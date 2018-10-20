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
from collections import deque
from .constants import VERSION


__all__ = ['CONFIG']


class Config(object):

    _CONFIG_FILENAME = u'_ivideo_config.json'

    def __init__(self):
        self.data = None
        self.read()

    def read(self):
        """ Load from config file """
        if self.data:
            return self.data
        try:
            path = self._CONFIG_FILENAME
            with open(path, 'rb') as f:
                self.data = json.load(f)
                f.close()
            if not os.path.exists(path):
                self.update(self.data)
        except:
            self.data = dict()
        return self.data

    def update(self, data):
        """ Update && Save """
        path = self._CONFIG_FILENAME
        data['version'] = VERSION
        data['last_model_id'] = data.get('last_model', self.mid)
        values = self.data.get('recent_deck_names', list())
        if isinstance(values, deque):
            self.data['recent_deck_names'] = list(values)
        self.data.update(data)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, sort_keys=True, ensure_ascii=False)
            f.close()

    def save(self):
        """ Save """
        self.update(self.data)

    @property
    def time_delta(self):
        return self.data.get('time_delta', 1.75)

    @property
    def video_width(self):
        return self.data.get('video_width', 320)

    @property
    def video_height(self):
        return self.data.get('video_height', -2)

    @property
    def mode(self):
        return self.data.get('mode', 'movie')

    @property
    def is_ignore_sdh_subtitle(self):
        return self.data.get('is_ignore_sdh_subtitle', True)
    
    @property
    def is_separate_fragments_without_subtitles(self):
        return self.data.get('is_separate_fragments_without_subtitles', False)

    @property
    def mid(self):
        return self.data.get('last_model_id', 0)

    @mid.setter
    def mid(self, value):
        self.data['last_model_id'] = value

    @property
    def recent_deck_names(self):
        values = self.data.get('recent_deck_names', list())
        if isinstance(values, list):
            names = deque(maxlen = 5)
            names.extendleft(values)
            self.data['recent_deck_names'] = names
        return self.data['recent_deck_names']

    @property
    def directory(self):
        return self.data.get('last_directory', '')
    
    @directory.setter
    def directory(self, value):
        self.data['last_directory'] = value

    @property
    def flds_map(self):
        return self.data.get('flds_map', list())

    @flds_map.setter
    def flds_map(self, value):
        self.data['flds_map'] = value

CONFIG = Config()
