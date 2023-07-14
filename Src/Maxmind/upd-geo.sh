# 35 13 * * 1,3 /usr/share/GeoIP/upd-geo.sh

# Execute updater
echo Executing GeoIpUpdate
/usr/bin/geoipupdate

# cleanup older backups
# echo Deleting backup mmdbs older than 14 days
# find /root/mmdb/backups* -mtime +14 -exec rm {} \;

# make a copy of orig files
# d=`date +%Y%m%d`

# make a copy of GeoCity
# echo making a copy of existing mmdb files
# /usr/bin/rm -f /root/mmdb/backups/GeoLite2-City.mmdb
# cp /etc/graylog/server/GeoLite2-City.mmdb /root/mmdb/backups
# mv /root/mmdb/backups/GeoLite2-City.mmdb /root/mmdb/backups/GeoLite2-City.$d.mmdb

# make a copy of ASN
# /usr/bin/rm -f /root/mmdb/backups/GeoLite2-ASN.mmdb
# cp /etc/graylog/server/GeoLite2-ASN.mmdb /root/mmdb/backups
# mv /root/mmdb/backups/GeoLite2-ASN.mmdb /root/mmdb/backups/GeoLite2-ASN.mmdb.$d.mmdb

# copy updated Geo City
echo copy new mmdb to tmp file
cp /usr/share/GeoIP/GeoLite2-City.mmdb /etc/graylog/server/GeoLite2-City.tmp
cp /usr/share/GeoIP/GeoLite2-ASN.mmdb /etc/graylog/server/GeoLite2-ASN.tmp

echo delete existing mmdb
/usr/bin/rm -f /etc/graylog/server/GeoLite2-City.mmdb
/usr/bin/rm -f /etc/graylog/server/GeoLite2-ASN.mmdb

echo pausing for 5s
sleep 5

echo rename .tmp to .mmdb
mv /etc/graylog/server/GeoLite2-City.tmp /etc/graylog/server/GeoLite2-City.mmdb
mv /etc/graylog/server/GeoLite2-ASN.tmp  /etc/graylog/server/GeoLite2-ASN.mmdb

# copy update Geo ASN
cp /usr/share/GeoIP/GeoLite2-City.mmdb /opt/graylog/
cp /usr/share/GeoIP/GeoLite2-ASN.mmdb /opt/graylog/

