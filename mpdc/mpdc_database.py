# coding: utf-8
import operator
import argparse
from collections import Counter

from mpdc.initialize import mpd, collectionsmanager, lastfm, cache, colors
from mpdc.libs.utils import repr_tags, info, warning, colorize
from mpdc.libs.parser import parser


# --------------------------------
# Program functions
# --------------------------------

def update(args):
    mpd.mpdclient.update()
    mpd.update_cache()
    cache.write('playlists', mpd.get_stored_playlists_info())
    collectionsmanager.feed(force=True)
    collectionsmanager.update_cache()


def check(args):
    songs = []
    song_tags_dict = mpd.get_all_songs_tags()
    for song in parser.parse(' '.join(args.collection)):
        tags = song_tags_dict[song]
        missing_tags = [tag for tag, value in tags.items() if not value]
        if missing_tags:
            warning(colorize(song, colors[0]))
            print('missing tag(s): ' + colorize(', '.join(missing_tags),
                                                colors[1 % len(colors)]))
        else:
            songs.append(tuple(sorted(tags.items())))
    duplicates = [dict(tags) for tags, nb in Counter(songs).items() if nb > 1]
    if duplicates:
        print('\nConflict(s) found:')
        print('------------------')
        for tags in duplicates:
            warning('Conflict with tags ' + colorize(repr_tags([tags['artist'],
                                                               tags['album'],
                                                               tags['title'],
                                                               tags['track']]),
                                                     colors[1 % len(colors)]))
            # necessary because MPDHelper's get_all_songs_tags falls back
            # to artist if albumartist is empty, while it's find_multiple
            # (mpdclient.find in fact) does not
            # not a solution really, so FIXME
            tags.pop('albumartist')
            files_matched = mpd.find_multiple(**tags)
            print('files matched:\n' + colorize('\n'.join(files_matched),
                                                colors[0]))

def lastfm_update_artists(args):
    tags = lastfm.artists_tags
    artists = sorted(mpd.list_artists())
    extra_artists = [artist for artist in tags if artist not in artists]
    info('{} extra artist(s)'.format(len(extra_artists)))
    for artist in extra_artists:
        del tags[artist]
    if tags:
        missing_artists = [artist for artist in artists if artist not in tags]
    else:
        missing_artists = artists
    info('{} missing artist(s)'.format(len(missing_artists)))
    for artist in missing_artists:
        print('Fetching {}'.format(artist))
        tags[artist] = lastfm.get_artist_tags(artist, update=True)
    cache.write('lastfm_artists_tags', tags)


def lastfm_update_albums(args):
    tags = lastfm.albums_tags
    albums = sorted(mpd.list_albums(), key=operator.itemgetter(1))
    extra_albums = [album for album in tags if album not in albums]
    info('{} extra album(s)'.format(len(extra_albums)))
    for album in extra_albums:
        del tags[album]
    if tags:
        missing_albums = [album for album in albums if album not in tags]
    else:
        missing_albums = albums
    info('{} missing album(s)'.format(len(missing_albums)))
    for album, artist in missing_albums:
        print('Fetching {} / {}'.format(artist, album))
        tags[(album, artist)] = lastfm.get_album_tags(album,
                                                      artist, update=True)
    cache.write('lastfm_albums_tags', tags)

def lastfm_update_tracks(args):
    known_tracks = set(lastfm.tracks_tags)
    all_tracks = set(mpd.list_tracks())
    #unneeded_tracks = known_tracks - all_tracks
    #for track in unneeded_tracks:
        #del lastfm.tracks_tags[album]
    missing_tracks = all_tracks - known_tracks
    info('{} missing track(s)'.format(len(missing_tracks)))
    for track, artist in missing_tracks:
        print('Fetching {} / {}'.format(artist, track))
        lastfm.tracks_tags[(track, artist)] = lastfm.get_track_tags(track,
                                                      artist, update=True)
    cache.write('lastfm_tracks_tags', lastfm.tracks_tags)

