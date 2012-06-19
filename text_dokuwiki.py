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

class Formatter(FormatterBase):
    """
        Send Dokuwiki formatted data.
    """

    hardspace = '&nbsp;'

    def __init__(self, request, **kw):
        apply(FormatterBase.__init__, (self, request), kw)
        self._current_depth = 1
        self._base_depth = 0
        self.in_pre = 0
        self._text = None # XXX does not work with links in headings!!!!!

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
            return '[[%s|%s' % (interwiki, pagename)
        else:
            return ']]'

    def url(self, on, url='', css=None, **kw):
        if css:
            str = ' class="%s"' % css
        else:
            str = ''
        return ('<jump href="%s"%s>' % (self._escape(url), str), '</jump>') [not on]

    def attachment_link(self, url, text, **kw):
        return '{{%s|%s}}' % (url, text)

    def attachment_image(self, url, **kw):
        return '{{%s|}' % (url,)

    def attachment_drawing(self, url, text, **kw):
        return '{{%s|%s}}' % (url, text)

    def text(self, text, **kw):
        self._did_para = 0
        if self._text is not None:
            self._text.append(text)
        return text

    def rule(self, size=0, **kw):
		# size not supported
		return '----\n'

    def icon(self, type):
        return '<icon type="%s" />' % type

    def strong(self, on, **kw):
        return ['**', '**'][not on]

    def emphasis(self, on, **kw):
        return ['//', '//'][not on]

    def highlight(self, on, **kw):
        return ['**', '**'][not on]

    def number_list(self, on, type=None, start=None, **kw):
        result = ''
        if self.in_p:
            result = self.paragraph(0)
        return result + ['<ol>', '</ol>\n'][not on]

    def bullet_list(self, on, **kw):
        result = ''
        if self.in_p:
            result = self.paragraph(0)
        return result + ['<ul>', '</ul>\n'][not on]

    def listitem(self, on, **kw):
        return ['<li>', '</li>\n'][not on]

    def code(self, on, **kw):
        return ['<code>', '</code>'][not on]

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
        return result + ['<file>', '</file>'][not on]

    def paragraph(self, on, **kw):
        FormatterBase.paragraph(self, on)
        return ['', '\n\n'][not on]

    def linebreak(self, preformatted=1):
        return ['\n', '\\\n'][not preformatted]

    def heading(self, on, depth, **kw):
        # heading depth reversed in dokuwiki
        heading_depth = 7 - depth

        if on:
            return u'%s ' % (u'=' * heading_depth)
        else:
            return u' %s' % (u'=' * heading_depth)

    def table(self, on, attrs={}, **kw):
        return ['<table>', '</table>'][not on]

    def table_row(self, on, attrs={}, **kw):
        return ['<tr>', '</tr>'][not on]

    def table_cell(self, on, attrs={}, **kw):
        return ['<td>', '</td>'][not on]

    def anchordef(self, id):
        return '<anchor id="%s"/>' % id

    def anchorlink(self, on, name='', **kw):
        id = kw.get('id',None)
        extra = ''
        if id:
            extra = ' id="%s"' % id
        return ('<link anchor="%s"%s>' % (name, extra) ,'</link>') [not on]

    def underline(self, on, **kw):
        return self.strong(on) # no underline in StyleBook

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
        attrs = {'src': src}
        for key, value in kw.items():
            if key in valid_attrs:
                attrs[key] = value
        return apply(FormatterBase.image, (self,), attrs) + '</img>'

    def code_area(self, on, code_id, code_type='code', show=0, start=-1, step=-1):
        return ('<codearea id="%s">' % code_id, '</codearea')[not on]

    def code_line(self, on):
        return ('<codeline>', '</codeline')[not on]

    def code_token(self, on, tok_type):
        return ('<codetoken type="%s">' % tok_type, '</codetoken')[not on]

    def code_line(self, on):
        return ('<codeline>', '</codeline')[not on]

    def code_token(self, on, tok_type):
        return ('<codetoken type="%s">' % tok_type, '</codetoken')[not on]

