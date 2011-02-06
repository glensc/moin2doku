#!/usr/bin/python
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
#
import sys, os, os.path, re, pdb
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

def get_current_revision(page_dir):
    rev_dir = os.path.join(page_dir, 'revisions')
    if isdir(rev_dir):
        revisions = listdir(rev_dir)
        revisions.sort()
        return os.path.join(rev_dir, revisions[-1])
    return ''

def copy_attachments(page_dir, attachment_dir):
  dir = os.path.join(page_dir,'attachments')
  if isdir(dir):
    attachments = listdir(dir)
    #pdb.set_trace()
    for attachment in attachments:
      cmd_string = 'cp "' + dir +'/' + attachment + '" "' + attachment_dir + attachment.lower() + '"'
      os.system ( cmd_string )

def convert_page(page, file):
    namespace = ':'
    for i in range(0, len(file) - 1):
      namespace += file[i] + ':'

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
        ('\["/(.*)"\]', '[['+file[-1]+':\\1]]'),
        ('\{{3}', '<>code>'),                        # code open
        ('\}{3}', '<>/code>'),                       # code close
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
    sys.exit(0)

def print_parameter_error():
    print >> sys.stderr, 'Incorrect parameters! Use --help switch to learn more.'
    sys.exit(1)

def fix_name( filename ):
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

#
# "main" starts here
#
if len(sys.argv) > 1:
    if sys.argv[1] in ('-h', '--help'):
        print_help()
    elif len(sys.argv) > 2:
        moin_pages_dir = sys.argv[1]
        output_dir = sys.argv[2]
    else:
        print_parameter_error()
else:
    print_parameter_error()

check_dirs(moin_pages_dir, output_dir)

print 'Input dir is: %s.' % moin_pages_dir
print 'Output dir is: %s.' % output_dir

pathnames = get_path_names(moin_pages_dir)

for pathname in pathnames:
    #pdb.set_trace() # start debugging here

    curr_rev = get_current_revision( pathname )
    if not os.path.exists( curr_rev ) : continue

    page_name = basename(pathname)
    if page_name.count('MoinEditorBackup') > 0 : continue # don't convert backups

    curr_rev_desc = file(curr_rev, 'r')
    curr_rev_content = curr_rev_desc.readlines()
    curr_rev_desc.close()

    page_name = fix_name( page_name )

    split = page_name.split('(2f)') # namespaces

    count = len(split)

    dateiname = split[-1]

    dir = output_dir
    # changed from attachment_dir = output_dir + '../media/':
    attachment_dir = output_dir + 'media/'
    if not isdir (attachment_dir):
      os.mkdir(attachment_dir)

    if count == 1:
      dir += 'unsorted'
      if not isdir (dir):
        os.mkdir(dir)

      attachment_dir += 'unsorted/'
      if not isdir (attachment_dir):
        os.mkdir(attachment_dir)

    for i in range(0, count - 1):

      dir += split[i] + '/'
      if not isdir (dir):
        os.mkdir(dir)

      attachment_dir += split[i] + '/'
      if not isdir (attachment_dir):
        os.mkdir(attachment_dir)

    if count == 1:
      str = 'unsorted/' + page_name
      split = str.split('/')
      curr_rev_content = convert_page(curr_rev_content, split)
    else:
      curr_rev_content = convert_page(curr_rev_content, split)

    out_file = os.path.join(dir, dateiname + '.txt')
    out_desc = file(out_file, 'w')
    out_desc.writelines([it.rstrip() + '\n' for it in curr_rev_content if it])
    out_desc.close()

    # pdb.set_trace() # start debugging here
    copy_attachments(pathname, attachment_dir)
