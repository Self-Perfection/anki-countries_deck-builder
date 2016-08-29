#!/usr/bin/python

# Copyright 2016 Alexander Meshcheryakov <alexander.s.m+git@gmail.com>
# License: GNU AGPL, version 3 or later; https://www.gnu.org/licenses/agpl.html

import argparse
import os
import re
import shutil
import signal
import sys
import tempfile
if sys.version_info >= (3,):
    import urllib.parse as urlquoter
    from urllib.parse import urlparse
else:
    import urllib as urlquoter
    from urlparse import urlparse

import requests

# Change this if you are going to fork this script for other purpose
user_agent = 'Anki countries deck builder bot (+https://github.com/Self-Perfection/anki-countries_deck-builder)'

parser = argparse.ArgumentParser(description='Countries deck generator for anki')
parser.add_argument('outfile', metavar='destination_file')
parser.add_argument('-s', '--sample', action='store_true',
        help='Build sample deck with just one note. Full download might be really long.')
parser.add_argument('--anki-libs-dir', default='/usr/share/anki',
        help='Directory with anki libraries (default: %(default)s)')
parser.add_argument('-l', '--languages', default='en,zh,es,ar,ru,pt,de,fr',
        help='Comma separated list of languages to retrieve (default: %(default)s). First item would be used in card templates.')
args = parser.parse_args()
sys.path.insert(0, args.anki_libs_dir)
if not args.outfile.endswith('.apkg'):
    args.outfile += '.apkg'
# Looks like anki libs change working directory to media directory of current deck
# Therefore absolute path should be stored before creating temporary deck
args.outfile = os.path.abspath(args.outfile)
default_language = args.languages.split(',')[0]

# Test your query interactively at https://query.wikidata.org/
query = '''SELECT ?country
(SAMPLE(?countryFlag) as ?countryFlag)
(SAMPLE(?locatorMap) as ?locatorMap)
WHERE
{
  #Or should it be Q3624078 (sovereign state)
  ?country wdt:P31 wd:Q6256 .
  ?country wdt:P41 ?countryFlag .
  ?country wdt:P242 ?locatorMap .
}
GROUP BY ?country'''
if args.sample:
    query += ' LIMIT 1'
query = urlquoter.quote_plus(query)
URL = 'https://query.wikidata.org/sparql?format=json&query=%s' % query

http_session = requests.Session()
http_session.headers['User-Agent'] = user_agent

response = http_session.get(URL).json()
print(response)

temp_dir = tempfile.mkdtemp(prefix='anki_deck_generator.')
media_dir = os.path.join(temp_dir, 'downloaded_media')
os.makedirs(media_dir)

def remove_temp_files():
    deck.close()
    shutil.rmtree(temp_dir, ignore_errors=True)
    #TODO should return error on ^C
    exit()

signal.signal(signal.SIGINT, lambda signal,frame: remove_temp_files())

from anki import Collection as aopen
from anki.exporting import *
deck = aopen(os.path.join(temp_dir, 'collection.anki2'))

dm = deck.models
m = dm.new('Country')
fm = dm.newField('Wikidata URI')
dm.addField(m, fm)
fm = dm.newField('Flag')
dm.addField(m, fm)
fm = dm.newField('Locator map')
dm.addField(m, fm)
for lang in args.languages.split(','):
    fm = dm.newField('Contry name ' + lang)
    dm.addField(m, fm)
t = dm.newTemplate('Flag -> country name')
t['qfmt'] = '<div class="flag">{{Flag}}</div>'
t['afmt'] = '{{FrontSide}}\n\n<hr id=answer>\n\n{{Contry name %s}}' % default_language
dm.addTemplate(m, t)
t = dm.newTemplate('Locator map -> country name')
t['qfmt'] = '{{Locator map}}'
t['afmt'] = '{{FrontSide}}\n\n<hr id=answer>\n\n{{Contry name %s}}' % default_language
dm.addTemplate(m, t)
m['css'] += '''

.flag img {
 border: 1px;
 border-style: solid;
}
'''
dm.add(m)


def download_image(URL):
    """Add file to media and return its basename of file"""
    print(URL)
    filename = urlquoter.unquote_plus(os.path.basename(urlparse(URL).path))
    r = http_session.get(URL)
    with open(os.path.join(media_dir, filename), "wb") as code:
        code.write(r.content)
    deck.media.addFile(os.path.join(media_dir, filename))
    return filename

for row in response['results']['bindings']:
    f = deck.newNote()
    f['Wikidata URI'] = row['country']['value']
    f['Flag'] = '<img src="%s"/>' % download_image(row['countryFlag']['value'])
    f['Locator map'] = '<img src="%s"/>' % download_image(row['locatorMap']['value'])

    wikidata_id = re.sub('https?://www.wikidata.org/entity/', '', f['Wikidata URI'])
    # See API docs at https://www.wikidata.org/w/api.php?action=help&recursivesubmodules=1#wbgetentities
    URL = ('https://www.wikidata.org/w/api.php' +
        '?action=wbgetentities&props=labels&format=json&' +
        'ids=%s&languages=%s' % (wikidata_id, args.languages.replace(',', '|')) )
    labels = http_session.get(URL).json()['entities'][wikidata_id]['labels']
    for lang in args.languages.split(','):
        f['Contry name ' + lang] = labels[lang]['value']

    deck.addNote(f)


e = AnkiPackageExporter(deck)
e.exportInto(args.outfile)

remove_temp_files()
