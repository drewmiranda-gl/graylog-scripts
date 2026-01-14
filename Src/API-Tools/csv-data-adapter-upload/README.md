# Introduction

This is a proof of concept tool that contains 2 parts:

1. `graylog-create-csv-adapter.sh`
    - Uploads a CSV file and creates a CSV data adapter that references the uploaded file
2. `graylog-update-csv-file.sh`
    - Uploads a CSV file and replaces the existing csv file for a given CSV data adapter

These scripts have been tested against and known to work with Graylog 6.3 and 7.0 .

# Usage

Prerequisites:
- [curl](https://curl.se/)
- [jq](https://jqlang.org/)

1. Make a copy of `.config.env.example` and name if `.config.env`
2. Populate ENVVARs (Environmental Variables)
3. Execute script
    - `./<filename>`
    - `bash ./<filename>`

## Configuration

Configuration is done via `.config.env`. You may optionall want to change the owner and/or change file permissions (e.g. `chmod 600 .config.env`) to prevent unauthorized access to sensitive data, such as the Graylog API token.

ENVVAR | Notes
---- | ----
`GRAYLOG_URI_BASE` | Base URI for Graylog API<br>Should **NOT** have a trailing slash. Examples:<br><br>http://graylog.domain.tld:9000<br>https://graylog.domain.tld
`GRAYLOG_API_TOKEN` | API Token that these scripts will use. Token must have permissions to upload CSV files and create/edit data adapters. For information about Graylog API Tokens, see [REST API Access Tokens](https://go2docs.graylog.org/current/setting_up_graylog/rest_api_access_tokens.htm) (docs.graylog.org)
`GRAYLOG_DATA_ADAPTER_NAME` | Data Adapter **name**. Note that this is NOT the title, but specifically the **name**. This is the same name that the Lookup table uses to reference its associated data adapter.
`GRAYLOG_CSV_FILE_NAME_FULLPATH` | Path to CSV file. Can be relative or absolute, as long as the script can resolve the path.