# * * * * * /root/fwd-journal-dir.sh >/dev/null 2>&1

curdt=$(date +"%Y-%m-%d %H:%M:%S")
curjsz=$(du /var/lib/graylog-forwarder/journal -s)
loglinez="$curdt $curjsz"
echo $loglinez >> /root/fwd-journal-dir.log
