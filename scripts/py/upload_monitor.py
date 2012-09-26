#!/usr/bin/env python
import sys, pycurl, os, cStringIO, json, subprocess, time, doCurl, j3mifier, indexer, constants, datetime, base64, message

get_unindexed = 'submissions/_design/submissions/_view/bytes_transferred'
get_submission = 'submissions/_design/submissions/_view/j3m?key=%s'
delete_submission = 'submissions/%s?rev=%s'
submissions_root = constants.submissions_root
derivatives_root = constants.derivativeRoot

def sendConfirmation(root):
	message.makeMessage(root, constants.submission_message)

def updateSubmissions(derivative):
	#delete the record so this is no longer in here...
	ds = derivative[1:-1].split(",")[0][1:-5]
	
	submission = doCurl.DoCurl(get_submission % ("%22" + ds + "%22")).perform()['rows'][0]['value']
	
	curl = doCurl.DoCurl(delete_submission % (submission['_id'], submission['_rev']))
	curl.setMethod("DELETE")
	curl.perform()
	sendConfirmation(ds)
	
def getUnindexedUploads():
	submissions = doCurl.DoCurl(get_unindexed).perform()['rows']
	for submission in submissions:
		print "finding torrents for %s..." % submission['key']
		# get the path key
		res = j3mifier.init(submission['key'])
		if res == False:
			print "still waiting for this submission to be complete"
		else:
			print "now indexing %s (mediatype: %s)" % (res[0], res[1])
			# this file should now be indexed!
			derivative = indexer.init(res[0], res[1], "passwrod")
			
			# if derivative is not null, clean up!
			if derivative != None:
				updateSubmissions(derivative.derivative['representation'])
				
print "hello upload monitor"		
getUnindexedUploads()