# coding: utf-8
import sys
import shlex
import argparse
import subprocess

from mpdc.initialize import mpd
from mpdc.libs.parser import parser


# --------------------------------
# Program functions
# --------------------------------

def add(args):
    songs = list(parser.parse(args.collection))
    if songs:
        mpd.add(songs)


def addp(args):
    songs = list(parser.parse(args.collection))
    if songs:
        mpd.add(songs)
        mpd.play_file(mpd.first_lately_added_song)


def insert(args):
    songs = list(parser.parse(args.collection))
    if songs:
        mpd.insert(songs)


def remove(args):
    songs = list(parser.parse(args.collection))
    if songs:
        mpd.remove(songs)


def keep(args):
    songs = parser.parse(args.collection)
    remove_songs = [s for s in mpd.get_playlist_songs() if s not in songs]
    if remove_songs:
        mpd.remove(remove_songs)


def replace(args):
    songs = list(parser.parse(args.collection))
    mpd.clear()
    if songs:
        mpd.add(songs)


def play(args):
    songs = parser.parse(args.collection)
    if songs:
        positions = mpd.get_playlist_positions()
        try:
            first_matched_song = next(s for s in positions if s in songs)
        except StopIteration:
            pass
        else:
            mpd.play(positions[first_matched_song][0])


def clear(args):
    mpd.clear()


def crop(args):
    mpd.crop()


# --------------------------------
# Commands parser
# --------------------------------

def setup_args(superparser):
    subparsers = superparser.add_subparsers()

    add_p = subparsers.add_parser('add', priority='-')
    add_p.add_argument('collection')
    add_p.set_defaults(func=add)

    addp_p = subparsers.add_parser('addp', priority='-')
    addp_p.add_argument('collection')
    addp_p.set_defaults(func=addp)

    insert_p = subparsers.add_parser('insert', priority='-')
    insert_p.add_argument('collection')
    insert_p.set_defaults(func=insert)

    replace_p = subparsers.add_parser('replace', priority='-')
    replace_p.add_argument('collection')
    replace_p.set_defaults(func=replace)

    remove_p = subparsers.add_parser('remove', aliases=['rm'], priority='-')
    remove_p.add_argument('collection')
    remove_p.set_defaults(func=remove)

    keep_p = subparsers.add_parser('keep', priority='-')
    keep_p.add_argument('collection')
    keep_p.set_defaults(func=keep)

    play_p = subparsers.add_parser('play', priority='-')
    play_p.add_argument('collection')
    play_p.set_defaults(func=play)

    clear_p = subparsers.add_parser('clear', priority='-')
    clear_p.set_defaults(func=clear)

    crop_p = subparsers.add_parser('crop', priority='-')
    crop_p.set_defaults(func=crop)
