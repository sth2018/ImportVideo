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
from anki.hooks import addHook, remHook
from .gui import *
from .constants import APP_ICON
from .lang import _


__all__ = ['config_menu']


def config_menu():
    """
    add menu to anki window menebar
    """
    action = QAction(APP_ICON, "Import Video...", mw)
    action.triggered.connect(lambda: show_dialog())
    mw.form.menuTools.addAction(action)


def browser_menu():
    """
    add add-on's menu to browser window
    """
    def on_setup_menus(browser):
        """
        on browser setupMenus was called
        """
        # main menu
        menu = browser.form.menubar.addMenu("Import Video")

        # import
        action = QAction(APP_ICON, _("IMPORT_VIDEO"), mw)
        action.triggered.connect(lambda: show_dialog())
        menu.addAction(action)

        # check update
        action = QAction(_('CHECK_UPDATE'), browser)
        action.triggered.connect(lambda: check_updates(background=False, parent=browser))
        menu.addAction(action)

        # About
        action = QAction(_('ABOUT'), browser)
        action.triggered.connect(lambda: show_about_dialog(browser))
        menu.addAction(action)

    addHook('browser.setupMenus', on_setup_menus)
