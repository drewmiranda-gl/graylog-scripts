# Graylog API Automation Tools

## Introduction

This is an attempt and making a new unified graylog API tool. Currently I have a collection of disparate scripts that are impossible to maintain. It will be helpful to have all functionality in one place.

## Installation and Requirements

* Python >= 3.10
* `python3 -m pip install -r requirements.txt`
* Configure properties in `config.yml`

## Usage

Examples...

Create an input in a forwarder input profile

```sh
python3 gl-api.py --config-file config.yml --action create-input-profile --title "Input Profile Name"
```

Create a new forwarder input profile and create a series of inputs in that profile

```sh
python3 gl-api.py --config-file config.yml --action create-forwarder-input --input-profile-id create --title "Default Inputs" --input-types beats,syslog_udp,syslog_tcp,gelf_udp
```

Command line arguments:

```
options:
  -h, --help            show this help message and exit
  --debug, --no-debug, -d
                        For debugging (default: None)
  --verbose, --no-verbose
                        For debugging (default: None)
  --config-file CONFIG_FILE, -c CONFIG_FILE
                        Config file to use. Defaults to config.yml (default: config.yml)
  --action {create-forwarder-input,create-input-profile,list-streams,share-all-dashboards,share-all-stream}
                        Action to perform (default: None)
  --bulk-file BULK_FILE
                        file to use for bulk actions (default: bulk.csv)
  --title TITLE         title attribute (default: )
  --description DESCRIPTION
                        description attribute (default: )
  --input-type {beats,gelf_tcp,gelf_udp,syslog_tcp,syslog_udp}
                        Input Type (default: )
  --input-types INPUT_TYPES
                        Comma Separated list of input types. Must be valid choices from
                        --input-type. Supersedes --input-type. (default: )
  --input-port INPUT_PORT
                        Input Port Number (default: 0)
  --input-profile-id INPUT_PROFILE_ID
                        Forwarder ID. Can also use create (creates new input profile) or
                        latest (uses most recently created input profile). (default: )
```