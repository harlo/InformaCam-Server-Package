#!/usr/bin/env python
import pycurl, base64, json, time, os.path, sys, constants
from datetime import datetime

un = 'BovineJonie'
pwd = 'aGoodManIsHardToFind'
api_url = 'https://stream.twitter.com/1/statuses/sample.json'
tcache_path = constants.cache_root + 'cache.json'
log_path = constants.log_root + 'daemon_log.json'
log_template = '{"timestamp": "%s", "message": "%s", "process": "otp.py"}'

class HoseSlurper:
	def __init__(self):
		self.caps = []
		curl = pycurl.Curl()
		curl.setopt(pycurl.URL, api_url)
		curl.setopt(pycurl.HTTPHEADER, ['Authorization: ' + base64.b64encode(un + ":" + pwd)])
		curl.setopt(pycurl.WRITEFUNCTION, self.tweet_callback)
		print '********* STARTING OTP SLURPER  **********'
		try:
			curl.perform()
		except pycurl.error:
			self.burn_list()
		
	def burn_list(self):
		print '********* STOPPING SLURPER **********'
		f = open(tcache_path, "w")
		f.writelines(json.dumps(self.caps))
		f.close()
		
		f = open(log_path, "a")
		f.writelines(log_template % (str(datetime.now()), "refreshed available tcache"))
		f.close()
		
	def tweet_callback(self, buffer):
		if(buffer.startswith('{"delete"') == False):
			if(len(self.caps) <= 500):
				self.caps.append(json.loads(buffer))
			else:
				return -1
				
hoseSlurper = HoseSlurper()