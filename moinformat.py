#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
from MoinMoin import wikimacro, wikiutil
from MoinMoin.Page import Page
from MoinMoin.parser.wiki import Parser

from text_dokuwiki import Formatter
from MoinMoin.request import RequestCLI

request = RequestCLI()
formatter = Formatter(request)

# pages/playground\(2f\)SyntaxReference/revisions/00000001
with open('syntaxreference.txt', 'r') as f:
	text = f.read()

parser = Parser(text, request)

# this needed for macros
request.formatter = formatter

p = Page(request, "test")
formatter.setPage(p)

parser.format(formatter)
