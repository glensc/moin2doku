#!/usr/bin/python
import sys, os, os.path
import re
from os import listdir
from os.path import isdir, basename

def check_dirs(moin_pages_dir, output_dir):
    if not isdir(moin_pages_dir):
        print >> sys.stderr, "MoinMoin pages directory doesn't exist!"
        sys.exit(1)

    if not isdir(output_dir):
        print >> sys.stderr, "Output directory doesn't exist!"
        sys.exit(1)

def get_page_names(moin_pages_dir):
    items = listdir(moin_pages_dir)
    pages = []
    for item in items:
        item = os.path.join(moin_pages_dir, item)
        if isdir(item):
            pages.append(item)
    return pages

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
    for attachment in attachments:
      os.system ('cp "' + dir +'/' + attachment + '" "' + attachment_dir +'"')

def convert_page(page, file):
    namespace = ':'
    for i in range(0, len(file) - 1):
      namespace += file[i] + ':'

    regexp = (
        ('\[\[TableOfContents.*\]\]', ''),            # remove
        ('\[\[BR\]\]$', ''),                        # newline at end of line - remove
        ('\[\[BR\]\]', '\n'),                       # newline
        ('#pragma section-numbers off', ''),        # remove
        ('^##.*?\\n', ''),                          # remove
        ('\[:(.*):',  '[[\\1]] '),                 # internal link
        ('\[\[(.*)/(.*)\]\]',  '[[\\1:\\2]]'),
        ('(\[\[.*\]\]).*\]', '\\1'),
        ('\[(http.*) .*\]', '[[\\1]]'),                  # web link
        ('\["/(.*)"\]', '[['+file[-1]+':\\1]]'),
        ('\{{3}', '<>code>'),                       # code open
        ('\}{3}', '<>/code>'),                      # code close
        ('^\s\s\s\s\*', '        *'),
        ('^\s\s\s\*', '      *'),
        ('^\s\s\*', '    *'),
        ('^\s\*', '  *'),                           # lists must have not only but 2 whitespaces before *
        ('^\s\s\s\s1\.', '      -'),
        ('^\s\s1\.', '    -'),
        ('^\s1\.', '  -'),
        ('^\s*=====\s*(.*)\s*=====\s*$', '=-=- \\1 =-=-'),           # heading 5
        ('^\s*====\s*(.*)\s*====\s*$', '=-=-=- \\1 =-=-=-'),        # heading 4
        ('^\s*===\s*(.*)\s*===\s*$', '=-=-=-=- \\1 =-=-=-=-'),       # heading 3
        ('^\s*==\s*(.*)\s*==\s*$', '=-=-=-=-=- \\1 =-=-=-=-=-'),     # heading 2
        ('^\s*=\s*(.*)\s=\s*$', '=-=-=-=-=-=- \\1 =-=-=-=-=-=-'),   # heading 1
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

if __name__ == '__main__':
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
    print

    pages = get_page_names(moin_pages_dir)
    for page in pages:
        curr_rev = get_current_revision(page)
        if os.path.exists(curr_rev):
            page_name = basename(page).lower()
            curr_rev_desc = file(curr_rev, 'r')
            curr_rev_content = curr_rev_desc.readlines()
            curr_rev_desc.close()

            if 'moineditorbackup' not in page_name: #dont convert backups
              page_name = page_name.replace('(2d)', '-')
              page_name = page_name.replace('(c3bc)', 'ue')
              page_name = page_name.replace('(c384)', 'Ae')
              page_name = page_name.replace('(c3a4)', 'ae')
              page_name = page_name.replace('(c3b6)', 'oe')

              split = page_name.split('(2f)') # namespaces
              count = len(split)
              dateiname = split[-1]

              dir = output_dir
              attachment_dir = output_dir + '../media/'
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
              copy_attachments(page, attachment_dir)
