#!/usr/bin/python2
#
# GCompris - check_voices.py
#
# Copyright (C) 2015 Bruno Coudoin <bruno.coudoin@gcompris.net>
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, see <http://www.gnu.org/licenses/>.
#
#
# The output is in markdown. A web page can be generated with:
# ./check_voices.py ../gcompris-kde
#
# (Requires python-markdown to be installed)
#
import os
import sys
import re
import copy
import json
from pprint import pprint
import polib
import codecs
import locale
from StringIO import StringIO
import markdown
from datetime import date
import polib
import glob

from PyQt5.QtCore import pyqtProperty, QCoreApplication, QObject, QUrl
from PyQt5.QtQml import qmlRegisterType, QQmlComponent, QQmlEngine

if len(sys.argv) < 2:
    print "Usage: check_voices.py [-v] path_to_gcompris"
    print "  -v:  verbose, show also files that are fine"
    print "  -nn: not needed, show extra file in the voice directory"
    sys.exit(1)

verbose = '-v' in sys.argv
notneeded = '-nn' in sys.argv
gcompris_qt = sys.argv[1]

# Force ouput as UTF-8
ref_stdout = sys.stdout
sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

# A global hash to hold a description on a key file like the UTF-8 char of
# the file.
descriptions = {}

def get_html_header():
    return """<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
  <meta charset="utf-8"/>
  <title>GCompris Voice Recording Status</title>
</head>
<body>
"""

def get_html_footer():
    today = date.today()
    return """</body>
<hr></hr>
<p>Page generated the {:s}</p>
</body>
""".format(today.isoformat())

def get_html_progress_bar(rate):
    return '<td width=200 height=30pt>' + \
        '<div style="border: 2px solid silver;background-color:#c00"><div style="background-color:#0c0;height:15px;width:{:d}%"></div></div>'.format(int(float(rate) * 100))

# '<hr style="color:#0c0;background-color:#0c0;height:15px; border:none;margin:0;" align="left" width={:d}% /></td>'.format(int(float(rate) * 100))

def title1(title):
    print title
    print '=' * len(title)
    print ''

def title2(title):
    print title
    print '-' * len(title)
    print ''

def title3(title):
    print '### ' + title
    print ''


def get_intro_from_code():
    '''Return a set for activities as found in GCompris ActivityInfo.qml'''

    activity_info = set()

    activity_dir = gcompris_qt + "/src/activities"
    for activity in os.listdir(activity_dir):
        # Skip unrelevant activities
        if activity == 'template' or \
           activity == 'menu' or \
           not os.path.isdir(activity_dir + "/" + activity):
            continue

        try:
            with open(activity_dir + "/" + activity + "/ActivityInfo.qml") as f:
                activity_info.add(activity + '.ogg')
                # TODO if we want to grab the string to translate
                #content = f.readlines()
                #for line in content:
                #    m = re.match('.*intro:.*\"(.*)\"', line)
                #    if m:
                #        # Intro voice is in m.group(1)
                #        break
        except IOError as e:
            pass

    return activity_info

