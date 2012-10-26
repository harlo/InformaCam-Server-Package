#!/usr/bin/env python
submissions_root = "/mnt/j3m/engine/submissions/"
derivativeRoot = "/mnt/j3m/engine/derivatives/"
cache_root = "/mnt/j3m/interface/ClientUpload/authCache/"
log_root =  "/mnt/j3m/log/"
engine_root = "/mnt/j3m/engine/"
cscripts_root = "/mnt/j3m/scripts/c__/"
logFile = "%sinformaCamServer_py.log" % log_root
chownTest = "/mnt/j3m/chownTest"

couchLogin = "http://highsteppers:youAreNotAServerAdmin"
masterUser = "ubuntu"

informaCam_metadata_name = "informaCam_metadata.json"
submission_message = "Thank you for your upload.  Your file has been received by InformaCam Server Alpha.\n\nDetails:\nReceived On: %s"