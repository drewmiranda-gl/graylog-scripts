# What is this?

This is a set of tools (scripts) to automate tasks related to the Sigma Rules Feature in Graylog.

It Generates a list of sigma rules using the files in the `rules` directory and sends web requests to Graylog's api to import these rules via the [SigmaHQ sigma](https://github.com/SigmaHQ/sigma) repo. This script does not upload the rules from the `rules` folder, but only compiles a list of file names. The rules are downloaded using the 'import from git' function in graylog.

Success and failure counts as well as any import errors.

## Why does this exist?

Presently there isn't a way to upload ALL rules from the [SigmaHQ sigma](https://github.com/SigmaHQ/sigma) repo without clicking into each subfolder one by one. This started from conversations about how to automate generating documentation and inspecting how graylog is parsing the sigma rule yaml into a graylog query.

# import_rules_docgen.py

Import sigma rules into Graylog Security.

## Prerequisites / Install

* Local copy of this repo (e.g. Download as Zip, or via git clone)
* Local copy of [SigmaHQ sigma](https://github.com/SigmaHQ/sigma) repo (specifically the `rules` directory)
* Python 3 (tested on 3.9.13)
* [pip](https://pypi.org/project/pip/)
    * Install required pip packages
        * `python3 -m pip install -r requirements.txt`
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

Specify a custom configuration filename. This is useful if you don't want your config file to conflict with the template/default config file from this repo. Will use the Github API to import all sigma rules via the SigmaHQ sigma repo.

```
python3 import_rules_docgen.py --config auth.ini
```

Import rules in the `rules` directory. To specify a different directory use `--dir`. Path is relative to the location of the python script.

```
python3 import_rules_docgen.py --config auth.ini --method file
```

## Command Line Arguments

```
  -h, --help            show this help message and exit
  --debug, --no-debug, -d
                        For debugging (default: None)
  --dir DIR             Directory of sigma rules (default: rules)
  --config CONFIG       Config Filename (default: config.ini)
  --verbose, --no-verbose
                        Verbose output. (default: False)
  --batch-size BATCH_SIZE
                        Max number of rules to import with each API request. (default: 100)
  --method METHOD       [api|file] Import Sigma via local files or via github API (default: file)
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

# export_rule_queries.py

Export sigma rules to markdown format.

## Prerequisites / Install

* Local copy of this repo (e.g. Download as Zip, or via git clone)
* Sigma rules in your Graylog Security environment
* Python 3 (tested on 3.9.13)
* [pip](https://pypi.org/project/pip/)
    * Install required pip packages
        * `python3 -m pip install -r requirements.txt`
* Configure contents of config.ini

## Instructions

execute

* `python3 export_rule_queries.py`

rules are exported into a series of folder beneath the `export` folder.

```
.\export
    |- categories
    |- products
    |- services 
```

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
python3 export_rule_queries.py
```

Specify a custom configuration filename. This is useful if you don't want your config file to conflict with the template/default config file from this repo.

```
python3 import_rules_docgen.py --config auth.ini
```

## Command Line Arguments

```
  -h, --help            show this help message and exit
  --debug, --no-debug, -d
                        For debugging (default: None)
  --config CONFIG       Config Filename (default: config.ini)
  --verbose, --no-verbose
                        Verbose output. (default: False)
  --perpage PERPAGE     Items Per Page. How many rules are returned from the graylog api at one time. (default: 100)
  --startpage STARTPAGE
                        Start Page. Graylog Sigma Rules page to start from. (default: 1)
  --endpage ENDPAGE     End Page. Graylog Sigma Rules page to end with. Useful to limit how many rules are exported at a given time. (default: 10000)
  --function FUNCTION   [markdown|ids] Type of operation/function to do. Markdown exports markdown files. IDs outputs a list of graylog IDs for each sigma rule,
                        one per line. IDs are helpful for doing bulk deletes. (default: markdown)
  --delete, --no-delete
                        Deletes existing markdown files (if present) before exporting rules to markdown. (default: True)

```

## Sample Output

```
Target Graylog Server: graylog.domain.tld
DELETING existing .md markdown files.
Skipping deletion: ./readme.md
Web Req: 1 of ?
Web Req: 2 of 23
Web Req: 3 of 23
Web Req: 4 of 23
Web Req: 5 of 23
Web Req: 6 of 23
Web Req: 7 of 23
Web Req: 8 of 23
Web Req: 9 of 23
Web Req: 10 of 23
Web Req: 11 of 23
Web Req: 12 of 23
Web Req: 13 of 23
Web Req: 14 of 23
Web Req: 15 of 23
Web Req: 16 of 23
Web Req: 17 of 23
Web Req: 18 of 23
Web Req: 19 of 23
Web Req: 20 of 23
Web Req: 21 of 23
Web Req: 22 of 23
Web Req: 23 of 23
Creating missing directory: export/
Creating missing directory: export/categories/
Creating missing directory: export/products/
Creating missing directory: export/services/

Categories: 39
Products: 21
Services: 56
```

# gen_sigma_fields.py

Used to gather information about sigma rules. Such as:

* Which fields are used in sigma rules
* Which fields are mapped via GIM (and which are not)
* What is the count of rules that use fields not mapped by GIM (and count of rules that do)
* What is the list of GIM incompatible fields
* What is the count of rules that do not specify and fields for the search query (and instead rely on full text search queries and a number of `OR` statements)

## Prerequisites

* Local copy of this repo (e.g. Download as Zip, or via git clone)
* Local copy of [SigmaHQ sigma](https://github.com/SigmaHQ/sigma) repo (specifically the `rules` directory)
* Python 3 (tested on 3.9.13)
* A copy of `core_sigma_field_map.csv` from an Illuminate Bundle (`illuminate/core/data/core_sigma_field_map.csv`) placed in the same directory as this python script.
## Instructions

execute

* `python3 gen_sigma_fields.py`

All output is output to console.

## Command Line Arguments

```
  -h, --help            show this help message and exit
  --debug, --no-debug, -d
                        For debugging (default: None)
  --dir DIR             Directory of sigma rules (default: rules)
  --csv CSV             Illuminate core sigma field map csv file. (default: core_sigma_field_map.csv)
  --verbose, --no-verbose
                        Verbose output. (default: False)
```

## Sample Output

```
Rules without fields in query: 48 of 2574 (2526 rules do have fields in query.)
["rules/web/web_jndi_exploit.yml", "rules/web/web_apache_threading_error.yml", "...", "..."]

GIM Compatible Fields (56 fields):
["TargetFilename", "Image", "CommandLine", "...", "..."]

GIM Incompatible Fields (Missing from illuminate csv lookup mapping) (405 fields):
["ImageName", "c-uri", "r-dns", "c-useragent", "cs-method", "...", "..."]

223 (of 2574) sigma rules have fields that are not mapped by Graylog Illuminate via core_sigma_field_map.csv
This means these rules cannot be effectively used with Graylog's Sigma Rules feature.
2351 (of 2574) sigma rules have fields that are mapped.
```
