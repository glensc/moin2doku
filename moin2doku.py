#!/usr/bin/python
# -*- coding: utf-8 -*-
# Setup VIM: ex: et ts=2 sw=2 :
#
# moin2doku.py
#
# A script for converting MoinMoin version 1.3+ wiki data to DokuWiki format.
# Call with the name of the directory containing the MoinMoin pages and that
# of the directory to receive the DokuWiki pages on the command line:
#
# python moin2doku.py ./moin/data/pages/ ./doku/
#
# then move the doku pages to e.g. /var/www/MyWikiName/data/pages/,
# move the media files to e.g. /var/www/MyWikiName/data/media/,
# set ownership: chown -R www-data:www-data /var/www/MyWikiName/data/pages/*
# chown -R www-data:www-data /var/www/MyWikiName/data/media/*
#
# This script doesn't do all the work, and some of the work it does is
# wrong. For instance attachment links end up with the trailing "|}}"
# on the line following the link. This works, but doesn't look good.
# The script interprets a "/" in a pagename as a namespace delimiter and
# creates and fills namespace subdirectories accordingly.
#
# version 0.1  02.2010  Slim Gaillard, based on the "extended python"
#                       convert.py script here:
#                       http://www.dokuwiki.org/tips:moinmoin2doku
# version 0.2 Elan Ruusamäe, moved to github, track history there
#                       https://github.com/glensc/moin2doku
#
import sys, os, os.path, re
import getopt
from os import listdir
from os.path import isdir, basename

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

def get_current_revision(page_dir):
  rev_dir = os.path.join(page_dir, 'revisions')
  # try "current" file first
  f = os.path.join(page_dir, 'current')
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

  print "%s rev: %s" % (page_dir, rev)
  f = os.path.join(rev_dir, rev)
  if not os.path.exists(f):
    # deleted pages have '00000002' in current, and no existing file
    return None

  return f

def copy_attachments(page_dir, attachment_dir):
  dir = os.path.join(page_dir, 'attachments')
  if not isdir(dir):
    return

  if not isdir(attachment_dir):
    os.mkdir(attachment_dir)

  attachments = listdir(dir)
  for attachment in attachments:
    cmd_string = 'cp -p "' + dir +'/' + attachment + '" "' + attachment_dir + attachment.lower() + '"'
    os.system(cmd_string)

def convert_markup(page, filename):
    """
    convert page markup
    """
    namespace = ':'
    for i in range(0, len(filename) - 1):
      namespace += filename[i] + ':'

    regexp = (
        ('\[\[TableOfContents.*\]\]', ''),          # remove
        ('\[\[BR\]\]$', ''),                        # newline at end of line - remove
        ('\[\[BR\]\]', '\n'),                       # newline
        ('#pragma section-numbers off', ''),        # remove
        ('^##.*?\\n', ''),                          # remove
        ('\["', '[['),                              # internal link open
        ('"\]', ']]'),                              # internal link close
        #('\[:(.*):',  '[[\\1]] '),                 # original internal link expressions
        #('\[\[(.*)/(.*)\]\]',  '[[\\1:\\2]]'),
        #('(\[\[.*\]\]).*\]', '\\1'),
        ('\[(http.*) .*\]', '[[\\1]]'),             # web link
        ('\["/(.*)"\]', '[['+filename[-1]+':\\1]]'),
        ('\{{3}', '<'+'code>'),                        # code open
        ('\}{3}', '<'+'/code>'),                       # code close
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
        ('(?<!\[)(\b[A-Z]+[a-z]+[A-Z][A-Za-z]*\b)','[[\\1]]'),  # CamelCase, dont change if CamelCase is in InternalLink
        ('\[\[Date\(([\d]{4}-[\d]{2}-[\d]{2}T[\d]{2}:[\d]{2}:[\d]{2}Z)\)\]\]', '\\1'),  # Date value
        ('attachment:(.*)','{{'+namespace+'\\1|}}')
    )

    for i in range(len(page)):
        line = page[i]
        for item in regexp:
            line = re.sub(item[0], item[1], line)
        page[i] = line
    return page

