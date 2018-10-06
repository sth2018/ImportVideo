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


from anki.lang import currentLang
try:
  basestring
except NameError:
  basestring = str

__all__ = ['_', '_cl', '_sl']


#Language Define, [Key, zh_CN, en]
_arr = [
    ['CHOOSE_NOTE_TYPES', u'选择笔记类型', u'Choose Note Type'],
    ['CHOOSE_DECK', u'选择课件', u'Choose Deck'],

    ['UPDATED', u'更新', u'Updated'],
    ['CARDS', u'卡片', u'Cards'],
    ['FAILURE', u'失败', u'Failure'],
    ['SUCCESS', u'成功', u'Success'],
    ['FIELDS', u'字段', u'Fields'],
    ['IGNORE', u'忽略', u'Ignore'],
    ['NOTE_TYPE_FIELDS', u'<b>笔记字段</b>', u'<b>Note Fields</b>'],
    ['ABOUT', u'关于', u'About'],
    ['REPOSITORY', u'项目地址', u'Project Repo'],
    ['FEEDBACK', u'反馈', u'Feedback'],
    ['VERSION', u'版本', u'Current Version'],
    ['LATEST_VERSION', u'已经是最新版本.', u'You are using the lastest version.'],
    ['ABNORMAL_VERSION', u'当前版本异常.', u'The current version is abnormal.'],
    ['CHECK_FAILURE', u'版本检查失败.', u'Version check failed.'],
    ['NEW_VERSION', u'检查到新版本:', u'New version available:'],
    ['UPDATE', u'更新', u'Update'],
    ['AUTO_UPDATE', u'自动检测新版本', u'Auto check new version'],
    ['CHECK_UPDATE', u'检测更新', u'Check Update'],
    ['SELECT_ALL', u'全选', u'All'],

    ['VIDEO', u'视频 ...', u'Video ...'],
    ['SUB01', u'字幕1 ...', u'Subtitles 01 ...'],
    ['SUB02', u'字幕2 ...', u'Subtitles 02 ...'],

    ['FLD_TIMESTAMP', u'时间戳', u'Timestamp'],
    ['FLD_IMAGE', u'截图', u'Image'],
    ['FLD_VIDEO', u'视频', u'Video'],
    ['FLD_SOUND', u'声音', u'Sound'],
    ['FLD_SUB01', u'字幕1', u'Subtitles 01'],
    ['FLD_SUB02', u'字幕2', u'Subtitles 02'],
]

_trans = {item[0]: {'zh_CN': item[1], 'en': item[2]} for item in _arr}


def _(key, lang=currentLang):
    '''get local language string'''
    if lang != 'zh_CN' and lang != 'en':
        lang = 'en'

    def disp(s):
        return s.lower().capitalize()
    
    if key not in _trans or lang not in _trans[key]:
        return disp(key)
    return _trans[key][lang]


def _cl(labels, lang=currentLang):
    '''get local language string from labels'''
    if isinstance(labels, basestring):
        return _(labels)
    if lang != 'zh_CN' and lang != 'en':
        lang = 'en'
    return labels[0] if lang == 'zh_CN' else labels[1]


def _sl(key):
    return _trans[key].values()