def init_intro_description_from_code(locale):
    '''Init the intro description as found in GCompris ActivityInfo.qml'''
    '''in the global descriptions hash'''

    po = None
    try:
        po = polib.pofile( gcompris_qt + '/po/gcompris_' + locale + '.po')
    except:
        print "**ERROR: Failed to load po file %s**" %(gcompris_qt + '/po/gcompris_' + locale + '.po')
        print ''

    activity_dir = gcompris_qt + "/src/activities"
    for activity in os.listdir(activity_dir):
        # Skip unrelevant activities
        if activity == 'template' or \
           activity == 'menu' or \
           not os.path.isdir(activity_dir + "/" + activity):
            continue

        descriptions[activity + '.ogg'] = ''
        try:
            with open(activity_dir + "/" + activity + "/ActivityInfo.qml") as f:
                content = f.readlines()

                for line in content:
                    m = re.match('.*title:.*\"(.*)\"', line)
                    if m:
                        title = m.group(1)
                        if po:
                            title = po.find(title).msgstr if po.find(title) else title
                        descriptions[activity + '.ogg'] += ' title: ' + title

                    m = re.match('.*description:.*\"(.*)\"', line)
                    if m:
                        title = m.group(1)
                        if po:
                            title = po.find(title).msgstr if po.find(title) else title
                        descriptions[activity + '.ogg'] += ' description: ' + title

                    m = re.match('.*intro:.*\"(.*)\"', line)
                    if m:
                        descriptions[activity + '.ogg'] += ' voice: ' + m.group(1)


            if not descriptions.has_key(activity + '.ogg'):
                print "**ERROR: Missing intro tag in %s**" %(activity + "/ActivityInfo.qml")
        except IOError as e:
            pass

    print ''


def init_country_names_from_code(locale):
    '''Init the country description as found in GCompris geography/resource/board/board*.qml'''
    '''in the global descriptions hash'''

    po = None
    try:
        po = polib.pofile( gcompris_qt + '/po/gcompris_' + locale + '.po')
    except:
        print "**ERROR: Failed to load po file %s**" %(gcompris_qt + '/po/gcompris_' + locale + '.po')
        print ''

    app = QCoreApplication(sys.argv)
    engine = QQmlEngine()
    component = QQmlComponent(engine)

    for qml in glob.glob(gcompris_qt + '/src/activities/geography/resource/board/*.qml'):
        component.loadUrl(QUrl(qml))
        board = component.create()
        levels = board.property('levels')
        for level in levels.toVariant():
            if level.has_key('soundFile') and level.has_key('toolTipText'):
                sound = level['soundFile'].split('/')[-1].replace('$CA', 'ogg')
                tooltip = level['toolTipText']
                if po:
                    tooltip = po.find(tooltip).msgstr if po.find(tooltip) else tooltip
                descriptions[sound] = tooltip


def get_locales_from_config():
    '''Return a set for locales as found in GCompris src/core/LanguageList.qml'''

    locales = set()

    source = gcompris_qt + "/src/core/LanguageList.qml"
    try:
        with open(source) as f:
            content = f.readlines()
            for line in content:
                m = re.match('.*\"locale\":.*\"(.*)\"', line)
                if m:
                    locale = m.group(1).split('.')[0]
                    if locale != 'system' and locale != 'en_US':
                        locales.add(locale)
    except IOError as e:
        print "ERROR: Failed to parse %s: %s" %(source, e.strerror)

    return locales


def get_locales_from_po_files():
    '''Return a set for locales for which we have a po file '''
    '''Run make getSvnTranslations first'''

    locales = set()

    locales_dir = gcompris_qt + "/po"
    for locale in os.listdir(locales_dir):
        locales.add(locale.split('_', 1)[1][:-3])

    return locales

def get_translation_status_from_po_files():
    '''Return the translation status from the po file '''
    '''For each locale as key we provide a list: '''
    ''' [ translated_entries, untranslated_entries, fuzzy_entries, percent ]'''
    '''Run make getSvnTranslations first'''

    # en locale has no translation file but mark it 100% done
    locales = {'en': [0, 0, 0, 1]}

    descriptions['en'] = 'US English'

    locales_dir = gcompris_qt + "/po"
    for locale_file in os.listdir(locales_dir):
        locale = locale_file.split('_', 1)[1][:-3]
        po = polib.pofile(locales_dir + '/' + locale_file)
        # Calc a global translation percent
        percent = 1 - \
            (float((len(po.untranslated_entries()) +
                    len(po.fuzzy_entries()))) /
             (len(po.translated_entries()) +
              len(po.untranslated_entries()) +
              len(po.fuzzy_entries())))
        locales[locale] = \
            [ len(po.translated_entries()),
              len(po.untranslated_entries()),
              len(po.fuzzy_entries()),
              percent ]

        # Save the translation team in the global descriptions
        if po.metadata.has_key('Language-Team'):
            team = po.metadata['Language-Team']
            team = re.sub(r' <.*>', '', team)
            descriptions[locale] = team
        else:
            descriptions[locale] = ''

    return locales

