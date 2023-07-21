import requests, configparser, argparse, time, json, re, os, subprocess, urllib3, yaml
from requests.auth import HTTPBasicAuth
from os.path import exists

# Disable HTTPS/TLS certificate warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

list_actions = []
list_actions.append("list-streams")
list_actions.append("share-all-stream")
list_actions.append("share-all-dashboards")
list_actions.append("create-input-profile")
list_actions.append("create-forwarder-input")
list_actions.append("create-admin-user")
list_actions.append("enable-geo-maxmind")
list_actions.append("add-sigmahq-repo")
list_actions.append("create-role")
list_actions.sort()

list_input_type = []
list_input_type.append("syslog_tcp")
list_input_type.append("syslog_udp")
list_input_type.append("gelf_tcp")
list_input_type.append("gelf_udp")
list_input_type.append("beats")
list_input_type.sort()

# defaults
parser = argparse.ArgumentParser(description="Just an example",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--debug", "-d", help="For debugging", action=argparse.BooleanOptionalAction)
parser.add_argument("--verbose", help="For debugging", action=argparse.BooleanOptionalAction)
parser.add_argument("--config-file", '-c', help='Config file to use. Defaults to config.yml', default="config.yml", type=str, required=False)
parser.add_argument("--action", help='Action to perform', type=str, choices=list_actions, required=True)
parser.add_argument("--bulk-file", help='file to use for bulk actions', default="bulk.csv", type=str, required=False)
parser.add_argument("--title", help='title attribute', default="", type=str, required=False)
parser.add_argument("--description", help='description attribute', default="", type=str, required=False)
parser.add_argument("--input-type", help='Input Type', type=str, default="", choices=list_input_type, required=False)
parser.add_argument("--input-types", help='Comma Separated list of input types. Must be valid choices from --input-type. Supersedes --input-type.', type=str, default="", required=False)
parser.add_argument("--input-port", help='Input Port Number', default=0, type=int, required=False)
parser.add_argument("--input-profile-id", help='Forwarder ID. Can also use create (creates new input profile) or latest (uses most recently created input profile).', default="", type=str, required=False)
parser.add_argument("--data-adapter-name", help='Name of Data Adapter to work with.', default="", type=str, required=False)
parser.add_argument("--lookup-key", help='ID of Data Adapter to work with.', default="", type=str, required=False)
parser.add_argument("--file", help='File for bulk operations. 1 entry per line', default="", type=str, required=False)
parser.add_argument("--firstname", help='First Name', default="", type=str, required=False)
parser.add_argument("--lastname", help='Last Name', default="", type=str, required=False)
parser.add_argument("--email", help='Email', default="", type=str, required=False)
parser.add_argument("--user-password", help='Password for user', default="", type=str, required=False)
parser.add_argument("--role-name", help='Role Name', default="", type=str, required=False)
parser.add_argument("--role-description", help='Role Description', default="", type=str, required=False)
parser.add_argument("--role-permissions", help='Comma separated list of permissions.', default="", type=str, required=False)
parser.add_argument("--add-users-to-role", help='Comma separated list of users. Needed when updating a role since it currently needs to be deleted when updating it.', default="", type=str, required=False)

args = parser.parse_args()

defText = "\033[0;30;50m"
alertText = "\033[1;33;50m"
errorText = "\033[1;31;50m"
successText = "\033[1;32;50m"
blueText = "\033[0;34;50m"

print(defText)

strConfigFile = args.config_file

# ================= BACKOFF START ==============================

# Number of seconds to wait before retrying after a socket error
iSocketRetryWaitSec = 5

# Maximum number of retries to attempt. script exits if max is reach so be careful!
iSocketMaxRetries = 300

# How many seconds to add before each retry
# backoff resets after a successful connection
iSocketRetryBackOffSec = 10

# maximum allowed retry wait in seconds
iSocketRetryBackOffMaxSec = 300

# how many retries before the backoff time is added before each retry
iSocketRetryBackOffGraceCount = 24

# ================= BACKOFF END ================================



# ================= FUNCTIONS START ==============================
def yaml_to_dict(file: str):
    if exists(file):
        with open(file) as f:
            doc = yaml.safe_load(f)
            return doc

def load_config_from_dict(dict_input: dict, noAuth: bool):
    if not dict_input:
        print(errorText + "config file is empty!" + defText)
        exit(1)

    if len(dict_input) == 0:
        print(errorText + "config file is empty!" + defText)
        exit(1)

    if not 'graylog_api' in dict_input:
        print(errorText + "graylog_api missing from config file." + defText)
        exit(1)
    
    if 'https' in dict_input['graylog_api']:
        if not dict_input['graylog_api']['https'] == True and not dict_input['graylog_api']['https'] == False:
            print("ERROR! Graylog API Config: https not set to true or false.")
            exit(1)
    else:
        print("ERROR! Graylog API Config: https not set")
        exit(1)
    
    if 'host' in dict_input['graylog_api']:
        if not len(dict_input['graylog_api']['host']) > 0:
            print("ERROR! Graylog API Config: host value length is 0")
            exit(1)
    else:
        print("ERROR! Graylog API Config: host not set")
        exit(1)

    if 'port' in dict_input['graylog_api']:
        if not len(str(dict_input['graylog_api']['port'])) > 0 and not int(dict_input['graylog_api']['port']) > 0:
            print("ERROR! Graylog API Config: port value is empty")
            exit(1)
    else:
        print("ERROR! Graylog API Config: port not set")
        exit(1)

    if 'graylog_api_token' in dict_input['graylog_api']:
        # token is empty
        if not len(dict_input['graylog_api']['graylog_api_token']) > 0:
            if noAuth == False:
                # check if username and password is set
                if 'username' in dict_input['graylog_api'] and 'password' in dict_input['graylog_api']:
                    if len(dict_input['graylog_api']['username']) and len(dict_input['graylog_api']['password']) > 0:
                        abc = "ok"
                    else:
                        print("ERROR! Graylog API Config: username and password empty")
                        exit(1)
                else:
                    print("ERROR! Graylog API Config: username and password not set")
                    exit(1)
    else:
        print("ERROR! Graylog API Config: graylog_api_token not set")
        exit(1)
    
    if len(dict_input['graylog_api']['username']) == 0 and len(dict_input['graylog_api']['password']) == 0 and len(dict_input['graylog_api']['graylog_api_token']) > 0:
        graylog_api_user = dict_input['graylog_api']['graylog_api_token']
        graylog_api_password = "token"
    else:
        graylog_api_user = dict_input['graylog_api']['username']
        graylog_api_password = dict_input['graylog_api']['password']

    return {
        "https": bool(dict_input['graylog_api']['https']),
        "host": str(dict_input['graylog_api']['host']),
        "port": dict_input['graylog_api']['port'],
        "user": str(graylog_api_user),
        "password": str(graylog_api_password)
    }

def graylogApiConfigIsValid(dictGraylogApi: dict, noAuth: bool):
    if 'https' in dictGraylogApi:
        if not dictGraylogApi['https'] == True and not dictGraylogApi['https'] == False:
            print("ERROR! Graylog API Config: https not set to true or false.")
            return False
    else:
        print("ERROR! Graylog API Config: https not set")
        return False
    
    if 'host' in dictGraylogApi:
        if not len(dictGraylogApi['host']) > 0:
            print("ERROR! Graylog API Config: host value length is 0")
            return False
    else:
        print("ERROR! Graylog API Config: host not set")
        return False

    if 'port' in dictGraylogApi:
        if not len(dictGraylogApi['port']) > 0 and not int(dictGraylogApi['port']) > 0:
            print("ERROR! Graylog API Config: port value is empty")
            return False
    else:
        print("ERROR! Graylog API Config: port not set")
        return False
    
    if noAuth == False:
        # check if username and password is set
        if 'user' in dictGraylogApi and 'password' in dictGraylogApi:
            if len(dictGraylogApi['user']) and len(dictGraylogApi['password']) > 0:
                return True
            else:
                print("ERROR! Graylog API Config: username and password empty")
                return False

        print("ERROR! Graylog API Config: username and password not set")
        return False
    
    return True

def mergeDict(dictOrig: dict, dictToAdd: dict, allowReplacements: bool):
    for item in dictToAdd:
        
        bSet = True
        if item in dictOrig:
            if allowReplacements == False:
                bSet = False
        
        if bSet == True:
            dictOrig[item] = dictToAdd[item]
    
    return dictOrig

def doGraylogApi(dictGraylogApi: dict, argMethod: str, argApiUrl: str, argHeaders: dict, argJson: dict, argFiles: dict, argData: str, argExpectedReturnCode: int, argReturnJson: bool):
    if graylogApiConfigIsValid(dictGraylogApi, False) == True:
        # build URI
        sArgBuildUri = ""
        if dictGraylogApi['https'] == True:
            sArgBuildUri = "https://"
        else:
            sArgBuildUri = "http://"

        sArgHost    = dictGraylogApi['host']
        sArgPort    = dictGraylogApi['port']
        sArgUser    = dictGraylogApi['user']
        sArgPw      = dictGraylogApi['password']

        # print(alertText + "Graylog Server: " + sArgHost + defText + "\n")

        # build server:host and concat with URI
        sArgBuildUri=sArgBuildUri+sArgHost+":"+sArgPort
        
        sUrl = sArgBuildUri + argApiUrl

        # add headers
        sHeaders = {"Accept":"application/json", "X-Requested-By":"python-requests"}
        sHeaders = mergeDict(sHeaders, argHeaders, True)
        
        if argMethod.upper() == "GET":
            try:
                r = requests.get(sUrl, headers=sHeaders, verify=False, auth=HTTPBasicAuth(sArgUser, sArgPw))
            except Exception as e:
                return {
                    "success": False,
                    "exception": e
                }
        elif argMethod.upper() == "POST":
            send = ""

            if not argFiles == False:
                send = "files"
            elif not argData  == False and len(argData) > 0:
                send = "data"
            else:
                send = "json"

            # print("send: " + send)
            # exit()

            if send == "json":
                try:
                    r = requests.post(sUrl, json = argJson, headers=sHeaders, verify=False, auth=HTTPBasicAuth(sArgUser, sArgPw))
                    # print(r.status_code)
                    # print(r.headers)
                    # print(r.text)
                    # exit()
                except Exception as e:
                    return {
                        "success": False,
                        "exception": e
                    }
            elif send == "data":
                try:
                    r = requests.post(sUrl, data = argData, headers=sHeaders, verify=False, auth=HTTPBasicAuth(sArgUser, sArgPw))
                except Exception as e:
                    return {
                        "success": False,
                        "exception": e
                    }
            elif send == "files":
                try:
                    r = requests.post(sUrl, json = argJson, files=argFiles, headers=sHeaders, verify=False, auth=HTTPBasicAuth(sArgUser, sArgPw))
                except Exception as e:
                    return {
                        "success": False,
                        "exception": e
                    }
        elif argMethod.upper() == "PUT":
            send = ""

            if not argFiles == False:
                send = "files"
            elif not argData  == False and len(argData) > 0:
                send = "data"
            else:
                send = "json"

            # print("send: " + send)
            # exit()

            if send == "json":
                try:
                    r = requests.put(sUrl, json = argJson, headers=sHeaders, verify=False, auth=HTTPBasicAuth(sArgUser, sArgPw))
                    # print(r.status_code)
                    # print(r.headers)
                    # print(r.text)
                    # exit()
                except Exception as e:
                    return {
                        "success": False,
                        "exception": e
                    }
        elif argMethod.upper() == "DELETE":
            send = ""

            if not argFiles == False:
                send = "files"
            elif not argData  == False and len(argData) > 0:
                send = "data"
            else:
                send = "json"

            # print("send: " + send)
            # exit()

            args_for_req = {}
            args_for_req["url"] = sUrl
            if not argJson == False:
                args_for_req["json"] = argJson
            args_for_req["headers"] = sHeaders
            args_for_req["verify"] = False
            args_for_req["auth"] = HTTPBasicAuth(sArgUser, sArgPw)

            if send == "json":
                try:
                    # r = requests.delete(sUrl, json = argJson, headers=sHeaders, verify=False, auth=HTTPBasicAuth(sArgUser, sArgPw))
                    r = requests.delete(**args_for_req)

                    # print(r.status_code)
                    # print(r.headers)
                    # print(r.text)
                    # exit()
                except Exception as e:
                    return {
                        "success": False,
                        "exception": e
                    }
        
        if r.status_code == argExpectedReturnCode:
            if argReturnJson:
                return {
                    "json": json.loads(r.text),
                    "status_code": r.status_code,
                    "success": True
                }
            else:
                return {
                    "text": r.text,
                    "status_code": r.status_code,
                    "success": True
                }
        else:
            return {
                "status_code": r.status_code,
                "success": False,
                "failure_reason": "Return code " + str(r.status_code) + " does not equal expected code of " + str(argExpectedReturnCode),
                "text": r.text
            } 
    else:
        return {"msg": "api_not_configured"}

def validate_input(validation_type: str, validation_value: str, error_msg: str, fatal: bool):
    match validation_type:
        case "not-empty":
            if len(validation_value):
                return True
            else:
                if fatal == True:
                    print(errorText + error_msg + defText)
                    exit(1)
                else:
                    return False
        case "file-exists":
            if exists(validation_value):
                return True
            else:
                if fatal == True:
                    print(errorText + error_msg + defText)
                    exit(1)
                else:
                    return False

def graylog_api_get_streams_list(dictGraylogApi: dict):
    r = doGraylogApi(dictGraylogApi, "GET", "/api/streams", {}, {}, False, False, 200, True)
    if r['success'] == True:
        if 'json' in r:
            if 'streams' in r['json']:
                return r['json']['streams']

    return False

def graylog_api_get_dashboard_list(dictGraylogApi: dict):
    r = doGraylogApi(dictGraylogApi, "GET", "/api/dashboards", {}, {}, False, False, 200, True)
    if r['success'] == True:
        if 'json' in r:
            if 'views' in r['json']:
                return r['json']['views']

    return False

def graylog_api_share(dictGraylogApi: dict, item_type: str, item_id: str, share_with_grn: str, share_level: str):
    api_url = "/api/authz/shares/entities/grn::::" + str(item_type) + ":" + str(item_id)
    json_payload = {
        "selected_grantee_capabilities":{
            share_with_grn:share_level
        }
    }
    r = doGraylogApi(dictGraylogApi, "POST", api_url, {}, json_payload, False, False, 200, True)
    return r

def bulk_graylog_api_share_stream(streams_list: dict, dictGraylogApi: dict, share_with_grn: str, share_level: str):
    if not streams_list:
        print(errorText + "ERROR! Streams list is empty" + defText)
        exit(1)
    
    for stream in streams_list:
        r = graylog_api_share(dictGraylogApi, "stream", stream['id'], share_with_grn, share_level)
        if r['success'] == True:
            print(successText + "Stream " + blueText + stream['title'] + successText + " shared successfully.")
        else:
            print(errorText + "Stream " + blueText + stream['title'] + errorText + " failed to share.")

def bulk_graylog_api_share_dashboard(dashboard_list: dict, dictGraylogApi: dict, share_with_grn: str, share_level: str):
    if not dashboard_list:
        print(errorText + "ERROR! Dashboard list is empty" + defText)
        exit(1)
    
    for dashboard in dashboard_list:
        r = graylog_api_share(dictGraylogApi, "dashboard", dashboard['id'], share_with_grn, share_level)
        if r['success'] == True:
            print(successText + "Dashboard " + blueText + dashboard['title'] + successText + " shared successfully.")
        else:
            print(errorText + "Dashboard " + blueText + dashboard['title'] + errorText + " failed to share.")

def create_input_profile(dictGraylogApi: dict, input_profile_title: str, input_profile_description: str):
    if len(input_profile_title) == 0:
        print(errorText + "ERROR! Title cannot be empty. Use --title" + defText)
        exit(1)

    api_url = "/api/plugins/org.graylog.plugins.forwarder/forwarder/profiles"
    json_payload = {
        "title": input_profile_title,
        "description": input_profile_description
    }
    r = doGraylogApi(dictGraylogApi, "POST", api_url, {}, json_payload, False, False, 200, True)
    if r['success'] == True:
        print(successText + "Input Profile " + blueText + input_profile_title + " " + successText + "successfully created." + defText)
        return r['json']['id']
    else:
        print(errorText + "Failed to create Input Profile " + blueText + input_profile_title + defText)
        return ""

def get_input_conf_json(argInputType: str, argPort: int, is_global: bool):
    port_to_use_for_input = argPort
    d = {}

    if argInputType.lower() == "syslog_tcp":
        if argPort == 0:
            port_to_use_for_input = 514

        d = {
            "title": "Syslog TCP",
            "type": "org.graylog2.inputs.syslog.tcp.SyslogTCPInput",
            "configuration": {
                "bind_address": "0.0.0.0",
                "port": port_to_use_for_input,
                "recv_buffer_size": 1048576,
                "number_worker_threads": 4,
                "tls_cert_file": "",
                "tls_key_file": "",
                "tls_enable": False,
                "tls_key_password": "",
                "tls_client_auth": "disabled",
                "tls_client_auth_cert_file": "",
                "tcp_keepalive": False,
                "use_null_delimiter": False,
                "max_message_size": 2097152,
                "override_source": None,
                "charset_name": "UTF-8",
                "force_rdns": False,
                "allow_override_date": True,
                "store_full_message": False,
                "expand_structured_data": False,
                "timezone": "UTC"
            }
        }
    elif argInputType.lower() == "syslog_udp":
        if argPort == 0:
            port_to_use_for_input = 514

        d = {
            "title": "Syslog UDP",
            "type": "org.graylog2.inputs.syslog.udp.SyslogUDPInput",
            "configuration": {
                "bind_address": "0.0.0.0",
                "port": port_to_use_for_input,
                "recv_buffer_size": 262144,
                "number_worker_threads": 4,
                "override_source": None,
                "charset_name": "UTF-8",
                "force_rdns": False,
                "allow_override_date": True,
                "store_full_message": False,
                "expand_structured_data": False,
                "timezone": "UTC"
            }
        }
    elif argInputType.lower() == "gelf_tcp":
        if argPort == 0:
            port_to_use_for_input = 12201
        
        d = {
            "title": "Gelf TCP",
            "type": "org.graylog2.inputs.gelf.tcp.GELFTCPInput",
            "configuration": {
                "bind_address": "0.0.0.0",
                "port": port_to_use_for_input,
                "recv_buffer_size": 1048576,
                "number_worker_threads": 4,
                "tls_cert_file": "",
                "tls_key_file": "",
                "tls_enable": False,
                "tls_key_password": "",
                "tls_client_auth": "disabled",
                "tls_client_auth_cert_file": "",
                "tcp_keepalive": False,
                "use_null_delimiter": True,
                "max_message_size": 2097152,
                "override_source": None,
                "charset_name": "UTF-8",
                "decompress_size_limit": 8388608
            }
        }
    elif argInputType.lower() == "gelf_udp":
        if argPort == 0:
            port_to_use_for_input = 12201
        
        d = {
            "title": "Gelf UDP",
            "type": "org.graylog2.inputs.gelf.udp.GELFUDPInput",
            "configuration": {
                "bind_address": "0.0.0.0",
                "port": port_to_use_for_input,
                "recv_buffer_size": 262144,
                "number_worker_threads": 4,
                "override_source": None,
                "charset_name": "UTF-8",
                "decompress_size_limit": 8388608
            }
        }
    elif argInputType.lower() == "beats":
        if argPort == 0:
            port_to_use_for_input = 5044
        
        d = {
            "title": "Beats",
            "type": "org.graylog.plugins.beats.Beats2Input",
            "configuration": {
                "bind_address": "0.0.0.0",
                "port": port_to_use_for_input,
                "recv_buffer_size": 1048576,
                "number_worker_threads": 4,
                "tls_cert_file": "",
                "tls_key_file": "",
                "tls_enable": False,
                "tls_key_password": "",
                "tls_client_auth": "disabled",
                "tls_client_auth_cert_file": "",
                "tcp_keepalive": False,
                "override_source": None,
                "charset_name": "UTF-8",
                "no_beats_prefix": False
            }
        }

    if is_global == True:
        d['global'] = True
    
    if len(d):
        return d

    print(errorText + "ERROR invalid input type specified." + defText)
    exit(1)
    return False

def create_forwarder_input(dictGraylogApi: dict, input_profile_id: str, input_type: str, input_port: int):
    if len(input_profile_id) == 0:
        print(errorText + "ERROR! forwarder id cannot be empty. Use --forwarder-id" + defText)
        exit(1)
    
    if len(input_type) == 0:
        print(errorText + "ERROR! input type cannot be empty. Use --input-type" + defText)
        exit(1)
    
    if input_port == 0:
        print(alertText + "No input port specified. Using default port for that input. (to set a port use --input-port)" + defText)
    
    json_payload_for_input_conf = get_input_conf_json(input_type, input_port, False)

    api_url = "/api/plugins/org.graylog.plugins.forwarder/forwarder/profiles/" + input_profile_id + "/inputs"
    r = doGraylogApi(dictGraylogApi, "POST", api_url, {}, json_payload_for_input_conf, False, False, 200, True)

    if r['success'] == True:
        print(successText + "Input " + blueText + json_payload_for_input_conf['title'] + " " + successText + "successfully created." + defText)
        if args.verbose == True:
            print(json.dumps(json_payload_for_input_conf, indent=4))
    else:
        print(errorText + "Failed to create Input " + blueText + json_payload_for_input_conf['title'] + defText)
        return ""

def safe_create_forwarder_input(input_type: str, input_port: int, input_profile_id: str):
    if not re.search("^[0-9a-f]{20}", str(input_profile_id)):
        print(errorText + "ERROR: Invalid input profile id '" + blueText + input_profile_id + "'" + defText)
        exit(1)

    # input_type = args.input_type
    safe_input_port = get_input_port_from_short_type(input_type, input_port)
    input_protocol = get_input_protocol_from_short_type(input_type)

    # get input to make sure port is not duplicated isn't duplicated
    inputs = get_forwarder_input_profile_inputs(graylog_api_conf_from_yaml, input_profile_id)
    is_port_and_protocol_in_use = check_if_input_on_same_port_and_protocol_exists(inputs, safe_input_port, input_protocol)
    
    if is_port_and_protocol_in_use == True:
        print(errorText + "ERROR: An input already exists on port " + str(safe_input_port) + "/" + input_protocol.lower() + defText)
        exit(1)
    else:
        create_forwarder_input(graylog_api_conf_from_yaml, input_profile_id, input_type, safe_input_port)

def get_input_is_tcp_or_udp(input_type: str):
    if re.search("tcp", str(input_type)) or re.search("beats", str(input_type)):
        return "tcp"
    elif re.search("udp", str(input_type)):
        return "udp"

    return ""

def get_input_protocol_from_short_type(input_type: str):
    input_conf = get_input_conf_json(input_type, 0, False)
    
    if len(input_type) == 0:
        print(errorText + "ERROR: Input type cannot be empty." + defText)
        exit(1)

    if not "type" in input_conf:
        print(errorText + "ERROR: Invalid Input type." + defText)
        exit(1)

    input_protocol = get_input_is_tcp_or_udp(input_conf["type"])
    if input_protocol.lower() == "udp" or input_protocol.lower() == "tcp":
        return input_protocol.lower()
    else:
        print(errorText + "ERROR: Invalid Input type." + defText)
        exit(1)

    return ""

def get_input_port_from_short_type(input_type: str, input_port: int):
    json_payload_for_input_conf = get_input_conf_json(input_type, input_port, False)
    if not "configuration" in json_payload_for_input_conf:
        print(errorText + "ERROR: Invalid Input type." + defText)
        exit(1)
    
    if not "port" in json_payload_for_input_conf["configuration"]:
        print(errorText + "ERROR: Invalid Input type." + defText)
        exit(1)
    
    return json_payload_for_input_conf["configuration"]["port"]

def get_forwarder_input_profile(dictGraylogApi: dict):
    api_url = "/api/plugins/org.graylog.plugins.forwarder/forwarder/profiles?query=&page=1&per_page=100"
    r = doGraylogApi(dictGraylogApi, "GET", api_url, {}, {}, False, False, 200, True)
    # print(json.dumps(r, indent=4))
    if not "json" in r:
        return []

    if not "forwarder_input_profiles" in r['json']:
        return []

    return r['json']['forwarder_input_profiles']

def get_most_recently_created_input_profile_id(dictGraylogApi: dict):
    sort_list = []
    dict_by_id = {}
    dict_by_created_date = {}
    input_profiles = get_forwarder_input_profile(dictGraylogApi)
    for input_profile in input_profiles:
        if 'id' in input_profile and 'created_at' in input_profile:
            dict_by_id[input_profile['id']] = input_profile
            dict_by_created_date[input_profile['created_at']] = input_profile
            sort_list.append(input_profile['created_at'])
    
    sort_list.sort(reverse=True)

    # return ""
    
    if len(sort_list) and 'id' in dict_by_created_date[sort_list[0]]:
        return dict_by_created_date[sort_list[0]]['id']

    return ""

def get_forwarder_input_profile_inputs(dictGraylogApi: dict, input_profile_id: str):
    api_url = "/api/plugins/org.graylog.plugins.forwarder/forwarder/profiles/" + input_profile_id + "/inputs?query=&page=1&per_page=100"
    r = doGraylogApi(dictGraylogApi, "GET", api_url, {}, {}, False, False, 200, True)
    
    inputs = []

    if not "json" in r:
        return {}
    
    if not "forwarder_inputs" in r['json']:
        return {}
    
    for input in r['json']['forwarder_inputs']:
        port_type_proto = get_input_is_tcp_or_udp(input['type'])
        # print(port_type_proto)
        if "configuration" in input:
            if "port" in input["configuration"]:
                # print(input["configuration"]["port"])
                # print()
                dict_for_list = {
                    "type": input['type'],
                    "protocol": port_type_proto,
                    "port": input["configuration"]["port"]
                }
                inputs.append(dict_for_list)

    # print(json.dumps(inputs, indent=4))
    return inputs

def check_if_input_on_same_port_and_protocol_exists(inputs_list: list, input_port: int, input_protocol: str):
    for input in inputs_list:
        if "port" in input and "protocol" in input:
            # print(input["port"])
            # print(input_port)
            if input["port"] == input_port:
                if input["protocol"].lower() == input_protocol.lower():
                    return True
    
    return False

def safe_add_entry_to_mongodb_lookup(graylog_api_conf_from_yaml: dict, data_adapter_name: str, lookup_key: str, file: str):
    validate_input("not-empty", data_adapter_name, "ERROR: Data Adapter Name cannot be empty. Use --data-adapter-name", True)
    validate_input("not-empty", lookup_key, "ERROR: Lookup Key cannot be empty. Use --lookup-key", True)
    validate_input("not-empty", file, "ERROR: File cannot be empty. Use --file", True)
    validate_input("file-exists", file, "ERROR: File '" + blueText + file + errorText + "' does not exist.", True)

def safe_create_user(graylog_api_conf_from_yaml: dict, user_first_name: str, user_last_name: str, user_email: str, user_password: str):
    validate_input("not-empty", user_first_name, "ERROR: First Name cannot be empty. Use --firstname", True)
    validate_input("not-empty", user_last_name, "ERROR: Last Name cannot be empty. Use --lastname", True)
    validate_input("not-empty", user_email, "ERROR: Email cannot be empty. Use --email", True)
    validate_input("not-empty", user_password, "ERROR: User Password cannot be empty. Use --user-password", True)

    json_payload_for_create_user = {
        "first_name": str(user_first_name),
        "last_name": str(user_last_name),
        "username": str(user_email),
        "email": str(user_email),
        "password": str(user_password),
        "roles": [
            "Reader",
            "Admin"
        ],
        "permissions": []
    }

    api_url = "/api/users"
    r = doGraylogApi(graylog_api_conf_from_yaml, "POST", api_url, {}, json_payload_for_create_user, False, False, 201, False)

    if r['success'] == True:
        print(successText + "User " + blueText + str(user_email) + " " + successText + "successfully created." + defText)
    else:
        print(errorText + "Failed to create User " + blueText + str(user_email) + defText)
        if "text" in r:
            print(alertText + r["text"] + defText)
        return ""

def enable_geo_maxmind(graylog_api_conf_from_yaml: dict):
    json_payload = {
            "enabled": True,
            "enforce_graylog_schema": True,
            "db_vendor_type": "MAXMIND",
            "city_db_path": "/etc/graylog/server/GeoLite2-City.mmdb",
            "asn_db_path": "/etc/graylog/server/GeoLite2-ASN.mmdb",
            "refresh_interval_unit": "MINUTES",
            "refresh_interval": 10,
            "use_s3": False
        }

    api_url = "/api/system/cluster_config/org.graylog.plugins.map.config.GeoIpResolverConfig"
    r = doGraylogApi(graylog_api_conf_from_yaml, "PUT", api_url, {}, json_payload, False, False, 202, False)
    
    if r['success'] == True:
        print(successText + "Successfully enabled Geo-Location Processor using: " + blueText + "MaxMind" + defText)
    else:
        print(errorText + "Failed to enable Geo-Location Processor using: " + blueText + "MaxMind" + defText)
        if "text" in r:
            print(alertText + r["text"] + defText)
        return ""

def add_sigmahq_repo(graylog_api_conf_from_yaml: dict):
    api_url = "/api/plugins/org.graylog.plugins.securityapp.sigma/sigma/repositories/default"
    r = doGraylogApi(graylog_api_conf_from_yaml, "PUT", api_url, {}, {}, False, False, 200, False)

    if r['success'] == True:
        resp_json = json.loads(r["text"])
        if "success_count" in resp_json:
            str_success_count = resp_json["success_count"]
        else:
            str_success_count = ""
        
        if "failure_count" in resp_json:
            str_failure_count = resp_json["failure_count"]
        else:
            str_failure_count = ""

        print(successText + "Successfully added Default Sigma Repo: SigmaHQ" + defText + "\n" + "Success: " + str(str_success_count) + ", Failure: " + str(str_failure_count))
    else:
        print(errorText + "Failed to add Default Sigma Repo: SigmaHQ" + defText)
        if "text" in r:
            print(alertText + r["text"] + defText)
        return ""

def does_role_exist(graylog_api_conf_from_yaml: dict, role_name: str):
    api_url = "/api/roles/" + role_name
    r = doGraylogApi(graylog_api_conf_from_yaml, "GET", api_url, {}, {}, False, False, 200, False)
    
    if "success" in r and r["success"] == True:
        return True
    else:
        return False

def safe_add_user_to_role(graylog_api_conf_from_yaml: dict, role_name: str, user_name: str):
    api_url = "/api/roles/" + str(role_name) + "/members/" + str(user_name)
    r = doGraylogApi(graylog_api_conf_from_yaml, "PUT", api_url, {}, {}, False, False, 204, False)
    if "success" in r and r["success"] == True:
        print(successText + "Successfully added user: '" + blueText + str(user_name) + defText + "' to role '" + blueText + str(role_name) + defText + "'")
    else:
        print(errorText + "Failed to add user: '" + blueText + str(user_name) + defText + "' to role '" + blueText + str(role_name) + defText + "'")

def safe_create_role(graylog_api_conf_from_yaml: dict, role_name: str, role_description: str, role_permissions: str, add_users_to_role: str):
    # args.role_name, args.role_description, args.role_permissions
    validate_input("not-empty", role_name, "ERROR: Role Name cannot be empty. Use --role-name", True)
    validate_input("not-empty", role_permissions, "ERROR: Role Permissions cannot be empty. Use --role-permissions", True)

    if len(role_description) == 0:
        role_description = role_name

    role_permissions_list = list(role_permissions.split(","))

    user_list = []
    if len(add_users_to_role) > 0:
        user_list = list(add_users_to_role.split(","))

    # check if role name exists
    b_does_role_exist = does_role_exist(graylog_api_conf_from_yaml, role_name)
    
    if b_does_role_exist == True:
        print(alertText + "Role '" + blueText + str(role_name) + defText + "' already exists. Must delete since it appears updating roles does not work (bug?)")
        delete_api_url = "/api/roles/" + str(role_name)
        r = doGraylogApi(graylog_api_conf_from_yaml, "DELETE", delete_api_url, {}, False, False, False, 204, False)
        if "success" in r and r["success"] == True:
            print(successText + "Successfully deleted role: '" + blueText + str(role_name) + defText + "'")
        else:
            print(errorText + "Failed to delete role: '" + blueText + str(role_name) + defText + "'")
            exit(1)

    api_url = "/api/roles"
    json_payload = {
        "name": str(role_name),
        "description": str(role_description),
        "permissions": role_permissions_list,
        "read_only": False
    }
    r = doGraylogApi(graylog_api_conf_from_yaml, "POST", api_url, {}, json_payload, False, False, 201, False)
    if "success" in r and r["success"] == True:
        print(successText + "Successfully created role: '" + blueText + str(role_name) + defText + "'")
    else:
        print(errorText + "Failed to create role: '" + blueText + str(role_name) + defText + "'")
        exit(1)
    
    if len(user_list):
        print("Adding users to role...")
        for user_name in user_list:
            safe_add_user_to_role(graylog_api_conf_from_yaml, role_name, user_name)
        # /roles/{rolename}/members/{username}

# ================= FUNCTIONS END ===============================





if not exists(strConfigFile):
    print(errorText + "ERROR! Config file '" + blueText + strConfigFile + errorText + "' does not exist!" + defText)
    exit(1)

dict_config = yaml_to_dict(strConfigFile)
graylog_api_conf_from_yaml = load_config_from_dict(dict_config, False)

print(alertText + "Graylog Server: " + graylog_api_conf_from_yaml['host'] + defText + "\n")

# do_action(graylog_api_conf_from_yaml, args.action)

# BE SURE to add actions to list above: list_actions
match args.action:
    case "list-streams":
        graylog_api_get_streams_list(graylog_api_conf_from_yaml)
    
    case "share-all-stream":
        streams_list = graylog_api_get_streams_list(graylog_api_conf_from_yaml)
        # stream_id = "000000000000000000000002"
        share_with_grn = "grn::::team:64653376b55b7e084a8ffe5a"
        share_level = "view"
        bulk_graylog_api_share_stream(streams_list, graylog_api_conf_from_yaml, share_with_grn, share_level)
    
    case "share-all-dashboards":
        dashboard_list = graylog_api_get_dashboard_list(graylog_api_conf_from_yaml)
        share_with_grn = "grn::::team:64653376b55b7e084a8ffe5a"
        share_level = "view"
        bulk_graylog_api_share_dashboard(dashboard_list, graylog_api_conf_from_yaml, share_with_grn, share_level)
    
    case "create-input-profile":
        input_profile_id = create_input_profile(graylog_api_conf_from_yaml, args.title, args.description)
        if len(input_profile_id) > 0:
            print("Input Profile ID: " + blueText + input_profile_id + defText)
    
    case "create-forwarder-input":
        input_profile_id_to_use = args.input_profile_id
        
        if input_profile_id_to_use.lower() == "create":
            print(alertText + "Magic input profile id '" + blueText + "create" + alertText + "' used. Will create new input profile and use that id." + defText)
            input_profile_id_to_use = create_input_profile(graylog_api_conf_from_yaml, args.title, args.description)
        elif input_profile_id_to_use.lower() == "latest":
            print(alertText + "Magic input profile id '" + blueText + "latest" + alertText + "' used. Will use id of most recently created input profile." + defText)
            input_profile_id_to_use = get_most_recently_created_input_profile_id(graylog_api_conf_from_yaml)
            print("Most recent input profile id: " + blueText + input_profile_id_to_use + defText)

        if len(args.input_types):
            print(alertText + "--input-types argument used. This will supersede --input-type" + defText)
            input_types_list = args.input_types.split(",")
        else:
            input_types_list = [args.input_type]

        # print(json.dumps(split_list, indent=4))
        # exit()

        for input_type_entry in input_types_list:
            if input_type_entry in list_input_type:
                safe_create_forwarder_input(input_type_entry, args.input_port, input_profile_id_to_use)
            else:
                print(alertText + "WARNING: Input type '" + blueText + input_type_entry + alertText + "' is invalid. Ignoring." + defText)

    case "create-admin-user":
        safe_create_user(graylog_api_conf_from_yaml, args.firstname, args.lastname, args.email, args.user_password)
    
    case "enable-geo-maxmind":
        enable_geo_maxmind(graylog_api_conf_from_yaml)
    
    case "add-sigmahq-repo":
        add_sigmahq_repo(graylog_api_conf_from_yaml)

    case "create-role":
        safe_create_role(graylog_api_conf_from_yaml, args.role_name, args.role_description, args.role_permissions, args.add_users_to_role)



# print(json.dumps(r, indent=4))