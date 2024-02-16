# python3.10 -m  pipreqs.pipreqs --encoding utf-8 . --force

import argparse
from os.path import exists
import yaml
import logging
import colorlog
from colorlog import ColoredFormatter
import requests
import json
from flatten_json import flatten
import re
import socket
import jsonpath_ng.ext as jp

parser = argparse.ArgumentParser()
parser.add_argument("--sources", help='Config file to use. Defaults to sources.yml', default="sources.yml", type=str, required=False)
parser.add_argument("--graylog", help='Config file to use. Defaults to graylog.yml', default="graylog.yml", type=str, required=False)
parser.add_argument("--log", help="Output Log File", default="run.log", type=str)
parser.add_argument("--console-level", default="INFO", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
parser.add_argument("--log-level", default="INFO", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
parser.add_argument("--send-graylog", help="For debugging", action=argparse.BooleanOptionalAction, default=True)

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

d_graylog_static_fields = {}
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

if exists(args.graylog):
    print("Using Graylog file: " + str(args.graylog))
        
    with open(args.graylog, 'r') as stream:
        d_yaml_out = yaml.safe_load(stream)
        
        b_graylog_config_valid = True
        if not "graylog" in d_yaml_out:
            b_graylog_config_valid = False
        
        if b_graylog_config_valid == True:
            if not "gelf_http" in d_yaml_out["graylog"]:
                b_graylog_config_valid = False
        if b_graylog_config_valid == True:
            if not "host" in d_yaml_out["graylog"]["gelf_http"]:
                b_graylog_config_valid = False
        if b_graylog_config_valid == True:
            if not "port" in d_yaml_out["graylog"]["gelf_http"]:
                b_graylog_config_valid = False

        if b_graylog_config_valid == True:
            get_graylog_conf = d_yaml_out["graylog"]
            gelf_http_host = str(get_graylog_conf["gelf_http"]["host"])
            gelf_http_port = str(get_graylog_conf["gelf_http"]["port"])

            if "static_fields" in get_graylog_conf:
                for static_field_key in get_graylog_conf["static_fields"]:
                    d_graylog_static_fields[static_field_key] = get_graylog_conf["static_fields"][static_field_key]

        else:
            logging.critical("Invalid Graylog Config")
            exit(1)
else:
    logging.critical("".join(["Sources file ", args.graylog, " does not exist!"]))
    exit(1)


def fetch_web(s_url: str, d_headers:dict ={}):
    args_for_req = {}
    args_for_req["url"] = s_url
    # args_for_req["json"] = argJson
    args_for_req["headers"] = d_headers
    # args_for_req["verify"] = False
    # args_for_req["auth"] = HTTPBasicAuth(sArgUser, sArgPw)

    try:
        # r = requests.delete(sUrl, json = argJson, headers=sHeaders, verify=False, auth=HTTPBasicAuth(sArgUser, sArgPw))
        r = requests.get(**args_for_req)

        # print(r.status_code)
        # print(r.headers)
        # print(r.text)
        # exit()
        # return json.loads(r.text)
        return r.text

    except Exception as e:
        logging.error(e)

def process_json(d_json: dict):
    rs_d_json = {}
    for key in d_json:
        new_key = key
        new_key = re.sub(r'(?i)_(\d+)', r"\1", new_key)

        rs_d_json[key] = d_json[key]
        rs_d_json[new_key] = d_json[key]

    return rs_d_json

def set_type_helper(type_set_set, data):
    if type_set_set == "str":
        return str(data)
    elif type_set_set == "int":
        return int(data)
    elif type_set_set == "float":
        return float(data)
    else:
        return data

def publish_gelf(s_source_url: str, d_json_payload: dict, d_source_config: dict, source_rule: str):
    d_json_payload["host"] = host_hostname
    d_json_payload["source_url"] = s_source_url
    d_json_payload["rule"] = source_rule
    for static_field_key in d_graylog_static_fields:
        d_json_payload[static_field_key] = d_graylog_static_fields[static_field_key]

    if "ignore_rules" in d_source_config:
        for ignore_rule in d_source_config["ignore_rules"]:
            val_to_compare = ""
            val_to_compare = d_json_payload[ignore_rule]

            logging.debug(ignore_rule)
            logging.debug(val_to_compare)

            if re.match(d_source_config["ignore_rules"][ignore_rule], val_to_compare):
                logging.debug("".join(["ignore_rule = ", val_to_compare, ": ", d_source_config["ignore_rules"][ignore_rule]]))
                return False

    if "field_types" in d_source_config:
        for field_typing in d_source_config["field_types"]:
            # logging.debug(field_typing)
            d_json_payload[field_typing] = set_type_helper(d_source_config["field_types"][field_typing], d_json_payload[field_typing])
            # if d_source_config["field_types"][field_typing] == "int":
                # d_json_payload[field_typing] = float(d_json_payload[field_typing])
    
    if "rename_fields" in d_source_config:
        for rename_this_field in d_source_config["rename_fields"]:
            if rename_this_field in d_json_payload:
                payload = d_json_payload[rename_this_field]
                if "field_types" in d_source_config:
                    if rename_this_field in d_source_config["field_types"]:
                        payload = set_type_helper(d_source_config["field_types"][rename_this_field], d_json_payload[rename_this_field])
                d_json_payload[d_source_config["rename_fields"][rename_this_field]] = payload
                d_json_payload.pop(rename_this_field)

    if "remove_fields" in d_source_config:
        for remove_field in d_source_config["remove_fields"]:
            d_json_payload.pop(remove_field)

    # s_json_text = json.dumps(d_json_payload)
    # logging.info(d_graylog_conf)
    
    args_for_req = {}
    args_for_req["url"] = "".join(["http://", gelf_http_host, ":", gelf_http_port, "/gelf"])
    args_for_req["json"] = d_json_payload
    args_for_req["headers"] = {"Content-Type":"application/json"}
    # args_for_req["verify"] = False
    # args_for_req["auth"] = HTTPBasicAuth(sArgUser, sArgPw)
    logging.debug(json.dumps(args_for_req, indent=4))

    if not args.send_graylog == True:
        logging.info("Not sending to graylog because --no-send-graylog used")
        return False

    try:
        # r = requests.delete(sUrl, json = argJson, headers=sHeaders, verify=False, auth=HTTPBasicAuth(sArgUser, sArgPw))
        r = requests.post(**args_for_req)

        logging.info("".join(["HTTP Response", "\n", "    URL:", s_source_url, "\n", "    Code:", str(r.status_code)]))
        # r.status_code
        # print(r.headers)
        # print(r.text)
        # exit()
        # return json.loads(r.text)
        # return r.text

    except Exception as e:
        logging.error(e)

def read_sources(get_sources: dict):
    for source in get_sources:
        b_enabled = True
        d_source_data = get_sources[source]

        if "enabled" in d_source_data:
            if d_source_data["enabled"] == False:
                b_enabled = False

        if b_enabled == True:
            b_valid = True
            if "url" in d_source_data:
                source_url = d_source_data["url"]
            else:
                b_valid = False
                
            if "interval_m" in d_source_data:
                source_interval = d_source_data["interval_m"]
            else:
                b_valid = False
            
            if b_valid == True:
                # print(source_url)
                # print(source_interval)
                logging.info("".join(["Fetch URL: ", source_url]))
                webrs = fetch_web(source_url)
                if webrs:
                    json_json =json.loads(webrs)
                    if "json_path" in d_source_data:
                        query = jp.parse(d_source_data["json_path"])
                        for match in query.find(json.loads(webrs)):
                            json_json = match.value
                            break;

                    b_flatten = False

                    if "flatten" in d_source_data:
                        if d_source_data["flatten"] == True:
                            b_flatten = True
                    
                    logging.debug("".join(["Flatten: ", str(b_flatten)]))

                    if b_flatten == True:
                        flat_json = flatten(json_json)
                    else:
                        flat_json = json_json
                    
                    # processed_json = process_json(flat_json)
                    processed_json = flat_json
                    

                    # print(json.dumps(processed_json, indent=4))

                    b_each_list_separate_log = False
                    if "each_list_separate_log" in d_source_data:
                        if d_source_data["each_list_separate_log"] == True:
                            b_each_list_separate_log = True

                    if b_each_list_separate_log == False:
                        publish_gelf(source_url, processed_json, d_source_data, source)
                    else:
                        logging.debug("Each item in list will be logged separately")
                        if "flatten_each_list_separate_log" in d_source_data:
                            flatten_each_list_separate_log = d_source_data["flatten_each_list_separate_log"]

                        for json_item in processed_json:
                            if flatten_each_list_separate_log == True:
                                flat_json = flatten(json_item)
                            else:
                                flat_json = json_item
                            # logging.debug(json_item)
                            publish_gelf(source_url, flat_json, d_source_data, source)
            else:
                logging.error("".join(["Invalid config for: ", source, ". MUST have a `url` property"]))
        else:
            logging.debug("".join(["Source ", source, " disabled."]))

logging.info('Init')

data = {
    "products": [
        {"name": "Apple", "price": 12.88, "tags": ["fruit", "red"]},
        {"name": "Peach", "price": 27.25, "tags": ["fruit", "yellow"]},
        {"name": "Cake", "tags": ["pastry", "sweet"]},
    ]
}

# find all product names:
query = jp.parse("products[*].name")
for match in query.find(data):
    print(match.value)

# exit()
    
read_sources(d_sources)
