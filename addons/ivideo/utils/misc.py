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


import glob
import os
import re
import shutil
import time
import subprocess

from aqt.qt import QIcon


__all__ = ['subprocess_args', 'srt_time_to_seconds', 'tsv_time_to_seconds',
            'get_time_parts', 'seconds_to_srt_time', 'seconds_to_tsv_time',
            'seconds_to_ffmpeg_time', 'fix_empty_lines', 'escape_double_quotes',
            'is_not_sdh_subtitle', 'read_subtitles', 'join_lines_within_subs',
            'remove_tags', 'sync_subtitles', 'change_subtitles_ending_time',
            'find_glob_files', 'guess_srt_file', 'format_filename',
            'get_ffmpeg_split_timestamps', 'get_model_byId',
            'clear_layout', 'rmfile', 'get_icon']



# Create a set of arguments which make a ``subprocess.Popen`` (and
# variants) call work with or without Pyinstaller, ``--noconsole`` or
# not, on Windows and Linux. Typical use::
#
#   subprocess.call(['program_to_run', 'arg_1'], **subprocess_args())
#
# When calling ``check_output``::
#
#   subprocess.check_output(['program_to_run', 'arg_1'],
#                           **subprocess_args(False))
def subprocess_args(include_stdout=True):
    # The following is true only on Windows.
    if hasattr(subprocess, 'STARTUPINFO'):
        # On Windows, subprocess calls will pop up a command window by default
        # when run from Pyinstaller with the ``--noconsole`` option. Avoid this
        # distraction.
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        # Windows doesn't search the path by default. Pass it an environment so
        # it will.
        env = os.environ
    else:
        si = None
        env = None

    # ``subprocess.check_output`` doesn't allow specifying ``stdout``::
    #
    #   Traceback (most recent call last):
    #     File "test_subprocess.py", line 58, in <module>
    #       **subprocess_args(stdout=None))
    #     File "C:\Python27\lib\subprocess.py", line 567, in check_output
    #       raise ValueError('stdout argument not allowed, it will be overridden.')
    #   ValueError: stdout argument not allowed, it will be overridden.
    #
    # So, add it only if it's needed.
    if include_stdout:
        ret = {'stdout': subprocess.PIPE}
    else:
        ret = {}

    # On Windows, running this from the binary produced by Pyinstaller
    # with the ``--noconsole`` option requires redirecting everything
    # (stdin, stdout, stderr) to avoid an OSError exception
    # "[Error 6] the handle is invalid."
    ret.update({
        'stdin': subprocess.PIPE,
        'stderr': subprocess.PIPE,
        'startupinfo': si,
        'env': env 
    })
    return ret

def srt_time_to_seconds(time):
    split_time = time.split(',')
    major, minor = (split_time[0].split(':'), split_time[1])
    return int(major[0]) * 3600 + int(major[1]) * 60 + int(major[2]) + float(minor) / 1000

def tsv_time_to_seconds(tsv_time):
    return srt_time_to_seconds(tsv_time.replace(".", ","))

def get_time_parts(time):
    millisecs = str(time).split(".")[1]
    if len(millisecs) != 3:
        millisecs = millisecs + ('0' * (3 - len(millisecs)))
    millisecs = int(millisecs)
    mins, secs = divmod(time, 60)
    hours, mins = divmod(mins, 60)

    return (hours, mins, secs, millisecs)

def seconds_to_srt_time(time):
    return '%02d:%02d:%02d,%03d' % get_time_parts(time)

def seconds_to_tsv_time(time):
    return '%d.%02d.%02d.%03d' % get_time_parts(time)

def seconds_to_ffmpeg_time(time):
    return '%02d:%02d:%02d.%03d' % get_time_parts(time)

def fix_empty_lines(content):
    return re.sub('\n\n+', '\n\n', content)

def escape_double_quotes(content):
    return re.sub('"', '&quot;', content)

