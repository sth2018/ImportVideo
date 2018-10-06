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


from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo
from .importor import Importor
from ..libs import ankihub
from ..lang import _
from ..constants import Endpoint, Template


__all__ = ['check_updates', 'show_dialog', 'show_about_dialog']


def check_updates(background=False, parent=None):
    '''check add-on last version'''
    try:
        parent = mw if parent is None else parent
        state = ankihub.update([Endpoint.check_version], Endpoint.version, background, parent)
        if not background:
            if state == 0:
                showInfo(_('LATEST_VERSION'))
            elif state == -1:
                showInfo(_('CHECK_FAILURE'))
    except:
        if not background:
            showInfo(_('CHECK_FAILURE'))


def show_dialog(browser=None):
    parent = mw if browser is None else browser
    win = Importor(parent)
    win.activateWindow()
    win.raise_()
    win.exec_()


def show_about_dialog(parent):
    '''open about dialog'''
    QMessageBox.about(parent, _('ABOUT'), Template.tmpl_about)
