import requests, configparser, argparse, time, json, re, os, subprocess, urllib3, yaml, datetime
from requests.auth import HTTPBasicAuth
from os.path import exists
from datetime import datetime, timedelta
from pytz import timezone

# Disable HTTPS/TLS certificate warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# execute via cron
# */5 * * * * /home/drew/tmp/shutdown/py-help.sh -u /home/drew/tmp/shutdown/shutdown-if-gl-inactive.py --config-file /home/drew/tmp/shutdown/config.yml --confirm >> /home/drew/tmp/shutdown/cron.log

parser = argparse.ArgumentParser(description="Just an example",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--debug", "-d", help="For debugging", action=argparse.BooleanOptionalAction, default=False)
parser.add_argument("--verbose", help="For debugging", action=argparse.BooleanOptionalAction, default=False)
parser.add_argument("--confirm", help="For debugging", action=argparse.BooleanOptionalAction, default=False)
parser.add_argument("--config-file", '-c', help='Config file to use. Defaults to config.yml', default="config.yml", type=str, required=False)
parser.add_argument("--skip-root-check", help="allow running as non root user.", action=argparse.BooleanOptionalAction, default=False)
parser.add_argument("--skip-uptime-check", help="", action=argparse.BooleanOptionalAction, default=False)
parser.add_argument("--skip-graylog-active-check", help="", action=argparse.BooleanOptionalAction, default=False)
parser.add_argument("--skip-sleep", help="", action=argparse.BooleanOptionalAction, default=False)
parser.add_argument("--debug-no-send-notification", help="", action=argparse.BooleanOptionalAction, default=False)
parser.add_argument("--debug-ignore-uptime-failsafe", help="", action=argparse.BooleanOptionalAction, default=False)

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
        if not len(str(dictGraylogApi['port'])) > 0 and not int(dictGraylogApi['port']) > 0:
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
        sArgPort    = str(dictGraylogApi['port'])
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
        elif argMethod.upper() == "DELETE":
            # print(sUrl)
            try:
                r = requests.delete(sUrl, headers=sHeaders, verify=False, auth=HTTPBasicAuth(sArgUser, sArgPw))
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

def get_uptime_sec():
    proc = subprocess.Popen(["uptime"], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    raw_out = out.strip()
    # print(raw_out)
    # raw_out = "21:54:34 up 16 days,  7:54,  1 user,  load average: 3.30, 1.86, 1.60"
    # raw_out = " 13:57:18 up 51 days, 18:31,  1 user,  load average: 0.15, 0.15, 0.43"
    # raw_out = " 21:54:34 up 7:54,  1 user,  load average: 3.30, 1.86, 1.60"

    # 0m
    # raw_out = " 16:55:18 up 10 min,  1 user,  load average: 2.49, 0.72, 0.25"

    result = re.search(r"\d{2}:\d{2}\s+up\s+([^,]+),", str(raw_out))
    uptime = result.group(1)
    # print(uptime)

    # X days
    if re.search("days", str(uptime), re.IGNORECASE):
        result_days = re.search(r"(\d+)\s+", str(uptime))
        uptime_days = result_days.group(1).strip()
        uptime_sec = int(uptime_days) * 24 * 60 * 60
        return int(uptime_sec)
    # hr:min
    elif re.search("^\d+:\d+$", str(uptime), re.IGNORECASE):
        result_hr = re.search(r"^(\d+):\d+$", str(uptime))
        uptime_hr = int(result_hr.group(1).strip())
        
        result_mn = re.search(r"^\d+:(\d+)$", str(uptime))
        uptime_mn = int(result_mn.group(1).strip())
        
        uptime_sec = int(uptime_hr) * 60 * 60
        uptime_sec = uptime_sec + (int(uptime_mn) * 60)
        return int(uptime_sec)
        
    # X min
    elif re.search("^\d+ min$", str(uptime), re.IGNORECASE):
        result_min = re.search(r"^(\d+)", str(uptime))
        uptime_min = result_min.group(1).strip()
        uptime_sec = int(uptime_min) * 60
        return int(uptime_sec)

    # print(uptime)
    return int(0)

def get_datetime_diff(t1: object, t2: object):
    # safety if audit is newer than current UTC time
    if t1 > t2:
        return int(0)
    delta = t2 - t1
    return delta.seconds

def get_most_recent_activity_via_audit_log(graylog_api_conf: dict):
    r = doGraylogApi(graylog_api_conf, "get", "/api/plugins/org.graylog.plugins.auditlog/entries?page=1&per_page=100", {}, {}, {}, {}, 200, True)
    # print(json.dumps(r, indent=4))

    timestamp_utc = ""
    audit_msg = ""
    audit_object = ""

    if not "json" in r:
        return False

    if not "entries" in r["json"]:
        return False
    
    if not len(r["json"]["entries"]):
        return False
    
    if not "timestamp" in r["json"]["entries"][0]:
        return False
    
    # we must get the most recent NON customization notification item
    # print(json.dumps(r["json"]["entries"], indent=4))
    # exit()
    for audit_entry in r["json"]["entries"]:
        ignore_entry = False

        if "object" in audit_entry and str(audit_entry["object"]) == "urn:graylog:unknown:notification":
            ignore_entry = True
        
        if ignore_entry == False:
            # print(json.dumps(audit_entry, indent=4))
            timestamp_utc = audit_entry["timestamp"]
            audit_msg = audit_entry["message"]
            audit_object = audit_entry["object"]
            break
    
    return {
        "timestamp": timestamp_utc,
        "message": audit_msg,
        "object": audit_object
    }

def get_boot_timestamp():
    uptime_sec = get_uptime_sec()
    boot_timestamp = datetime.now(timezone('UTC')) - timedelta(seconds=uptime_sec)
    return boot_timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f%z")

def get_most_recent_activity_via_user(graylog_api_conf: dict, username: str):
    # fall back to boot/startup date
    boot_timestamp = str(get_boot_timestamp())
    warning_msg = alertText + "Warning! No recenty acvitiy found for user " + blueText + str(username) + alertText + ". Using boot time as last activity." + defText
    # boot_timestamp = None

    # get users
    r = doGraylogApi(graylog_api_conf, "get", "/api/users?include_permissions=false&include_sessions=true", {}, {}, {}, {}, 200, True)
    
    if not "json" in r:
        print(warning_msg)
        return boot_timestamp

    if not "users" in r["json"]:
        print(warning_msg)
        return boot_timestamp
    
    if not len(r["json"]["users"]):
        print(warning_msg)
        return boot_timestamp
    
    for user_entry in r["json"]["users"]:
        entry_username = user_entry["username"]
        if entry_username.lower() == username.lower():
            # we got'em
            latest_activity = user_entry["last_activity"]
            if latest_activity:
                return latest_activity
            else:
                print(warning_msg)
                return boot_timestamp

    print(warning_msg)
    return boot_timestamp

def is_graylog_cluster_active(graylog_api_conf: dict, idle_threshold_sec: int):
    # audit_entry = get_most_recent_activity_via_audit_log(graylog_api_conf)
    # timestamp_utc = audit_entry["timestamp"]
    # audit_msg = audit_entry["message"]
    # audit_object = audit_entry["object"]

    timestamp_utc = get_most_recent_activity_via_user(graylog_api_conf, "admin")
    # print(timestamp_utc)
    # exit()
    # timestamp_utc = r["json"]["entries"][0]["timestamp"]

    print("Last Activity for 'Admin' (UTC): " + blueText + str(timestamp_utc) + defText)
    timestamp_utc_obj = datetime.strptime(timestamp_utc, '%Y-%m-%dT%H:%M:%S.%f%z')
    # .strftime("%Y-%m-%dT%H:%M:%S")
    # print(timestamp_utc_obj)

    now_utc = datetime.now(timezone('UTC'))
    # print(now_utc)

    delta_sec = get_datetime_diff(timestamp_utc_obj, now_utc)
    # t1 = timestamp_utc_obj
    # t2 = now_utc
    # print("t1 (audit) = " + str(t1))
    # print("t2 (now) = " + str(t2))
    # delta = t2 - t1
    # print(delta.seconds)
    # print(delta_sec)
    # exit()

    print("    " + blueText + str(delta_sec) + defText + "s ago. Threshold: " + str(idle_threshold_sec) + "s")

    if delta_sec > idle_threshold_sec:
        return {
            "active": False,
            "last_activity": str(timestamp_utc),
            "last_acitivity_sec_ago": str(delta_sec)
        }
    
    return {
        "active": True,
        "last_activity": str(timestamp_utc),
        "last_acitivity_sec_ago": str(delta_sec)
    }

    # print(json.dumps(r["json"]["entries"][0]["timestamp"], indent=4))

def get_graylog_customication_notifications(graylog_api_conf: dict):
    r = doGraylogApi(graylog_api_conf, "get", "/api/plugins/org.graylog.plugins.customization/notifications", {}, {}, {}, {}, 200, True)
    if 'success' in r and "json" in r and r['success'] == True:
        return r["json"]

    return False

def do_delete_notification(graylog_api_conf: dict, notification_gid: str):
    # print(defText + "Deleting notification: " + blueText + notification_gid + defText)
    url = "/api/plugins/org.graylog.plugins.customization/notifications/" + str(notification_gid)
    r = doGraylogApi(graylog_api_conf, "delete", url, {}, {}, {}, {}, 200, True)
    # print(json.dumps(r, indent=4))
    if 'success' in r and r['success'] == True:
        print(successText + "Successfully deleted notification: " + blueText + notification_gid + defText)
    else:
        print(errorText + "Failed to delete notification: " + blueText + notification_gid + defText)

def do_remove_all_existing_notifications(graylog_api_conf: dict):
    notifications = get_graylog_customication_notifications(graylog_api_conf)
    if notifications and len(notifications) > 0:
        # print(json.dumps(notifications, indent=4))
        for notification in notifications:
            # print(notification)
            do_delete_notification(graylog_api_conf, notification)

def do_create_graylog_notification(graylog_api_conf: dict, title: str, short_msg: str, long_msg: str):
    url = "/api/plugins/org.graylog.plugins.customization/notifications"
    json_payload = {
        "title": str(title),
        "shortMessage": str(short_msg),
        "longMessage": str(long_msg),
        "isActive": True,
        "isDismissible": False,
        "atLogin": True,
        "isGlobal": True,
        "variant": "warning",
        "hiddenTitle": False
    }
    r = doGraylogApi(graylog_api_conf, "post", url, {}, json_payload, {}, {}, 200, True)
    if "success" in r and r['success'] == True:
        print(successText + "Notification successfully created." + defText)
    else:
        print(errorText + "Notification creation failed." + defText)
        print(json.dumps(r, indent=4))

def do_update_cluster_notification(graylog_api_conf: dict, title: str, short_msg: str, long_msg: str):
    if args.debug_no_send_notification == False:
        # ensure we don't have stale or orphaned notifications.
        do_remove_all_existing_notifications(graylog_api_conf)
        # create fresh new notification!
        do_create_graylog_notification(graylog_api_conf, title, short_msg, long_msg)
    else:
        print(alertText + "--debug-no-send-notification used, skipping posting cluster notification")

# ================= FUNCTIONS END ===============================

# verify running as root
whoami = os.popen('whoami').read().strip()
print("Executing as user: " + blueText + str(whoami) + defText)
if whoami.lower() != 'root':
    if args.skip_root_check == False:
        print(errorText + "ERROR! please execute as root. (or use " + blueText + "--skip-root-check" + errorText + ")" + defText)
        exit(1)

if not exists(strConfigFile):
    print(errorText + "ERROR! Config file '" + blueText + strConfigFile + errorText + "' does not exist!" + defText)
    exit(1)

dict_config = yaml_to_dict(strConfigFile)
graylog_api_conf_from_yaml = load_config_from_dict(dict_config, False)

b_is_active_dict = is_graylog_cluster_active(graylog_api_conf_from_yaml, 1800)

do_update_cluster_notification(graylog_api_conf_from_yaml, "Automatic shutdown warning!", "This cluster will automatically shutdown after 30 minutes of inactivity. Last activity: " + str(b_is_active_dict["last_activity"]) + " (" + str(b_is_active_dict["last_acitivity_sec_ago"]) + "s ago)", "https://graylogdocumentation.atlassian.net/wiki/spaces/SE/pages/2876145668/Graylog+Snapshot+testing+via+automated+AWS+instance")

uptime_sec = get_uptime_sec()
print("Uptime in seconds: " + blueText + str(uptime_sec) + defText)

if args.skip_uptime_check == False:
    if int(uptime_sec) < 600:
        print(alertText + "Saftey Check: system must be up for at least 10m (600s)" + defText)
        print("    Bypass with " + blueText + "--skip-uptime-check" + defText)
        exit(1)
    else:
        print(successText + "System up for at least 10m (600s)" + defText)
    
    # failsafe? uptime TOO long?
    # uptime > 6h
    if int(uptime_sec) > 21600:
        print(alertText + "Uptime greater than 6h. Intending to shutdown!" + defText + "\n" + "   Ignore by using --debug-ignore-uptime-failsafe")
        if args.debug_ignore_uptime_failsafe == False:
            if args.confirm == True:
                shut_cmd = "shutdown -h now"
                print(errorText + "executing '" + blueText + str(shut_cmd) + defText)
                os.system(shut_cmd)
            else:
                print(alertText + "   use " + blueText + "--confirm" + alertText + " flag to allow shutdown to complete" + defText)
            exit(0)
        else:
            print("--debug-ignore-uptime-failsafe used. Ignoring uptime failsafe.")

print(alertText + "Graylog Server: " + graylog_api_conf_from_yaml['host'] + defText)

b_is_active = b_is_active_dict["active"]
print("Is Graylog Cluster Active: " + blueText + str(b_is_active) + defText)

if args.skip_graylog_active_check == True:
    print(alertText + "--skip-graylog-active-check flag used. Ignoring graylog activity check.")
    b_is_active = False

if b_is_active == False:
    print(alertText + "Graylog Cluster inactive. Intending to shutdown!" + defText)
    get_five_min_from_now = datetime.utcnow() + timedelta(minutes=5)
    # print(get_five_min_from_now)
    # exit()
    do_update_cluster_notification(graylog_api_conf_from_yaml, "Shutting down...", "This cluster will shut down at " + str(get_five_min_from_now) + " UTC", "https://graylogdocumentation.atlassian.net/wiki/spaces/SE/pages/2876145668/Graylog+Snapshot+testing+via+automated+AWS+instance")
    if args.confirm == True:
        if args.skip_sleep == False:
            print("sleeping for " + blueText + "5m (300s)" + defText)
            time.sleep(300)
        shut_cmd = "shutdown -h now"
        print(errorText + "executing '" + blueText + str(shut_cmd) + defText)
        os.system(shut_cmd)
    else:
        print(alertText + "   use " + blueText + "--confirm" + alertText + " flag to allow shutdown to complete" + defText)
else:
    print(alertText + "Graylog cluter is active. Cannot continue." + defText)
    print(alertText + "   use " + blueText + "--skip-graylog-active-check" + alertText + " flag to override." + defText)

# print(json.dumps(r, indent=4))