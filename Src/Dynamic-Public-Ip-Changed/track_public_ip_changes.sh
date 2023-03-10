SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# track_public_ip_changes.sh

workingpath=/opt/track_public_ip_changes
pastvaluefile=$workingpath/prev_ip
logfile=$workingpath/log.log

echo "workingpath=${workingpath}" >> $logfile
echo "pastvaluefile=${pastvaluefile}" >> $logfile

iFileExists=0
iIpHasChanged=0

which dig >> $logfile
dig +short myip.opendns.com @resolver1.opendns.com >> $logfile

if [ -f "$pastvaluefile" ]; then
    iFileExists=1
    echo "prev_ip file exists." >> $logfile
else
    echo "prev_ip file DOES NOT exist." >> $logfile
fi

echo "iFileExists = ${iFileExists}" >> $logfile

publicip=$(dig +short myip.opendns.com @resolver1.opendns.com)

if [ $iFileExists -eq 1 ]; then
    previp=$(cat $pastvaluefile | grep -oP "^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$")
    echo "Previously Recorded Ip: ${previp}"
    echo "Previously Recorded Ip: ${previp}" >> $logfile
    
    echo "Current Ip: $publicip"
    echo "Current Ip: $publicip" >> $logfile

    if [ "$previp" != "$publicip" ]; then
        echo "IP Address has changed!"
        iIpHasChanged=1
    fi
else
    echo "File does not already exist, writing current Public IP to prev_ip" >> $logfile
    echo "${publicip}" > $pastvaluefile
fi


if [ $iIpHasChanged -eq 1 ]; then
    now=$(date)
    echo "${now} :: ip_changed=1, old_ip=${previp}, new_ip=${publicip}" >> $logfile
    echo "${publicip}" > $pastvaluefile
else
    now=$(date)
    echo "${now} :: ip_changed=0, ip=${publicip}" >> $logfile
fi


