#!/usr/bin/env python
submissions_root = "/path/to/submissons_root/"
derivativeRoot = "/path/to/derivatives/"
cache_root = "/path/to/interface/ClientUpload/authCache/"
log_root =  "/path/to/log/"
engine_root = "/path/to/engine/"
cscripts_root = "/path/to/scripts/c__/"
logFile = "%sinformaCamServer_py.log" % log_root

couchLogin = "http://couchdb_username:couchdb_password"
masterUser = "user(not root)"

informaCam_metadata_name = "informaCam_metadata.json"
submission_message = "Thank you for your upload.  Your file has been received by InformaCam Server Alpha.\n\nDetails:\nReceived On: %s"

clients_root = '/path/to/clients/'
public_assets_root = '%spublic_assets/' % clients_root
organizationName = "your_org_name"
trusted_destination_url = "xxxxx.onion"

client_manifest = "trustedDestinationURL=%s;password=%s"
bashscripts_root = engine_root
csr_subj = "/CN=InformaCam Server Alpha/C=US/ST=New-York/L=Brooklyn/O=The Guardian Project/OU=Department of Metadata/emailAddress=%s"

cert_root = '/path/to/synergy/ca/'
webUser = "www-data (or whatever)"

d_auth = "gpg_auth"
d_root = '/path/to/.gnupg'

xform_root = "%sform_manifests/" % engine_root
xform_dump = "%sform_dump/" % engine_root
