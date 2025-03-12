# graylog-active-write-index-which-indexer-node

## What is this?

This is a bash script that:

1. Queries Graylog api
    * `/api/system/indices/index_sets` to get a list of Index Set IDs
    * `/api/system/indexer/overview/<index_set_id>` to find which index is the current deflector index
2. Queries OpenSearch `/_cat/shards`
3. Outputs a CSV file with a list of deflector index names in the following format:
    * `index,shard,prirep,state,node`
    * Which can be opened in a tool like Microsoft Excel for quick sorting/filtering

## How to use?

### Prerequisites

This requires the following packages:

* `curl`
* `jq`

### Install/Configure/Run

1. Save files to your local device
    * `get.sh`
    * `config.sh`
2. Configure
    * `GRAYLOG_URL_BASE`
        * Graylog Base URL. Must not contain a path nor slashes (`/`)
        * Examples:
            * `http://host.domain.tld:9000`
            * `https://host.domain.tld`
    * `GRAYLOG_API_TOKEN`
        * API token that has permissions to query the above API endpoints
        * Tested with an admin token
    * `OPENSEARCH_URL_BASE`
        * OpenSearch Base URL. Must not contain a path nor slashes (`/`)
        * Examples:
            * `http://host.domain.tld:9200`
3. Execute `get.sh`
    * `bash get.sh`
    * or
        * `chmod +x get.sh`
        * `./get.sh`
4. look for output csv file: `deflector_indices_opensearch.csv`