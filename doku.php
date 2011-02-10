#!/usr/bin/php
<?php
# -*- coding: utf-8 -*-
# Setup VIM: ex: et ts=2 sw=2 :
#
# PHP side Bridge of accessing DokuWiki functions from Python.
# See README for details.
#
# Author: Elan Ruusamäe <glen@pld-linux.org>
#
# You should probably adjust path to DOKU_INC.

if ('cli' != php_sapi_name()) die();

define('DOKU_INC', '/usr/share/dokuwiki/');
require_once DOKU_INC.'inc/init.php';
require_once DOKU_INC.'inc/common.php';
require_once DOKU_INC.'inc/cliopts.php';

switch ($argv[1]) {
case 'cleanID':
	echo cleanID($argv[2]);
	break;
case 'wikiFn':
	echo wikiFn($argv[2]);
	break;
case 'mediaFn':
	echo mediaFn($argv[2]);
	break;
case 'getNS':
	echo getNS($argv[2]);
	break;
default:
	die("Unknown knob: {$argv[1]}");
}
