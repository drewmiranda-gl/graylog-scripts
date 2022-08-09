mongjs=$(mongo graylog --eval 'db.traffic.find({}).limit(2).sort({bucket:-1})' --quiet | tail -n 1)
numonly=$(echo $mongjs | grep -oP "\"output\"\s?:\s?{\s?.*?NumberLong\(\d+\)" | grep -oP "\(\d+\)" | grep -oP "\d+")
curl -X POST -H 'Content-Type: application/json' -d "{ \"version\": \"1.1\", \"host\": \"example.org\", \"short_message\": \"A short message\", \"level\": 5, \"_some_info\": \"foo\", \"mongo_json\":\"$numonly\" }" 'http://graylog.drew.local:12201/gelf'
