# anki-countries_deck-builder

## Overview
This tool grabs countries related data from free knowledge base [Wikidata](https://www.wikidata.org/) and converts it to a deck for spaced repetition flashcard program [Anki](http://ankisrs.net/).

This version retrieves:
* Countries names for arbitrary list of languages
* SVG flag for each country

It should be relatively easy to extend list of retrieved data.

## Usage
This script requires `requests` python library and Anki sources.

`requests` should be installed the standard way for your operating system (unix users, search for `python-requests` or `python2-requests` package, depending on your python version).

If script does not finds your Anki installation sources your have to specify path to anki libs with `--anki-libs-dir` switch:
`./builder.py --anki-libs-dir=/path/to/anki`

Other command line options should be self-explanatory, check `./builder.py --help`
