#!/bin/bash

# 5 * * * * /root/today-total-gl-traffic.sh >/dev/null 2>&1

authb64=$(cat authb64.txt)

glClusterLicenseTrafficLimitBytes=$(curl --location --request GET 'http://graylog.drew.local:9000/api/plugins/org.graylog.plugins.license/licenses/status/for-subject?subject=/license/enterprise/views' --header "Authorization: Basic $authb64" | jq '.status.license.enterprise.traffic_limit')

sample=$(curl --location --request GET 'http://graylog.drew.local:9000/api/system/cluster/traffic' --header "Authorization: Basic $authb64" | jq '.output')
echo "${sample}" > out.txt
File="out.txt"
Lines=$(cat $File)
prevLine=""

mostRecentDate=$(cat out.txt | tail -n 2 | head -n 1 | grep -oP "\"\d{4}\-\d{2}\-\d{2}" | grep -oP "\d{4}\-\d{2}\-\d{2}")

BRANCH_REGEX="^[0-9]"
iTodayTrafficBytes=0

for Line in $Lines
do
    if [[ $Line =~ $BRANCH_REGEX ]];
    then
        lineDate=$(echo $prevLine | grep -oP "\"\d{4}\-\d{2}\-\d{2}" | grep -oP "\d{4}\-\d{2}\-\d{2}" )
        # echo $lineDate
        if [ "$lineDate" == "$mostRecentDate" ];
        then
            lineTraffic=$(echo $Line | grep -oP "\d+")
            # echo "================="
            # echo "$prevLine ... $Line"
            echo "$lineDate : $lineTraffic"

            iTodayTrafficBytes=$(( $iTodayTrafficBytes + $lineTraffic ))
        fi
    fi
    prevLine=$Line
done

echo "Current Day Total Traffic: $iTodayTrafficBytes"
iTrfKb=$(( $iTodayTrafficBytes / 1000 ))
iTrfMb=$(( $iTrfKb / 1000 ))

iTrfLimitKb=$(( $glClusterLicenseTrafficLimitBytes / 1000 ))
iTrfLimitMb=$(( $iTrfLimitKb / 1000 ))
echo "Traffic Limit: $glClusterLicenseTrafficLimitBytes"

curl -X POST -H 'Content-Type: application/json' -d "{ \"host\": \"graylog_traffic\", \"short_message\": \"graylog traffic\", \"date_only\":\"$mostRecentDate\", \"gl_todays_traffic_bytes\":$iTodayTrafficBytes, \"gl_todays_traffic_kb\":$iTrfKb, \"gl_todays_traffic_mb\":$iTrfMb, \"gl_traffic_limit_bytes\":$glClusterLicenseTrafficLimitBytes, \"gl_traffic_limit_kb\":$iTrfLimitKb, \"gl_traffic_limit_mb\":$iTrfLimitMb }" 'http://graylog.drew.local:12201/gelf'
