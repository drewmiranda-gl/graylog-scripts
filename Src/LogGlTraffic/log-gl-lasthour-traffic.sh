# 5 * * * * /root/log-gl-lasthour-traffic.sh >/dev/null 2>&1

curdt=$(date +"%Y-%m-%d")
mongjs=$(mongo graylog --eval 'db.traffic.find({}).limit(2).sort({bucket:-1})' --quiet | tail -n 1)
numonly=$(echo $mongjs | grep -oP "\"output\"\s?:\s?{\s?.*?NumberLong\(\d+\)" | grep -oP "\(\d+\)" | grep -oP "\d+")
dateonly=$(echo $mongjs | grep -oP "ISODate\((.*?)\)" | grep -oP "\d{4}-\d{2}-\d{2}")
utc_hour_only=$(echo $mongjs | grep -oP "ISODate\((.*?)\)" | grep -oP "\d{4}-\d{2}-\d{2}T\d{2}" | grep -oP "T\d{2}" | grep -oP "\d+")
# curl -X POST -H 'Content-Type: application/json' -d "{ \"host\": \"graylog_traffic\", \"short_message\": \"graylog traffic\", \"mongo_output_traffic_bytes\":\"$numonly\", \"date_only\":\"$curdt\" }" 'http://graylog.drew.local:12201/gelf'
echo "{ \"host\": \"graylog_traffic\", \"short_message\": \"graylog traffic\", \"mongo_output_traffic_bytes\":$numonly, \"date_only\":\"$dateonly\", \"utc_hour_only\":\"$utc_hour_only\" }" >> /var/log/graylog-traffic/traffic.log
