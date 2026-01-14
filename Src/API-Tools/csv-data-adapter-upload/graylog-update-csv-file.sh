#!/bin/bash

# wget https://raw.githubusercontent.com/drewmiranda-gl/graylog-scripts/refs/heads/main/Src/API-Tools/csv-data-adapter-upload/graylog-update-csv-file.sh

# graylog-update-csv-file.sh
# 
# Usage:
# ./graylog-update-csv-file.sh
# or
# bash graylog-update-csv-file.sh
# 
# Uploads a new CSV file in place of an existing one, for a CSV Data Adapter

# DECLARE VARIABLES ===========================================================
case "$OSTYPE" in
  darwin*|bsd*)
    # echo "Detected OS: MacOS (${OSTYPE})"
    # CLICOLOR=1
    # export CLICOLOR=1
    # export TERM="xterm-256color"
    # autoload -U colors && colors
    RED="\x1B[31m"
    GREEN="\x1B[32m"
    BLUE="\x1B[34m"
    YELLOW="\x1B[33m"
    ENDCOLOR="\x1B[0m"
    ;;
  *)
    RED="\e[31m"
    GREEN="\e[32m"
    BLUE="\e[34m"
    YELLOW="\e[33m"
    ENDCOLOR="\e[0m"
  ;;
esac


CURDIR=$(pwd)
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
CONFIG_FILE_ABS_PATH="${SCRIPT_DIR}/.config.env"

# FUNCTIONS ===================================================================

# VALIDATE_MISSING_ENVVAR
# 
# Usage:
# VALIDATE_MISSING_ENVVAR "ENV_VAR_NAME"
# 
# Tests if the specified ENVVAR is empty. Exits if empty.
VALIDATE_MISSING_ENVVAR() {
    local ENVVAR="$1"
    if [[ -z ${!ENVVAR} ]]; then
        echo -e "${RED}ERROR${ENDCOLOR}: envvar not configured ${BLUE}${ENVVAR}${ENDCOLOR}. Please reference ${BULE}.config.env.example${ENDCOLOR}"
        exit 1
    fi
}

# EXIT_ON_WHICH_EMPTY
# 
# Usage:
# EXIT_ON_WHICH_EMPTY "binary_name"
# 
# Uses which to test if a program exists. Exists if missing.
EXIT_ON_WHICH_EMPTY() {
    (which $1 >/dev/null 2>&1)
    exit_code=$?
    if (( $exit_code > 0 )); then
        echo "ERROR: cannot find ${1}"
        exit
    fi
}

# VALIDATION AND SAFETY CHECKS ================================================
if [ -f "${CONFIG_FILE_ABS_PATH}" ]; then
    source "${CONFIG_FILE_ABS_PATH}"
else
    echo -e "${RED}ERROR${ENDCOLOR}: missing config file: ${CONFIG_FILE_ABS_PATH}"
    echo -e "Consult ${BLUE}.config.env.example${ENDCOLOR} as an example and copy to ${GREEN}.config.env${ENDCOLOR}"
    exit 1
fi

VALIDATE_MISSING_ENVVAR "GRAYLOG_URI_BASE"
VALIDATE_MISSING_ENVVAR "GRAYLOG_API_TOKEN"
VALIDATE_MISSING_ENVVAR "GRAYLOG_DATA_ADAPTER_NAME"
VALIDATE_MISSING_ENVVAR "GRAYLOG_CSV_FILE_NAME_FULLPATH"

EXIT_ON_WHICH_EMPTY "curl"
EXIT_ON_WHICH_EMPTY "jq"

# =============================================================================
# =============================================================================
# =============================================================================
# MAIN LOGIC OF SCRIPT ========================================================

# trim tailing slash, we cannot have it
GRAYLOG_URI_BASE=$(echo $GRAYLOG_URI_BASE | sed 's/\/$//')

# TEST THAT WE CAN SUCCESSFULLY AUTH
INITIAL_CURL_HTTP_CODE=$(curl \
    -s -o /dev/null -w "%{http_code}" \
    "${GRAYLOG_URI_BASE}/api/system/lookup/adapters?page=1&per_page=1" \
    --user "${GRAYLOG_API_TOKEN}":token)
# echo $INITIAL_CURL_HTTP_CODE
if [[ $INITIAL_CURL_HTTP_CODE -eq 200 ]]; then
    echo -e "${GREEN}Verified that we can successfully authenticate to Graylog API.${ENDCOLOR}"
else
    echo -e "${RED}ERROR${ENDCOLOR}: ${RED}Failed to authenticate${ENDCOLOR} to Graylog API using token. HTTP Code: ${RED}${INITIAL_CURL_HTTP_CODE}${ENDCOLOR} . Please verify token is correct."
    exit 1
fi

# check if data adapter already exists
echo -e "Checking if data table ${BLUE}${GRAYLOG_DATA_ADAPTER_NAME}${ENDCOLOR} already exists..."
currs=""
curl_rs_exit_code=0
currs=$(curl \
    --silent \
    --fail \
    -X GET \
    "${GRAYLOG_URI_BASE}/api/system/lookup/adapters?page=1&per_page=50&sort=title&order=desc&query=name%3A%22${GRAYLOG_DATA_ADAPTER_NAME}%22" \
    --user "${GRAYLOG_API_TOKEN}":token)
curl_rs_exit_code=$?
# verify curl returned a successful (0) exit code
if (( $curl_rs_exit_code > 0 )); then
    echo -e "${RED}ERROR${ENDCOLOR}: CURL ERROR ${curl_rs_exit_code}. Upload failed."
    echo "$CSV_UPLOAD_CURL_RS"
    exit 1
