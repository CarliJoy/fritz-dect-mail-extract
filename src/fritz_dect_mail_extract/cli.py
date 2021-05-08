"""
This is a skeleton file that can serve as a starting point for a Python
console script. To run this script uncomment the following lines in the
``[options.entry_points]`` section in ``setup.cfg``::

    console_scripts =
         fibonacci = fritz_dect_mail_extract.skeleton:run

Then run ``pip install .`` (or ``pip install -e .`` for editable mode)
which will install the command ``fibonacci`` inside your current environment.

Besides console scripts, the header (i.e. until ``_logger``...) of this file can
also be used as template for Python modules.

Note:
    This skeleton file can be safely removed if not needed!

References:
    - https://setuptools.readthedocs.io/en/latest/userguide/entry_point.html
    - https://pip.pypa.io/en/stable/reference/pip_install
"""

import argparse
import logging
import sys
from pathlib import Path

from fritz_dect_mail_extract import __version__
from fritz_dect_mail_extract.constants import ENV_NAMES
from fritz_dect_mail_extract.exceptions import ExtractionError
from fritz_dect_mail_extract.extractor import do_extract, get_server_data

__author__ = "Carli* Freudenberg"
__copyright__ = "Carli* Freudenberg"
__license__ = "MIT"

_logger = logging.getLogger(__name__)


# ---- CLI ----
# The functions defined in this section are wrappers around the main Python
# API allowing them to be called directly from the terminal as a CLI
# executable/script.


def parse_args(args):
    """Parse command line parameters

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--help"]``).

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = argparse.ArgumentParser(
        description=(
            "Extract FritzDect status mails (i.e. Energy usage) "
            "sent from FritzBox via IMAP"
        )
    )
    parser.add_argument(
        "--version",
        action="version",
        version="fritz-dect-mail-extract {ver}".format(ver=__version__),
    )
    for name, env_value in ENV_NAMES.items():
        parser.add_argument(
            f"--{name.lower()}",
            dest=name.lower(),
            help=f"IMAP {name.lower()}. Defaults to environmental variable {env_value}",
            type=str,
            default=None,
        )
    parser.add_argument(
        "target_folder", help="Path to directory to save files", type=Path
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        help="set loglevel to INFO",
        action="store_const",
        const=logging.INFO,
    )
    parser.add_argument(
        "-vv",
        "--very-verbose",
        dest="loglevel",
        help="set loglevel to DEBUG",
        action="store_const",
        const=logging.DEBUG,
    )
    return parser.parse_args(args)


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(
        level=loglevel, stream=sys.stdout, format=logformat, datefmt="%Y-%m-%d %H:%M:%S"
    )


def main(args):
    """Run command line

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--verbose", "42"]``).
    """
    args = parse_args(args)
    setup_logging(args.loglevel)
    _logger.debug("Starting extraction")
    server_data = get_server_data(args.server, args.username, args.password)
    if not args.target_folder.is_dir():
        raise ExtractionError(
            f"The target path '{args.target_folder}' is not a directory."
        )
    try:
        do_extract(server_data, args.target_folder)
    except ExtractionError as e:
        _logger.error(e)
        exit(1)


def run():
    """Calls :func:`main` passing the CLI arguments extracted from :obj:`sys.argv`

    This function can be used as entry point to create console scripts with setuptools.
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    # ^  This is a guard statement that will prevent the following code from
    #    being executed in the case someone imports this file instead of
    #    executing it as a script.
    #    https://docs.python.org/3/library/__main__.html

    # After installing your project with pip, users can also run your Python
    # modules as scripts via the ``-m`` flag, as defined in PEP 338::
    #
    #     python -m fritz_dect_mail_extract.skeleton 42
    #
    run()
