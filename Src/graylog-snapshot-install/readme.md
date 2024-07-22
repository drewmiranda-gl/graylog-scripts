# What is this?

This is an "installer" for graylog using a `.tgz` build or snapshot.

Its intention is to be used with snapshot builds since official releases can be installed via linux packages.

Quick, easy, straight to the point:

```shell
suydo python3 install.py --tgz download --install-openjdk --install-opensearch --install-mongod
```

If you need to install pip and pip reqs:
```shell
sudo apt update && sudo apt install python3-pip
sudo python3 -m pip install -r requirements.txt --ignore-installed
```

# Prerequisites

* Python >= 3.9
* Graylog `.tgz` release
    * Note: use `--tgz download` to have this script automatically download the latest snapshot.
* Bundled JDK or OpenJDK installed
    * Note: use `--install-openjdk` to have this script install OpenJDK
* [OpenSearch installed](https://github.com/Graylog2/se-poc-docs/blob/main/src/On%20Prem%20POC/installing%20opensearch.md) and running (Graylog will attempt to connect via `http://127.0.0.1:9200`)
    * Note: use `--install-opensearch` to have this script install OpenSearch
* [MongoDB](https://github.com/Graylog2/se-poc-docs/blob/main/src/On%20Prem%20POC/installing%20mongodb.md) installed and running (Graylog will attempt to connect via `mongodb://localhost/graylog`)
    * Note: use `--install-mongod` to have this script install MongoDB

# Instructions

## Preparation

* Upload all files in this directory to server where graylog will be installed
* Upload graylog `.tgz` release file

## Installation

Elevate to root:

```shell
sudo su
```

Enable execution for `py-help.sh`

```shell
chmod +x py-help.sh
```

Execute:

```shell
./py-help.sh install.py --tgz <filename.tgz>
```

Important info:

* Web Interface listens on HTTP port 9000
* Admin login info:
    * username: admin
    * password: admin

Sample output: ![](img/sample-output.png)