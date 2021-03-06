# coding: utf-8
import json
import time
import socket
import urllib.parse
import urllib.error
import urllib.request
from operator import itemgetter
from datetime import datetime, timedelta

from mpdc.initialize import cache
from mpdc.libs.utils import similarity, warning


class LastfmHelper:

    api_key = '4e0ccb62907dedff2c1445d752236a2e'
    url = 'http://ws.audioscrobbler.com/2.0/?api_key={}&format=json'. \
          format(api_key)
    delay = timedelta(0, 1)
    last_request = datetime.now() - delay

    methods = {
        'artist_tags': '&method=artist.gettoptags&artist={artist}'
                       '&autocorrect=1',
        'album_tags': '&method=album.gettoptags&artist={artist}'
                      '&album={album}&autocorrect=1',
        'track_tags': '&method=track.gettoptags&artist={artist}'
                      '&track={track}&autocorrect=1',
    }

    # all tags containing this considered bad
    bad_substrings = ['beaut', 'awesome', 'epic', 'masterpiece', 'favorite',
                      'favourite', 'recommend', 'fuckin',
                      ':3', ':d',
                     ]
    # all tags containing this with spaces around considered bad
    # i.e. 'foo i bar', 'i qweqwe', 'ololo i' and 'i' will be dropped
    bad_words = ['i', 'my', 'you', 'it', 'love', 'me', 'nice', 'sex', 'sexy',
                 'fav',
                ]
    # drop all tags below this count
    min_count = 3

    min_similarity = 0.30

    def __init__(self):
        self.timeout = 0
        self.artists_tags = cache.read('lastfm_artists_tags')
        self.albums_tags = cache.read('lastfm_albums_tags')
        self.tracks_tags = cache.read('lastfm_tracks_tags')

        if not (self.artists_tags and self.albums_tags and self.tracks_tags):
            warning('You should update the LastFM database')

    def request(self, method, **args):
        if self.last_request + self.delay > datetime.now():
            time_to_sleep = self.last_request + self.delay - datetime.now()
            time.sleep(time_to_sleep.total_seconds())

        args_ = {key: urllib.parse.quote(value) for key, value in args.items()}
        url = self.url + self.methods[method].format(**args_)

        try:
            raw_json = urllib.request.urlopen(url, timeout=15).read()
        except (socket.timeout, urllib.error.URLError):
            if self.timeout == 3:
                warning('Cannot send the request after 4 attempts')
                self.timeout = 0
                return None
            self.timeout += 1
            warning('Time out... attempt n°' + str(self.timeout + 1))
            return self.request(method, **args)
        else:
            self.last_request = datetime.now()
            response = json.loads(raw_json.decode('utf-8'))
            if 'error' in response:
                warning('LastFM error: {}'.format(response['message']))
                return None
            self.timeout = 0
            return response

    def sanitize_tags(self, tags):
        if not isinstance(tags, list):
            tags = [tags]
        tags_sanitized = {}
        for tag in tags:
            if any(bad not in tag['name'].lower() for bad in self.bad_substrings) \
            or any(bad not in tag['name'].split() for bad in self.bad_words) \
            or int(tag['count']) < min_count:
                continue
            tags_sanitized[tag['name'].lower()] = int(tag['count'])
        return tags_sanitized

    def get_artist_tags(self, artist, update=False):
        if not update:
            if artist in self.artists_tags:
                return self.artists_tags[artist]
            return {}
        else:
            data = self.request('artist_tags', artist=artist)
            if data is not None:
                if 'tag' in data.get('toptags', {}):
                    return self.sanitize_tags(data['toptags']['tag'])
            return {}

    def get_album_tags(self, album, artist, update=False):
        if not update:
            if (album, artist) in self.albums_tags:
                return self.albums_tags[(album, artist)]
            return {}
        else:
            data = self.request('album_tags', artist=artist, album=album)
            if data is not None:
                if 'tag' in data.get('toptags', {}):
                    return self.sanitize_tags(data['toptags']['tag'])
            return {}

    def get_track_tags(self, track, artist, update=False):
        if not update:
            if (track, artist) in self.albums_tags:
                return self.tracks_tags[(track, artist)]
            return {}
        else:
            data = self.request('track_tags', track=track, artist=artist)
            if data is not None:
                if 'tag' in data.get('toptags', {}):
                    return self.sanitize_tags(data['toptags']['tag'])
            return {}

    def search_artists(self, pattern):
        for artist, tags in self.artists_tags.items():
            if any(pattern in tag for tag in tags):
                yield artist

    def find_artists(self, pattern):
        for artist, tags in self.artists_tags.items():
            if pattern in tags:
                yield artist

    def search_albums(self, pattern):
        for album, tags in self.albums_tags.items():
            if any(pattern in tag for tag in tags):
                yield album

    def find_albums(self, pattern):
        for album, tags in self.albums_tags.items():
            if pattern in tags:
                yield album

    def search_tracks(self, pattern):
        for track, tags in self.tracks_tags.items():
            if any(pattern in tag for tag in tags):
                yield track

    def find_tracks(self, pattern):
        for track, tags in self.tracks_tags.items():
            if pattern in tags:
                yield track

    def get_similar_artists(self, query):
        if not self.artists_tags:
            warning('You should update the LastFM database')
            return
        scores = {}
        for artist, tags in self.artists_tags.items():
            if tags:
                score = similarity(tags, query)
                if score > LastfmHelper.min_similarity:
                    scores[artist] = score
        scores_desc = sorted(scores.items(), key=itemgetter(1), reverse=True)
        for artist in scores_desc:
            yield artist

    def get_similar_albums(self, query):
        scores = {}
        for (album, artist), tags in self.albums_tags.items():
            if tags:
                score = similarity(tags, query)
                if score > LastfmHelper.min_similarity:
                    scores[(album, artist)] = score
        scores_desc = sorted(scores.items(), key=itemgetter(1), reverse=True)
        for album in scores_desc:
            yield album
