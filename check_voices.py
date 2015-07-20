#!/usr/bin/python

import os
import sys
import re
import json
from pprint import pprint
import polib

if len(sys.argv) < 2:
    print "Usage: check_voices.py [-v] path_to_gcompris"
    print "  -v: verbose, show also files that are fine"
    sys.exit(1)

verbose = '-v' in sys.argv
gcompris_qt = sys.argv[1]

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

def print_intro_description_from_code():
    '''Print the intro description as found in GCompris ActivityInfo.qml'''

    title = "Activity Intro description"
    print ''
    print title
    print '-' * len(title)
    print ''

    activity_dir = gcompris_qt + "/src/activities"
    for activity in os.listdir(activity_dir):
        # Skip unrelevant activities
        if activity == 'template' or not os.path.isdir(activity_dir + "/" + activity):
            continue

        try:
            with open(activity_dir + "/" + activity + "/ActivityInfo.qml") as f:
                content = f.readlines()
                for line in content:
                    m = re.match('.*intro:.*\"(.*)\"', line)
                    if m:
                        print "%-32s %s" %(activity, m.group(1))
                        break
        except IOError as e:
            pass

    print ''


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

    locales = {}

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

    return locales

def get_words_from_code():
    '''Return a set for words as found in GCompris content-<locale>.json'''
    try:
        with open(gcompris_qt + '/src/activities/imageid/resource/content-' + locale + '.json') as data_file:
            data = json.load(data_file)
    except:
        print ''
        print "Missing resource file %s" %(gcompris_qt + '/src/activities/imageid/resource/content-' + locale + '.json')
        print ''
        return set()

    # Consolidate letters
    words = set()
    for word in data.keys():
        words.add(word)

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
        print "Missing resource file %s" %(gcompris_qt + '/src/activities/gletters/resource/default-' + locale + '.json')
        print ''
        return set()

    # Consolidate letters
    letters = set()
    for level in data['levels']:
        for w in level['words']:
            multiletters = ""
            for one_char in w:
                multiletters += 'U{:04X}'.format(ord(one_char))
            letters.add(multiletters + '.ogg')

    return letters

def diff_set(title, code, files):

    if not code and not files:
        return

    print title
    print '-' * len(title)

    if verbose and code & files:
        print ''
        print "These files are correct:"
        for f in code & files:
            print ' ' + f
        print ''

    if code - files:
        print ''
        print "These files are missing:"
        for f in code - files:
            print ' ' + f
        print ''

    if files - code:
        print ''
        print "These files are not needed:"
        for f in files - code:
            print ' ' + f
        print ''

def diff_locale_set(title, code, files):

    if not code and not files:
        return

    print title
    print '-' * len(title)
    if verbose:
        print ''
        print "We have voices for these locales:"
        missing = []
        for locale in code:
            if os.path.isdir(locale):
                print ' ' + locale
            else:
                # Shorten the locale and test again
                shorten = locale.split('_')
                if os.path.isdir(shorten[0]):
                    print ' ' + locale
                else:
                    missing.append(locale)
    print ''
    print "We miss voices for these locales:"
    for f in missing:
        print ' ' + f
    print ''

def check_locale_config(title, stats, locale_config):
    '''Display and return locales that are translated above a fixed threshold'''
    print title
    print '-' * len(title)
    print ''
    LIMIT = 0.8
    sorted_config = list(locale_config)
    sorted_config.sort()
    good_locale = []
    for locale in sorted_config:
        if stats.has_key(locale):
            if stats[locale][3] < LIMIT:
                print "%10s" %(locale)
            else:
                good_locale.append(locale)
        else:
            # Shorten the locale and test again
            shorten = locale.split('_')[0]
            if stats.has_key(shorten):
                if stats[shorten][3] < LIMIT:
                    print "%10s" %(locale)
                else:
                    good_locale.append(shorten)
            else:
                print "%10s no translation at all" %(locale)

    print ''
    print 'There is %d locales above %d%% translation: %s' %(len(good_locale), LIMIT * 100,
                                                           ' '.join(good_locale))

    return good_locale

stats = get_translation_status_from_po_files()
check_locale_config("Locales to remove from LanguageList.qml (translation level < 80%)",
                    stats, get_locales_from_config())

print_intro_description_from_code()

# Calc the big list of locales we have to check
all_locales = get_locales_from_po_files() | get_locales_from_file()

for locale in all_locales:
    print ''
    print '==================== %s ====================' %(locale)
    print ''
    diff_set("Intro ({:s}/intro/)".format(locale), get_intro_from_code(), get_files(locale, 'intro'))
    diff_set("Letters ({:s}/alphabet/)".format(locale), get_gletter_alphabet(), get_files(locale, 'alphabet'))
    diff_set("Misc ({:s}/misc/)".format(locale), get_files('en', 'misc'), get_files(locale, 'misc'))
    diff_set("Colors ({:s}/colors/)".format(locale), get_files('en', 'colors'), get_files(locale, 'colors'))
    diff_set("Geography ({:s}/geography/)".format(locale), get_files('en', 'geography'), get_files(locale, 'geography'))
    diff_set("Words ({:s}/words/)".format(locale), get_words_from_code(), get_files(locale, 'words'))



