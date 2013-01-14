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

clients_root = '/mnt/j3m/clients/'
public_assets_root = '%spublic_assets/' % clients_root
organizationName = "guardian_project"
trusted_destination_url = "iuh5kpanrxnor5ut.onion"

client_manifest = "trustedDestinationURL=%s;password=%s"
bashscripts_root = engine_root
csr_subj = "/CN=InformaCam Server Alpha/C=US/ST=New-York/L=Brooklyn/O=The Guardian Project/OU=Department of Metadata/emailAddress=%s"

cert_root = '/mnt/j3m/synergy/ca/'
webUser = "www-data"

d_auth = "ainRan.5"
d_root = '/home/ubuntu/.gnupg'

xform_root = "%sform_manifests/" % engine_root
xform_dump = "%sform_dump/" % engine_root