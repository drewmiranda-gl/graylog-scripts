# Prereqs

* Maxmind account
* License Key (can be obtained for free and allows access to GeoLite2)

# Setup

## Install geoipupdate

1. [Download latest release](https://github.com/maxmind/geoipupdate/releases) of desired package type (e.g. deb, rpm)
    * This example will use deb package
    * `wget https://github.com/maxmind/geoipupdate/releases/download/v4.9.0/geoipupdate_4.9.0_linux_amd64.deb` 
    * Note, replace URL with URL of latest applicable download file
2. Install
    * `dpkg -i geoipupdate_4.9.0_linux_amd64.deb`
3. Update Config File

Input AccountID

```
echo "Acccount ID and license availaable via"
echo "   https://www.maxmind.com/en/my_license_key"
# echo -n "Enter IP of Opensearch Server: " && tmpip=$(head -1 </dev/stdin)
echo -n "Enter Maxmind Account ID:"
read mmacctid

```

Input License Key
```
echo -n "Enter Maxmind License Key:"
read mmlickey
```

Update Configuration File
```
sudo sed -i "s/^AccountID .*/AccountID $mmacctid/gi" /etc/GeoIP.conf
sudo sed -i "s/^LicenseKey .*/LicenseKey $mmlickey/gi" /etc/GeoIP.conf
sudo sed -i "s/^EditionIDs .*/EditionIDs GeoLite2-ASN GeoLite2-City GeoLite2-Country/gi" /etc/GeoIP.conf

```

## Cronjob

1. Save `upd-geo.sh` on the graylog-server in path `/usr/share/GeoIP`
2. Make executable
    * `chmod +x /usr/share/GeoIP/upd-geo.sh`
3. Add to crontab

```
(sudo crontab -l 2>/dev/null; echo "35 13 * * 2,5 /usr/share/GeoIP/upd-geo.sh") | sudo crontab -
```