def print_help():
    print "Usage: moinconv.py <moinmoin pages directory> <output directory>"
    print "Convert MoinMoin pages to DokuWiki."
    print "Options:"
    print "-f Overwrite output files"
    sys.exit(0)

def unquote(filename):
    filename = filename.lower()
    filename = filename.replace('(2d)', '-')          # hyphen
    filename = filename.replace('(20)', '_')          # space->underscore
    filename = filename.replace('(2e)', '_')          # decimal point->underscore
    filename = filename.replace('(29)', '_')          # )->underscore
    filename = filename.replace('(28)', '_')          # (->underscore
    filename = filename.replace('.', '_')             # decimal point->underscore
    filename = filename.replace('(2c20)', '_')        # comma + space->underscore
    filename = filename.replace('(2028)', '_')        # space + (->underscore
    filename = filename.replace('(2920)', '_')        # ) + space->underscore
    filename = filename.replace('(2220)', 'inch_')    # " + space->inch + underscore
    filename = filename.replace('(3a20)', '_')        # : + space->underscore
    filename = filename.replace('(202827)', '_')      # space+(+'->underscore
    filename = filename.replace('(2720)', '_')        # '+ space->underscore
    filename = filename.replace('(c3bc)', 'ue')       # umlaut
    filename = filename.replace('(c384)', 'Ae')       # umlaut
    filename = filename.replace('(c3a4)', 'ae')       # umlaut
    filename = filename.replace('(c3b6)', 'oe')       # umlaut
    return filename

def convertfile(pathname, overwrite = False):
    print "-> %s" % pathname
    curr_rev = get_current_revision(pathname)
    if curr_rev == None:
        print "SKIP %s: no current revision" % pathname
        return

    if not os.path.exists(curr_rev):
        print "SKIP %s: filename missing" % curr_rev
        return

    page_name = basename(pathname)
    if page_name.count('MoinEditorBackup') > 0:
        print "SKIP %s: skip backups" % pathname
        return

    content = readfile(curr_rev)

    page_name = unquote(page_name)
    print "dokuname: %s" % page_name

  # split by namespace separator
    ns = page_name.split('(2f)')
    count = len(ns)
    id = ns[-1]

    dir = output_dir
    attachment_dir = output_dir + 'media/'

    # root namespace files go to "unsorted"
    if count == 1:
      ns.insert(0, 'unsorted')

    for p in ns[:-1]:
      dir = os.path.join(dir, p);
      attachment_dir = os.path.join(p);

    content = convert_markup(content, ns)
    out_file = os.path.join(dir, id + '.txt')
    writefile(out_file, content, overwrite = overwrite)

    copy_attachments(pathname, attachment_dir)

    return 1

#
# "main" starts here
#
try:
    opts, args = getopt.getopt(sys.argv[1:], 'hf', [ "help" ])
except getopt.GetoptError:
    print >> sys.stderr, 'Incorrect parameters! Use --help switch to learn more.'
    sys.exit(1)

overwrite = False
for o, a in opts:
  if o == "--help" or o == "-h":
      print_help()
  if o == "-f":
      overwrite = True

if len(args) != 2:
  print >> sys.stderr, 'Incorrect parameters! Use --help switch to learn more.'
  sys.exit(1)

(moin_pages_dir, output_dir) = args

check_dirs(moin_pages_dir, output_dir)

print 'Input dir is: %s.' % moin_pages_dir
print 'Output dir is: %s.' % output_dir

pathnames = get_path_names(moin_pages_dir)
converted = 0
for pathname in pathnames:
    res = convertfile(pathname, overwrite = overwrite)
    if res != None:
      converted += 1

print "Processed %d files, converted %d" % (len(pathnames), converted)
