#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source ${SCRIPT_DIR}/config.sh
WORKING_STATE_FILE=${SCRIPT_DIR}/gl_indices
WORKING_STATE_ONLY_DEFLECTOR_NAMES=${SCRIPT_DIR}/gl_delfector_indices
OUTPUT_OPENSEARCH_DEFLECTORS=${SCRIPT_DIR}/deflector_indices_opensearch.csv

COMMA_INDEX_FOR_INDEX_SETS__INDEX_SET_ID=1
COMMA_INDEX_FOR_INDEX_SETS__INDEX_SET_TITLE=2

COMMA_INDEX_OPENSEARCH__INDEX=1
COMMA_INDEX_OPENSEARCH__SHARD=2
COMMA_INDEX_OPENSEARCH__PRIREP=3
COMMA_INDEX_OPENSEARCH__STATE=4
COMMA_INDEX_OPENSEARCH__NODE=5

RED="\e[31m"
YELLOW="\e[33m"
BLUE="\e[34m"
ENDCOLOR="\e[0m"

ERROR_CONTROL() {
    if (( $1 > 0 )); then
        echo "NON ZERO EXIT CODE: ${1}"
        exit
    fi
}

EXIT_ON_EMPTY() {
    if [[ -z $1 ]]; then
        # echo "${2}"
        echo -e "${RED}${2}${ENDCOLOR}"
        exit 1
    fi
}

EXIT_ON_WHICH_EMPTY() {
    (which $1 > /dev/null)
    exit_code=$?
    if (( $exit_code > 0 )); then
        echo -e "${RED}ERROR:${ENDCOLOR} cannot find ${1}"
        echo "Resolve by installing package: ${2}"
        exit
    fi
}

CONCAT(){
    echo "$1$2"
}

to_lowercase(){
    echo $(echo ${1} | awk '{print tolower($1)}')
}

escape_quotes() {
  local input="$1"
  echo "$input" | sed 's/"/\\"/g'
}

TRIM_LAST_SLASH() {
    # echo $1
    echo "$1" | sed 's/\/$//'
}

GRAYLOG_URL_BASE=$(TRIM_LAST_SLASH $GRAYLOG_URL_BASE)
OPENSEARCH_URL_BASE=$(TRIM_LAST_SLASH $OPENSEARCH_URL_BASE)

EXEC_CURL() {
    CURL_URL="$1"
    USNPWBASESIXFOUR=$(echo -n $2 | openssl base64 -A)

    HEADER_AUTH="--header"
    HEADER_AUTH_VAL="Authorization: Basic ${USNPWBASESIXFOUR}"
    if [[ -z $1 ]]; then
        HEADER_AUTH=""
        HEADER_AUTH_VAL=""
    fi

    curl --silent --location "$CURL_URL" $HEADER_AUTH "$HEADER_AUTH_VAL"
}

QUERY_GRAYLOG_API() {
    API_URL=$1
    # GRAYLOG_API_TOKEN
    # GRAYLOG_URL_BASE
    CURL_URL="${GRAYLOG_URL_BASE}${API_URL}"
    USNPW="${GRAYLOG_API_TOKEN}:token"
    EXEC_CURL "$CURL_URL" "$USNPW"
    
}

QUERY_OPENSEARCH_API() {
    API_URL=$1
    # GRAYLOG_API_TOKEN
    # GRAYLOG_URL_BASE
    CURL_URL="${OPENSEARCH_URL_BASE}${API_URL}"
    EXEC_CURL "$CURL_URL"
}

GET_QUERY_GL_INDEX_SETS() {
    # echo -e "${BLUE}Building list of Graylog Index Sets${ENDCOLOR}"
    JSON=$(QUERY_GRAYLOG_API "/api/system/indices/index_sets?skip=0&limit=0&stats=false")
    echo $JSON | jq -r '.index_sets[] | .id + "," + .title'
}

GET_QUERY_GL_INDEX_SET_DEFLECTOR() {
    INDEX_SET_ID="$1"
    JSON=$(QUERY_GRAYLOG_API "/api/system/indexer/overview/${INDEX_SET_ID}")
    echo $JSON | jq -r '.deflector.current_target'
}

WRITE_INDEX_SET_INFO_TO_CSV() {
    echo -e "${BLUE}Outputting list of Graylog deflector index names to temp file${ENDCOLOR}: '${WORKING_STATE_FILE}'..."
    echo "id,name,deflector" > $WORKING_STATE_FILE
    echo "" > $WORKING_STATE_ONLY_DEFLECTOR_NAMES

    ISSET=0
    while IFS= read -r line ; do
        if (( ISSET > 1000 )); then
            break
        fi
        INDEX_SET_ID=$(echo $line | cut -d',' -f$COMMA_INDEX_FOR_INDEX_SETS__INDEX_SET_ID)
        INDEX_SET_TITLE=$(echo $line | cut -d',' -f$COMMA_INDEX_FOR_INDEX_SETS__INDEX_SET_TITLE)
        INDEX_SET_DEFLECTOR=$(GET_QUERY_GL_INDEX_SET_DEFLECTOR $INDEX_SET_ID)
        
        OUTPUT_LINE="${INDEX_SET_ID},${INDEX_SET_TITLE},${INDEX_SET_DEFLECTOR}"
        # echo $OUTPUT_LINE
        echo $OUTPUT_LINE >> $WORKING_STATE_FILE
        echo $INDEX_SET_DEFLECTOR >> $WORKING_STATE_ONLY_DEFLECTOR_NAMES

        ISSET=$((ISSET+1))
    done <<< "$1"
}

