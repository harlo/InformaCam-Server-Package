#!/usr/bin/env python
import sys, os, cStringIO, logging, constants, string, random, subprocess, gnupg

# generate a good password for certificate
def generatePassword():
	orderings = [string.ascii_uppercase, string.digits, string.ascii_lowercase, string.digits, string.ascii_uppercase]
	random.shuffle(orderings)
	choices = ''.join(orderings)
	numChars = random.choice(range(21,46))
	return ''.join(random.choice(choices) for x in range(numChars))
	
def caller(cmd, desired):
	print " ".join(cmd)
		
	ex = subprocess.Popen(
		cmd,
		stdin=subprocess.PIPE,
		stderr=subprocess.STDOUT
	)
	
	result = ex.communicate()[0]
	print result
	
	if result == desired:
		return True
	else:
		return False

class InformaCamClient():
	def __init__(self, username, email, pgpkeyfile):
		self.username = username
		self.email = email
		self.pgpkeyfile = pgpkeyfile
		self.password = generatePassword()
		self.directory = "%s%s/" % (constants.clients_root, username)

	def initClient(self):
		# make a folder for user
		# put your image in that folder
		# put your public key in that folder
		cmds = ["mkdir %s" % self.directory, "cp %s%s.png %s" % (constants.public_assets_root, constants.organizationName, self.directory),"cp %s%s.asc %s" % (constants.public_assets_root, constants.organizationName, self.directory)]
	
		for cmd in cmds:
			ex = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
			ex.communicate()
		
		# make a manifest (trustedDestinationURL=x;password=x)
		manifest = open(self.directory + constants.organizationName + ".txt", "w+")
		manifest.write(constants.client_manifest % (constants.trusted_destination_url, self.password))
		manifest.close()
		return True

	def createCertificate(self):
		print "GENERATING CERTIFICATE..."
		cmds = [
			["openssl","genrsa","-des3","-passout","pass:%s" % self.password,"-out","%s%s.key" % (self.directory, self.username), "4096"],
			["openssl","req","-subj","%s" % (constants.csr_subj % self.email), "-new","-key","%s%s.key" % (self.directory, self.username),"-passin","pass:%s" % self.password,"-out","%s%s.csr" % (self.directory, self.username)],
			["openssl","ca","-in","%s%s.csr" % (self.directory, self.username),"-cert","%sinformacamserveralpha.crt" % constants.cert_root,"-keyfile","%sinformacamserveralpha.key" % constants.cert_root,"-out","%s%s.crt" % (self.directory, self.username),"-batch"],
			["openssl","pkcs12","-export","-clcerts","-in","%s%s.crt" % (self.directory, self.username),"-inkey","%s%s.key" % (self.directory, self.username),"-passin","pass:%s" % self.password,"-passout","pass:%s" % self.password,"-out","%s%s.p12" % (self.directory, self.username)]
		]
		
		for cmd in cmds:
			if caller(cmd,None) != True:
				return False
						
		return True
		
	def cleanup(self):
		cmds = [
			["mkdir","%s%s" % (self.directory, constants.organizationName)],
			["mv","%s%s.asc" % (self.directory, constants.organizationName), "%s%s" % (self.directory, constants.organizationName)],
			["mv","%s%s.png" % (self.directory, constants.organizationName), "%s%s" % (self.directory, constants.organizationName)],
			["mv","%s%s.txt" % (self.directory, constants.organizationName), "%s%s" % (self.directory, constants.organizationName)],
			["mv","%s%s.p12" % (self.directory, self.username), "%s%s" % (self.directory, constants.organizationName)]
		]
		
		for cmd in cmds:
			if caller(cmd,None) != True:
				return False
				
		return True

	def encrypt(self):
		gpg = gnupg.GPG()
		key_data = open(self.pgpkeyfile).read()
		key_import = gpg.import_keys(key_data)
		
		self.fingerprint = key_import.results[0]['fingerprint']
		print self.fingerprint
		
		with open("%s%s.zip" % (self.directory, constants.organizationName),"rb") as f:
			status = gpg.encrypt_file(f, always_trust=True, recipients=self.fingerprint, output="%s%s.ictd" % (self.directory, constants.organizationName))
		
		cmds = [
			["chown","%s:%s" % (constants.masterUser, constants.webUser),"%s%s.ictd" % (self.directory, constants.organizationName)]
		]
		
		for cmd in cmds:
			if caller(cmd, None) != True:
				return False
		
		return True

	def finalize(self):
		cmds = [
			# zip it up
			["zip","-j","-r","%s%s.zip" % (self.directory, constants.organizationName), "%s%s/" % (self.directory, constants.organizationName)],
		]
		
		for cmd in cmds:
			if caller(cmd,None) != True:
				return False
		
		if self.encrypt() != True:
			return False
		
		return True

	def export(self):
		# should return path to file, and credentials to add to sources in db
		return [
			"%s%s.ictd" % (self.directory, constants.organizationName),
			'{"sourceId":"%s"}' % self.fingerprint
		]

logger = logging.getLogger('newClients_py')
handler = logging.FileHandler(constants.logFile)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

if len(sys.argv) != 4:
	logger.info("new client invoked (failed!) with the following args:")
	for arg in sys.argv:
		logger.info(arg)
		
	sys.exit("please enter username, email address, and path to PGP key")

logger.info("new client invoked...")
ifc = InformaCamClient(sys.argv[1], sys.argv[2], sys.argv[3])
result = False

if ifc.initClient() == True:
	if ifc.createCertificate() == True:
		if ifc.cleanup() == True:
			if ifc.finalize() == True:
				export = ifc.export()

print export