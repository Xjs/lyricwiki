#!/usr/bin/python
"""
lyricwiki.py -- get lyrics from lyrics.wikia.com
usage: lyricwiki.py "Artist" "Song"
"""

import sys
import unicodedata
from restkit import Resource
import html5lib
from html5lib import treebuilders
import simplejson
from urllib import unquote

parser = html5lib.HTMLParser(tree=treebuilders.getTreeBuilder("lxml"))
charset = 'utf-8' # TODO: get this from HTTP response

def proper_unicode(string):
    return unicodedata.normalize('NFC', unicode(string, charset))

def url_from_api(artist, song):
    """Get URL to lyrics article from lyrics.wikia.com API"""
    r =  Resource('http://lyrics.wikia.com', headers={'Accept':'application/json'})
    json = r.get('/api.php', fmt='json', artist=proper_unicode(artist), song=proper_unicode(song))
    if not isinstance(json, basestring):
        # Compatibility for restkit >= 0.9
        json = json.unicode_body
    json = json[6:].replace("'", '"') # replace needed because wikia doesn't provide us with valid JSON. [6:] needed because it says "song = " first.
    d = simplejson.loads(json)
    if d['lyrics'] == 'Not found':
        raise ValueError("No lyrics for {song} by {artist}".format(song=song, artist=artist))
    else:
        print >>sys.stderr, 'url =', d['url']
        return unicode(unquote(d['url'].encode(charset)), charset)
    
def artist_song_from_api_url(url):
    """Get wiki-compatible artist, song tuple from URL retrieved from API"""
    return tuple(url[len('http://lyrics.wikia.com/'):].rsplit(':', 1))

def edit_url_from(url):
    """Get URL to "edit this page" from a given lyrics page"""
    source = Resource(url).get()
    if not isinstance(source, basestring):
        source = source.unicode_body
    document = parser.parse(source)
    
    edit_link = document.find(".//{http://www.w3.org/1999/xhtml}a[@id='ca-edit']")
    return ''.join(['http://lyrics.wikia.com', dict(edit_link.items())['href']])
    
def lyrics_from(base_url, *arguments, **parameters):
    """Get lyrics string from an edit page"""
    edit_source = Resource(base_url).get(*arguments, **parameters)
    if not isinstance(edit_source, basestring):
        edit_source = edit_source.unicode_body
    edit_document = parser.parse(edit_source)
    
    wiki_source = edit_document.find(".//{http://www.w3.org/1999/xhtml}textarea[@id='wpTextbox1']").text
    start = wiki_source.find("<lyrics>")+len("<lyrics>")
    end = wiki_source.find("</lyrics>")
    return wiki_source[start:end].strip()

def lyrics(artist, song):
    """Get lyrics using the API and an edit page"""
    api_url = url_from_api(artist, song)
    artist_song = artist_song_from_api_url(api_url)
    return lyrics_from('http://lyrics.wikia.com/', 'index.php', title=u'{0}:{1}'.format(*artist_song), action='edit')

print >>sys.stderr, sys.argv

try:
    return_value = lyrics(*sys.argv[1:])
    print return_value.encode(charset)
except ValueError, e:
    print >>sys.stderr, str(e)
    sys.exit(1)