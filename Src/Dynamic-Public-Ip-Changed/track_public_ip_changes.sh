#! /bin/bash

# track_public_ip_changes.sh

workingpath=/opt/track_public_ip_changes
pastvaluefile=$workingpath/prev_ip
logfile=$workingpath/log.log

iFileExists=0
iIpHasChanged=0

if [ -f "$pastvaluefile" ]; then
    iFileExists=1
fi

if [[ "$iFileExists" == "1" ]]; then
    previp=$(cat $pastvaluefile | grep -oP "^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$")
    echo "Previously Recorded Ip: ${previp}"
    publicip=$(dig +short myip.opendns.com @resolver1.opendns.com)
    echo "Current Ip: $publicip"

    if [[ "$previp" != "$publicip" ]]; then
        echo "IP Address has changed!"
        iIpHasChanged=1
    fi
else
    echo "${publicip}" > $pastvaluefile
fi


if [[ "$iIpHasChanged" == "1" ]]; then
    now=$(date)
    echo "${now} :: ip_changed=1, old_ip=${previp}, new_ip=${publicip}" >> logfile
    echo "${publicip}" > $pastvaluefile
else
    now=$(date)
    echo "${now} :: ip_changed=0, ip=${publicip}" >> logfile
fi
