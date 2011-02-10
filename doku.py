#!/usr/bin/python
# -*- coding: utf-8 -*-
# Setup VIM: ex: noet ts=2 sw=2 :
# Bridge for Python code to invoke DokuWiki functions.
# 
# Author: Elan Ruusamäe <glen@pld-linux.org>

import sys
import subprocess

class DokuWiki:
	def __init__(self):
		self.callcache = {}

	def __call(self, call, id):
		key = "%s-%s" % (call, id)
		if not self.callcache.has_key(key):
			cmd = ['./doku.php', call, id]
			res = subprocess.Popen(cmd, stdin = None, stdout = subprocess.PIPE, stderr = sys.stderr, close_fds = True).communicate()
			self.callcache[key] = res[0]
		return self.callcache[key]

	def wikiFn(self, id):
		return self.__call('wikiFn', id)

	def mediaFn(self, id):
		return self.__call('mediaFn', id)

	def getNS(self, id):
		return self.__call('getNS', id)

	def cleanID(self, id):
		return self.__call('cleanID', id)