def get_words_from_code():
    '''Return a set for words as found in GCompris lang/resource/content-<locale>.json'''
    try:
        with open(gcompris_qt + '/src/activities/lang/resource/content-' + locale + '.json') as data_file:
            data = json.load(data_file)
    except:
        print ''
        print "**ERROR: missing resource file %s**" %(gcompris_qt + '/src/activities/lang/resource/content-' + locale + '.json')
        print '[Instructions to create this file](%s)' %('http://gcompris.net/wiki/Voice_translation_Qt#Lang_word_list')
        print ''
        return set()

    # Consolidate letters
    words = set()
    for word in data.keys():
        # Skip alphabet letter, they are already handled by the alphabet set
        if word[0] == 'U' or word[0] == '1':
            continue
        words.add(word)
        descriptions[word] = u'[{:s}](http://gcompris.net/incoming/lang/words.html#{:s})'.format(data[word], word.replace('.ogg', ''))

    return words

def get_wordsgame_from_code():
    '''Return nothing but tells if the required GCompris wordsgame/resource/default-<locale>.json is there'''

    if not os.path.isfile(gcompris_qt + '/src/activities/wordsgame/resource/default-' + locale + '.json'):
        print ''
        print "**ERROR: missing resource file %s**" %(gcompris_qt + '/src/activities/wordsgame/resource/default-' + locale + '.json')
        print '[Instructions to create this file](%s)' %('http://gcompris.net/wiki/Word_Lists_Qt#Wordsgame_.28Typing_words.29')

        return set()

    # We don't really have voices needs here, just check the file exists
    return set()

def get_click_on_letter_from_code():
    '''Return nothing but tells if the required GCompris click_on_letter/resource/levels-<locale>.json is there'''

    if not os.path.isfile(gcompris_qt + '/src/activities/click_on_letter/resource/levels-' + locale + '.json'):
        print ''
        print "**ERROR: missing resource file %s**" %(gcompris_qt + '/src/activities/click_on_letter/resource/levels-' + locale + '.json')
        print '[Instructions to create this file TBD](%s)' %('TBD')

        return set()

    # We don't really have voices needs here, just check the file exists
    return set()

def get_geography_on_letter_from_code():
    '''Return all the countries in geography/resource/board/board-x.json'''
    words = set()
    
    app = QCoreApplication(sys.argv)
    engine = QQmlEngine()
    component = QQmlComponent(engine)
    for qml in glob.glob(gcompris_qt + '/src/activities/geography/resource/board/*.qml'):
        component.loadUrl(QUrl(qml))
        board = component.create()
        levels = board.property('levels')
        for level in levels.toVariant():
            if level.has_key('soundFile') and (not level.has_key('type') or level['type'] != "SHAPE_BACKGROUND"):
                sound = level['soundFile'].split('/')[-1].replace('$CA', 'ogg')
                words.add(sound)
    return words

def get_files(locale, voiceset):
    to_remove = set(['README'])
    try:
        return set(os.listdir(locale + '/' + voiceset)) - to_remove
    except:
        return set()

def get_locales_from_file():
    locales = set()
    for file in os.listdir('.'):
        if os.path.isdir(file) \
           and not os.path.islink(file) \
           and file[0] != '.':
            locales.add(file)

    return locales