GET_OPENSEARCH_SHARDS() {
    JSON=$(QUERY_OPENSEARCH_API "/_cat/shards?format=json")
    echo $JSON | jq -r '.[] | .index + "," + .shard + "," + .prirep +  "," + .state + "," + .node'
}

FIND_DEFLECTOR_IN_OPENSEARCH() {
    echo -e "${BLUE}Comparing list of Graylog deflector indices to OpenSearch...${ENDCOLOR}"
    SHARDS=$(GET_OPENSEARCH_SHARDS)

    echo "index,shard,prirep,state,node" > $OUTPUT_OPENSEARCH_DEFLECTORS

    while IFS= read -r line ; do
        # echo ""
        # echo $line

        # COMMA_INDEX_OPENSEARCH__INDEX
        # COMMA_INDEX_OPENSEARCH__SHARD
        # COMMA_INDEX_OPENSEARCH__STATE
        # COMMA_INDEX_OPENSEARCH__NODE

        OPENSEARCH_INDEX=$(echo $line | cut -d',' -f$COMMA_INDEX_OPENSEARCH__INDEX)
        OPENSEARCH_SHARD=$(echo $line | cut -d',' -f$COMMA_INDEX_OPENSEARCH__SHARD)
        OPENSEARCH_PRIREP=$(echo $line | cut -d',' -f$COMMA_INDEX_OPENSEARCH__PRIREP)
        OPENSEARCH_STATE=$(echo $line | cut -d',' -f$COMMA_INDEX_OPENSEARCH__STATE)
        OPENSEARCH_NODE=$(echo $line | cut -d',' -f$COMMA_INDEX_OPENSEARCH__NODE)

        # echo $OPENSEARCH_INDEX

        # while IFS= read -r line ; do
        #     INDEX_SET_ID=$(echo $line | cut -d',' -f$COMMA_INDEX_FOR_INDEX_SETS__INDEX_SET_ID)
        #     INDEX_SET_TITLE=$(echo $line | cut -d',' -f$COMMA_INDEX_FOR_INDEX_SETS__INDEX_SET_TITLE)
        #     INDEX_SET_DEFLECTOR=$(GET_QUERY_GL_INDEX_SET_DEFLECTOR $INDEX_SET_ID)
        #     if [ "$OPENSEARCH_INDEX" == "$INDEX_SET_DEFLECTOR" ]; then
        #         echo $OPENSEARCH_INDEX
        #         echo -e "Deflector Index: ${YELLOW}${OPENSEARCH_INDEX}${ENDCOLOR}"
        #     else
        #         echo "NOT a deflector index: ${OPENSEARCH_INDEX}"
        #     fi
        # done <<< "$(cat $WORKING_STATE_FILE)"

        if [ ! -z $(grep "$OPENSEARCH_INDEX" "$WORKING_STATE_ONLY_DEFLECTOR_NAMES") ]; then
            echo -e "Deflector Index: ${YELLOW}${OPENSEARCH_INDEX}${ENDCOLOR}"
            echo "${OPENSEARCH_INDEX},${OPENSEARCH_SHARD},${OPENSEARCH_PRIREP},${OPENSEARCH_STATE},${OPENSEARCH_NODE}" >> $OUTPUT_OPENSEARCH_DEFLECTORS
        else
            # echo "NOT a deflector index: ${OPENSEARCH_INDEX}"
            a=1
        fi

    done <<< "$SHARDS"
    echo -e "${BLUE}Output final CSV file: ${ENDCOLOR} $OUTPUT_OPENSEARCH_DEFLECTORS"
}

MAIN() {
    # 1. Get list of index sets
    # id,name,deflector
    INDEX_SETS=$(GET_QUERY_GL_INDEX_SETS)
    WRITE_INDEX_SET_INFO_TO_CSV "$INDEX_SETS"
    
    # 2. compare with OpenSearch shards
    FIND_DEFLECTOR_IN_OPENSEARCH
}

# verify dependencies
EXIT_ON_WHICH_EMPTY "curl" "curl"
EXIT_ON_WHICH_EMPTY "jq" "jq"

# verify inputs/config
MSG_EMPTY="empty or not configured. See config.sh"
EXIT_ON_EMPTY "$GRAYLOG_URL_BASE" "\$GRAYLOG_URL_BASE${MSG_EMPTY}"
EXIT_ON_EMPTY "$GRAYLOG_API_TOKEN" "\$GRAYLOG_API_TOKEN${MSG_EMPTY}"
EXIT_ON_EMPTY "$OPENSEARCH_URL_BASE" "\$OPENSEARCH_URL_BASE${MSG_EMPTY}"

MAIN