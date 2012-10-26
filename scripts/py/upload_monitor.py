#!/usr/bin/env python
import sys, pycurl, os, cStringIO, json, subprocess, time, doCurl, j3mifier, indexer, constants, datetime, base64, message

get_unindexed = 'submissions/_design/submissions/_view/bytes_transferred'
get_submission = 'submissions/_design/submissions/_view/j3m?key=%s'
get_import = 'submissions/_design/submissions/_view/path?key=%s'
get_submission_for_delete = 'submissions/%s'
delete_submission = 'submissions/%s?rev=%s'
submissions_root = constants.submissions_root
derivatives_root = constants.derivativeRoot

def sendConfirmation(root):
	message.makeMessage(root, constants.submission_message)
	
def updateImportedSubmission(path):
	submission_id = doCurl.DoCurl(get_import % ("%22" + path + "%22")).perform()['rows'][0]['value']
	
	submission_rev = doCurl.DoCurl(get_submission_for_delete % (submission_id)).perform()['_rev']
		
	curl = doCurl.DoCurl(delete_submission % (submission_id, submission_rev))
	curl.setMethod("DELETE")
	curl.perform()

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
		
		try:
			if submission['value']['importFlag'] == True:
				isImport = submission['value']['importFlag']
				res = [submission['value']['path'],submission['value']['mediaType']]
		except:
			# get the path key
			res = j3mifier.init(submission['key'])
			isImport = False
				
		if res == False:
			print "still waiting for this submission to be complete"
		else:
			print "now indexing %s (mediatype: %s)" % (res[0], res[1])
			# this file should now be indexed!
			derivative = indexer.init(res[0], res[1], isImport)
			
			# if derivative is not null, clean up!
			if derivative != None:
				if isImport == False:
					updateSubmissions(derivative.derivative['representation'])
				else:
					print "is import!"
					#updateImportedSubmission(res[0])
				
print "hello upload monitor"		
getUnindexedUploads()