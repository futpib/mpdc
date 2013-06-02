
import subprocess

from mpdc.initialize import mpd

def mpc(args):
    try:
        output = subprocess.check_output(mpd.mpc_c + args.mpc_args)
        print(output.decode().strip())
    except subprocess.CalledProcessError:
        pass

# --------------------------------
# Commands parser
# --------------------------------

def setup_args(superparser, parents=()):
    superparser.set_defaults(func=mpc)
    superparser.add_argument('mpc_args', nargs='+')

