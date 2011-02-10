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

	def __getattr__(self, callback):
		self.callback = callback
		return self.__dokucall

	def __dokucall(self, *args):
		args = list(args)
		key = "%s:%s" % (self.callback, ",".join(args))
		if not self.callcache.has_key(key):
			cmd = ['./doku.php', self.callback ] + args
			res = subprocess.Popen(cmd, stdin = None, stdout = subprocess.PIPE, stderr = sys.stderr, close_fds = True).communicate()
			print "%s->%s" % (cmd, res)
			self.callcache[key] = res[0]
		return self.callcache[key]
