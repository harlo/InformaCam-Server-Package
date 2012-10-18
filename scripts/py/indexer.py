#!/usr/bin/env python
import sys, os, cStringIO, json, subprocess, time, constants, keywords

'''
	argv: filename mediaType gpg_password
'''
couchQuery = "http://highsteppers:youAreNotAServerAdmin@localhost:5984/derivatives"
updateQuery = "http://highsteppers:youAreNotAServerAdmin@localhost:5984/submissions"
derivativeRoot = constants.derivativeRoot

omits = ["Got obscura marker","Generic APPn ffe0 loaded. Marker string: JFIF", "Component", "Didn't find"]

IMAGE = 400
VIDEO = 401

#TODO: do a real job at this
keywordOmits = keywords.keywordOmits

couchTemplate = '{"dateCreated":%d, "sourceId":"%s", "representation":%s, "keywords":%s, "locationOnSave":%s, "location":%s, "j3m":%s, "mediaType":%d, "timestampIndexed":%d, "discussions":%s}'
dictTemplate = [('dateCreated', 0),('sourceId', ""),('representation', []),('keywords', []), ('locationOnSave',[]),('location',[]),('j3m',""),('mediaType',0),('timestampIndexed',0),('discussions',[])]

class Derivative():
	def __init__(self, fn, mt, pw):
		self.filename = fn
		self.mediaType = int(mt)

		self.password = pw
		self.derivative = dict(dictTemplate)
		if(self.getMetadata() == True):
			#self.decryptMetadata() // is broken, fix later
			
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
				if(line.find("file: %s" %(self.filename)) == -1 and self.isOmitable(line) is False):
					self.j3m = self.j3m + line
			else:
				break
		return True
		
	def decryptMetadata(self):
		print("decrypting: \n%s" %(self.j3m))
		decrypt = subprocess.Popen(["gpg"], stdout=subprocess.PIPE)
		while True:
			line = decrypt.stdout.readline()
			if line != '':
				print(line)
			else:
				break
	
	def createDerivative(self):
		self.parseJ3M()
		self.derivative['timestampIndexed'] = int(time.time()) * 1000
		d = (couchTemplate % (self.derivative['dateCreated'], self.derivative['sourceId'], self.derivative['representation'], self.derivative['keywords'], self.derivative['locationOnSave'], self.derivative['location'], self.derivative['j3m'], self.derivative['mediaType'], self.derivative['timestampIndexed'], self.derivative['discussions'])).__str__()

		cmd = 'curl -H "Content-Type: application/json" -X POST -d \'%s\' %s' % (d,couchQuery)
		
		couch = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
		output = couch.communicate()[0]

				
	def parseJ3M(self):
		self.derivative['j3m'] = self.j3m
		
		j = json.loads(self.j3m)
		
		self.derivative['mediaType'] = self.mediaType
		self.derivative['dateCreated'] = j['genealogy']['dateCreated']
		self.derivative['sourceId'] = j['genealogy']['createdOnDevice']['deviceFingerprint']
		self.derivative['location'] = self.getAllLocations(j['data']['mediaCapturePlayback'])
		self.derivative['locationOnSave'] = self.findClosestLocation(self.derivative['dateCreated'], j['data']['mediaCapturePlayback'])
		if(j['data'].get('annotations')):
			self.derivative['keywords'] = self.parseForKeywords(j['data']['annotations'])
			self.derivative['discussions'] = self.parseAnnotations(j['data']['annotations'])
		
		self.derivative['representation'] = self.createRepresentations()
		
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
		chownFolder = subprocess.Popen(["sudo","chown","-R", "ubuntu:www-data", baseRoot + "messages"] , stdout=subprocess.PIPE)
		chownFolder.communicate()
		
		makeFolder = subprocess.Popen(["mkdir", baseRoot + "annotations"], stdout=subprocess.PIPE)
		makeFolder.communicate()
		
		copy = subprocess.Popen(["cp",self.filename, baseRoot + baseName], stdout=subprocess.PIPE)
		if copy.communicate()[0] == "":
				representations.append(baseName)
				# TODO: THIS IS NOT SETTING PROPERLY-- WHY?
				if self.mediaType == IMAGE:
					print "is image"
					self.derivative['mediaType'] = IMAGE
				elif self.mediaType == VIDEO:
					print "is mkv"
					# todo: make the three more derivatives!
					cmd = "ffmpeg -y -i %s -acodec copy -vcodec copy %s"
					mp4 = subprocess.Popen(cmd % (self.filename, baseRoot + base + ".mp4"), shell=True, stdin=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
					if mp4.communicate()[0] == None:
						representations.append(base + ".mp4")
			
					cmd = "ffmpeg2theora %s"
					ogg = subprocess.Popen(cmd % (baseRoot + base + ".mp4"), shell=True, stdin=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
					
					if ogg.communicate()[0] == None:
						representations.append(base + ".ogv")
						
					self.derivative['mediaType'] = VIDEO
			
		return '["' + '","'.join(representations) + '"]'
	
	def parseAnnotations(self, annotations):
		discussions = []
		for a in annotations:
			discussionDict = '{"date":%d,"originatedBy":"%s","timeIn":%d,"timeOut":%d,"duration":%d,"annotations":[%s],"regionBounds":%s}'
			annotationDict = '{"content":"%s","submittedBy":"%s", "date":%d}'
			regionBoundsDict = '{"regionCoordinates":{"region_top":%d,"region_left":%d},"regionDimensions":{"region_height":%d,"region_width":%d}}'
			videoRegionBoundsDict = '{"timestamp":%d,"regionCoordinates":{"region_top":%d,"region_left":%d},"regionDimensions":{"region_height":%d,"region_width":%d}}'
			if(a['obfuscationType'].find('InformaTagger') != -1) or (a['obfuscationType'].find('identify') != -1 or (a['obfuscationType'].find('pixel') != -1)):
				annotation = ""
				try:
					subjectAlias = a['subject']['alias']
					annotation = (annotationDict % (subjectAlias, self.derivative['sourceId'], a['timestamp'])).__str__()
				except:
					print "error getting a[subject][alias]"
				print annotation
				
				if self.mediaType == IMAGE:
					timeIn = 0
					timeOut = 0
					duration = 0
					regionBounds = (regionBoundsDict % (a['regionBounds']['regionCoordinates']['region_top'],a['regionBounds']['regionCoordinates']['region_left'],a['regionBounds']['regionDimensions']['region_height'],a['regionBounds']['regionDimensions']['region_width']))
					discussion = (discussionDict % (self.derivative['dateCreated'],self.derivative['sourceId'], timeIn, timeOut, duration, annotation, regionBounds)).__str__()
				# todo: how to parse the video...
			
				elif self.mediaType == VIDEO:
					timeIn = a['videoStartTime']
					timeOut = a['videoEndTime']
					duration = a['videoEndTime'] - a['videoStartTime']
					videoTrail = []
					
					for vt in a['videoTrail']:
						regionBounds = (videoRegionBoundsDict % (vt['timestamp'],vt['regionCoordinates']['region_top'],vt['regionCoordinates']['region_left'],vt['regionDimensions']['region_height'],vt['regionDimensions']['region_width']))
						
						videoTrail.append(regionBounds)
					
					discussion = (discussionDict % (self.derivative['dateCreated'],self.derivative['sourceId'], timeIn, timeOut, duration, annotation, "[" + ",".join(videoTrail) + "]")).__str__()

				# TODO burn this annotation to a flat file?
				discussions.append(discussion)
		
		print "[" + ",".join(discussions) + "]"
		return "[" + ",".join(discussions) + "]"
	
	def parseForKeywords(self, annotations):
		keywords = []
		for a in annotations:
			if(a['obfuscationType'].find('InformaTagger') != -1 or a['obfuscationType'].find('identify') != -1 or a['obfuscationType'].find('pixel') != -1):
				alias = ""
				try:
					alias = a['subject']['alias']
				except:
					print "error getting a[subject][alias]"
					
				words = alias.split(" ")
				for w in words:
					match = False
					for o in keywordOmits:
						if w.lower() == o:
							match = True
							break
							
					if(match == False):
						try:
							i = keywords.index(w.lower())
						except ValueError:
							keywords.append(w.lower())

		return '["' + '","'.join(keywords) + '"]'
	
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

def init(fn, mt, pw):
	return Derivative(fn, mt, pw)
	
'''
if len(sys.argv) != 4:
	sys.exit("please enter filename, mediaType, and password")
else:
	filename = sys.argv[1]
	mediaType = sys.argv[2]
	password = sys.argv[3]
	derivative = Derivative(filename, mediaType, password)

'''