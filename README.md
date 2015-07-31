Complete MoinMoin to DokuWiki converter
=======================================

Uses native MoinMoin modules to handle converting and translating paths.
Converts also page history and edit-log.

http://www.dokuwiki.org/tips:moinmoin2doku

Tested with MoinMoin 1.5 and DokuWiki 2012-09-10 releases

You need to run this on host where both MoinMoin and DokuWiki are configured,
it uses current configuration from both wikis.

Edit doku.php if your DokuWiki installation is other than /usr/share/dokuwiki

To convert moinmoin all pages with history, invoke:
```
$ ./moin2doku.py -a -d /var/lib/dokuwiki
```

To convert single page (FrontPage):
```
$ ./moin2doku.py -F moinmoin/data/pages/FrontPage -d out
```

You should invoke `bin/indexer.php` after conversion to make all pages are indexed.

and ensure ownership of files is correct:
(`www-data:www-data` being your uid/gid webserver runs):
```
# chown -R www-data:www-data /var/lib/dokuwiki/pages/*
# chown -R www-data:www-data /var/lib/dokuwiki/media/*
```
additionally, depending on your configuration, you may need to gzip the attic pages.

History
=======

version 0.1 (2010-02)
-------------------

Slim Gaillard, based on the "extended python" convert.py script here:
https://www.dokuwiki.org/tips:moinmoin2doku?rev=1297006559#extended_python

version 0.2 (2011)
----------------

Elan Ruusamäe, moved to github, track history there
https://github.com/glensc/moin2doku

version 1.0 (2012)
----------------

Complete moinmoin to dokuwiki converter, uses native moinmoin code to handle
converting and translating paths. Converts also page history and edit-log.

This marks the project "done", I will no longer develop it or support it, as I got my conversion done. However, I do accept patches (pull requests) to sane amount.

I put repo online so others have better starting point than I did.