def get_gletter_alphabet():
    try:
        with open(gcompris_qt + '/src/activities/gletters/resource/default-' + locale + '.json') as data_file:
            data = json.load(data_file)
    except:
        print ''
        print "**ERROR: Missing resource file %s**" %(gcompris_qt + '/src/activities/gletters/resource/default-' + locale + '.json')
        print '[Instructions to create this file](%s)' %('http://gcompris.net/wiki/Word_Lists_Qt#Simple_Letters_.28Typing_letters.29_level_design')
        print ''
        return set()

    # Consolidate letters
    letters = set()
    for level in data['levels']:
        for w in level['words']:
            multiletters = ""
            for one_char in w.lower():
                multiletters += 'U{:04X}'.format(ord(one_char))
            letters.add(multiletters + '.ogg')
            descriptions[multiletters + '.ogg'] = w.lower()

    # Add numbers needed for words
    for i in range(10, 21):
        letters.add(str(i) + '.ogg')

    return letters

def diff_set(title, code, files):
    '''Returns a stat from 0 to 1 for this report set'''

    if not code and not files:
        return 0

    title2(title)

    if verbose and code & files:
        title3("These files are correct")
        print '| File | Description |'
        print '|------|-------------|'
        sorted = list(code & files)
        sorted.sort()
        for f in sorted:
            if descriptions.has_key(f):
                print u'| %s | %s |' %(f, descriptions[f])
            else:
                print '|%s |  |' %(f)
        print ''

    if code - files:
        title3("These files are missing")
        print '| File | Description |'
        print '|------|-------------|'
        sorted = list(code - files)
        sorted.sort()
        for f in sorted:
            if descriptions.has_key(f):
                print u'| %s | %s |' %(f, descriptions[f])
            else:
                print '|%s |  |' %(f)
        print ''

    if notneeded and files - code:
        title3("These files are not needed")
        print '| File | Description |'
        print '|------|-------------|'
        sorted = list(files - code)
        sorted.sort()
        for f in sorted:
            if descriptions.has_key(f):
                print u'|%s | %s|' %(f, descriptions[f])
            else:
                print '|%s |  |' %(f)
        print ''

    return 1 - float(len(code - files)) / len(code | files)

def diff_locale_set(title, code, files):

    if not code and not files:
        return

    title2(title)
    if verbose:
        title3("We have voices for these locales:")
        missing = []
        for locale in code:
            if os.path.isdir(locale):
                print '* ' + locale
            else:
                # Shorten the locale and test again
                shorten = locale.split('_')
                if os.path.isdir(shorten[0]):
                    print '* ' + locale
                else:
                    missing.append(locale)
    print ''
    print "We miss voices for these locales:"
    for f in missing:
        print '* ' + f
    print ''

def check_locale_config(title, stats, locale_config):
    '''Display and return locales that are translated above a fixed threshold'''
    title2(title)
    LIMIT = 0.8
    sorted_config = list(locale_config)
    sorted_config.sort()
    good_locale = []
    for locale in sorted_config:
        if stats.has_key(locale):
            if stats[locale][3] < LIMIT:
                print u'* {:s} ({:s})'.format((descriptions[locale] if descriptions.has_key(locale) else ''), locale)
            else:
                good_locale.append((descriptions[locale] if descriptions.has_key(locale) else ''))
        else:
            # Shorten the locale and test again
            shorten = locale.split('_')[0]
            if stats.has_key(shorten):
                if stats[shorten][3] < LIMIT:
                    print u'* {:s} ({:s})'.format((descriptions[shorten] if descriptions.has_key(shorten) else ''), shorten)
                else:
                    good_locale.append(descriptions[shorten] if descriptions.has_key(shorten) else '')
            else:
                print "* %s no translation at all" %(locale)

    print ''
    good_locale.sort()
    print 'There are %d locales above %d%% translation: %s' %(len(good_locale), LIMIT * 100,
                                                              ', '.join(good_locale))

    return good_locale

#
# main
# ===

reports = {}
sys.stdout = reports['stats'] = StringIO()

string_stats = get_translation_status_from_po_files()
check_locale_config("Locales to remove from LanguageList.qml (translation level < 80%)",
                    string_stats, get_locales_from_config())

