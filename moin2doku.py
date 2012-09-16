#!/usr/bin/python
# -*- coding: utf-8 -*-
# Setup VIM: ex: et ts=2 sw=2 :
#
# Main Script doing the conversion.
# See README for details.
#
# Author: Elan Ruusamäe <glen@pld-linux.org>

import sys, os, os.path, re
import getopt
from shutil import copyfile, copystat
from os import listdir
from os.path import isdir, basename
from doku import DokuWiki

def check_dirs(moin_pages_dir, output_dir):
  if not isdir(moin_pages_dir):
    print >> sys.stderr, "MoinMoin pages directory doesn't exist!"
    sys.exit(1)

  if not isdir(output_dir):
    print >> sys.stderr, "Output directory doesn't exist!"
    sys.exit(1)

def get_path_names(moin_pages_dir):
  items = listdir(moin_pages_dir)
  pathnames = []

  for item in items:
      item = os.path.join(moin_pages_dir, item)
      if isdir(item):
          pathnames.append(item)

  return pathnames

def readfile(filename):
  return file(filename, 'r').readlines()

def writefile(filename, content, overwrite=False):
  dir = os.path.split(filename)[0]
  if not isdir(dir):
    os.makedirs(dir);

  if os.path.exists(filename) and overwrite == False:
    raise OSError, 'File already exists: %s' % filename

  f = file(filename, 'w')
  f.writelines([it.rstrip() + '\n' for it in content if it])
  f.close()

def get_current_revision(pagedir):
  rev_dir = os.path.join(pagedir, 'revisions')
  # try "current" file first
  f = os.path.join(pagedir, 'current')
  if os.path.exists(f):
    rev = readfile(f)[0].rstrip()
    try:
      int(rev)
    except ValueError, e:
      raise OSError, 'corrupted: %s: %s' % (f, rev)
  else:
    if not isdir(rev_dir):
      return None
    revisions = listdir(rev_dir)
    revisions.sort()
    rev = revisions[-1]

  print "%s rev: %s" % (pagedir, rev)
  f = os.path.join(rev_dir, rev)
  if not os.path.exists(f):
    # deleted pages have '00000002' in current, and no existing file
    return None

  return f

# pagedir = MoinMoin page dir
# ns = DokuWiki namespace where attachments to copy
def copy_attachments(pagedir, ns):
  dir = os.path.join(pagedir, 'attachments')
  if not isdir(dir):
    return

  attachment_dir = dw.mediaFn(ns)
  if not isdir(attachment_dir):
    os.makedirs(attachment_dir);

  attachments = listdir(dir)
  for attachment in attachments:
    src = os.path.join(dir, attachment)
    dst = dw.mediaFn(dw.cleanID("%s/%s" % (ns, attachment)))
    copyfile(src, dst)
    copystat(src, dst)

# convert page markup
# pagename: name of current page (MoinMoin name)
# content: page content (MoinMoin markup)
def convert_markup(pagename, content):
  """
  convert page markup
  """
  namespace = ':'
