# 35 13 * * 1,3 /usr/share/GeoIP/upd-geo.sh

# Execute updater
/usr/bin/geoipupdate

# cleanup older backups
find /root/mmdb/backups* -mtime +14 -exec rm {} \;

# make a copy of orig files
d=`date +%Y%m%d`

# make a copy of GeoCity
/usr/bin/rm -f /root/mmdb/backups/GeoLite2-City.mmdb
cp /etc/graylog/server/GeoLite2-City.mmdb /root/mmdb/backups
mv /root/mmdb/backups/GeoLite2-City.mmdb /root/mmdb/backups/GeoLite2-City.$d.mmdb

# make a copy of ASN
/usr/bin/rm -f /root/mmdb/backups/GeoLite2-ASN.mmdb
cp /etc/graylog/server/GeoLite2-ASN.mmdb /root/mmdb/backups
mv /root/mmdb/backups/GeoLite2-ASN.mmdb /root/mmdb/backups/GeoLite2-ASN.mmdb.$d.mmdb

# copy updated Geo City
cp /usr/share/GeoIP/GeoLite2-City.mmdb /etc/graylog/server/
cp /usr/share/GeoIP/GeoLite2-ASN.mmdb /etc/graylog/server/

# copy update Geo ASN
cp /usr/share/GeoIP/GeoLite2-City.mmdb /opt/graylog/
cp /usr/share/GeoIP/GeoLite2-ASN.mmdb /opt/graylog/

