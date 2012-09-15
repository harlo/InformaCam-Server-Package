#!/usr/bin/env python
import sys, os, subprocess

new_admin_template = '{"displayName":"%s","username":"%s","unpw":"%s"}'
cmd = 'curl -H "Content-Type: application/json" -X POST -d \'%s\' %s'
url = 'http://highsteppers:youAreNotAServerAdmin@localhost:5984/admin'

def registerAdmin():
	admin_ = new_admin_template % (displayname, username, (username + password))
	couch = subprocess.Popen(cmd % (admin_, url), shell=True, stdin=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True);
	res = couch.communicate()[0]
	if(res != None):
		sys.exit("sorry, cannot create new user %s" % username)
	else:
		sys.exit("new user %s created" % username)

if len(sys.argv) != 4:
	sys.exit("please enter display name (in quotes), username, and password")
else:
	displayname = sys.argv[1]
	username = sys.argv[2]
	password = sys.argv[3]
	print "registering new user:"
	print "display name: %s" % displayname
	print "username: %s" % username
	print "password: %s" % password

	registerAdmin()