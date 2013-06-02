
import sys as _sys

from argparse import *
from argparse import _SubParsersAction


PRIORITY_AUTO_MAX = '+'
PRIORITY_AUTO_MIN = '-'

class _AbbrevSubparsersAction(_SubParsersAction):

    def add_parser(self, *args, **kwargs):
        """
        Introduced arguments:
            - priority=None -- if not None, makes parser accept abbreviations
                for created subparser and sets it's priority.
                None value disables abbreviation (default).
                Use '{max}' or '{min}' to automatically set highest
                or least priority in the subparsers group.
        """.format(max=PRIORITY_AUTO_MAX, min=PRIORITY_AUTO_MIN)

        priority = kwargs.pop('priority', None)
        aliases = kwargs.get('aliases', ())
        parser = super().add_parser(*args, **kwargs)

        if priority is not None:
            if priority in (PRIORITY_AUTO_MAX, PRIORITY_AUTO_MIN):
                minmax = max if priority == PRIORITY_AUTO_MAX else min
                ps = [p.priority for (_, p) in self._name_parser_map.items()]
                ps = filter(lambda p: p is not None, ps)
                ps = list(ps)
                if not ps:
                    priority = 0
                else:
                    priority = minmax(ps) + minmax(-1, 1)
            parser.priority = priority
        parser.aliases = aliases
        return parser

class AbbrevArgumentParser(ArgumentParser):
    """
    ArgumentParser with subparsers abbreviation support.
    For example 'update' can be abbreviated as 'upd' or 'u',
    if set to be abbreviated and has priority over other arguments.
    Aliases can only match comletely or not match at all
    (alias can't be abbreviated).
    """

    def __init__(self, *a, **ka):
        super().__init__(*a, **ka)
        # override default parsers class
        self.register('action', 'parsers', _AbbrevSubparsersAction)
        self.priority = None
        self.aliases = ()

    def parse_known_args(self, args=None, *a, **ka):
        if args is None:
            args = _sys.argv[1:]
        else:
            args = list(args)

        if args:
            first_arg = args[0]
            subs = self._get_subparsers().items()
            subs = [(c, p) for (c, p) in subs if p.priority is not None]
            subs = sorted(subs, key=lambda x: x[1].priority, reverse=True)
            for cmd, sub in subs:
                if cmd in sub.aliases and cmd != first_arg:
                    # no abbreviation for aliases
                    # i.e. do not let higher priority aliases dim lower priority abbreviations
                    continue
                if cmd.startswith(first_arg):
                    # replace abbreviation with full command,
                    # so argparse does not notice
                    args[0] = cmd
                    break
        return super().parse_known_args(args, *a, **ka)

    def _get_subparsers(self):
        result = {}
        if self._subparsers and self._subparsers._actions:
            for action in self._subparsers._actions:
                if action.choices:
                    result.update(action.choices)
        return result


