#!/usr/bin/env python
import sys, pycurl, os, cStringIO, json, subprocess, time, doCurl, j3mifier, indexer, constants, datetime, base64, message, logging

get_unindexed = 'submissions/_design/submissions/_view/bytes_transferred'
get_submission = 'submissions/_design/submissions/_view/j3m?key=%s'
get_import = 'submissions/_design/submissions/_view/path?key=%s'
get_submission_for_delete = 'submissions/%s'
delete_submission = 'submissions/%s?rev=%s'
submissions_root = constants.submissions_root
derivatives_root = constants.derivativeRoot

def doSudoTest():
	makeFolder = subprocess.Popen(["mkdir", constants.chownTest], stdout=subprocess.PIPE)
	testResult = makeFolder.communicate()[0]
	
	chownFolder = subprocess.Popen(["chown","-R", "www-data:www-data", constants.chownTest] , stdout=subprocess.PIPE)
	testResult = chownFolder.communicate()[0]

def sendConfirmation(root):
	message.makeMessage(root, constants.submission_message)
	logger.info("sent confirmation to %s" % root)
	
def updateImportedSubmission(path):
	submission_id = doCurl.DoCurl(get_import % ("%22" + path + "%22")).perform()['rows'][0]['value']
	
	submission_rev = doCurl.DoCurl(get_submission_for_delete % (submission_id)).perform()['_rev']
		
	curl = doCurl.DoCurl(delete_submission % (submission_id, submission_rev))
	curl.setMethod("DELETE")
	curl.perform()
	logger.info("deleted submission %s" % path)

def updateSubmissions(derivative):
	#delete the record so this is no longer in here...
	ds = derivative[1:-1].split(",")[0][1:-5]
	
	submission = doCurl.DoCurl(get_submission % ("%22" + ds + "%22")).perform()['rows'][0]['value']
	
	curl = doCurl.DoCurl(delete_submission % (submission['_id'], submission['_rev']))
	curl.setMethod("DELETE")
	curl.perform()
	logger.info("deleted submission %s" % ds)
	sendConfirmation(ds)
	
def getUnindexedUploads():
	submissions = doCurl.DoCurl(get_unindexed).perform()['rows']
	for submission in submissions:
		res = False
		isWhole = False
		isImport = False
		print "finding torrents for %s..." % submission['key']
		
		try:
			if(submission['value']['importFlag'] == True):
				isImport = submission['value']['importFlag']
				res = [submission['value']['path'],submission['value']['mediaType']]
		except Exception as err:
			print err				
			try:
				 if(submission['value']['whole_upload'] == True):
				 	isWhole = submission['value']['whole_upload']
					res = [submission['value']['path'],submission['value']['mediaType']]
			except Exception as err2:
				print err2
				res = j3mifier.init(submission['key'])
			
			# get the path key
			# return False
				
		if res == False:
			print "still waiting for this submission to be complete"
			logger.info("performed check: no new complete submissions")
		else:
			print "now indexing %s (mediatype: %s)" % (res[0], res[1])
			logger.info("attempting to index %s (mediatype: %s)" % (res[0], res[1]))
			# this file should now be indexed!
			derivative = indexer.init(res[0], res[1], isImport)
			
			# if derivative is not null, clean up!
			if derivative != None and derivative.success == True:
				if(isImport == False and isWhole == False):
					updateSubmissions(derivative.derivative['representation'])
				else:
					updateImportedSubmission(res[0])
			else:
				print "derivative could not be generated"
				logger.info("Failed to instantiate derivative.  skipping")

logger = logging.getLogger('informaCamServer_py')
handler = logging.FileHandler(constants.logFile)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

print "hello upload monitor"
logger.info("upload monitor invoked")

#doSudoTest()	
getUnindexedUploads()