# What is this?

This is an "installer" for graylog using a `.tgz` build or snapshot.

Its intention is to be used with snapshot builds since official releases can be installed via linux packages.

# Prerequisites

* Python >= 3.9
* Graylog `.tgz` release

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