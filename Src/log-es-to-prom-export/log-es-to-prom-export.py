# python3.10 -m  pipreqs.pipreqs --encoding utf-8 . --force

import argparse
from os.path import exists
import os
import yaml
import logging
import colorlog
from colorlog import ColoredFormatter
import requests
import json
import re
import socket
from flatten_json import flatten

parser = argparse.ArgumentParser()
parser.add_argument("--sources", help='Config file to use. Defaults to sources.yml', default="sources.yml", type=str, required=False)
parser.add_argument("--out", help='File to write output to', default="out.txt", type=str, required=False)
parser.add_argument("--log", help="Output Log File", default="run.log", type=str)
parser.add_argument("--console-level", default="INFO", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
parser.add_argument("--log-level", default="INFO", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])

args = parser.parse_args()

host_hostname = socket.gethostname()

logger = logging.getLogger('PythonFetchAndLog')
logger.setLevel(logging.DEBUG)
logFile = str(args.log)

def log_level_from_string(log_level: str):
    if log_level.upper() == "DEBUG":
        return logging.DEBUG
    elif log_level.upper() == "INFO":
        return logging.INFO
    elif log_level.upper() == "WARN":
        return logging.WARN
    elif log_level.upper() == "ERROR":
        return logging.ERROR
    elif log_level.upper() == "CRITICAL":
        return logging.CRITICAL

    return logging.INFO

# handlers
logging_file_handler = logging.FileHandler(logFile)
logging_file_handler.setLevel(log_level_from_string(str(args.log_level)))
formatter = logging.Formatter('%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s', '%Y-%m-%d %H:%M:%S')
logging_file_handler.setFormatter(formatter)
logger.addHandler(logging_file_handler)

logging_console_handler = colorlog.StreamHandler()
logging_console_handler.setLevel(log_level_from_string(str(args.console_level)))
formatter = ColoredFormatter(
        '%(asctime)s.%(msecs)03d %(log_color)s%(levelname)-8s%(reset)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        reset=True,
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )
logging_console_handler.setFormatter(formatter)
logger.addHandler(logging_console_handler)

# alias so we don't break existing logging
logging = logger




if exists(args.sources):
    print("Using Sources file: " + str(args.sources))

    with open(args.sources, 'r') as stream:
        d_yaml_out = yaml.safe_load(stream)
        if not "sources" in d_yaml_out:
            logging.critical("Invalid config.yml")
            exit(1)
        d_sources = d_yaml_out['sources']
else:
    logging.critical("".join(["Sources file ", args.sources, " does not exist!"]))
    exit(1)

def read_sources(get_sources: dict):
    str_final_concat = ""
    
    for source in get_sources:
        b_enabled = True
        d_source_data = get_sources[source]
        source_url = ""
        json_payload = {}

        if "enabled" in d_source_data:
            if d_source_data["enabled"] == False:
                b_enabled = False
        
        if b_enabled == True:
            b_valid = True
            if "http_uri" in d_source_data:
                source_url = d_source_data["http_uri"]
            else:
                b_valid = False
                logger.warning("".join(["Source '", source, "' missing required property 'http_uri'."]))
            
            if "json_payload" in d_source_data:
                json_payload = d_source_data["json_payload"]
            else:
                b_valid = False
                logger.warning("".join(["Source '", source, "' missing required property 'json_payload'."]))
        
            if b_valid == True:
                rs_json = search_elasticsearch(source_url, json_payload)
                rs_prom = json_to_prom_exporter_format(rs_json)
                str_final_concat = "".join([str_final_concat, rs_prom])

    return str_final_concat

def writeToFile(handle, text):
    handle.write(text + "\n")

def console_debug_out_json_from_jsonobj(arg):
    logger.debug(json.dumps(arg, indent=4))

def json_to_prom_exporter_format(str_arg_json):
    l_ignore_keys = ["@timestamp"]
    d_new = {}
    d_labels = {}
    d_metrics = {}

    # remove unwanted stuf
    for key_name in str_arg_json:
        if not key_name in l_ignore_keys:
            # logger.debug(key_name)
            d_new[key_name] = str_arg_json[key_name]
    
    flat_json = flatten(d_new)
    
    # build labels and metrics
    for key_name in flat_json:
        if type(flat_json[key_name]) == int:
            logger.debug("".join(["Field ", key_name, " is NUMERIC"]))
            d_metrics[key_name] = flat_json[key_name]
        else:
            logger.debug("".join(["Field ", key_name, " is NOT numeric"]))
            d_labels[key_name] = flat_json[key_name]
    
    str_label_concat = ""
    i_labels = 0
    for label_key_name in d_labels:
        if i_labels > 0:
            str_label_concat = "".join([str_label_concat, ", "])
        str_label_concat = "".join([str_label_concat, label_key_name, "=", '"', d_labels[label_key_name], '"'])
        i_labels = i_labels + 1
    
    # logger.debug(str_label_concat)

    str_metric_concat = ""
    for metric_key_name in d_metrics:
        str_metric_concat = "".join([str_metric_concat, metric_key_name, "{", str_label_concat,"}", " ", str(d_metrics[metric_key_name]), "\n"])

    logger.debug(str_metric_concat)
    return str_metric_concat
    return ""

def search_elasticsearch(str_web_uri, str_arg_payload):
    d_json_payload = str_arg_payload

    args_for_req = {}
    args_for_req["url"] = "".join([str_web_uri, "/_search"])
    args_for_req["json"] = d_json_payload
    args_for_req["headers"] = {"Content-Type":"application/json"}
    logging.debug(json.dumps(args_for_req, indent=4))

    try:
        # r = requests.delete(sUrl, json = argJson, headers=sHeaders, verify=False, auth=HTTPBasicAuth(sArgUser, sArgPw))
        r = requests.post(**args_for_req)

        logging.info("".join([
                "HTTP Response", 
                "\n", "    URL:", args_for_req["url"], 
                "\n", "    Code:", str(r.status_code)
            ]))
        # r.status_code
        # print(r.headers)
        # print(r.text)
        # exit()
        # return json.loads(r.text)
        # return r.text

    except Exception as e:
        logging.error(e)

    rs_json = json.loads(r.text)
    # rs_json_text = json.dumps(rs_json, indent=4)
    # logger.debug(rs_json_text)

    if not "hits" in rs_json:
        logger.warning("'hits' not found in rs_json")
        return ""
    
    if not "hits" in rs_json["hits"]:
        logger.warning("'hits' not found in rs_json['hits']")
        return ""

    try:
        return rs_json["hits"]["hits"][0]["_source"]
    except Exception as e:
        logging.error(e)

    return ""

def write_prom_output(text_to_write):
    sFileTemp = args.out + ".tmp"
    if exists(sFileTemp):
        os.remove(sFileTemp)
    
    f = open(sFileTemp, "a")
    writeToFile(f, text_to_write)
    if exists(sFileTemp):
        os.rename(sFileTemp,args.out)

    return ""


output_to_export = read_sources(d_sources)
write_prom_output(output_to_export)
exit()



# 1. query ES
str_payload = {
        "query": {
            "bool" : {
                "must": [
                    {"term" : {"measurement_name": "net"}},
                    {"term" : {"tag.interface": "mvneta0"}}
                ]
            }
        },
        "size": 1,
        "sort" : [
            { "@timestamp" : "desc" }
        ]
    }
rs_json = search_elasticsearch("http://pve-dock-pf-es.drew.local:9201", str_payload)

# 2. format to exporter
rs_prom = json_to_prom_exporter_format(rs_json)

# 3. write output
write_prom_output(rs_prom)