def is_not_sdh_subtitle(sub):
    reg_exp_round_braces = r"^\([^)]*\)(\s*\([^)]*\))*$"
    reg_exp_square_braces = r"^\[[^\]]*\](\s*\[[^\]]*\])*$"
    reg_exp_round_braces_with_tags = r"^(?:- )?(?:<[^>]+>)*\([^)]*\)(\s*\([^)]*\))*(?:<[^>]+>)*$"
    reg_exp_round_braces_with_tags_multiline = r"^(\([^)]*\)(\s*\([^)]*\))*|\s|-|(?:<[^>]+>)*)*$"

    if re.match(reg_exp_round_braces, sub):
        return False
    elif re.match(reg_exp_square_braces, sub):
        return False
    elif re.match(reg_exp_round_braces_with_tags, sub):
        return False
    elif re.match(reg_exp_round_braces_with_tags_multiline, sub):
        return False

    return True

def read_subtitles(content, is_ignore_SDH):
    en_subs = []
    
    sub_list = content.strip().split('\n\n')
    for sub in sub_list:
        sub_chunks = sub.split('\n')
        if (len(sub_chunks) >= 3):
            sub_timecode =  sub_chunks[1].split(' --> ')
            
            sub_start = srt_time_to_seconds(sub_timecode[0].strip())
            sub_end = srt_time_to_seconds(sub_timecode[1].strip())
            sub_content = " ".join(sub_chunks[2:]).replace("\t", " ")
            sub_content = re.sub(r"\n +", "\n", sub_content)
            sub_content = re.sub(r"  +", " ", sub_content)
            sub_content = sub_content.strip()

            if len(sub_content) > 0:
                if not is_ignore_SDH:
                    en_subs.append((sub_start, sub_end, sub_content))
                else:
                    if is_not_sdh_subtitle(sub_content):
                        en_subs.append((sub_start, sub_end, sub_content))
                    else:
                        print "Ignore subtitle: %s" % repr(sub_content)
            else:
                print "Empty subtitle: %s" % repr(sub)
        else:
            print "Ignore subtitle: %s" % repr(sub)
   
    return en_subs

# [(start_time, end_time, subtitle), (), ...], [(...)], ...
def join_lines_within_subs(subs):
    subs_joined = []

    global duration_longest_phrase
    duration_longest_phrase = 0

    for sub in subs:
        sub_start = sub[0][0]
        sub_end = sub[-1][1]

        sub_content = ""
        for s in sub:
            sub_content = sub_content + " " + s[2]
        
        subs_joined.append((sub_start, sub_end, sub_content.strip()))

        if sub_end - sub_start > duration_longest_phrase:
            duration_longest_phrase = int(sub_end - sub_start)

    return subs_joined

def remove_tags(sub):
    sub = re.sub(r"<[^>]+>", "", sub)
    sub = re.sub(r"  +", " ", sub)
    sub = sub.strip()

    return sub

def sync_subtitles(en_subs, cn_subs):
    subs = []

    for en_sub in en_subs:
        en_sub_start = en_sub[0]
        en_sub_end = en_sub[1]
        sub_content = []

        subs.append((en_sub_start, en_sub_end, sub_content))

        for cn_sub in cn_subs:
            cn_sub_start = cn_sub[0]
            cn_sub_end = cn_sub[1]
            cn_sub_content = cn_sub[2]

            if cn_sub_start < en_sub_start:
                if cn_sub_end > en_sub_start and cn_sub_end < en_sub_end:
                    sub_content.append(cn_sub_content) # TODO
                elif cn_sub_end >= en_sub_end:
                    sub_content.append(cn_sub_content) 
            elif cn_sub_start >= en_sub_start and cn_sub_start < en_sub_end:
                if cn_sub_end <= en_sub_end:
                    sub_content.append(cn_sub_content)
                elif cn_sub_end > en_sub_end:
                    sub_content.append(cn_sub_content) # TODO

    tmp_subs = subs
    subs = []

    for sub in tmp_subs:
        sub_start = sub[0]
        sub_end = sub[1]
        sub_content = " ".join(sub[2])

        subs.append((sub_start, sub_end, sub_content))

    return subs

