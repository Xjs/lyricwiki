#!/usr/bin/python
from sys import argv
from restkit import Resource
import html5lib
from html5lib import treebuilders
import simplejson

parser = html5lib.HTMLParser(tree=treebuilders.getTreeBuilder("lxml"))

def url_from_api(artist, song):
    r =  Resource('http://lyrics.wikia.com', headers={'Accept':'application/json'})
    json = r.get('/api.php', fmt='json', artist=artist, song=song)
    json = json[6:].replace("'", '"') # replace needed because wikia doesn't provide us with valid JSON. [6:] needed because it says "song = " first.
    d = simplejson.loads(json)
    return d['url']
    
def artist_song_from_api_url(url):
    return tuple(url[len('http://lyrics.wikia.com/'):].split(':'))

def edit_url_from(url):
    source = Resource(url).get()
    document = parser.parse(source)
    
    edit_link = document.find(".//{http://www.w3.org/1999/xhtml}a[@id='ca-edit']")
    return ''.join(['http://lyrics.wikia.com', dict(edit_link.items())['href']])
    
def lyrics_from(base_url, *arguments, **parameters):
    edit_source = Resource(base_url).get(*arguments, **parameters)
    edit_document = parser.parse(edit_source)
    
    wiki_source = edit_document.find(".//{http://www.w3.org/1999/xhtml}textarea[@id='wpTextbox1']").text
    start = wiki_source.find("<lyrics>")+len("<lyrics>")
    end = wiki_source.find("</lyrics>")
    return wiki_source[start:end].strip()

def lyrics(artist, song):
    api_url = url_from_api(artist, song)
    artist_song = artist_song_from_api_url(api_url)
    return lyrics_from('http://lyrics.wikia.com/', 'index.php', title='{0}:{1}'.format(*artist_song), action='edit')

print lyrics(*argv[1:])