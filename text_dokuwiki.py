# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Dokuwiki Formatter

    @copyright: 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>
    @copyright: 2011-2012 Elan Ruusamäe <glen@delfi.ee>
    @license: GNU GPL, see COPYING for details.
"""

from xml.sax import saxutils
from MoinMoin.formatter.base import FormatterBase
from MoinMoin import config
from MoinMoin.Page import Page
from types import *

# TODO: let base class MoinMoin/formatter/base.py handle not implemented methods

class Formatter(FormatterBase):
    """
        Send Dokuwiki formatted data.
    """

    hardspace = '&nbsp;'
#    hardspace = ' '

    def __init__(self, request, **kw):
        apply(FormatterBase.__init__, (self, request), kw)
        self._current_depth = 1
        self._base_depth = 0
        self.in_pre = 0
        self.in_table = 0
        self._text = None # XXX does not work with links in headings!!!!!

        self.list_depth = 0
        self.list_type = ' '
        # dokuwiki namespace spearator, ':' or '/', see 'useslash' config
        self.ns_sep = '/';

    def _escape(self, text, extra_mapping={"'": "&apos;", '"': "&quot;"}):
        return saxutils.escape(text, extra_mapping)

    def startDocument(self, pagename):
        encoding = config.charset
        return '<?xml version="1.0" encoding="%s"?>\n<s1 title="%s">' % (
            encoding, self._escape(pagename))

    def endDocument(self):
        result = ""
        while self._current_depth > 1:
            result += "</s%d>" % self._current_depth
            self._current_depth -= 1
        return result + '</s1>'

    def lang(self, on, lang_name):
        return ('<div lang="">' % lang_name, '</div>')[not on]

    def sysmsg(self, on, **kw):
        return ('<sysmsg>', '</sysmsg>')[not on]

    def rawHTML(self, markup):
        return '<html>' + markup + '</html>'

    def pagelink(self, on, pagename='', page=None, **kw):
        apply(FormatterBase.pagelink, (self, on, pagename, page), kw)
        if page is None:
            page = Page(self.request, pagename, formatter=self)
        return page.link_to(self.request, on=on, **kw)

    def interwikilink(self, on, interwiki='', pagename='', **kw):
        if on:
            return '[[%s%s%s|' % (interwiki, self.ns_sep, pagename)
        else:
            return ']]'

    def url(self, on, url='', css=None, **kw):
        return ('[[%s|' % (self._escape(url)), ']]') [not on]

    def attachment_link(self, url, text, **kw):
        return '{{%s|%s}}' % (url, text)

    def attachment_image(self, url, **kw):
        return '{{%s|}}' % (url,)

    def attachment_drawing(self, url, text, **kw):
        return '{{%s|%s}}' % (url, text)

    def text(self, text, **kw):
        self._did_para = 0
        if self._text is not None:
            self._text.append(text)
        return text

    def rule(self, size=0, **kw):
        # size not supported
        if size >= 4:
            return '----\n'
        else:
            return '-' * size + '\n'

    def icon(self, type):
        return '<icon type="%s" />' % type

    def strong(self, on, **kw):
        return ['**', '**'][not on]

    def emphasis(self, on, **kw):
        return ['//', '//'][not on]

    def highlight(self, on, **kw):
        return ['**', '**'][not on]

    def number_list(self, on, type=None, start=None, **kw):
        # list type not supported
        if on:
            self.list_depth += 1
            self.list_type = '-'
        else:
            self.list_depth -= 1
            self.list_type = ' '

        return ['', '\n'][on]

    def bullet_list(self, on, **kw):
        if on:
            self.list_depth += 1
            self.list_type = '*'
        else:
            self.list_depth -= 1
            self.list_type = ' '

        return ['', '\n'][on]

    def listitem(self, on, **kw):
        # somewhy blockquote uses "listitem" call
        return [(' ' * self.list_depth * 2) + self.list_type + ' ', '\n'][not on]

    def code(self, on, **kw):
        """ `typewriter` or {{{typerwriter}}, for code blocks i hope codeblock works """
        return ["''", "''"][not on]

    def sup(self, on, **kw):
        return ['<sup>', '</sup>'][not on]

    def sub(self, on, **kw):
        return ['<sub>', '</sub>'][not on]

    def strike(self, on, **kw):
        return ['<del>', '</del>'][not on]

    def preformatted(self, on, **kw):
        FormatterBase.preformatted(self, on)
        result = ''
        if self.in_p:
            result = self.paragraph(0)
        return result + ['<file>', '</file>\n'][not on]

    def paragraph(self, on, **kw):
        FormatterBase.paragraph(self, on)
        if self.in_table or self.list_depth:
            return ''
        return ['', '\n\n'][not on]

    def linebreak(self, preformatted=1):
        return ['\n', '\\\n'][not preformatted]

    def heading(self, on, depth, **kw):
        # heading depth reversed in dokuwiki
        heading_depth = 7 - depth

        if on:
            return u'%s ' % (u'=' * heading_depth)
        else:
            return u' %s\n' % (u'=' * heading_depth)

    def table(self, on, attrs={}, **kw):
        if on:
            self.in_table = 1
        else:
            self.in_table = 0
        return ''

    def table_row(self, on, attrs={}, **kw):
        return ['\n', '|'][not on]

    def table_cell(self, on, attrs={}, **kw):
        return ['|', ''][not on]

    def anchordef(self, id):
        # not supported
        return ''

    def anchorlink(self, on, name='', **kw):
        # kw.id not supported, we hope the anchor matches existing heading on page
        return ('[[#', ']]') [not on]

    def underline(self, on, **kw):
        return ['__', '__'][not on]

    def definition_list(self, on, **kw):
        result = ''
        if self.in_p:
            result = self.paragraph(0)
        return result + ['<gloss>', '</gloss>'][not on]

    def definition_term(self, on, compact=0, **kw):
        return ['<label>', '</label>'][not on]

    def definition_desc(self, on, **kw):
        return ['<item>', '</item>'][not on]

    def image(self, src=None, **kw):
        valid_attrs = ['src', 'width', 'height', 'alt', 'title']

        url = src
        if '?' in url:
            url += '&'
        else:
            url += '?'

        attrs = {}
        for key, value in kw.items():
            if key in valid_attrs:
                attrs[key] = value

        # TODO: finish this
        if attrs.has_key('width'):
            url += attrs['width']

        return '{{' + url + '}}'

    def code_area(self, on, code_id, code_type='code', show=0, start=-1, step=-1):
        syntax = ''
        # switch for Python: http://simonwillison.net/2004/may/7/switch/
        try:
            syntax = {
                'ColorizedPython': 'python',
                'ColorizedCPlusPlus': 'cpp',
            }[code_type]
        except KeyError:
            pass

        return ('<code %s>' % syntax , '</code>')[not on]

    def code_line(self, on):
        return ('', '\n')[on]

    def code_token(self, on, tok_type):
        # not supported
        return ''

    def comment(self, text):
        # real comments (lines with two hash marks)
        if text[0:2] == '##':
            return "/* %s */" % text[2:]

        # some kind of macro
        tokens = text.lstrip('#').split(None, 1)
        if tokens[0] in ('language'):
            return ''

        if tokens[0] == 'acl':
            # TODO: fill acl.auth.php
            return  ''

        if tokens[0] == 'pragma':
            return "/* pragma: %s */" % " ".join(tokens[1:])

        return "/* %s */" % text.lstrip('#')

    def macro(self, macro_obj, name, args):
        def email(args):
            mail = args.replace(' AT ', '@')
            mail = mail.replace(' DOT ', '.')
            return '[[%s|%s]]' % (mail, args)

        try:
            lookup = {
                'BR' : '\\\\',
                'MailTo' : email,
                'GetText' : args,
            }[name]
        except KeyError:
            lookup = '/* UndefinedMacro: %s(%s) */' % (name, args)

        if type(lookup) == FunctionType:
            text = lookup(args)
        else:
            text = lookup
        return text
