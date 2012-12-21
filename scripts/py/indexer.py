#!/usr/bin/env python
import sys, os, cStringIO, json, subprocess, time, constants, keywords, gnupg, base64, xform_mapper
from pprint import pprint

'''
	argv: filename mediaType isImport
'''
couchQuery = "%s@localhost:5984/derivatives" % constants.couchLogin
updateQuery = "%s@localhost:5984/submissions" % constants.couchLogin
derivativeRoot = constants.derivativeRoot

omits = ["Got obscura marker","Generic APPn ffe0 loaded. Marker string: JFIF", "Component", "Didn't find"]

IMAGE = 400
VIDEO = 401

#TODO: do a real job at this
keywordOmits = keywords.keywordOmits

couchTemplate = '{"dateCreated":%d, "sourceId":"%s", "representation":%s, "keywords":%s, "locationOnSave":%s, "location":%s, "j3m":%s, "mediaType":%d, "timestampIndexed":%d, "discussions":%s, "importFlag":%s}'
dictTemplate = [('dateCreated', 0),('sourceId', ""),('representation', []),('keywords', []), ('locationOnSave',[]),('location',[]),('j3m',""),('mediaType',0),('timestampIndexed',0),('discussions',[]),('importFlag',False)]

class Derivative():
	def __init__(self, fn, mt, isImport):
		self.filename = fn
		self.mediaType = int(mt)

		if isImport == False:
			self.isImport = "false"
		else:
			self.isImport = "true"
			
		self.derivative = dict(dictTemplate)
		self.derivative['importFlag'] = self.isImport
		if(self.getMetadata() == True):
			self.createDerivative()
	
	def getMetadata(self):
		if self.mediaType == IMAGE:
			self.derivative['mediaType'] = IMAGE
			return self.getImageMetadata()
		elif self.mediaType == VIDEO:
			self.derivative['mediaType'] = VIDEO
			return self.getVideoMetadata()
	
	def getVideoMetadata(self):
		print "trying to look at %s with command " % self.filename
		
		paths = self.filename.split("/")
		root = "/".join(paths[:len(paths) -1]) + "/"
		mdFilePath = root + constants.informaCam_metadata_name
		print root
		
		cmd = "ffmpeg -y -dump_attachment:t:0 %s -i %s" % (mdFilePath, self.filename)
		print cmd
		
		j3mparser = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
		if(j3mparser.communicate()[0] == None):
			self.j3m = open(mdFilePath, 'r').read()
			return True
		else:
			return False
	
	def getImageMetadata(self):
		print "trying to look at %s" % self.filename
		j3mparser = subprocess.Popen(["%sj3mparser.out" % constants.cscripts_root, self.filename], stdout=subprocess.PIPE)
		self.j3m = ""
		while True:
			line = j3mparser.stdout.readline()
			if line != '':
				try:
					if(line.find("file: %s" %(self.filename)) == -1 and self.isOmitable(line) is False):
						self.j3m = self.j3m + line
				except Exception as err:
					print err
					break
		return True
		
	def decryptMetadata(self):
		gpg = gnupg.GPG()
		j3m = base64.b64decode(self.j3m)
		try:
			decrypted_data = gpg.decrypt(j3m, passphrase=str(constants.d_auth))
			pprint(vars(decrypted_data))
			
			if(decrypted_data.ok):
				self.j3m = decrypted_data.data
				return True
				
			return False
		except Exception, error:
			print "ERROR"
			print error
			return False
	
	def createDerivative(self):
		self.parseJ3M()
		if self.success == True:
			self.derivative['timestampIndexed'] = int(time.time()) * 1000
			d = (couchTemplate % (self.derivative['dateCreated'], self.derivative['sourceId'], self.derivative['representation'], self.derivative['keywords'], self.derivative['locationOnSave'], self.derivative['location'], self.derivative['j3m'], self.derivative['mediaType'], self.derivative['timestampIndexed'], self.derivative['discussions'], self.derivative['importFlag'])).__str__()
	
			cmd = 'curl -H "Content-Type: application/json" -X POST -d \'%s\' %s' % (d,couchQuery)
			
			couch = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
			output = couch.communicate()[0]
				
	def parseJ3M(self):
		j = None
		try:
			j = json.loads(self.j3m)
		except Exception as err:
			print err
			print "might need to decrypt"
			if self.decryptMetadata():
				j = json.loads(self.j3m)
		
		if j == None:
			self.success = False
			return				
		
		self.derivative['j3m'] = self.j3m
		self.derivative['mediaType'] = self.mediaType
		self.derivative['dateCreated'] = j['genealogy']['dateCreated']
		self.derivative['sourceId'] = j['intent']['owner']['publicKeyFingerprint']
		self.derivative['location'] = self.getAllLocations(j['data']['mediaCapturePlayback'])
		self.derivative['locationOnSave'] = self.findClosestLocation(self.derivative['dateCreated'], j['data']['mediaCapturePlayback'])
		if(j['data'].get('annotations')):
			self.buildAnnotations(j['data']['annotations'])
		
		self.derivative['representation'] = self.createRepresentations()
		self.success = True
		
	def createRepresentations(self):
		representations = []
		paths = self.filename.split("/")
		baseName = paths[len(paths) - 1]
		baseRoot = derivativeRoot + baseName[:-4] + "/"
		base = baseName[:-4]	
		
		# make annotations folder, messages folder
		makeFolder = subprocess.Popen(["mkdir", baseRoot], stdout=subprocess.PIPE)
		makeFolder.communicate()
		
		makeFolder = subprocess.Popen(["mkdir", baseRoot + "messages"], stdout=subprocess.PIPE)
		makeFolder.communicate()
		
		makeFolder = subprocess.Popen(["mkdir", baseRoot + "annotations"], stdout=subprocess.PIPE)
		makeFolder.communicate()
		
		copy = subprocess.Popen(["cp",self.filename, baseRoot + baseName], stdout=subprocess.PIPE)
		if copy.communicate()[0] == "":
				representations.append(baseName)
				
				if self.mediaType == IMAGE:
					print "is image"
					self.derivative['mediaType'] = IMAGE
				elif self.mediaType == VIDEO:
					print "is mkv"
					cmd = "ffmpeg -y -i %s -acodec copy -vcodec copy %s"
					mp4 = subprocess.Popen(cmd % (self.filename, baseRoot + base + ".mp4"), shell=True, stdin=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
					if mp4.communicate()[0] == None:
						representations.append(base + ".mp4")
			
					cmd = "ffmpeg2theora %s"
					ogg = subprocess.Popen(cmd % (baseRoot + base + ".mp4"), shell=True, stdin=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
					
					if ogg.communicate()[0] == None:
						representations.append(base + ".ogv")
						
					self.derivative['mediaType'] = VIDEO
		
		chownFolder = subprocess.Popen(["chown","-R", "%s:www-data" % constants.masterUser, baseRoot] , stdout=subprocess.PIPE)
		chownFolder.communicate()	
		return '["' + '","'.join(representations) + '"]'
	
	def buildAnnotations(self, annotations):
		keywords = []
		discussions = []
		discussionDict = '{"date":%d,"originatedBy":"%s","timeIn":%d,"timeOut":%d,"duration":%d,"annotations":[%s],"regionBounds":%s}'
		annotationDict = '{"content":%s,"submittedBy":"%s", "date":%d}'
		
		for a in annotations:
			map = xform_mapper.XFormMap(a['subject']['form_namespace'])
			map.mapAnswers(a['subject']['form_data'])
			
			try:
				for key, val in map.form_data['form_data'].iteritems():					
					if type(val).__name__ == 'list':
						for v in val:
							kw = parseKeyword(v, keywords)
							if kw is not None:
								for k in kw:
									keywords.append(k)
					else:
						kw = parseKeyword(val, keywords)
						if kw is not None:
							for k in kw:
								keywords.append(k)
							
				annotation = (annotationDict % (map.form_data_string, self.derivative['sourceId'],a['timestamp'])).__str__()
				
				if self.mediaType == IMAGE:
					timeIn = 0
					timeOut = 0
					duration = 0
					regionBoundsDict = '{"regionCoordinates":{"region_top":%d,"region_left":%d},"regionDimensions":{"region_height":%d,"region_width":%d}}'
					regionBounds = (regionBoundsDict % (a['regionBounds']['regionCoordinates']['region_top'],a['regionBounds']['regionCoordinates']['region_left'],a['regionBounds']['regionDimensions']['region_height'],a['regionBounds']['regionDimensions']['region_width']))
					discussion = (discussionDict % (self.derivative['dateCreated'],self.derivative['sourceId'], timeIn, timeOut, duration, annotation, regionBounds)).__str__()
				
				elif self.mediaType == VIDEO:
					timeIn = a['videoStartTime']
					timeOut = a['videoEndTime']
					duration = a['videoEndTime'] - a['videoStartTime']
					videoTrail = []
					regionBoundsDict = '{"timestamp":%d,"regionCoordinates":{"region_top":%d,"region_left":%d},"regionDimensions":{"region_height":%d,"region_width":%d}}'
					
					for vt in a['videoTrail']:
						regionBounds = (regionBoundsDict % (vt['timestamp'],vt['regionCoordinates']['region_top'],vt['regionCoordinates']['region_left'],vt['regionDimensions']['region_height'],vt['regionDimensions']['region_width']))
						videoTrail.append(regionBounds)
						
					discussion = (discussionDict % (self.derivative['dateCreated'],self.derivative['sourceId'], timeIn, timeOut, duration, annotation, "[" + ",".join(videoTrail) + "]")).__str__()
				
				# TODO burn this annotation to a flat file?
				discussions.append(discussion)
			except Exception as err:
				print err
				continue

		self.derivative['keywords'] = '["' + '","'.join(keywords) + '"]'
		self.derivative['discussions'] = "[" + ",".join(discussions) + "]"
	
	def getAllLocations(self, capturePlayback):
		locations = []
		for c in capturePlayback:
			s = c['sensorPlayback']
			if(s.get('gps_coords')):
				locations.append(s['gps_coords'])
					
		return "[" + ",".join(locations) + "]"
	
	def findClosestLocation(self, dateCreated, capturePlayback):
		for c in capturePlayback:
			s = c['sensorPlayback']
			if(s.get('gps_coords') and abs(c['timestamp'] - dateCreated) <= 5000):
				return s['gps_coords']
			
	def isOmitable(self, line):
		for o in omits:
			if line.find(o) != -1:
				return True
		return False


def parseKeyword(val, keywords):
	found_words = []
	for w in val.split():
		match = False
		for o in keywordOmits:
			if w.lower() == o:
				match = True
				break
			
		if(match == False):
			try:
				i = keywords.index(w.lower())
			except ValueError:
				found_words.append(w.lower())
					
	if len(found_words) > 0:
		return found_words
	else:
		return None

def init(fn, mt, isImport):
	return Derivative(fn, mt, isImport)
	
'''
if len(sys.argv) != 4:
	sys.exit("please enter filename, mediaType, and import status")
else:
	filename = sys.argv[1]
	mediaType = sys.argv[2]
	isImport = sys.argv[3]
	derivative = Derivative(filename, mediaType, isImport)

'''