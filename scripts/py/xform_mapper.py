#!/usr/bin/env python
import constants, json, base64, zlib, time, datetime, subprocess

control_input = 1
control_select_one = 2
control_select_multi = 3
control_audio_upload = 4

class XFormMap():
	def __init__(self, namespace, baseRoot, base):
		self.m_root = getManifestFromTitle(namespace)
		if self.m_root != None:
			self.manifest = self.m_root['manifest']
			self.iText = self.m_root['iText_en']
			self.baseRoot = baseRoot
			self.base = base
		
	def mapAnswers(self, answers):
		form_data_template = "{\"form_data\":{%s}}"
		form_data = []
		form_omits = []
		
		for key, val in answers.iteritems():
			#print "%s => %s" % (key, val)
			
			value = None
			if self.manifest[key] == control_input:
				value = "\"%s\"" % val
			elif self.manifest[key] == control_select_one:
				value = self.getOneSelection(key, val)
			elif self.manifest[key] == control_select_multi:
				value = self.getMultiSelection(key, val.split(" "))
			elif self.manifest[key] == control_audio_upload:
				value = self.createAudioAnnotation(key, val)
				form_omits.append(key)

			form_data.append("\"%s\":%s" % (key, value))
			
		self.form_data_string = "{%s}" % ",".join(form_data)

		self.form_data = json.loads(form_data_template % ",".join(form_data))
		for omit in form_omits:
			del self.form_data['form_data'][omit]
		
	def getOneSelection(self, key, val):
		return "\"%s\"" % self.iText[key][int(val) -1]
		
	def getMultiSelection(self, key, val):
		ans = []
		for v in val:
			ans.append("\"%s\"" % self.iText[key][int(v) -1])
		
		return "[%s]" % ",".join(ans)
		
	def createAudioAnnotation(self, key, val):
		f = "%s%s%s.3gp" % (self.baseRoot, int(time.mktime(datetime.datetime.now().timetuple())), self.base)
		f_ = "%soga" % f[1:-3]
		
		file = open(f,'w+')
		file.write(zlib.decompress(base64.b64decode(val), 16+zlib.MAX_WBITS))
		file.close()
		
		cmd = "ffmpeg2theora %s" % f
		print cmd
		
		oga = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
		if oga.communicate()[0] == None:
			return "\"%s\"" % f_
		else:
			return "\%s\"" % f
	
def getManifestFromTitle(namespace):
	m = open("%s%s.json" % (constants.xform_root, namespace.replace(" ","_").replace(".","_")))
	line = ""
	while 1:
		l = m.readline()
		if not l:
			break
		line += l
	
	try:
		manifest = json.loads(line)
	except Exception as err:
		print err
		manifest = None
		
	return manifest

'''
xform_map = XFormMap("iWitness v 1.0")
ans = "{\"iW_race\": \"chihuahua/bulldog\", \"iW_ethnicity\": \"none\", \"iW_name\": \"frank\", \"iW_nationality\": \"american\", \"iW_political_affiliation\": \"puppy party\", \"iW_religion\": \"food-motivated\", \"iW_individual_identifiers\": \"2 4\", \"iW_alias\": \"mummers\", \"iW_gender\": \"2\"}"

xform_map.mapAnswers(json.loads(ans))
'''