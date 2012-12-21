#!/bin/sh
user_base="/mnt/j3m/clients"
cert_base="/mnt/j3m/synergy/ca"

mkdir $user_base/$1/

openssl genrsa -des3 -out $user_base/$1/$1.key 4096
openssl req -new -key $user_base/$1/$1.key -out $user_base/$1/$1.csr
openssl ca -in $user_base/$1/$1.csr -cert $cert_base/informacamserveralpha.crt -keyfile $cert_base/informacamserveralpha.key -out $user_base/$1/$1.crt

openssl pkcs12 -export -clcerts -in $user_base/$1/$1.crt -inkey $user_base/$1/$1.key -out $user_base/$1/$1.p12

FILES=$user_base/$1/*
for file in $FILES
do
	chown ubuntu:ubuntu $file
done
