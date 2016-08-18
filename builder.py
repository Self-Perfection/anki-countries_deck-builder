#!/usr/bin/python

import argparse
import os
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

query = '''SELECT ?country ?countryLabel ?countryFlag
WHERE 
{
  #Or should it be Q3624078 (sovereign state)
  ?country wdt:P31 wd:Q6256 .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
  ?country wdt:P41 ?countryFlag .
}'''


parser = argparse.ArgumentParser(description='Countries deck generator for anki')
parser.add_argument('outfile', metavar='destination_file')
parser.add_argument('-s', '--sample', action='store_true',
        help='Build sample deck with just one note. Full download might be really long.')
parser.add_argument('--anki-libs-dir', default='/usr/share/anki',
        help='Directory with anki libraries (default: %(default)s)')
args = parser.parse_args()
sys.path.insert(0, args.anki_libs_dir)
if not args.outfile.endswith('.apkg'):
    args.outfile += '.apkg'
# Looks like anki libs change working directory to media directory of current deck
# Therefore absolute path should be stored before creating temporary deck
args.outfile = os.path.abspath(args.outfile)

query = urlquoter.quote_plus(query)
URL = 'https://query.wikidata.org/sparql?format=json&query=%s' % query

#TODO migrate to urllib for reducing dependencies?
#TODO make sure content-encoding gzip is used
http_session = requests.Session()

response = http_session.get(URL).json()
print(response)

#TODO: check if files should be downloaded directly to deck.media.dir()
media_dir = tempfile.mkdtemp(prefix='anki_deck_generator.', suffix='.downloaded_media')
(fd, temp_deck_path) = tempfile.mkstemp(prefix='anki_deck_generator.', suffix=".anki2")
os.close(fd)
os.unlink(temp_deck_path)

def graceful_exit():
    import shutil
    print('Removing %s' % media_dir)
    shutil.rmtree(media_dir, ignore_errors=True)
    #TODO should return error on ^C
    exit()

signal.signal(signal.SIGINT, lambda signal,frame: graceful_exit())

from anki import Collection as aopen
from anki.exporting import *
deck = aopen(temp_deck_path)


for row in response['results']['bindings']:
    ## Ewww, urllib.URLopener().retrieve does not follow TLS and other redirects
    ## But it has uber feature to not redownload file if it is already present
    #testfile = urllib.URLopener()
    #print testfile.retrieve(row['countryFlag']['value'])

    URL = row['countryFlag']['value']
    print(URL)
    #Caches whole file in RAM, redownloads if it is already present and does it use gzip?
    r = http_session.get(URL)
    filename = urlquoter.unquote_plus(os.path.basename(urlparse(URL).path))

    with open(os.path.join(media_dir, filename), "wb") as code:
        code.write(r.content)

    f = deck.newNote()
    f['Front'] = '<img src="%s"/>' % filename
    f['Back'] = row['countryLabel']['value']
    deck.addNote(f)
    deck.media.addFile(os.path.join(media_dir, filename))

    if args.sample:
        break


e = AnkiPackageExporter(deck)
e.exportInto(args.outfile)


#graceful_exit()
