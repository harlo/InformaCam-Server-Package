#!/bin/bash
function payload() {
	otpTime=86400 + date +%s
	python /mnt/j3m/scripts/py/otp.py
	while [ true ]; do
		if [ date +%s >= optTime ]; then
			python /mnt/j3m/scripts/py/otp.py
		fi
			
		python /mnt/j3m/scripts/py/upload_monitor.py
		sleep 20
	done
}
source daemon-functions.sh