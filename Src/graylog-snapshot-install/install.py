# simple script to handle an install of a graylog snapshot via .tgz
# https://jenkins.ci.torch.sh/job/Graylog-Snapshots/job/graylog2-server/job/master/

# TASKS
# 1. extract contents of .tgz
# 
# 2. get name of extracted folder
# 
# 3. copy/move files to proper path
#   * /usr/share/graylog-server/bin
#   * /etc/default/graylog-server
#   * /var/lib/graylog-server/journal
#   * /var/log/graylog-server/
#   https://go2docs.graylog.org/5-0/setting_up_graylog/default_file_locations.html
# 
# 4. configure server.conf
#   * /etc/graylog/server/server.conf
# 
# 5. create service
# 

import argparse, shutil, os, requests, time, json, subprocess
from os.path import exists
from requests.auth import HTTPBasicAuth

parser = argparse.ArgumentParser(description="Just an example",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--tgz", help="Graylog Snap .tgz file", required=True)
parser.add_argument("--erase-mongodb", help="Erase graylog mongodb database", action=argparse.BooleanOptionalAction, default=False)
parser.add_argument("--erase-opensearch", help="Erase graylog opensearch indexes", action=argparse.BooleanOptionalAction, default=False)
parser.add_argument("--wait-for-opensearch", help="if script should wait until opensearch api is reachable", action=argparse.BooleanOptionalAction, default=False)
parser.add_argument("--debug", help="debug stuff", action=argparse.BooleanOptionalAction, default=False)
parser.add_argument("--skip-root-check", help="allow running as non root user.", action=argparse.BooleanOptionalAction, default=False)

args = parser.parse_args()

# font
#                       Style
#                       v Color
#                       v v  Background
#                       v v  v
defText         = "\033[0;30;50m"       # Black
boldText        = "\033[1;30;50m"       # Black
alertText       = "\033[1;33;50m"       # yellow
errorText       = "\033[1;31;50m"       # red
successText     = "\033[1;32;50m"       # green
blueText        = "\033[0;34;50m"       # blue

print(defText)

dictGraylogApi = {
    "https": False,
    "host": "127.0.0.1",
    "port": "9000",
    "user": "admin",
    "password": "admin"
}

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

def deleteIfExists(argPath, bIsFolder):
    if bIsFolder == True:
        if exists(argPath):
            shutil.rmtree(argPath)

def listdirs(folder):
    return [d for d in os.listdir(folder) if os.path.isdir(os.path.join(folder, d))]

def extract(tar_url, extract_path='./extract'):
    print("Extracting " + blueText + tar_url + defText)
    deleteIfExists(extract_path, True)

    if exists(tar_url):
        os.system("mkdir " + extract_path)
        # print(tar_url)
        extract_cmd = "tar -xzf " + tar_url + " --directory " + extract_path
        # print(extract_cmd)
        os.system(extract_cmd)
        
        dir_list = listdirs(extract_path)
        if len(dir_list) > 0:
            print(successText + "Successfully extracted to " + blueText + extract_path + "/" + dir_list[0] + defText)
            return extract_path + "/" + dir_list[0]

    else:
        print("ERROR! File does not exist!")

def move_to_path(argSrc, argDst):
    print("Moving " + blueText + argSrc + defText + " to " + blueText + argDst + defText)
    deleteIfExists(argDst, True)
    os.system("mkdir -p " + argDst)

    # rsynccmd = "rsync -a " + argSrc + " " + argDst
    rsynccmd = "rsync -a " + argSrc + "/* " + argDst
    # print(rsynccmd)
    o = os.system(rsynccmd)

# verify running as root
whoami = os.popen('whoami').read().strip()
if whoami.lower() != 'root':
    if args.skip_root_check == False:
        print(errorText + "ERROR! please execute as root. (or use --skip-root-check)" + defText)
        exit(1)

def graylogApiConfigIsValid():
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

def do_opensearch_api(argMethod: str, argApiUrl: str, argHeaders: dict, argJson: dict, argFiles: dict, argExpectedReturnCode: int, argReturnJson: bool):
    sUrl = "http://127.0.0.1:9200" + argApiUrl
    # print(sUrl)

    # add headers
    sHeaders = {"Accept":"application/json", "X-Requested-By":"python-ctpk-upl"}
    sHeaders = mergeDict(sHeaders, argHeaders, True)

    if argMethod.upper() == "GET":
        try:
            r = requests.get(sUrl, headers=sHeaders, verify=False)
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

def doGraylogApi(argMethod: str, argApiUrl: str, argHeaders: dict, argJson: dict, argFiles: dict, argExpectedReturnCode: int, argReturnJson: bool):
    if graylogApiConfigIsValid() == True:
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
        sHeaders = {"Accept":"application/json", "X-Requested-By":"python-ctpk-upl"}
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
            if argFiles == False:
                try:
                    r = requests.post(sUrl, json = argJson, headers=sHeaders, verify=False, auth=HTTPBasicAuth(sArgUser, sArgPw))
                except Exception as e:
                    return {
                        "success": False,
                        "exception": e
                    }
            else:
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

def do_wait_until_online():
    iSocketRetries = 0
    iSocketInitialRetryBackOff = iSocketRetryWaitSec

    while iSocketRetries < iSocketMaxRetries:
        if iSocketRetries > 0:
            print("Retry " + str(iSocketRetries) + " of " + str(iSocketMaxRetries))

        r = doGraylogApi("GET", "/api/", {}, {}, False, 200, True)
        if 'success' in r:
            if r['success'] == False:
                if "exception" in r:
                    print(errorText)
                    print(r["exception"])
                    print(defText)

                    print("Waiting " + str(iSocketInitialRetryBackOff) + "s Max backoff: " + str(iSocketRetryBackOffMaxSec) + "s)...")
                    # sleep for X seconds
                    time.sleep(iSocketInitialRetryBackOff)

                    # Increment socket retry count
                    iSocketRetries = iSocketRetries + 1

                    # If the number of retries exceeds the intial backoff retry grace count
                    #   Don't apply backoff for the first X number of retries in case the error was short lived
                    if iSocketRetries > iSocketRetryBackOffGraceCount:
                        # if backoff value is less than max, keep adding backoff value to delay
                        if iSocketInitialRetryBackOff < iSocketRetryBackOffMaxSec:
                            iSocketInitialRetryBackOff = iSocketInitialRetryBackOff + iSocketRetryBackOffSec

                        # if backoff value exceeds max, set to max
                        if iSocketInitialRetryBackOff > iSocketRetryBackOffMaxSec:
                            iSocketInitialRetryBackOff = iSocketRetryBackOffMaxSec

                    # If socket retries exceeds max, exit script
                    if iSocketRetries > iSocketMaxRetries:
                        print("ERROR! To many socket retries")
                        return False

            elif r['success'] == True:
                print(successText + "Graylog Cluster is Online" + defText)
                return True
    return False

def do_wait_for_indexer():
    iSocketRetries = 0
    iSocketInitialRetryBackOff = iSocketRetryWaitSec

    while iSocketRetries < iSocketMaxRetries:
        if iSocketRetries > 0:
            print("Retry " + str(iSocketRetries) + " of " + str(iSocketMaxRetries))

        r = do_opensearch_api("GET", "", {}, {}, False, 200, True)
        if 'success' in r:
            if r['success'] == False:
                # if "exception" in r:
                print(errorText)
                print(r["exception"])
                print(defText)

                print("Waiting " + str(iSocketInitialRetryBackOff) + "s (Max backoff: " + str(iSocketRetryBackOffMaxSec) + "s)...")
                # sleep for X seconds
                time.sleep(iSocketInitialRetryBackOff)

                # Increment socket retry count
                iSocketRetries = iSocketRetries + 1

                # If the number of retries exceeds the intial backoff retry grace count
                #   Don't apply backoff for the first X number of retries in case the error was short lived
                if iSocketRetries > iSocketRetryBackOffGraceCount:
                    # if backoff value is less than max, keep adding backoff value to delay
                    if iSocketInitialRetryBackOff < iSocketRetryBackOffMaxSec:
                        iSocketInitialRetryBackOff = iSocketInitialRetryBackOff + iSocketRetryBackOffSec

                    # if backoff value exceeds max, set to max
                    if iSocketInitialRetryBackOff > iSocketRetryBackOffMaxSec:
                        iSocketInitialRetryBackOff = iSocketRetryBackOffMaxSec

                # If socket retries exceeds max, exit script
                if iSocketRetries > iSocketMaxRetries:
                    print("ERROR! To many socket retries")
                    return False

            elif r['success'] == True:
                print(successText + "OpenSearch Cluster is Online" + defText)
                return True
    return False

def erase_mongodb():
    print(alertText + "Deleting MongoDB database " + blueText + "graylog" + defText)
    proc = subprocess.Popen(["mongosh mongodb://127.0.0.1:27017/graylog --quiet --eval 'printjson(db.dropDatabase())'"], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    print("program output:", out)

def erase_opensearch():
    print(alertText + "Deleting OpenSearch indices " + blueText + "_all" + defText)
    
    if args.wait_for_opensearch == True:
        print(alertText + "waiting until graylog-server is online..." + defText)
        do_wait_for_indexer()

    if args.debug == False:
        x = requests.delete('http://127.0.0.1:9200/_all')
        print(x.text)

print(alertText + "Stopping " + blueText + "graylog-server" + defText)
os.system("systemctl stop graylog-server")

# prelim whatever
print("Erase graylog mongo db: " + str(args.erase_mongodb))
if args.erase_mongodb == True:
    erase_mongodb()

print("Erase opensearch indexes: " + str(args.erase_opensearch))
if args.erase_opensearch == True:
    erase_opensearch()

# 1. Extract .tgz and get path

if not exists(args.tgz):
    print(errorText + "ERROR! snapshot tgz file " + blueText + str(args.tgz) + errorText + " does not exist!" + defText)
    exit(1)

extracted_path = extract(args.tgz)
# extracted_path = "./extract/graylog-5.1.0-SNAPSHOT-20230331094000-linux-x64"
# print("Extracted Path: " + extracted_path)

# 2. move to correct path
move_to_path(extracted_path, "/usr/share/graylog-server")

# 3. copy launch script for service
print("Copying service ExecStart file")
os.system("cp -f graylog-server /usr/share/graylog-server/bin")
os.system("chmod +x /usr/share/graylog-server/bin/graylog-server")

# 4. create graylog user
print("Creating user: " + blueText + "graylog" + defText)
os.system("sudo adduser --system --disabled-password --disabled-login --home /var/empty --no-create-home --quiet --force-badname --group graylog")

# 5. Copy Service File
print("Installing service: " + blueText + "graylog-server" + defText)
os.system("cp -f graylog-server.service /etc/systemd/system/graylog-server.service")
os.system("systemctl daemon-reload")

# 6. Build server.conf
print("Building config " + blueText + "server.conf" + defText)
os.system("mkdir -p /etc/graylog/server/")
os.system("cp -f server.conf /etc/graylog/server/server.conf")
os.system("cp -f log4j2.xml /etc/graylog/server/log4j2.xml")

# admin pw
print("    setting admin password to " + alertText + "admin" + defText)
admin_pw_hash = os.popen('echo -n admin | sha256sum | cut -d" " -f1').read().strip()
sedcmd = 'sed -i "s/root_password_sha2 =.*/root_password_sha2 = ' + admin_pw_hash + '/g" /etc/graylog/server/server.conf'
os.system(sedcmd)

# pw secret
print("    setting password secret")
pwsecret = os.popen('openssl rand -hex 32').read().strip()
sedcmd = 'sed -i "s/password_secret =.*/password_secret = ' + pwsecret + '/g" /etc/graylog/server/server.conf'
os.system(sedcmd)

# bind to 0.0.0.0
print("    bind to " + blueText + "0.0.0.0:9000" + defText)
sedcmd = "sed -i 's/#http_bind_address = 127.0.0.1.*/http_bind_address = 0.0.0.0:9000/g' /etc/graylog/server/server.conf"
os.system(sedcmd)

# set paths
print("    bin_dir: " + blueText + "/usr/share/graylog-server/bin" + defText)
sedcmd = "sed -i 's/bin_dir = .*/bin_dir = \/usr\/share\/graylog-server\/bin/g' /etc/graylog/server/server.conf"
os.system(sedcmd)

print("    plugin_dir: " + blueText + "/usr/share/graylog-server/plugin" + defText)
sedcmd = "sed -i 's/plugin_dir = .*/plugin_dir = \/usr\/share\/graylog-server\/plugin/g' /etc/graylog/server/server.conf"
os.system(sedcmd)

print("    data_dir: " + blueText + "/var/lib/graylog-server" + defText)
sedcmd = "sed -i 's/data_dir = .*/data_dir = \/var\/lib\/graylog-server/g' /etc/graylog/server/server.conf"
os.system(sedcmd)

print("    message_journal_dir: " + blueText + "/var/lib/graylog-server/journal" + defText)
sedcmd = "sed -i 's/message_journal_dir = .*/message_journal_dir = \/var\/lib\/graylog-server\/journal/g' /etc/graylog/server/server.conf"
os.system(sedcmd)

# log dir
print("create log dir")
os.system("mkdir -p /var/log/graylog-server/")

# jvm defaults
# /etc/default/graylog-server
print("copy jvm defaults file: " + blueText + "/etc/default/graylog-server" + defText)
os.system("cp -f graylog-server-jvm-def /etc/default/graylog-server")

# journal and data dirs
print("create journal dir")
os.system("mkdir -p /var/lib/graylog-server/journal/")

# owners and permissions and cool stuff
print("Set graylog as owner for all required folders:")

print("    " + blueText + "/etc/graylog" + defText)
os.system("sudo chown -R graylog:graylog /etc/graylog")

print("    " + blueText + "/usr/share/graylog-server" + defText)
os.system("sudo chown -R graylog:graylog /usr/share/graylog-server")

print("    " + blueText + "/var/log/graylog-server" + defText)
os.system("sudo chown -R graylog:graylog /var/log/graylog-server")

print("    " + blueText + "/var/lib/graylog-server" + defText)
os.system("sudo chown -R graylog:graylog /var/lib/graylog-server")

# set timezone to UTC
print("Setting timezone: " + blueText + "UTC" + defText)
os.system("timedatectl set-timezone UTC")

# enable and start
print("Enabling service: " + blueText + "graylog-server" + defText)
os.system("systemctl enable graylog-server")
print("Starting service: " + blueText + "graylog-server" + defText)
os.system("systemctl start graylog-server")

print(alertText + "waiting until graylog-server is online..." + defText)
do_wait_until_online()
print(successText + "Completed." + defText)