def change_subtitles_ending_time(subs, subs_with_line_timings, is_separate_fragments_without_subtitles, time_delta):
    shift = 0
    subs_in = list(subs)
    for idx in range(1, len(subs_in)):
        (start_time, end_time, subtitle) = subs_in[idx]
        (prev_start_time, prev_end_time, prev_subtitle) = subs_in[idx - 1]

        if prev_end_time < start_time:
            if is_separate_fragments_without_subtitles and (start_time - prev_end_time) > time_delta * 2:
                subs.insert(idx + shift, (prev_end_time, start_time, ""))
                if subs_with_line_timings is not None:
                    subs_with_line_timings.insert(idx + shift, [(prev_end_time, start_time, "")])
                shift = shift + 1
            else:
                subs[idx + shift - 1] = (prev_start_time, start_time, prev_subtitle)

    (start_time, end_time, subtitle) = subs[0]
    if start_time > 15:
        pass
        #subs.insert(0, (0.0, start_time, ""))
        #if subs_with_line_timings is not None:
        #    subs_with_line_timings.insert(0, [(0.0, start_time, "")])
    else:
        subs[0] = (0.0, end_time, subtitle)

    (start_time, end_time, subtitle) = subs[-1]
    if is_separate_fragments_without_subtitles:
        subs.append((end_time, end_time + 600, ""))
        if subs_with_line_timings is not None:
            subs_with_line_timings.append([(end_time, end_time + 600, "")])
    else:
        subs[-1] = (start_time, end_time + 600, subtitle)

def find_glob_files(glob_pattern):
    # replace the left square bracket with [[]
    glob_pattern = re.sub(r'\[', '[[]', glob_pattern)
    # replace the right square bracket with []] but be careful not to replace
    # the right square brackets in the left square bracket's 'escape' sequence.
    glob_pattern = re.sub(r'(?<!\[)\]', '[]]', glob_pattern)

    return glob.glob(glob_pattern)

def guess_srt_file(video_file, mask_list, default_filename):
    for mask in mask_list:
        glob_pattern = video_file[:-4] + mask
        glob_result = find_glob_files(glob_pattern)
        if len(glob_result) >= 1:
            return os.path.realpath(glob_result[0])
    else:
        return default_filename

def format_filename(deck_name):
    """
    Returns the given string converted to a string that can be used for a clean
    filename. Specifically, leading and trailing spaces are removed; other
    spaces are converted to underscores; and anything that is not a unicode
    alphanumeric, dash, underscore, or dot, is removed.
    >>> get_valid_filename("john's portrait in 2004.jpg")
    'johns_portrait_in_2004.jpg'
    """
    s = deck_name.strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)

def get_ffmpeg_split_timestamps(deck_name, en_sub):
    prefix = format_filename(deck_name)
    start_time = seconds_to_tsv_time(en_sub[0])
    end_time = seconds_to_tsv_time(en_sub[1])
    return [prefix + "_" + start_time + "-" + end_time,\
            seconds_to_ffmpeg_time(en_sub[0]),\
            seconds_to_ffmpeg_time(en_sub[1])]

def get_model_byId(models, id):
    for m in list(models.all()):
        if m['id'] == id:
            return m
    return None

def clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()
        else:
            clear_layout(item.layout())

def rmfile(f):
    try:
        if os.path.exists(f):
            os.remove(os.path.realpath(f))
        return True
    except os.error, err:
        print err
        return False

def get_icon(filename):
    curdir = os.path.dirname(os.path.abspath(__file__))
    pardir = os.path.join(curdir, os.pardir)
    path = os.path.join(pardir, 'res', filename)
    return QIcon(path)
