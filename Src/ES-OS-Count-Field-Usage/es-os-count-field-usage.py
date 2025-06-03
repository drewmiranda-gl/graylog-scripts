# cat list of indices
# http://hplap.geek4u.net:9200/_cat/indices

# count fields
# curl -XGET ‘localhost:9200/graylog_2/?pretty’ | grep type | wc -l

import requests, configparser, argparse, time, json, re, os, subprocess, urllib3, yaml
from requests.auth import HTTPBasicAuth
from os.path import exists

urllib3.disable_warnings()

parser = argparse.ArgumentParser(description="Just an example",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--api-url", help='ES/OS API URL. e.g. http://localhost:9200', default="http://localhost:9200", type=str, required=True)
parser.add_argument("--verify", help="Verify HTTPS/TLS Cert", action=argparse.BooleanOptionalAction, default=True)
parser.add_argument("--username", help='If using HTTP Basic Auth, username to auth with', default="", type=str, required=False)
parser.add_argument("--password", help='If using HTTP Basic Auth, password to auth with', default="", type=str, required=False)
parser.add_argument("--cert", help='Client Certificate Auth: cert file (.crt)', default="", type=str, required=False)
parser.add_argument("--key", help='Client Certificate Auth: key file (.key)', default="", type=str, required=False)
parser.add_argument("--warm", help="Include Warm Tier.", action=argparse.BooleanOptionalAction, default=False)

args = parser.parse_args()
b_tls_verify = args.verify
b_include_warm_tier_indices = args.warm

b_use_http_basic_auth = False
arg_username = ""
arg_password = ""
if len(args.username) and len(args.password):
    b_use_http_basic_auth = True
    arg_username = str(args.username)
    arg_password = str(args.password)

b_use_client_cert_auth = False
arg_cert_cert = ""
arg_cert_key = ""
if len(args.cert) and len(args.key):
    b_use_http_basic_auth = False
    b_use_client_cert_auth = True
    arg_cert_cert = str(args.cert)
    arg_cert_key = str(args.key)

defText = "\033[0;30;50m"
alertText = "\033[1;33;50m"
errorText = "\033[1;31;50m"
successText = "\033[1;32;50m"
blueText = "\033[0;34;50m"

print(defText)

def mergeDict(dictOrig: dict, dictToAdd: dict, allowReplacements: bool):
    for item in dictToAdd:
        
        bSet = True
        if item in dictOrig:
            if allowReplacements == False:
                bSet = False
        
        if bSet == True:
            dictOrig[item] = dictToAdd[item]
    
    return dictOrig

def api_url_formatter(url: str):
    if re.search("/$", str(url)):
        return re.sub("/$", "", url)
    return url

def get_indices(url_base: str):
    d_indices = {}
    sUrl = url_base + "/_cat/indices?h=health,status,index,docs.count"
    # print("Obtaining list of indices via '" + blueText + str(sUrl) + defText + "'")
    sHeaders = {}

    args_for_req = {}
    args_for_req["url"] = sUrl
    args_for_req["headers"] = sHeaders
    args_for_req["verify"] = b_tls_verify
    if b_use_http_basic_auth == True:
        args_for_req["auth"] = HTTPBasicAuth(arg_username, arg_password)
    if b_use_client_cert_auth == True:
        args_for_req["cert"] = (arg_cert_cert, arg_cert_key)

    try:
        r = requests.get(**args_for_req)
        if not int(r.status_code) == 200:
            print(errorText + "ERROR! Expected HTTP status 200, but instead received "  + str(r.status_code) + defText)
            exit(1)
    except Exception as e:
        print(e)
        exit(1)
    
    lines = r.text.splitlines()
    i = 1
    for line in lines:
        tmp_index_health = ""
        tmp_index_status = ""
        tmp_index = ""
        tmp_index_doc_count = 0

        # print(str(i) + ": " + str(line))
        # print(line)
        rs = re.search(r"^(\w+)\s+(\w+)\s+(\S+)\s+(\d+)$", str(line))
        tmp_index_health = str(rs.group(1).strip())
        tmp_index_status = str(rs.group(2).strip())
        tmp_index = str(rs.group(3).strip())
        tmp_index_doc_count = int(rs.group(4).strip())
        
        i = i + 1

        if tmp_index_doc_count > 0 and tmp_index_health.lower() == "green":
            b_include_this_index = True

            if b_include_warm_tier_indices == False:
                if re.search(r"_warm_\d+$", str(tmp_index)):
                    b_include_this_index = False

            if b_include_this_index == True:
                d_indices[tmp_index] = {
                    "index": tmp_index,
                    "health": tmp_index_health,
                    "status": tmp_index_status,
                    "doc_count": tmp_index_doc_count
                }
        # break

    return d_indices

def get_fields_from_index(url_base: str, index: str):
    list_index_fields = []

    sUrl = url_base + "/" + str(index)
    # print("Obtaining list of fields from index " + str(index) + " via '" + blueText + str(sUrl) + defText + "'")
    sHeaders = {}

    args_for_req = {}
    args_for_req["url"] = sUrl
    args_for_req["headers"] = sHeaders
    args_for_req["verify"] = b_tls_verify
    if b_use_http_basic_auth == True:
        args_for_req["auth"] = HTTPBasicAuth(arg_username, arg_password)
    if b_use_client_cert_auth == True:
        args_for_req["cert"] = (arg_cert_cert, arg_cert_key)

    try:
        r = requests.get(**args_for_req)
        # print(r.text)
        if not int(r.status_code) == 200:
            print(errorText + "ERROR! Expected HTTP status 200, but instead received "  + str(r.status_code) + defText)
            exit(1)
    except Exception as e:
        print(r)
    
    rs_json = json.loads(r.text)
    index_key = ""
    for index_details in rs_json:
        index_key = index_details
        break

    if not len(index_key):
        return False

    if not "mappings" in rs_json[index_key]:
        return False

    if not "properties" in rs_json[index_key]["mappings"]:
        return False
    
    for field in rs_json[index_key]["mappings"]["properties"]:
        # d_index_fields
        # print(field)
        # d_index_fields[index][field] = 1
        list_index_fields.append(str(field))

    # print(json.dumps(d_index_fields, indent=4))
    # print(json.dumps(rs_json[index_key]["mappings"]["properties"], indent=4))
    return list_index_fields

def count_usage_of_field_in_index(url_base: str, index: str, field: str):
    sUrl = url_base + "/" + index + "/_count/"
    # print("Querying index " + str(index) + " to count usage of field " + str(field) + " via '" + blueText + str(sUrl) + defText + "'")
    sHeaders = {"Accept":"application/json", "X-Requested-By":"python-requests"}
    json_payload = {
        "query": {
            "exists": {
                "field": field
            }
        }
    }

    args_for_req = {}
    args_for_req["url"] = sUrl
    args_for_req["headers"] = sHeaders
    args_for_req["json"] = json_payload
    args_for_req["verify"] = b_tls_verify
    if b_use_http_basic_auth == True:
        args_for_req["auth"] = HTTPBasicAuth(arg_username, arg_password)
    if b_use_client_cert_auth == True:
        args_for_req["cert"] = (arg_cert_cert, arg_cert_key)

    try:
        r = requests.get(**args_for_req)
        # print(r.text)
        if not int(r.status_code) == 200:
            print(errorText + "ERROR! Expected HTTP status 200, but instead received "  + str(r.status_code) + defText)
            exit(1)
    except Exception as e:
        print(e)
    
    rs_json = json.loads(r.text)
    if "count" in rs_json:
        return rs_json["count"]
    
    return 0

print("API URL: '" + blueText + str(api_url_formatter(args.api_url))+ defText + "'")

d_indices = get_indices(api_url_formatter(args.api_url))
# print(json.dumps(d_indices, indent=4))

for index in d_indices:
    list_index_fields = get_fields_from_index(api_url_formatter(args.api_url), index)
    for field in list_index_fields:
        count = 0
        # print(field)
        count = count_usage_of_field_in_index(api_url_formatter(args.api_url), index, field)
        print(str(index) + "," + str(field) + "," + str(count))
