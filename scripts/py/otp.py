#!/usr/bin/env python
import pycurl, base64, json, time, os.path, sys, constants, logging
from datetime import datetime

un = 'BovineJonie'
pwd = 'aGoodManIsHardToFind'
api_url = 'https://stream.twitter.com/1/statuses/sample.json'
tcache_path = constants.cache_root + 'cache.json'
log_path = '%sauthTokenCron_py.log' % constants.log_root

class HoseSlurper:
	def __init__(self):
		self.caps = []
		curl = pycurl.Curl()
		curl.setopt(pycurl.URL, api_url)
		curl.setopt(pycurl.HTTPHEADER, ['Authorization: ' + base64.b64encode(un + ":" + pwd)])
		curl.setopt(pycurl.WRITEFUNCTION, self.tweet_callback)
		print '********* STARTING OTP SLURPER  **********'
		logger.info('********* STARTING OTP SLURPER  **********')
		try:
			curl.perform()
		except pycurl.error:
			self.burn_list()
		
	def burn_list(self):
		print '********* STOPPING SLURPER **********'
		logger.info('********* STOPPING SLURPER **********')
		f = open(tcache_path, "w")
		f.writelines(json.dumps(self.caps))
		f.close()
		
		logger.info("refreshed available tcache")
		
	def tweet_callback(self, buffer):
		if(buffer.startswith('{"delete"') == False):
			if(len(self.caps) <= 500):
				self.caps.append(json.loads(buffer))
			else:
				return -1


logger = logging.getLogger('sauthTokenCron_py')
handler = logging.FileHandler(log_path)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
				
hoseSlurper = HoseSlurper()