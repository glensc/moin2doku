#!/usr/bin/python
# -*- coding: utf-8 -*-
# Setup VIM: ex: et ts=2 sw=2 :
#
# Main Script doing the conversion.
# See README for details.
#
# Author: Elan Ruusamäe <glen@pld-linux.org>

import sys, os, os.path, re, codecs
import getopt
from MoinMoin import user
from MoinMoin.request import RequestCLI
from MoinMoin.logfile import editlog
from MoinMoin.Page import Page
from shutil import copyfile, copystat
from os import listdir, mkdir
from os.path import isdir, basename
from doku import DokuWiki
from moinformat import moin2doku

USEC = 1000000

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

  metadir = os.path.join(output_dir, 'meta')
  if not isdir(metadir):
    mkdir(metadir)

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

  f = codecs.open(filename, 'w', 'utf-8')
  f.write(content)
  f.close()

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

def convert_editlog(pagedir, overwrite = False):
  changes = []
  pagedir  = os.path.abspath(pagedir)
  print "pagedir: %s" % pagedir
  pagename = wikiname(pagedir)
  pagelog = os.path.join(pagedir, 'edit-log')
  edit_log = editlog.EditLog(request, filename = pagelog)
  for log in edit_log:
    # not supported. perhaps add anyway?
    if log.action in ('ATTNEW', 'ATTDEL', 'ATTDRW'):
      continue

    # 1201095949  192.168.2.23    E   start   glen@delfi.ee
    author = log.hostname
    if log.userid:
      userdata = user.User(request, log.userid)
      if userdata.name:
        author = userdata.name

    try:
      action = {
        'SAVE' : 'E',
        'SAVENEW' : 'C',
        'SAVE/REVERT' : 'R',
      }[log.action]
    except KeyError:
      action = log.action

    entry = [str(log.ed_time_usecs / USEC), log.addr, action, dw.cleanID(log.pagename), author, log.comment]
    changes.append("\t".join(entry))

  out_file = os.path.join(output_dir, 'meta', dw.metaFN(pagename, '.changes'))
  writefile(out_file, "\n".join(changes), overwrite = overwrite)

def convertfile(pagedir, overwrite = False):
  pagedir  = os.path.abspath(pagedir)
  pagename = wikiname(pagedir)

  page = Page(request, pagename)
  if page.isUnderlayPage():
    print "SKIP UNDERLAY"
    return

  current_rev = page.current_rev()
  for rev in page.getRevList():
    page = Page(request, pagename, rev = rev)
    pagefile, realrev, exists = page.get_rev(rev = rev);

    content = moin2doku(pagename, page.get_raw_body())

    if rev == current_rev:
      out_file = os.path.join(output_dir, 'pages', dw.wikiFN(pagename))
    else:
      mtime = str(page.mtime_usecs() / USEC)
      out_file = os.path.join(output_dir, 'attic', dw.wikiFN(pagename, mtime))

    writefile(out_file, content, overwrite = overwrite)
    copystat(pagefile, out_file)

  ns = dw.getNS(dw.cleanID(pagename))
  copy_attachments(pagedir, ns)

  # convert edit-log, it's always present even if current page is not
  convert_editlog(pagedir, overwrite = overwrite)

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
request = RequestCLI()

if input_file != None:
  res = convertfile(input_file, overwrite = overwrite)
else:
  pathnames = get_path_names(moin_pages_dir)
  converted = 0
  for pathname in pathnames:
    if pathname.count('MoinEditorBackup') > 0:
      print "SKIP %s: skip backups" % pathname
      continue

    res = convertfile(pathname, overwrite = overwrite)
    if res != None:
      converted += 1
  print "Processed %d files, converted %d" % (len(pathnames), converted)