fi

data_adapter_found_count=0
data_adapter_found_count=$(echo ${currs} | jq '.count')
jq_ret_code=$?
if [ $jq_ret_code -gt 0 ]; then
    echo -e "${RED}ERROR${ENDCOLOR}: invalid json returned."
    echo -e "${YELLOW}${currs}${ENDCOLOR}"
    echo -e "${RED}ERROR${ENDCOLOR}: invalid json returned above."
    exit 1
fi

if [ $data_adapter_found_count -lt 1 ]; then
    echo -e "${RED}Data adapter missing${ENDCOLOR}: ${BLUE}${GRAYLOG_DATA_ADAPTER_NAME}${ENDCOLOR}"
    echo "Please use ${BLUE}graylog-create-csv-adapter.sh${ENDCOLOR} to create data adapter."
    exit 1
else
    echo -e "${GREEN}Data table exists${ENDCOLOR}: ${BLUE}${GRAYLOG_DATA_ADAPTER_NAME}${ENDCOLOR}"
fi

# Validate that CSV file exists
if [ ! -f "${GRAYLOG_CSV_FILE_NAME_FULLPATH}" ]; then
    echo -e "${RED}ERROR${ENDCOLOR}: CSV file missing: ${BLUE}${GRAYLOG_CSV_FILE_NAME_FULLPATH}${ENDCOLOR}"
    exit 1
else
    echo -e "${GREEN}Validated CSV file exists${ENDCOLOR}: ${BLUE}${GRAYLOG_CSV_FILE_NAME_FULLPATH}${ENDCOLOR}"
fi

# Upload CSV file
echo "Upload CSV File..."
curl_rs_exit_code=0
CSV_UPLOAD_CURL_RS=$(curl -X POST "${GRAYLOG_URI_BASE}/api/plugins/org.graylog.plugins.cloud/data_adapters/csv_files" \
    --fail \
    --silent \
    --user "${GRAYLOG_API_TOKEN}":token \
    -H 'accept: application/json' \
    -H 'x-requested-by: XMLHttpRequest' \
    -F "file=@${GRAYLOG_CSV_FILE_NAME_FULLPATH};type=text/csv")
curl_rs_exit_code=$?
# verify curl returned a successful (0) exit code
if (( $curl_rs_exit_code > 0 )); then
    echo -e "${RED}ERROR${ENDCOLOR}: CURL ERROR ${curl_rs_exit_code}. Upload failed."
    echo "$CSV_UPLOAD_CURL_RS"
    exit 1
fi
# obtain file_id returned from csv upload curl request
UPLOADED_DATA_ADAPTER_FILE_ID=$(echo $CSV_UPLOAD_CURL_RS | jq -r '.id')
echo -e "${GREEN}Uploaded File Successfully${ENDCOLOR}: ${BLUE}${UPLOADED_DATA_ADAPTER_FILE_ID}${ENDCOLOR}"

# Get existing Data Adapter config
EXISTING_GRAYLOG_DATA_ADAPTER_JSON_CONF=$(curl \
    --silent \
    --fail \
    "${GRAYLOG_URI_BASE}/api/system/lookup/adapters?page=1&per_page=1&sort=title&order=desc&query=name%3A%22${GRAYLOG_DATA_ADAPTER_NAME}%22" \
    --user "${GRAYLOG_API_TOKEN}":token)
GRAYLOG_DATA_ADAPTER_ID=$(echo $EXISTING_GRAYLOG_DATA_ADAPTER_JSON_CONF | jq -r '.data_adapters[].id')

EXISTING_GRAYLOG_DATA_ADAPTER_JSON_CONF=""
EXISTING_GRAYLOG_DATA_ADAPTER_JSON_CONF=$(curl \
    --silent \
    --fail \
    "${GRAYLOG_URI_BASE}/api/system/lookup/adapters/${GRAYLOG_DATA_ADAPTER_ID}" \
    --user "${GRAYLOG_API_TOKEN}":token)
# echo -e "${RED}${EXISTING_GRAYLOG_DATA_ADAPTER_JSON_CONF}${ENDCOLOR}"

NEW_GRAYLOG_DATA_ADAPTER_JSON_CONF=$(echo $EXISTING_GRAYLOG_DATA_ADAPTER_JSON_CONF | jq ".config.file_id = \"${UPLOADED_DATA_ADAPTER_FILE_ID}\"")

echo -e "${YELLOW}${NEW_GRAYLOG_DATA_ADAPTER_JSON_CONF}${ENDCOLOR}"

# Update existing Data Adapter with new CSV file_id
curl_rs_exit_code=0
curl "${GRAYLOG_URI_BASE}/api/system/lookup/adapters/${GRAYLOG_DATA_ADAPTER_ID}" \
    --silent \
    --fail \
    --user "${GRAYLOG_API_TOKEN}":token \
    -X 'PUT' \
    -H 'accept: application/json' \
    -H 'content-type: application/json' \
    -H 'x-requested-by: XMLHttpRequest' \
    --data-raw "${NEW_GRAYLOG_DATA_ADAPTER_JSON_CONF}"
curl_rs_exit_code=$?
# verify curl returned a successful (0) exit code
if (( $curl_rs_exit_code > 0 )); then
    echo -e "${RED}ERROR${ENDCOLOR}: CURL ERROR ${curl_rs_exit_code}. Upload failed."
    echo "$CSV_UPLOAD_CURL_RS"
    exit 1
fi

echo -e "${GREEN}Data Adapter CSV File Updated Successfully${ENDCOLOR}"