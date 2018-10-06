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


import sys
from anki.utils import isMac
from aqt.qt import *
from ..constants import APP_ICON


__all__ = ['Dialog']


class Dialog(QDialog):
    '''
    Base used for all dialog windows.
    '''

    def __init__(self, parent, title):
        '''
        Set the modal status for the dialog, sets its layout to the
        return value of the _ui() method, and sets a default title.
        '''

        self._title = title
        self._parent = parent
        super(Dialog, self).__init__(parent)

        self.setModal(True)
        self.setWindowFlags(
            self.windowFlags() &
            ~Qt.WindowContextHelpButtonHint
        )
        self.setWindowIcon(APP_ICON)
        self.setWindowTitle(
            title if "Import Video" in title
            else "Import Video - " + title
        )
        # 2 & 3 & mac compatible
        if isMac and sys.hexversion >= 0x03000000:
            QApplication.setStyle('Fusion')
