#!/usr/bin/python

import os
import sys
import re
import json
from pprint import pprint

if len(sys.argv) != 3:
    print "Usage: check_voices.py locale path_to_gcompris"
    sys.exit(1)

locale = sys.argv[1]
gcompris_qt = sys.argv[2]

def get_intro_from_code():
    '''Return a set for activities as found in GCompris ActivityInfo.qml'''

    activity_info = set()

    activity_dir = gcompris_qt + "/src/activities"
    filesInDir = []
    for activity in os.listdir(activity_dir):
        # Skip unrelevant activities
        if activity == 'template':
            continue

        try:
            with open(activity_dir + "/" + activity + "/ActivityInfo.qml") as f:
                activity_info.add(activity + '.ogg')
                content = f.readlines()
                for line in content:
                    m = re.match('.*intro:.*\"(.*)\"', line)
                    if m:
                        # Intro voice is in m.group(1)
                        break
        except:
            pass


    return activity_info

def get_files(locale, path):
    return set(os.listdir(locale + '/' + path))

def get_gletter_alphabet():
    with open(gcompris_qt + '/src/activities/gletters/resource/default-' + locale + '.json') as data_file:
        data = json.load(data_file)

    # Consolidate letters
    letters = set()
    for level in data['levels']:
        for w in level['words']:
            letters.add('U{:04X}.ogg'.format(ord(w.lower())))

    return letters

def get_words_from_code():
    '''Return a set for words as found in GCompris content-<locale>.json'''
    with open(gcompris_qt + '/src/activities/imageid/resource/content-' + locale + '.json') as data_file:
        data = json.load(data_file)

    # Consolidate letters
    words = set()
    for word in data.keys():
        words.add(word)

    return words

def diff_set(title, code, files):
    print title
    print '-' * len(title)
    print ''
    print "These files are correct:"
    for f in code & files:
        print ' ' + f
    print ''
    print "These files are missing:"
    for f in code - files:
        print ' ' + f
    print ''
    print "These files are not needed:"
    for f in files - code:
        print ' ' + f
    print ''

diff_set("Intro (intro/)", get_intro_from_code(), get_files(locale, 'intro'))
diff_set("Letters (alphabet/)", get_gletter_alphabet(), get_files(locale, 'alphabet'))
diff_set("Misc (misc/)", get_files('en', 'misc'), get_files(locale, 'misc'))
diff_set("Colors (colors/)", get_files('en', 'colors'), get_files(locale, 'colors'))
diff_set("Geography (geography/)", get_files('en', 'geography'), get_files(locale, 'geography'))
diff_set("Words (words/)", get_words_from_code(), get_files(locale, 'words'))
