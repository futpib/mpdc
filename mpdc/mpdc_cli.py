
import sys

from mpdc.libs.argparse_abbrev import AbbrevArgumentParser

from mpdc import (
    mpdc_playlist,
    mpdc_collections,
    mpdc_database,
    mpdc_configure,
    mpdc_mpc,
)

SUBPARSERS = (
    ('playlist', mpdc_playlist, 'Actions on current mpd playlist'),
    ('collections', mpdc_collections, 'Actions on collections'),
    (('database', 'db'), mpdc_database, 'Actions on database'),
    ('configure', mpdc_configure, 'Change, create configuration file or switch profile'),
)

MPC_COMMAND = ':'

def main():
    argparser = AbbrevArgumentParser(add_help=False)
    subparsers = argparser.add_subparsers()

    for cmd, module, help in SUBPARSERS:
        if isinstance(cmd, tuple):
            subparser = subparsers.add_parser(cmd[0], aliases=cmd[1:], help=help, priority='-')
        else:
            subparser = subparsers.add_parser(cmd, help=help, priority='-')
        module.setup_args(subparser)

    # can't find an argparse-way solution for this (mpc colon):
    mpc_parser = AbbrevArgumentParser(add_help=False)
    mpdc_mpc.setup_args(mpc_parser)
    mpc_argv = None
    argv = sys.argv[1:] # exclude executable name
    # if MPC_COMMAND passed, split argv on before it and after it.
    # First part goes to main parser, mpc part gets splitted and goes to mpc parser
    if MPC_COMMAND in argv:
        n = argv.index(MPC_COMMAND)
        mpc_argv = argv[n+1:]
        argv = argv[:n]
    # in case user mentioned MPC_COMMAND multiple times
    mpc_argv_lists = []
    while mpc_argv:
        if MPC_COMMAND in mpc_argv:
            n = mpc_argv.index(MPC_COMMAND)
            mpc_argv_lists.append(mpc_argv[:n])
            mpc_argv = mpc_argv[n+1:]
        else:
            mpc_argv_lists.append(mpc_argv)
            break

    parsed = argparser.parse_args(argv)
    if 'func' in parsed:
        parsed.func(parsed)
    elif not mpc_argv_lists:
        argparser.print_help()

    for argv in mpc_argv_lists:
        parsed_mpc = mpc_parser.parse_args(argv)
        if 'func' in parsed_mpc:
            parsed_mpc.func(parsed_mpc)
        else:
            mpc_parser.print_help()
            break


if __name__ == '__main__':
    main()
