=======================
fritz-dect-mail-extract
=======================


Extract FritzDect status mails (i.e. Energy usage) sent from FritzBox via IMAP.


Description
===========

Provides the command ``dectmailextract``::

    usage: dectmailextract [-h] [--version] [--password PASSWORD] [--username USERNAME] [--server SERVER] [-v] [-vv] target_folder

    Extract FritzDect status mails (i.e. Energy usage) sent from FritzBox via IMAP

    positional arguments:
      target_folder        Path to directory to save files

    optional arguments:
      -h, --help           show this help message and exit
      --version            show program's version number and exit
      --password PASSWORD  IMAP password. Defaults to environmental variable DECT_MAIL_EXTRACT_PASSWORD
      --username USERNAME  IMAP username. Defaults to environmental variable DECT_MAIL_EXTRACT_USER
      --server SERVER      IMAP server. Defaults to environmental variable DECT_MAIL_EXTRACT_SERVER
      -v, --verbose        set loglevel to INFO
      -vv, --very-verbose  set loglevel to DEBUG



.. _pyscaffold-notes:

Note
====

This project has been set up using PyScaffold 4.0.1. For details and usage
information on PyScaffold see https://pyscaffold.org/.
