#!/usr/bin/env python
import sys, os, json, subprocess, base64, doCurl, constants

'''
	this script takes all the j3m torrent files and concats them
'''

def updateBytesTransferred(lookup, torrent_path):

	lookup = "submissions/_design/submissions/_view/j3m?key=%s" % ("%22" + lookup + "%22")
	print lookup
	curl = doCurl.DoCurl(lookup)
	j = curl.perform()['rows'][0]['value']
	
	bytesTransferred = 0
	for f in os.walk(torrent_path):
		for file in f[2]:
			if(file != ".DS_Store"):
				bytesTransferred += os.stat(torrent_path +  "/" + file).st_size

	j3m = curl.uReplace(j['j3m'])
	
	couch = 'http://highsteppers:youAreNotAServerAdmin@localhost:5984/'
	update = "submissions/%s?rev=%s" % (j['_id'],j['_rev'])
	u = '{"_id":"%s","_rev":"%s","bytes_expected":%d,"bytes_transferred":%d,"j3m":%s,"j3m_bytes_expected":%s,"mediaType":%d,"sourceId":"%s","timestamp_created":%d,"timestamp_indexed":%d,"timestamp_scheduled":%d}' % (j['_id'],j['_rev'],j['bytes_expected'],bytesTransferred,j3m,j['j3m_bytes_expected'],j['mediaType'],j['sourceId'],j['timestamp_created'],j['timestamp_indexed'],j['timestamp_scheduled'])
		
	curl.putOverride(update, u)
	return 1

def getTorrentDescriptor(lookup):
	lookup = "submissions/_design/submissions/_view/j3m?key=%s" % ("%22" + lookup + "%22")
	curl = doCurl.DoCurl(lookup)
	j = curl.perform()['rows']
	
	if len(j) > 0:
		return j[0]['value']['j3m']
	else:
		return None

def checkForUploadedTorrents(torrent_path, torrent_descriptor):
	num_chunks = 0
	print torrent_path
	for f in os.walk(torrent_path):
		for file in f[2]:
			if(file != ".DS_Store"):
				num_chunks += 1
				print(file)
	
	print "chunks found: %d" % num_chunks
	if num_chunks < int(torrent_descriptor['num_chunks']):
		return False
	else:
		return True
		
def buildMediaObject(torrent_path, torrent_descriptor):
	data = ""
	cmd = "sudo chown -R ubuntu:www-data %s" % torrent_path
	p_update = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
	print p_update.communicate()[0]
	print cmd
	
	for n in range(0, torrent_descriptor['num_chunks']):
		f = torrent_path + '/' + ("%d_.j3mtorrent" % n)
		file = open(f, 'r')
		print f
		b64 = json.loads(file.read())
		
		blob = base64.b64decode(b64['blob'])
		data += blob
		file.close()
	
	m = torrent_path + '/' + torrent_descriptor['originalHash'];
	if torrent_descriptor['mediaType'] == 400:
		m += ".jpg"
	elif torrent_descriptor['mediaType'] == 401:
		m += ".mkv"
	
	media = open(m, "w+")
	media.write(data)
	media.close()
	
	if os.stat(m).st_size == torrent_descriptor['totalBytesExpected']:
		return [m, torrent_descriptor['mediaType']]
	else:
		return False

def init(key):
	print key;
	path = doCurl.DoCurl('submissions/%s' % key).perform()['path']
	paths = path.split("/")
	torrent_descriptor = getTorrentDescriptor(paths[len(paths) - 1])
	
	if torrent_descriptor != None:
		if checkForUploadedTorrents(path, torrent_descriptor) == True:
			return buildMediaObject(path, torrent_descriptor)
		else:
			return False
	else:
		sys.exit("this media has no descriptor")