#  for i in range(0, len(filename) - 1):
#    namespace += filename[i] + ':'

  # http://www.pld-linux.org/SyntaxReference
  regexp = (
  ('\[\[TableOfContents.*\]\]', ''),          # remove
  ('\[\[BR\]\]$', ''),                        # newline at end of line - remove
  ('\[\[BR\]\]', '\n'),                       # newline
  ('#pragma section-numbers off', ''),        # remove
  ('^##.*?\\n', ''),                          # comments: remove
  ('^#(pragma|format|redirect|refresh|language|acl)(.*?)\n', ''), # remove all
  ('^#deprecated(.*)\n', '<note warning>This page is deprecated<note>\n'),	# deprecated

  # Other elements
      # break
  ('(<<BR>>)|(\[\[BR]])', '\\\\ '),

      # horizontal line
  ('^\s*-{4,}\s*$', '----\n'),
  # Macros and another foolish - simply remove
      # macros
  ('<<.+?>>', ''),
  ('\[\[Anchor\(\w+\)\]\]', ''),
  ('\[\[(PageCount|RandomPage)\]\]', ''),

#    ('\["', '[['),                              # internal link open
#    ('"\]', ']]'),                              # internal link close
  # internal links
  ('\[:(.+)\]',  '[[\\1]]'),
  # TODO: handle more depths
  ('\[\[(.*)/(.*)\]\]',  'B[[\\1:\\2]]'),
  # wiki:xxx
  ('\[wiki:([^\s]+)\s+(.+)]',  '[[\\1|\\2]]'),
  ('wiki:([^\s]+)\s+(.+)',  '[[\\1|\\2]]'),
  ('wiki:([^\s]+)',  '[[\\1]]'),
  ('(\[\[.+\]\]).*\]', '\\1'),

  # web link without title
  ('\[((?:http|https|file)[^\s]+)\]', '[[\\1]]'),
  # web link with title
  ('\[((?:http|https|file)[^\s]+)\s+(.+?)\]', '[[\\1|\\2]]'),

#  ('\["/(.*)"\]', '[['+filename[-1]+':\\1]]'),

  # code blocks
  # open and language
  ('\{{3}#!(python|php)', '<'+'code \\1>'),
  # code open
  ('\{{3}', '<'+'code>'),
  # close
  ('\}{3}', '<'+'/code>'),

  ('^\s\s\s\s\*', '        *'),
  ('^\s\s\s\*', '      *'),
  ('^\s\s\*', '    *'),
  ('^\s\*', '  *'),                           # lists must have 2 whitespaces before the asterisk
  ('^\s\s\s\s1\.', '      -'),
  ('^\s\s1\.', '    -'),
  ('^\s1\.', '  -'),
  ('^\s*=====\s*(.*)\s*=====\s*$', '=-=- \\1 =-=-'),           # heading 5
  ('^\s*====\s*(.*)\s*====\s*$', '=-=-=- \\1 =-=-=-'),         # heading 4
  ('^\s*===\s*(.*)\s*===\s*$', '=-=-=-=- \\1 =-=-=-=-'),       # heading 3
  ('^\s*==\s*(.*)\s*==\s*$', '=-=-=-=-=- \\1 =-=-=-=-=-'),     # heading 2
  ('^\s*=\s*(.*)\s=\s*$', '=-=-=-=-=-=- \\1 =-=-=-=-=-=-'),    # heading 1
  ('=-', '='),
  ('\|{2}', '|'),                             # table separator
  ('\'{5}(.*)\'{5}', '**//\\1//**'),          # bold and italic
  ('\'{3}(.*)\'{3}', '**\\1**'),              # bold
  ('\'{2}(.*)\'{2}', '//\\1//'),              # italic
  ('`(.*?)`', "''\\1''"),							# monospaced
  ('(?<!\[)(\b[A-Z]+[a-z]+[A-Z][A-Za-z]*\b)','[[\\1]]'),  # CamelCase, dont change if CamelCase is in InternalLink
  ('\[\[Date\(([\d]{4}-[\d]{2}-[\d]{2}T[\d]{2}:[\d]{2}:[\d]{2}Z)\)\]\]', '\\1'),  # Date value
  ('attachment:(.*)','{{'+namespace+'\\1|}}')
  )

  for i in range(len(content)):
    line = content[i]
    for item in regexp:
      line = re.sub(item[0], item[1], line)
    content[i] = line
  return content

def print_help():
  print "Usage: moinconv.py <moinmoin pages directory> <output directory>"
  print "Convert MoinMoin pages to DokuWiki."
  print "Options:"
  print "-o      - overwrite output files"
  print "-f FILE - convert signle file"
  sys.exit(0)

# return unicode encoded wikiname
# input is a dir from moinmoin pages/ dir
def wikiname(filename):
  from MoinMoin import wikiutil
  return wikiutil.unquoteWikiname(basename(filename))

def convertfile(pagedir, overwrite = False):
  pagedir  = os.path.abspath(pagedir)
  print "-> %s" % pagedir
  curr_rev = get_current_revision(pagedir)
  if curr_rev == None:
    print "SKIP %s: no current revision" % pagedir
    return

  if not os.path.exists(curr_rev):
    print "SKIP %s: filename missing" % curr_rev
    return

  pagename = wikiname(pagedir)
  print "pagename: [%s]" % pagename

  if pagename.count('MoinEditorBackup') > 0:
    print "SKIP %s: skip backups" % pagedir
    return

  content = readfile(curr_rev)
  content = convert_markup(pagename, content)
  out_file = os.path.join(output_dir, dw.wikiFN(pagename))
  print "dokuname: [%s]" % out_file
  writefile(out_file, content, overwrite = overwrite)

  ns = dw.getNS(dw.cleanID(pagename))
  copy_attachments(pagedir, ns)

  return 1

#
# "main" starts here
#
try:
  opts, args = getopt.getopt(sys.argv[1:], 'hof:', [ "help" ])
except getopt.GetoptError, e:
  print >> sys.stderr, 'Incorrect parameters! Use --help switch to learn more.: %s' % e
  sys.exit(1)

overwrite = False
inputfile = None
for o, a in opts:
  if o == "--help" or o == "-h":
    print_help()
  if o == "-o":
    overwrite = True
  if o == "-f":
    inputfile = a

if len(args) != 2:
  print >> sys.stderr, 'Incorrect parameters! Use --help switch to learn more.'
  sys.exit(1)

(moin_pages_dir, output_dir) = args

check_dirs(moin_pages_dir, output_dir)

print 'Input dir is: %s.' % moin_pages_dir
print 'Output dir is: %s.' % output_dir

dw = DokuWiki()

if inputfile != None:
  res = convertfile(inputfile, overwrite = overwrite)
else:
  pathnames = get_path_names(moin_pages_dir)
  converted = 0
  for pathname in pathnames:
    res = convertfile(pathname, overwrite = overwrite)
    if res != None:
      converted += 1
  print "Processed %d files, converted %d" % (len(pathnames), converted)
