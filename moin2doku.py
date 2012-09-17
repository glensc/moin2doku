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
from os import listdir, mkdir
from os.path import isdir, basename
from doku import DokuWiki
from moinformat import moin2doku

def scan_underlay_pages(dirpath):
  pages = []
  paths = get_path_names(dirpath, basenames = True)
  for path in paths:
    pages.append(wikiname(path))
  return pages

def check_dirs(moin_pages_dir, output_dir):
  if moin_pages_dir and not isdir(moin_pages_dir):
    print >> sys.stderr, "MoinMoin pages directory doesn't exist!"
    sys.exit(1)

  if not isdir(output_dir):
    print >> sys.stderr, "Output directory doesn't exist!"
    sys.exit(1)

  pagedir = os.path.join(output_dir, 'pages')
  if not isdir(pagedir):
    mkdir(pagedir)

  mediadir = os.path.join(output_dir, 'media')
  if not isdir(mediadir):
    mkdir(mediadir)

def get_path_names(moin_pages_dir, basenames = False):
  items = listdir(moin_pages_dir)
  pathnames = []

  for item in items:
      absitem = os.path.join(moin_pages_dir, item)
      if isdir(absitem):
        if basenames:
          pathnames.append(item)
        else:
          pathnames.append(absitem)

  return pathnames

def readfile(filename):
  with open(filename, 'r') as f:
    text = f.read()
  return unicode(text.decode('utf-8'))

def writefile(filename, content, overwrite=False):
  dir = os.path.split(filename)[0]
  if not isdir(dir):
    os.makedirs(dir);

  if os.path.exists(filename) and overwrite == False:
    raise OSError, 'File already exists: %s' % filename

  f = file(filename, 'w')
  f.write(content)
  f.close()

def get_current_revision(pagedir):
  rev_dir = os.path.join(pagedir, 'revisions')
  # try "current" file first
  f = os.path.join(pagedir, 'current')
  if os.path.exists(f):
    rev = readfile(f).rstrip()
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
  srcdir = os.path.join(pagedir, 'attachments')
  if not isdir(srcdir):
    return

  attachment_dir = os.path.join(output_dir, 'media', dw.mediaFN(ns))
  if not isdir(attachment_dir):
    os.makedirs(attachment_dir);

  attachments = listdir(srcdir)
  for attachment in attachments:
    src = os.path.join(srcdir, attachment)
    dst = os.path.join(output_dir, 'media', dw.mediaFN(dw.cleanID("%s/%s" % (ns, attachment))))
    copyfile(src, dst)
    copystat(src, dst)

def print_help():
  program = sys.argv[0]
  print "Usage: %s -m <moinmoin pages directory> -d <output directory>" % program
  print "Convert MoinMoin pages to DokuWiki."
  print "Options:"
  print "-m DIR  - MoinMoin pages dir"
  print "-d DIR  - Dokuwiki pages dir"
  print "-f      - overwrite output files"
  print "-F FILE - convert single file"
  print ""
  print "%s -m moinmoin/data/pages /var/lib/dokuwiki/pages" % program
  print "%s -F moinmoin/data/pages/frontpage -d out" % program
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

  if pagename in moin_underlay_pages:
    print "SKIP %s: page in underlay" % pagename
    return

  if pagename.count('BadContent') > 0:
    print "SKIP %s: internal page" % pagedir
    return

  content = readfile(curr_rev)
#  print "content:[%s]" % content
#  content = convert_markup(pagename, content)
  content = moin2doku(pagename, content)

  out_file = os.path.join(output_dir, 'pages', dw.wikiFN(pagename))
  print "dokuname: [%s]" % out_file
  try:
    writefile(out_file, content, overwrite = overwrite)
  except OSError, e:
    print e
    return 0

  ns = dw.getNS(dw.cleanID(pagename))
  copy_attachments(pagedir, ns)

  return 1

#
# "main" starts here
#
try:
  opts, args = getopt.getopt(sys.argv[1:], 'hfm:u:d:F:', [ "help" ])
except getopt.GetoptError, e:
  print >> sys.stderr, 'Incorrect parameters! Use --help switch to learn more.: %s' % e
  sys.exit(1)

overwrite = False
input_file = None
moin_pages_dir = None
moin_underlay_pages = []
output_dir = None
for o, a in opts:
  if o == "--help" or o == "-h":
    print_help()
  if o == "-f":
    overwrite = True
  if o == "-m":
    moin_pages_dir = a
  if o == "-u":
    moin_underlay_pages = scan_underlay_pages(a)
  if o == "-d":
    output_dir = a
  if o == "-F":
    input_file = a

if not moin_pages_dir and not input_file:
  print_help()
  print >> sys.stderr, 'No input file or page dir to process'
  sys.exit(1)

check_dirs(moin_pages_dir, output_dir)

print "Input dir is: '%s'" % moin_pages_dir
print "Output dir is: '%s'" % output_dir

dw = DokuWiki()

if input_file != None:
  res = convertfile(input_file, overwrite = overwrite)
else:
  pathnames = get_path_names(moin_pages_dir)
  converted = 0
  for pathname in pathnames:
    res = convertfile(pathname, overwrite = overwrite)
    if res != None:
      converted += 1
  print "Processed %d files, converted %d" % (len(pathnames), converted)
