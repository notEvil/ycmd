#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Google Inc.
#
# This file is part of YouCompleteMe.
#
# YouCompleteMe is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# YouCompleteMe is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with YouCompleteMe.  If not, see <http://www.gnu.org/licenses/>.

import os
from nose.tools import eq_, raises
import StringIO
from ycmd.completers.go.gocode_completer import GoCodeCompleter
from ycmd.request_wrap import RequestWrap
from ycmd import user_options_store

TEST_DIR = os.path.dirname( os.path.abspath( __file__ ) )
DATA_DIR = os.path.join( TEST_DIR, "testdata" )
PATH_TO_TEST_FILE = os.path.join( DATA_DIR, "test.go" )
PATH_TO_POS121_RES = os.path.join( DATA_DIR, "gocode_output_offset_121.json" )
PATH_TO_POS215_RES = os.path.join( DATA_DIR, "gocode_output_offset_215.json" )
PATH_TO_POS292_RES = os.path.join( DATA_DIR, "gocode_output_offset_292.json" )
EXPECTED_PRINT_COMPLETION = [ ]

REQUEST_DATA = {
  'line_num': 1,
  'filepath' : PATH_TO_TEST_FILE,
  'file_data' : { PATH_TO_TEST_FILE : { 'filetypes' : [ 'go' ] } }
}



class GoCodeCompleter_test( object ):
  def setUp( self ):
    self._completer = GoCodeCompleter(
      user_options_store.DefaultOptions() )


  def _BuildRequest( self, line_num, column_num ):
    request = REQUEST_DATA.copy()
    request[ 'column_num' ] = column_num
    request[ 'line_num' ] = line_num
    with open(PATH_TO_TEST_FILE, 'r') as testfile:
      request[ 'file_data' ][ PATH_TO_TEST_FILE ][ 'contents' ] = testfile.read()
    return RequestWrap( request )

  # Test line-col to offset in the file before any unicode occurrences.
  def ComputeCandidatesInnerOffsetBeforeUnicode_test( self ):
    with open(PATH_TO_POS121_RES, 'r') as gocodeoutput:
      mock = MockPopen(returncode=0, stdout=gocodeoutput.read(), stderr="")
    self._completer._popener = mock
    # Col 8 corresponds to cursor at log.Pr^int("Line 7 ...
    self._completer.ComputeCandidatesInner(self._BuildRequest(7, 8))
    eq_(mock.cmd, ['gocode', '-f=json', 'autocomplete', PATH_TO_TEST_FILE, "121"])

  # Test line-col to offset in the file after a unicode occurrences.
  def ComputeCandidatesInnerAfterUnicode_test( self ):
    with open(PATH_TO_POS215_RES, 'r') as gocodeoutput:
      mock = MockPopen(returncode=0, stdout=gocodeoutput.read(), stderr="")
    self._completer._popener = mock
    # Col 9 corresponds to cursor at log.Pri^nt("Line 7 ...
    self._completer.ComputeCandidatesInner(self._BuildRequest(9, 9))
    eq_(mock.cmd, ['gocode', '-f=json', 'autocomplete', PATH_TO_TEST_FILE, "215"])

  # Test end to end parsing of completed results.
  def ComputeCandidatesInner_test( self ):
    with open(PATH_TO_POS292_RES, 'r') as gocodeoutput:
      mock = MockPopen(returncode=0, stdout=gocodeoutput.read(), stderr="")
    self._completer._popener = mock
    # Col 40 corresponds to cursor at ..., log.Prefi^x ...
    result = self._completer.ComputeCandidatesInner(self._BuildRequest(10, 40))
    eq_(mock.cmd, ['gocode', '-f=json', 'autocomplete', PATH_TO_TEST_FILE, "292"])
    eq_(result, [{
        'menu_text': u'Prefix',
        'insertion_text': u'Prefix',
        'extra_menu_info': u'func() string'
    }])

  # Test gocode failure.
  @raises(RuntimeError)
  def ComputeCandidatesInnerGoCodeFailure_test( self ):
    mock = MockPopen(returncode=1, stdout="", stderr="")
    self._completer._popener = mock
    self._completer.ComputeCandidatesInner(self._BuildRequest(1, 1))

  # Test JSON parsing failure.
  @raises(RuntimeError)
  def ComputeCandidatesInnerParseFailure_test( self ):
    mock = MockPopen(returncode=0, stdout="{this isn't parseable", stderr="")
    self._completer._popener = mock
    self._completer.ComputeCandidatesInner(self._BuildRequest(1, 1))

  # Test empty results error (different than no results).
  @raises(RuntimeError)
  def ComputeCandidatesInnerNoResultsFailure_test( self ):
    mock = MockPopen(returncode=0, stdout="[]", stderr="")
    self._completer._popener = mock
    self._completer.ComputeCandidatesInner(self._BuildRequest(1, 1))


class MockSubprocess(object):
  def __init__( self, returncode, stdin ):
    self.returncode = returncode
    self.stdin = stdin


  def wait( self ):
    return self.returncode



class MockPopen(object):
  def __init__(self, returncode=None, stdout=None, stderr=None):
    self._returncode = returncode
    self._stdout = stdout
    self._stderr = stderr
    # cmd and stdin will be populated when a subprocess is created.
    self.cmd = None
    self.stdin = None


  def __call__(self, cmd, stdout=None, stderr=None, stdin=None):
    self.cmd = cmd
    self.stdin = StringIO.StringIO()
    if stdout is not None:
      stdout.write(self._stdout)
      stdout.close()
    if stderr is not None:
      stderr.write(self._stderr)
      stderr.close()
    return MockSubprocess( self._returncode, self.stdin )
