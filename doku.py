#!/usr/bin/python
# -*- coding: utf-8 -*-
# Setup VIM: ex: noet ts=2 sw=2 :
#
# Python side Bridge of accessing DokuWiki functions from Python.
# See README for details.
#
# Author: Elan Ruusamäe <glen@pld-linux.org>

import sys
import subprocess

class DokuWiki:
	def __init__(self):
		self.callcache = {}

	def __getattr__(self, method):
		def wrap(method):
			def wrapped(*args):
				return self.__call(method, *args)
			return wrapped
		return wrap(method)

	def __call(self, method, *args):
		args = list(args)
		key = "%s:%s" % (method, ",".join(args))
		if not self.callcache.has_key(key):
			cmd = ['./doku.php', method ] + args
			res = subprocess.Popen(cmd, stdin = None, stdout = subprocess.PIPE, stderr = sys.stderr, close_fds = True).communicate()
			self.callcache[key] = unicode(res[0].decode('utf-8'))
			print "%s->%s" % (cmd, self.callcache[key])
		return self.callcache[key]
