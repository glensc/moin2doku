#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
from MoinMoin import wikimacro, wikiutil
from MoinMoin.Page import Page
from MoinMoin.parser.wiki import Parser

from text_dokuwiki import Formatter
from MoinMoin.request import RequestCLI

request = RequestCLI()
formatter = Formatter(request)

text = """
= Headers =
== Header 2 ==
=== Header 3 ===
==== Header 4 ====
===== Header 5 =====
"""

parser = Parser(text, request)

# this needed for macros
request.formatter = formatter

p = Page(request, "test")
formatter.setPage(p)

parser.format(formatter)
