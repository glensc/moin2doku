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
    revisions = listdir(rev_dir)
    revisions.sort()
    return os.path.join(rev_dir, revisions[-1])


def convert_page(page):
    regexp = (
        ('\[\[TableOfContents\]\]', ''),            # remove
        ('\[\[BR\]\]$', ''),                        # newline at end of line - remove
        ('\[\[BR\]\]', '\n'),                       # newline
        ('#pragma section-numbers off', ''),        # remove
        ('^##.*?\\n', ''),                          # remove
        ('\["(.*)"\]',  '[[\\1]]'),                 # internal link
        ('(\[http.*\])', '[\\1]'),                  # web link
        ('\{{3}', '<>code>'),                       # code open
        ('\}{3}', '<>/code>'),                      # code close
        ('^\s\*', '  *'),                           # lists must have not only but 2 whitespaces before *
        ('={5}(\s.*\s)={5}$', '==\\1=='),           # heading 5
        ('={4}(\s.*\s)={4}$', '===\\1}==='),        # heading 4
        ('={3}(\s.*\s)={3}$', '====\\1===='),       # heading 3
        ('={2}(\s.*\s)={2}$', '=====\\1====='),     # heading 2
        ('={1}(\s.*\s)={1}$', '======\\1======'),   # heading 1
        ('\|{2}', '|'),                             # table separator
        ('\'{5}(.*)\'{5}', '**//\\1//**'),          # bold and italic
        ('\'{3}(.*)\'{3}', '**\\1**'),              # bold
        ('\'{2}(.*)\'{2}', '//\\1//'),              # italic
        ('(?<!\[)(\b[A-Z]+[a-z]+[A-Z][A-Za-z]*\b)','[[\\1]]'),  # CamelCase, dont change if CamelCase is in InternalLink
        ('\[\[Date\(([\d]{4}-[\d]{2}-[\d]{2}T[\d]{2}:[\d]{2}:[\d]{2}Z)\)\]\]', '\\1')  # Date value
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
        curr_rev_desc = file(curr_rev, 'r')
        curr_rev_content = curr_rev_desc.readlines()
        curr_rev_desc.close()

        curr_rev_content = convert_page(curr_rev_content)

        page_name = basename(page).lower()
        out_file = os.path.join(output_dir, page_name + '.txt')
        out_desc = file(out_file, 'w')
        out_desc.writelines([it.rstrip() + '\n' for it in curr_rev_content if it])
        out_desc.close()

        print 'Migrated %s to %s.' % (basename(page), basename(out_file))