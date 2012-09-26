#!/usr/bin/env python
import cStringIO, time, constants, datetime, base64, hashlib

def makeMessage(root, msgTemplate):
	timenow_str = datetime.datetime.now()
	timenow = int(time.mktime(timenow_str.timetuple()))
	
	print timenow
	print timenow_str
	
	msg = msgTemplate % timenow_str
	
	print msg
	
	md5 = hashlib.md5()
	md5.update(base64.b64encode(msg))
	msgPath = "%s%s/messages/%d_%s.txt" % (constants.derivativeRoot, root, timenow, md5.hexdigest())
	
	message = open(msgPath, "w+")
	message.write(msg)
	message.close