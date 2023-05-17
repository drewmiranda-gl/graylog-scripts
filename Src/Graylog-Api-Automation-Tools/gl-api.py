import requests, configparser, argparse, time, json, re, os, subprocess, urllib3, yaml
from requests.auth import HTTPBasicAuth
from os.path import exists

# Disable HTTPS/TLS certificate warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

list_actions = []
list_actions.append("list-streams")
list_actions.append("share-all-stream")
list_actions.sort()

# defaults
parser = argparse.ArgumentParser(description="Just an example",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--debug", "-d", help="For debugging", action=argparse.BooleanOptionalAction)
parser.add_argument("--config-file", '-c', help='Config file to use. Defaults to config.yml', default="config.yml", type=str, required=False)
parser.add_argument("--action", help='Action to perform', type=str, choices=list_actions, required=True)
parser.add_argument("--bulk-file", help='file to use for bulk actions', default="bulk.csv", type=str, required=False)

args = parser.parse_args()
configFromArg = vars(args)

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
        if not len(dict_input['graylog_api']['port']) > 0 and not int(dict_input['graylog_api']['port']) > 0:
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
                        return True
                    else:
                        print("ERROR! Graylog API Config: username and password empty")
                        exit(1)

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

def graylog_api_get_streams_list(dictGraylogApi: dict):
    r = doGraylogApi(dictGraylogApi, "GET", "/api/streams", {}, {}, False, False, 200, True)
    if r['success'] == True:
        if 'json' in r:
            if 'streams' in r['json']:
                return r['json']['streams']

    return False

def graylog_api_share_stream(dictGraylogApi: dict, stream_id: str, share_with_grn: str, share_level: str):
    api_url = "/api/authz/shares/entities/grn::::stream:" + str(stream_id)
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
        r = graylog_api_share_stream(dictGraylogApi, stream['id'], share_with_grn, share_level)
        if r['success'] == True:
            print(successText + "Stream " + blueText + stream['title'] + successText + " shared successfully.")
        else:
            print(errorText + "Stream " + blueText + stream['title'] + errorText + " failed to share.")

# ================= FUNCTIONS END ===============================





if not exists(strConfigFile):
    print(errorText + "ERROR! Config file '" + blueText + strConfigFile + errorText + "' does not exist!" + defText)
    exit(1)

dict_config = yaml_to_dict(strConfigFile)
graylog_api_conf_from_yaml = load_config_from_dict(dict_config, False)

print(alertText + "Graylog Server: " + graylog_api_conf_from_yaml['host'] + defText + "\n")

# do_action(graylog_api_conf_from_yaml, args.action)
match args.action:
    case "list-streams":
        graylog_api_get_streams_list(graylog_api_conf_from_yaml)
    case "share-all-stream":
        streams_list = graylog_api_get_streams_list(graylog_api_conf_from_yaml)
        # stream_id = "000000000000000000000002"
        share_with_grn = "grn::::team:64653376b55b7e084a8ffe5a"
        share_level = "view"
        bulk_graylog_api_share_stream(streams_list, graylog_api_conf_from_yaml, share_with_grn, share_level)