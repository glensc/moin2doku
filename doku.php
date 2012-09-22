#!/usr/bin/php
<?php
# -*- coding: utf-8 -*-
# Setup VIM: ex: noet ts=2 sw=2 :
#
# PHP side Bridge of accessing DokuWiki functions from Python.
# See README for details.
#
# Author: Elan Ruusamäe <glen@pld-linux.org>
# Version: 1.0
#
# You should probably adjust path to DOKU_INC.

if ('cli' != php_sapi_name()) die();

define('DOKU_INC', '/usr/share/dokuwiki/');
require_once DOKU_INC.'inc/init.php';
require_once DOKU_INC.'inc/common.php';
require_once DOKU_INC.'inc/cliopts.php';

# disable gzip regardless of config, then we don't have to compress when converting
$conf['compression'] = 0; //compress old revisions: (0: off) ('gz': gnuzip) ('bz2': bzip)

# override start page, as there's currently configured temporary frontpage
$conf['start'] = 'start'; //name of start page

function strip_dir($dir, $fn) {
	global $conf;
	return end(explode($dir.'/', $fn, 2));
}

switch ($argv[1]) {
case 'cleanID':
	echo cleanID($argv[2]);
	break;
case 'wikiFN':
	if ($argc > 3 && $argv[3]) {
		echo strip_dir($conf['olddir'], wikiFN($argv[2], $argv[3]));
	} else {
		echo strip_dir($conf['datadir'], wikiFN($argv[2]));
	}
	break;
case 'mediaFN':
	echo strip_dir($conf['mediadir'], mediaFN($argv[2]));
	break;
case 'metaFN':
	echo strip_dir($conf['metadir'], metaFN($argv[2], $argv[3]));
	break;
case 'getNS':
	echo getNS($argv[2]);
	break;
case 'getId':
	echo getId();
	break;
default:
	die("Unknown knob: {$argv[1]}");
}
