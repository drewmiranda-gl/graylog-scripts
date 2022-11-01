# What is this?

This is a set of tools (scripts) to automate tasks related to the Sigma Rules Feature in Graylog.

It Generates a list of sigma rules using the files in the `rules` directory and sends web requests to Graylog's api to import these rules via the [SigmaHQ sigma](https://github.com/SigmaHQ/sigma) repo. This script does not upload the rules from the `rules` folder, but only compiles a list of file names. The rules are downloaded using the 'import from git' function in graylog.

Success and failure counts as well as any import errors.

## Why does this exist?

Presently there isn't a way to upload ALL rules from the [SigmaHQ sigma](https://github.com/SigmaHQ/sigma) repo without clicking into each subfolder one by one. This started from conversations about how to automate generating documentation and inspecting how graylog is parsing the sigma rule yaml into a graylog query.

# How to use?

## Prerequisites

* Local copy of this repo (e.g. Download as Zip, or via git clone)
* Local copy of [SigmaHQ sigma](https://github.com/SigmaHQ/sigma) repo (specifically the `rules` directory)
* Python 3 (tested on 3.9.13)
    * Python modules
        * requests (pip install requests)
        * configparser (pip install configparser)
* Configure contents of config.ini

## Instructions

1. Copy rules from the SigmaHQ sigma repo and place in `rules` folder
2. execute
    * `python3 import_rules_docgen.py`

## config.ini

Argument | Description
---- | ----
https | true/false . If true, web URL will use HTTPS.
host | server to connect to for graylog api.
port | port to connect to for graylog api.
user | Graylog user that has access to run API actions.
password | password for user.

NOTE: to use a different file name, use the `--config ConfigFileName` argument.

## Examples

Default arguments.

```
python3 import_rules_docgen.py
```

Specify a custom configuration filename. This is useful if you don't want your config file to conflict with the template/default config file from this repo.

```
python3 import_rules_docgen.py --config auth.ini
```

## Command Line Arguments

```
optional arguments:
  -h, --help            show this help message and exit
  --debug, --no-debug, -d
                        For debugging (default: None)
  --dir DIR             Directory of sigma rules (default: rules)
  --config CONFIG       Config Filename (default: config.ini)
  --verbose, --no-verbose
                        Verbose output. (default: False)
  --batch-size BATCH_SIZE
                        Max number of rules to import with each API request. (default: 100)
```

## Sample Output

```
user@DEVICE SigmaRulesDocGen % python3 import_rules_docgen.py --config auth.ini --batch-size=5

Target Graylog Server: server.domain.tld

Loading from directory "rules"

Found 6 sigma rules.
Batch Size: 5

Web Request 1 of 2
    Importing 5 sigma rules...
    Success Count: 5 Failure Count: 0

Web Request 2 of 2
    Importing 1 sigma rules...
    Success Count: 1 Failure Count: 0

Total Success Count: 6
Total Failure Count: 0
```