def lastfm_get_artist_tags(args):
    tracks = parser.parse(' '.join(args.collection))
    artists = set()
    for track in tracks:
        albumartist, artist = mpd.get_tags(track, tags_list=['albumartist','artist'])
        if artist:
            artists.add(artist)
        if albumartist:
            artists.add(albumartist)
    for artist in artists:
        if artist in lastfm.artists_tags and lastfm.artists_tags[artist]:
            print(':: %s:' % artist)
            print(', '.join(lastfm.artists_tags[artist]))

def lastfm_get_album_tags(args):
    tracks = parser.parse(' '.join(args.collection))
    albums_albumartists = set()
    for track in tracks:
        album, albumartist = mpd.get_tags(track, tags_list=['album','albumartist'])
        if album and albumartist:
            albums_albumartists.add((album, albumartist))
    for item in albums_albumartists:
        if item in lastfm.albums_tags and lastfm.albums_tags[item]:
            album, albumartist = item
            print(':: %s — %s:' % (albumartist, album))
            print(', '.join(lastfm.albums_tags[item]))

def lastfm_get_track_tags(args):
    tracks = parser.parse(' '.join(args.collection))
    tracks_artists = set()
    for trackfile in tracks:
        trackname, artist, albumartist = mpd.get_tags(trackfile, tags_list=['title','artist','albumartist'])
        if trackname and albumartist:
            tracks_artists.add((trackname, albumartist))
        if trackname and artist:
            tracks_artists.add((trackname, artist))
    for item in tracks_artists:
        if item in lastfm.tracks_tags and lastfm.tracks_tags[item]:
            track, artist = item
            print(':: %s — %s:' % (artist, track))
            print(', '.join(lastfm.tracks_tags[item]))


# --------------------------------
# Commands parser
# --------------------------------

def setup_args(superparser):
    subparsers = superparser.add_subparsers()

    update_p = subparsers.add_parser('update', priority='-')
    update_p.set_defaults(func=update)

    check_p = subparsers.add_parser('check', priority='-')
    check_p.add_argument('collection', nargs='*')
    check_p.set_defaults(collection=['all'], func=check)

    lastfm_p = subparsers.add_parser('lastfm', priority='-')
    lastfm_sp = lastfm_p.add_subparsers()

    lastfm_get_p = lastfm_sp.add_parser('get', priority='-')
    lastfm_get_sp = lastfm_get_p.add_subparsers()

    lastfm_get_artist_tags_p = lastfm_get_sp.add_parser('artisttags', priority='-')
    lastfm_get_artist_tags_p.add_argument('collection', nargs='+')
    lastfm_get_artist_tags_p.set_defaults(func=lastfm_get_artist_tags)

    lastfm_get_album_tags_p = lastfm_get_sp.add_parser('albumtags', priority='-')
    lastfm_get_album_tags_p.add_argument('collection', nargs='+')
    lastfm_get_album_tags_p.set_defaults(func=lastfm_get_album_tags)

    lastfm_get_track_tags_p = lastfm_get_sp.add_parser('tracktags', priority='-')
    lastfm_get_track_tags_p.add_argument('collection', nargs='+')
    lastfm_get_track_tags_p.set_defaults(func=lastfm_get_track_tags)

    lastfm_update_p = lastfm_sp.add_parser('update', priority='-')
    lastfm_update_sp = lastfm_update_p.add_subparsers()

    lastfm_update_artists_p = lastfm_update_sp.add_parser('artists', priority='-')
    lastfm_update_artists_p.set_defaults(func=lastfm_update_artists)

    lastfm_update_albums_p = lastfm_update_sp.add_parser('albums', priority='-')
    lastfm_update_albums_p.set_defaults(func=lastfm_update_albums)

    lastfm_update_tracks_p = lastfm_update_sp.add_parser('tracks', priority='-')
    lastfm_update_tracks_p.set_defaults(func=lastfm_update_tracks)

