#!/usr/bin/env python
import cStringIO, json, pycurl, subprocess, constants

class DoCurl(object):
	def __init__(self, query):
		self.buf = cStringIO.StringIO()
		url = ('%s@localhost:5984/%s' % (constants.couchLogin, query)).__str__()
		curl = pycurl.Curl()
		curl.setopt(pycurl.URL, url)
		curl.setopt(pycurl.WRITEFUNCTION, self.buf.write)
		self.curl = curl
	
	def setMethod(self, method):
		self.curl.setopt(pycurl.CUSTOMREQUEST, method)
	
	def perform(self):
		self.curl.perform()
		b_string = self.buf.getvalue()
		self.buf.flush()
		self.buf.close()
		return json.loads(b_string)
	
	def uReplace(self, dict):
		newDict = []
		for item in dict:
			if dict.get(item).__class__.__name__ == "unicode":
				newDict.append("\"%s\":\"%s\"" % (item, dict.get(item)))
			elif dict.get(item).__class__.__name__ == "bool":
				newDict.append("\"%s\":%s" % (item, str(dict.get(item)).lower()))
			elif dict.get(item).__class__.__name__ == "dict":
				newDict.append("\"%s\":%s" % (item, self.uReplace(dict.get(item))))
			else:
				newDict.append("\"%s\":%d" % (item, dict.get(item)))
		return "{" + ",".join(newDict) + "}"
	
	def putOverride(self, query, json):
		url = ('%s@localhost:5984/%s' % (constants.couchLogin, query)).__str__()
		
		cmd = 'curl -H "Content-Type: application/json" -X PUT -d \'%s\' %s' % (json, url)
		print cmd
		
		p_update = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
		return p_update.communicate()[0]