# Calc the big list of locales we have to check
all_locales = get_locales_from_po_files() | get_locales_from_file()
all_locales = list(all_locales)
all_locales.sort()

stats = {}
global_descriptions = copy.deepcopy(descriptions)

for locale in all_locales:
    sys.stdout = reports[locale] = StringIO()

    descriptions = copy.deepcopy(global_descriptions)
    init_intro_description_from_code(locale)
    init_country_names_from_code(locale)

    title1(u'{:s} ({:s})'.format((descriptions[locale] if descriptions.has_key(locale) else ''), locale))

    lstats = {'locale': locale}
    lstats['intro'] = diff_set("Intro ({:s}/intro/)".format(locale), get_intro_from_code(), get_files(locale, 'intro'))
    lstats['letter'] = diff_set("Letters ({:s}/alphabet/)".format(locale), get_gletter_alphabet(), get_files(locale, 'alphabet'))

    descriptions['click_on_letter.ogg'] = "Must contains the voice: 'Click on the letter:'"
    lstats['misc'] = diff_set("Misc ({:s}/misc/)".format(locale), get_files('en', 'misc'), get_files(locale, 'misc'))

    lstats['color'] = diff_set("Colors ({:s}/colors/)".format(locale), get_files('en', 'colors'), get_files(locale, 'colors'))
    lstats['geography'] = diff_set("Geography ({:s}/geography/)".format(locale), get_geography_on_letter_from_code(), get_files(locale, 'geography'))
    lstats['words'] = diff_set("Words ({:s}/words/)".format(locale), get_words_from_code(), get_files(locale, 'words'))
    lstats['wordsgame'] = diff_set("Wordsgame", get_wordsgame_from_code(), set())
    lstats['click_on_letter'] = diff_set("Click on letter", get_click_on_letter_from_code(), set())
    stats[locale] = lstats

sys.stdout = reports['summary'] = StringIO()
sorted_keys = stats.keys()
sorted_keys.sort()
title1("GCompris Voice Recording Status Summary")
print '| Locale | Strings | Misc | Letters | Colors | Geography | Words | Intro|'
print '|--------|---------|------|---------|--------|-----------|-------|------|'
for locale in sorted_keys:
    stat = stats[locale]
    print u'| [{:s} ({:s})](voice_status_{:s}.html) | {:.2f} | {:.2f} | {:.2f} | {:.2f} | {:.2f} | {:.2f} | {:.2f} |' \
        .format((descriptions[locale] if descriptions.has_key(locale) else ''), stat['locale'], locale,
                string_stats[locale][3] if string_stats.has_key(locale) else 0,
                stat['misc'], stat['letter'], stat['color'], stat['geography'],
                stat['words'], stat['intro'])

#
# Now we have all the reports
#

extensions=['markdown.extensions.tables']

sys.stdout = ref_stdout

with codecs.open("index.html", "w",
                 encoding="utf-8",
                 errors="xmlcharrefreplace"
             ) as f:
    f.write(get_html_header())

    summary = markdown.markdown(reports['summary'].getvalue(), extensions=extensions)
    summary2 = ""
    for line in summary.split('\n'):
        m = re.match('<td>(\d\.\d\d)</td>', line)
        if m:
            rate = m.group(1)
            summary2 += get_html_progress_bar(rate)
        else:
            summary2 += line

        summary2 += '\n'

    f.write(summary2 + '\n')

    f.write(markdown.markdown(reports['stats'].getvalue(), extensions=extensions))
    f.write(get_html_footer())

for locale in sorted_keys:
    with codecs.open("voice_status_{:s}.html".format(locale), "w",
                     encoding="utf-8",
                     errors="xmlcharrefreplace"
                 ) as f:
        f.write(get_html_header())
        f.write(markdown.markdown(reports[locale].getvalue(), extensions=extensions))
        f.write(get_html_footer())
