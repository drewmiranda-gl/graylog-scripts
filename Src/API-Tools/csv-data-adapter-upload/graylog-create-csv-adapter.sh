#!/bin/bash

# wget https://raw.githubusercontent.com/drewmiranda-gl/graylog-scripts/refs/heads/main/Src/API-Tools/csv-data-adapter-upload/graylog-create-csv-adapter.sh

# graylog-create-csv-adapter.sh
# 
# Usage:
# ./ graylog-create-csv-adapter.sh
# or
# bash graylog-create-csv-adapter.sh
# 
# Uploads a CSV file and creates a CSV data adapter using uploaded CSV file

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

# check if data adapter already exists
echo -e "Checking if data table ${BLUE}${GRAYLOG_DATA_ADAPTER_NAME}${ENDCOLOR} already exists..."
currs=""
currs=$(curl \
    --silent \
    --fail \
    -X GET \
    "${GRAYLOG_URI_BASE}/api/system/lookup/adapters?page=1&per_page=50&sort=title&order=desc&query=name%3A%22${GRAYLOG_DATA_ADAPTER_NAME}%22" \
    --user "${GRAYLOG_API_TOKEN}":token)
curl_rs_exit_code=0
curl_rs_exit_code=$?
# verify curl returned a successful (0) exit code
if (( $? > 0 )); then
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

if [ $data_adapter_found_count -gt 0 ]; then
    echo -e "${YELLOW}Data adapter already exists${ENDCOLOR}: ${BLUE}${GRAYLOG_DATA_ADAPTER_NAME}${ENDCOLOR}"
    echo ${currs} | jq
    exit 0
fi

echo -e "${YELLOW}Data table does not exist${ENDCOLOR}: ${BLUE}${GRAYLOG_DATA_ADAPTER_NAME}${ENDCOLOR}"

# Validate that CSV file exists
if [ ! -f "${GRAYLOG_CSV_FILE_NAME_FULLPATH}" ]; then
    echo -e "${RED}ERROR${ENDCOLOR}: CSV file missing: ${BLUE}${GRAYLOG_CSV_FILE_NAME_FULLPATH}${ENDCOLOR}"
    exit 1
else
    echo -e "${GREEN}Validated CSV file exists${ENDCOLOR}: ${BLUE}${GRAYLOG_CSV_FILE_NAME_FULLPATH}${ENDCOLOR}"
fi

# Upload CSV file
echo "Upload CSV File..."
CSV_UPLOAD_CURL_RS=$(curl -X POST "${GRAYLOG_URI_BASE}/api/plugins/org.graylog.plugins.cloud/data_adapters/csv_files" \
    --fail \
    --silent \
    --user "${GRAYLOG_API_TOKEN}":token \
    -H 'accept: application/json' \
    -H 'x-requested-by: XMLHttpRequest' \
    -F "file=@${GRAYLOG_CSV_FILE_NAME_FULLPATH};type=text/csv")
curl_rs_exit_code=0
curl_rs_exit_code=$?
# verify curl returned a successful (0) exit code
if (( $? > 0 )); then
    echo -e "${RED}ERROR${ENDCOLOR}: CURL ERROR ${curl_rs_exit_code}. Upload failed."
    echo "$CSV_UPLOAD_CURL_RS"
    exit 1
fi
# obtain file_id returned from csv upload curl request
UPLOADED_DATA_ADAPTER_FILE_ID=$(echo $CSV_UPLOAD_CURL_RS | jq -r '.id')
echo -e "${GREEN}Uploaded File Successfully${ENDCOLOR}: ${BLUE}${UPLOADED_DATA_ADAPTER_FILE_ID}${ENDCOLOR}"

# Create CSV Data Adapter
echo "Creating CSV Data Adapter..."
GRAYLOG_DATA_ADAPTER_FILE_ID="${UPLOADED_DATA_ADAPTER_FILE_ID}"
curl "${GRAYLOG_URI_BASE}/api/system/lookup/adapters" \
    --silent \
    --fail \
    --user "${GRAYLOG_API_TOKEN}":token \
    -H 'accept: application/json' \
    -H 'content-type: application/json' \
    -H 'x-requested-by: XMLHttpRequest' \
    --data-raw "{\"id\":null,\"title\":\"${GRAYLOG_DATA_ADAPTER_NAME}\",\"description\":\"\",\"name\":\"${GRAYLOG_DATA_ADAPTER_NAME}\",\"config\":{\"type\":\"uploadcsvfile\",\"file_id\":\"${GRAYLOG_DATA_ADAPTER_FILE_ID}\",\"separator\":\",\",\"quotechar\":\"\\\"\",\"key_column\":\"a\",\"value_column\":\"b\",\"case_insensitive_lookup\":false}}"
curl_rs_exit_code=0
curl_rs_exit_code=$?
# verify curl returned a successful (0) exit code
if (( $? > 0 )); then
    echo -e "${RED}ERROR${ENDCOLOR}: CURL ERROR ${curl_rs_exit_code}. Data Adapter creation failed."
    exit 1
fi
echo ""
echo -e "${GREEN}CSV Data Adapter Successfully Created${ENDCOLOR}: ${BLUE}${GRAYLOG_DATA_ADAPTER_NAME}${ENDCOLOR}"