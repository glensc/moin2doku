#!/usr/bin/python
# -*- coding: utf-8 -*-
# Setup VIM: ex: noet ts=2 sw=2 :
#
# Main Script doing the conversion.
# See README for details.
#
# Author: Elan Ruusamäe <glen@pld-linux.org>
# Version: 1.0

import sys, os, os.path, re, codecs
import getopt
from MoinMoin import user, wikiutil
from MoinMoin.request import RequestCLI
from MoinMoin.logfile import editlog
from MoinMoin.Page import Page
from shutil import copyfile, copystat
from os import listdir, mkdir
from os.path import isdir, basename
from doku import DokuWiki
from moinformat import moin2doku

USEC = 1000000

def init_dirs(output_dir):
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

def readfile(filename):
	with open(filename, 'r') as f:
		text = f.read()
	return unicode(text.decode('utf-8'))

def writefile(filename, content, overwrite=False):
	dir = os.path.dirname(os.path.abspath(filename))
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
	print "Usage: %s OPTIONS" % program
	print "Convert MoinMoin pages to DokuWiki."
	print "Options:"
	print "-d DIR  - output directory"
	print "-a      - Convert Attic pages (history)"
	print "-f      - overwrite output files"
	print "-F FILE - convert single file"
	print "-r FILE - write config for redirect plugin"
	print ""
	print "%s -a -d /var/lib/dokuwiki" % program
	print "%s -F moinmoin/data/pages/frontpage -d out" % program
	sys.exit(0)

# return unicode encoded wikiname
# input is a dir from moinmoin pages/ dir
def wikiname(filename):
	return wikiutil.unquoteWikiname(basename(filename))

def convert_editlog(pagedir, output = None, overwrite = False):
	pagedir = os.path.abspath(pagedir)
	print "pagedir: %s" % pagedir
	pagename = wikiname(pagedir)
	if not output:
		output = pagename
	pagelog = os.path.join(pagedir, 'edit-log')
	edit_log = editlog.EditLog(request, filename = pagelog)

	changes = {}
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

		mtime = str(log.ed_time_usecs / USEC)
		changes[mtime] = "\t".join([mtime, log.addr, action, dw.cleanID(log.pagename), author, log.comment])

	# see if we have missing entries, try to recover
	page = Page(request, pagename)
	if len(page.getRevList()) != len(changes):
		print "RECOVERING edit-log, missing %d entries" % (len(page.getRevList()) - len(changes))
		for rev in page.getRevList():
			page = Page(request, pagename, rev = rev)
			mtime = page.mtime_usecs() / USEC

			if not mtime:
				pagefile, realrev, exists = page.get_rev(rev = rev);
				if os.path.exists(pagefile):
					mtime = int(os.path.getmtime(pagefile))
					print "Recovered %s: %s" % (rev, mtime)

			mtime = str(mtime)
			if not changes.has_key(mtime):
				changes[mtime] = "\t".join([mtime, '127.0.0.1', '?', dw.cleanID(pagename), 'root', 'recovered entry'])
				print "ADDING %s" % mtime

	changes = sorted(changes.values())
	out_file = os.path.join(output_dir, 'meta', dw.metaFN(output, '.changes'))
	writefile(out_file, "\n".join(changes), overwrite = overwrite)

def convertfile(pagedir, output = None, overwrite = False):
	pagedir = os.path.abspath(pagedir)
	pagename = wikiname(pagedir)
	if not output:
		output = pagename

	page = Page(request, pagename)
	if page.isUnderlayPage():
		print "SKIP UNDERLAY"
		return

	current_exists = page.exists()
	current_rev = page.current_rev()

	if convert_attic:
		revs = page.getRevList()
	else:
		revs = [current_rev]

	for rev in revs:
		page = Page(request, pagename, rev = rev)
		pagefile, realrev, exists = page.get_rev(rev = rev);
		print "EXISTS loop: %s " % exists

		mtime = page.mtime_usecs() / USEC

		if not mtime:
			if os.path.exists(pagefile) != exists:
				raise Exception, "IT SHOULD NOT HAPPEN"

			if os.path.exists(pagefile):
				mtime = int(os.path.getmtime(pagefile))
				print "recovered %s: %s" % (rev, mtime)

			if not mtime:
				print "NO REVISION: for %s" % pagefile
				continue

		if rev == current_rev:
			out_file = os.path.join(output_dir, 'pages', dw.wikiFN(output))
			if not convert_attic and not exists:
				# if not converting attic, allow current version may not exist anymore
				continue
		else:
			out_file = os.path.join(output_dir, 'attic', dw.wikiFN(output, str(mtime)))

		content = moin2doku(pagename, page.get_raw_body())
		if len(content) == 0:
#			raise Exception, "No content"
			print "NO CONTENT: exists: %s,%s" % (exists, os.path.exists(pagefile))

		writefile(out_file, content, overwrite = overwrite)
		copystat(pagefile, out_file)

	ID = dw.cleanID(output)
	ns = dw.getNS(ID)
	copy_attachments(pagedir, ns)

	# convert edit-log, it's always present even if current page is not
	convert_editlog(pagedir, output = output, overwrite = overwrite)

	# add to redirect.conf if filenames differ
	# and page must exist (no redirect for deleted pages)
	if redirect_conf and current_exists:
		# redirect dokuwiki plugin is quite picky
		# - it doesn't understand if entries are not lowercase
		# - it doesn't understand if paths are separated by forward slash
		old_page = pagename.lower().replace('/', ':').replace(' ', '_')
		if old_page != ID:
			redirect_map[old_page] = ID

	return 1

#
# "main" starts here
#
try:
	opts, args = getopt.getopt(sys.argv[1:], 'hfad:F:r:', [ "help" ])
except getopt.GetoptError, e:
	print >> sys.stderr, 'Incorrect parameters! Use --help switch to learn more.: %s' % e
	sys.exit(1)

overwrite = False
input_file = None
output_dir = None
convert_attic = False
redirect_conf = False
redirect_map = {}
for o, a in opts:
	if o == "--help" or o == "-h":
		print_help()
	if o == "-f":
		overwrite = True
	if o == "-a":
		convert_attic = True
	if o == "-r":
		redirect_conf = a
	if o == "-d":
		output_dir = a
	if o == "-F":
		input_file = a

if not output_dir:
	print_help()
	sys.exit(1)

print "Output dir is: '%s'" % output_dir
init_dirs(output_dir)

dw = DokuWiki()
request = RequestCLI()

if input_file != None:
	res = convertfile(input_file, overwrite = overwrite)
else:
	converted = 0

	# special: process frontpage so that MoinMoin frontpage gets saved as DokuWiki frontpage
	page = wikiutil.getFrontPage(request)
	res = convertfile(page.getPagePath(), output = dw.getId(), overwrite = overwrite)
	if res != None:
		converted += 1

	# get list of all pages in wiki
	pages = request.rootpage.getPageDict(user = '', exists = not convert_attic)
	for page in pages.values():
		res = convertfile(page.getPagePath(), overwrite = overwrite)
		if res != None:
			converted += 1
	print "Processed %d files, converted %d" % (len(pages) + 1, converted)

if redirect_conf:
	print "Writing %s: %d items" % (redirect_conf, len(redirect_map))
	content = '\n'.join('\t'.join(pair) for pair in redirect_map.items())
	writefile(redirect_conf, content, overwrite = overwrite)
