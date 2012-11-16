#!/usr/bin/env python
# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 2.0
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# The Initial Developer of the Original Code is Christian Holler (decoder).
#
# Contributors:
#  Christian Holler <decoder@mozilla.com> (Original Developer)
#
# ***** END LICENSE BLOCK *****

import sys
import os
import subprocess
import re

from bugzilla.agents import BMOAgent
from bugzilla.models import Bug, Attachment, Flag, User, Comment
from bugzilla.utils import urljoin, qs, get_credentials, FILE_TYPES
from sets import Set

# We can use "None" for both instead to not authenticate
username, password = get_credentials()

# Load our agent for BMO
bz = BMOAgent(username, password)

# Search for all fixed bugs that have a security rating of critical or high
options = {
    # Must be a bug in Core product which is FIXED
    'product':          'Core',
    'resolution':       'FIXED',
    # Ignore old bugs, should be fixed at most 180 days ago
    'chfieldto':        'Now',
    'chfieldfrom':      '-60d',
    'chfield':          'resolution',
    'chfieldvalue':     'FIXED',
     # Advanced search criteria
    'query_format':     'advanced',
     # Should have an [sg:crit/high tag in whiteboard
    'type0-0-0':        'regexp',
    'field0-0-0':       'status_whiteboard',
    'value0-0-0':       '\[sg:(critical|high)',
    # or have a sec-crit/high keyword 
    'type0-0-1':        'regexp',
    'field0-0-1':       'keywords',
    'value0-0-1':       '(sec-critical|sec-high)',
    'include_fields':   '_default',
}

def fetchBug(bug_id):
  """Fetch the bug for the given bug_id and apply necessary workarounds."""
  bug = bz.get_bug(bug_id)
  # This is a workaround for bug 782967
  if len(bug.depends_on) > 0:
    if isinstance(bug.depends_on[0], str):
      bug.depends_on = [ int("".join(bug.depends_on)) ]
  return bug

def extractRevisionsFromURL(text):
  """Extract mozilla-central revisions from a given text."""
  if (text == None):
    return None
  
  revisions = []
  
  tokens = text.split()
  for token in tokens:
    if (re.match('^https?://hg\.mozilla\.org/mozilla\-central/rev/[a-f0-9]{12}$', token)):
      revisions.append(token[-12:])

  if (len(revisions) > 0):
    return revisions

  return None

def hgDiffStat(repoDir, rev):
  """Given a HG repository and revision, return the files touched by that revision."""
  origCwd = os.getcwd()
  os.chdir(repoDir)

  if debug:
    print "Running hg diff..."
  
  diffOut = subprocess.check_output(['hg', 'diff', '-c', rev, '--stat']).split("\n")

  os.chdir(origCwd)

  files = []
  for line in diffOut:
    if (line.find("|") > 0):
      parts = line.split('|')
      files.append(parts[0].strip())

  if debug:
    print files

  return files

def scanBug(bugnum, repoDir):
  """Process a single bug given by the bug number.
  
  Args:
    bugnum (int): The numeric ID of the bug to process.
    repoDir (str): The path to the repository that we should use.

  Returns:
    list. The list of files touched by the fix of this bug.
    
  """
  # Fetch the bug
  bug = fetchBug(bugnum)
  
  for comment in bug.comments:
    revs = extractRevisionsFromURL(comment.text)

    if (revs == None):
      continue

    if debug:
      print revs

    totalFiles = []

    for rev in revs:
      files = hgDiffStat(repoDir, rev)
      totalFiles.extend(files)

    #return map(os.path.dirname, totalFiles)

    # Make the list unique before returning: If a single bug patched
    # a file twice, then this should not be counted as two bugs.
    return list(set(totalFiles))

  print "Warning: No fix found in bug " + str(bugnum)

def main():
  # Get the bugs from the api
  buglist = bz.get_bug_list(options)

  if len(buglist) == 0:
    print "No bugs found."
    sys.exit(0)

  print "Found %s bugs:" % (len(buglist))

  dirs = {}
  cnt = 0;
  for bug in buglist:
    cnt += 1
    dirList = scanBug(bug.id, "repos/mozilla-central")

    if dirList == None:
      continue

    dirList = list(set(dirList))
    for dirEntry in dirList:
      if dirs.has_key(dirEntry):
        dirs[dirEntry] += 1;
      else:
        dirs[dirEntry] = 1

  from operator import itemgetter

  xs = sorted(dirs.items(), key=itemgetter(1))
  xs.reverse()

  for tup in xs:
    fn = tup[0]

    # Ignore files that contain test or docs/
    if fn.find("test") == -1 and fn.find("docs/") == -1:
      spaces = " " * (80-len(fn))
      print fn + spaces + str(tup[1])

if __name__ == '__main__':
    main()
