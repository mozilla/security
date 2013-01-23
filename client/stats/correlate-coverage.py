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
import urllib2
import fileinput
import lxml.html

from mechanize import Browser


def getCurrentCoverageDirectory(baseURL):
  mech = Browser()
  mech.open(baseURL)
  
  currentLink = None
  
  for link in mech.links():
    # Find the first directory link that is not the parent
    if (link.url.endswith("/") and not link.url.startswith("/")):
      currentLink = link
      break
    
  if currentLink == None:
    mech.close()
    raise "Unable to find current coverage directory"
  
  linkURL = currentLink.base_url + currentLink.url
  mech.close()
  
  return linkURL
  
def getFileCoverage(baseURL, filename):
  """For a given filename, fetch coverage from an online LCOV source."""
  covURL = baseURL + filename + ".gcov.html"
  
  mech = Browser()
  try:
    urlObj = mech.open(covURL)
  except:
    return ("N/A", "N/A", "N/A", "N/A")
  
  parsedUrlObj = lxml.html.parse(urlObj)
  
  
  branchCoveragePercent = "N/A"
  branchCoverageMissing = "N/A"
  lineCoveragePercent = "N/A"
  lineCoverageMissing = "N/A"

  try:
    # Xpath to the coverage, see below
    lineCoveragePercent = float(parsedUrlObj.xpath("/html/body/table[1]/tr[3]/td/table/tr[2]/td[7]")[0].text.replace(" %", ""));
    # ------------------------------------------------------------------------------------^
    #   2 - line coverage
    #   3 - function coverage
    #   4 - branch coverage
    # ------------------------------------------------------------------------------------------^
    #   5 - # hit
    #   6 - # total
    #   7 - % hit

    lineCoverageHit = int(parsedUrlObj.xpath("/html/body/table[1]/tr[3]/td/table/tr[2]/td[5]")[0].text)
    lineCoverageTotal = int(parsedUrlObj.xpath("/html/body/table[1]/tr[3]/td/table/tr[2]/td[6]")[0].text)
    lineCoverageMissing = lineCoverageTotal - lineCoverageHit
  except ValueError:
    pass

  try:
    branchCoveragePercent = float(parsedUrlObj.xpath("/html/body/table[1]/tr[3]/td/table/tr[4]/td[7]")[0].text.replace(" %", ""));
    branchCoverageHit = int(parsedUrlObj.xpath("/html/body/table[1]/tr[3]/td/table/tr[4]/td[5]")[0].text)
    branchCoverageTotal = int(parsedUrlObj.xpath("/html/body/table[1]/tr[3]/td/table/tr[4]/td[6]")[0].text)
    branchCoverageMissing = branchCoverageTotal - branchCoverageHit
  except ValueError:
    pass
 
  mech.close()
  
  return (lineCoveragePercent, lineCoverageMissing, branchCoveragePercent, branchCoverageMissing)
  
def main():
  currentCovURL = getCurrentCoverageDirectory("http://people.mozilla.org/~choller/firefox/coverage/")
  dataDescriptorFollows = False

  for record in fileinput.input():
    record = record.lstrip().rstrip()
    
    # Preserve comments, possibly append new data column description though
    if record.startswith('#'):
      if "DATA DESCRIPTOR FOLLOWS" in record:
        dataDescriptorFollows = True
        print record
      elif dataDescriptorFollows:
        print record + " | % Line Coverage | Number of lines missing | % Branch Coverage | Number of branches missing"
        dataDescriptorFollows = False
      else:
        print record

      continue

    recordElements = record.split()
    
    if (len(recordElements) != 2):
      print "Warning: Ignoring malformed record: " + record
      continue

    cov = getFileCoverage(currentCovURL, recordElements[0])
  
    covMetric = "N/A"

    try:
      covMetric = (float(recordElements[1]) / (float(cov[0]) / float(100))) * float(cov[1])
    except:
      pass
    
    print record + " " + str(cov[0]) + " " + str(cov[1]) + " " + str(cov[2]) + " " + str(cov[3]) #+ " " + str(covMetric)

if __name__ == '__main__':
    main()
