#!/bin/bash

root_check() {
    get_curusr=$(whoami)
    if [ $get_curusr == "root" ]
    then
        ok="okhere"
    else
        echo "ERROR! Please run as root."
        echo "Try: 'sudo su' to elevate and then run install script again."
	echo "OR sudo bash $0"
        exit 1
    fi
}
root_check

wget https://github.com/maxmind/geoipupdate/releases/download/v6.0.0/geoipupdate_6.0.0_linux_amd64.deb
dpkg -i geoipupdate_6.0.0_linux_amd64.deb

echo "Acccount ID and license availaable via"
echo "   https://www.maxmind.com/en/my_license_key"
# echo -n "Enter IP of Opensearch Server: " && tmpip=$(head -1 </dev/stdin)
echo -n "Enter Maxmind Account ID:"
read mmacctid

echo -n "Enter Maxmind License Key:"
read mmlickey

sudo sed -i "s/^AccountID .*/AccountID $mmacctid/gi" /etc/GeoIP.conf
sudo sed -i "s/^LicenseKey .*/LicenseKey $mmlickey/gi" /etc/GeoIP.conf
sudo sed -i "s/^EditionIDs .*/EditionIDs GeoLite2-ASN GeoLite2-City GeoLite2-Country/gi" /etc/GeoIP.conf

# install update script
mkdir -p /usr/share/GeoIP/
cp -f upd-geo.sh /usr/share/GeoIP/
chmod +x /usr/share/GeoIP/upd-geo.sh
(sudo crontab -l 2>/dev/null; echo "35 13 * * 2,5 /usr/share/GeoIP/upd-geo.sh") | sudo crontab -
