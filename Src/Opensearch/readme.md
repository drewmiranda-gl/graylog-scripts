# Custom Opensearch/Elasticsearch Index Template for Graylog Schema Field Mappings

## What is this?

This is an example and reference custom index template for Elasticsearch/Opensearch (lucene_version 7 or higher) that explicitly maps the datatype of fields that cannot be dynamically typed. For example, elasticsearch/opensearch will not dynamically type a field as `ip` nor `integer`. In order to type fields as these, an explicit field mapping must be declared using an index template.

## Why does this exist?

The short answer is that in order to use elasticsearch/opensearch to do aggregations on fields, the field types across all indices contained in the aggregation, **MUST** be the same data type. This creates challenges when mixing log messages from [Graylog Illuminate](https://docs.graylog.org/docs/illuminate) (Which strictly adheres to the [Graylog Schema](https://schema.graylog.org/en/stable/)) incises and non Graylog Illuminate indices, such as those created by end users. If any of the non Graylog illumiate incidences contain fields that are part of the Graylog Schema, widgets will return errors because of aggregation errors from elaticsearch/opensearch.

The only solution to this is to explicitly declare data types for fields in non illuminate indices so that the data types match the data types in graylog illuminate indices

## How to use this?

### Prerequisites

* lucene_version 7 or higher
* Ability to send web requests to your elasticsearch/opensearch cluster

### Disclaimer

This information is provided as is and without any warranty.

Specifying an index template will override ALL default mappings from the out of box graylog default. For this reason, it is incredibly important that the mappings from the default graylog template are also declared in your custom index template.

Failing to do so will break your graylog cluster and no messages will be viewable from graylog.

Be sure to test on a cluster and on data that you don’t care about.

### Usage

1. Modify the index template `.json` file to include the pattern of indices you want this index template to apply to:
    * `"index_patterns": ["indexPrefixA_*", "indexPrefixB_*"],`
        * Multiple values can be listed, be sure to end with `*` so that it will match all indices
    * NOTE: index templates apply ONLY to newly created indices and DO NOT apply to any existing indices. To apply to an index set immediately:
        1. Go to the index set configuration page of the desired index
        2. Maintenance / Rotate active write index
2. Send web request
    * Method: `PUT`
    * Address: `/_index_template/gimness_template?pretty`
        * NOTE: you will need to specify the full address of the web request
            * example: `http://servername.domain.tld:9200/_index_template/index_template_name?pretty`
                * Replace `index_template_name` with the name of the index template. The name of the template doesn't affect index settings nor field mappings, but allows you to assign a name so you can view/delete it later.
    * Headers:
        * Content-Type: application/json
    * Body: raw
        * json from `.json` file

If the cluster accepts the request and there are no errors/issues, you will receive an `HTTP 200` status code with the following json response:

```json
{
    "acknowledged": true
}
```
