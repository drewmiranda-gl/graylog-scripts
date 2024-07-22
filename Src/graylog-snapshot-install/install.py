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

import argparse
import shutil
import os
import requests
import time
import json
import subprocess
from os.path import exists
from requests.auth import HTTPBasicAuth
from tqdm import tqdm

parser = argparse.ArgumentParser(description="Just an example",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--tgz", help="Graylog Snap .tgz file. Hint: use download to automatically download the latest.", required=True)
parser.add_argument("--erase-mongodb", help="Erase graylog mongodb database", action=argparse.BooleanOptionalAction, default=False)
parser.add_argument("--erase-opensearch", help="Erase graylog opensearch indexes", action=argparse.BooleanOptionalAction, default=False)
parser.add_argument("--wait-for-opensearch", help="if script should wait until opensearch api is reachable", action=argparse.BooleanOptionalAction, default=False)
parser.add_argument("--debug", help="debug stuff", action=argparse.BooleanOptionalAction, default=False)
parser.add_argument("--skip-root-check", help="allow running as non root user.", action=argparse.BooleanOptionalAction, default=False)
parser.add_argument("--test-wait-for-online", action=argparse.BooleanOptionalAction, default=False)
parser.add_argument("--graylog-api-host", help="Graylog Snap .tgz file", required=False, default="127.0.0.1")
parser.add_argument("--install-opensearch", action=argparse.BooleanOptionalAction, default=False)
parser.add_argument("--install-mongod", action=argparse.BooleanOptionalAction, default=False)
parser.add_argument("--install-openjdk", action=argparse.BooleanOptionalAction, default=False)
parser.add_argument("--overwrite-download", action=argparse.BooleanOptionalAction, default=False)

args = parser.parse_args()

graylog_snapshot_tgz_file = str(args.tgz)

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
    "host": str(args.graylog_api_host),
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
    else:
        if exists(argPath):
            os.remove(argPath)

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
        # print(sUrl)

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

    print("do_wait_until_online")

    import json
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
                elif "status_code" in r:
                    print(errorText + "HTTP Return Code: " + str(r["status_code"]) + defText)

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
                print(successText + "Graylog Cluster is Online" + defText)
                return True
    return False

def do_wait_for_indexer():
    iSocketRetries = 0
    iSocketInitialRetryBackOff = iSocketRetryWaitSec

    while iSocketRetries < iSocketMaxRetries:
        if iSocketRetries > 0:
            print("OpenSearch Retry " + str(iSocketRetries) + " of " + str(iSocketMaxRetries))

        r = do_opensearch_api("GET", "", {}, {}, False, 200, True)
        if 'success' in r:
            if r['success'] == False:
                # if "exception" in r:
                print(errorText + "Cannot reach OpenSearch!" + defText + " Waiting " + str(iSocketInitialRetryBackOff) + "s (Max backoff: " + str(iSocketRetryBackOffMaxSec) + "s)...")
                print(errorText + str(r["exception"]) + defText)

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
        print(alertText + "waiting until OpenSearch is online..." + defText)
        do_wait_for_indexer()

    if args.debug == False:
        x = requests.delete('http://127.0.0.1:9200/_all')
        print(x.text)

def download_file_via_github(arg_url, arg_out_file):
    print("Downloading latest: " + blueText + arg_out_file + defText + " (via github)")
    deleteIfExists(arg_out_file, False)
    os.system("wget --quiet " + arg_url + " -O " + arg_out_file)
    if not exists(arg_out_file):
        print(errorText + "ERROR: Failed to download '" + arg_out_file + "'. Cannot continue." + defText)
        exit(2)
    return ""

def patch_file(arg_source_file, arg_patch_file):
    # os.system("patch server.conf < graylog-server.conf.patch")
    
    # "patch server.conf < graylog-server.conf.patch"
    proc = subprocess.Popen(["".join(["patch ", arg_source_file, " < ", arg_patch_file])], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    raw_out = out.strip().decode()
    
    raw_err = ""
    if err:
        raw_err = err.strip().decode()

    if proc.returncode == 0:
        print(successText + raw_out + defText)
    else:
        print(errorText + raw_err + defText)
        exit(1)

def exec_w_stdout(arg_cmd: str, exit_on_err: bool, suppress_output: bool):
    proc = subprocess.Popen([arg_cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    raw_out = out.strip().decode()
    
    raw_err = ""
    if err:
        raw_err = err.strip().decode()

    if proc.returncode == 0:
        if suppress_output == False:
            print(successText + raw_out + defText)
        else:
            print(successText + "Success (" + str(proc.returncode) + ")" + defText)
    else:
        print(errorText + raw_err + defText)
        if exit_on_err == True:
            exit(1)
    return ""

def get_download_url_from_downloads_graylog_org(build_artifact: str):
    url = "https://downloads.graylog.org/nightly-builds?limit=1&artifacts=" + build_artifact
    response = requests.get(url)

    if not response:
        print("ERROR, no 'response'")
        exit(1)
    
    if not int(response.status_code) == 200:
        print("ERROR, HTTP Status: " + str(response.status_code))
        exit(1)
    
    json_obj = json.loads(response.text)

    if not "artifacts" in json_obj:
        print("ERROR, artifacts not found in json response")
        exit(1)
    
    if not len(json_obj['artifacts']):
        print("ERROR, 0 not found in json_obj['artifacts']")
        exit(1)

    return json_obj['artifacts'][0]

def do_download_build_from_downloads_graylog_org(build_artifact: str, overwrite: bool):
    json_artifact = get_download_url_from_downloads_graylog_org(build_artifact)
    url_to_download = json_artifact['url']
    local_filename = json_artifact['filename']
    print("Attempting to download build " + blueText + url_to_download + defText)
    
    if overwrite == False:
        if exists(local_filename):
            print(alertText + "NOTE: Use --overwrite-download to force skipped file to be downloaded." + defText)
            print(successText + "Skipping file because already downloaded: " + blueText + local_filename + defText)
            return local_filename

    url = url_to_download
    # Streaming, so we can iterate over the response.
    response = requests.get(url, stream=True)
    total_size_in_bytes= int(response.headers.get('content-length', 0))
    block_size = 1024 #1 Kibibyte
    progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
    with open(local_filename, 'wb') as file:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            file.write(data)
    progress_bar.close()
    if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
        print("ERROR, something went wrong")
    
    print(successText + "Downloaded file successfully: " + blueText + local_filename + defText)
    return local_filename























































if args.test_wait_for_online == True:
    do_wait_until_online()

if args.install_openjdk == True:
    print("Installing OpenJDK... (This may take a minute...)")
    exec_w_stdout("bash install_openjdk.sh", True, True)

if args.install_opensearch == True:
    print("Installing OpenSearch... (This will take a couple of minutes...)")
    exec_w_stdout("bash install_opensearch_2.sh", True, True)

if args.install_mongod == True:
    print("Installing Mongod... (This may take a minute...)")
    exec_w_stdout("bash install_mongod.sh", True, True)
    print("Sleeping for 10s to allow mongod time to fully boot...")
    time.sleep(10)

# =============================================================================
# 0. get needed files

# graylog-server-jvm-def
download_file_via_github("https://raw.githubusercontent.com/Graylog2/fpm-recipes/6.0/recipes/graylog-server/files/environment", "graylog-server-jvm-def")
download_file_via_github("https://raw.githubusercontent.com/Graylog2/fpm-recipes/6.0/recipes/graylog-server/files/graylog-server.sh", "graylog-server")
download_file_via_github("https://raw.githubusercontent.com/Graylog2/fpm-recipes/6.0/recipes/graylog-server/files/systemd.service", "graylog-server.service")
download_file_via_github("https://raw.githubusercontent.com/Graylog2/fpm-recipes/6.0/recipes/graylog-server/files/log4j2.xml", "log4j2.xml")
download_file_via_github("https://raw.githubusercontent.com/Graylog2/graylog2-server/master/misc/graylog.conf", "server.conf")
download_file_via_github("https://raw.githubusercontent.com/Graylog2/fpm-recipes/6.0/recipes/graylog-server/patches/graylog-server.conf.patch", "graylog-server.conf.patch")
patch_file("server.conf", "graylog-server.conf.patch")

# =============================================================================

# print(alertText + "Stopping " + blueText + "graylog-server" + defText)
# os.system("systemctl stop graylog-server")

# prelim whatever
print("Erase graylog mongo db: " + str(args.erase_mongodb))
if args.erase_mongodb == True:
    erase_mongodb()

print("Erase opensearch indexes: " + str(args.erase_opensearch))
if args.erase_opensearch == True:
    erase_opensearch()

# 0. Cleanup ???? - https://go2docs.graylog.org/5-1/setting_up_graylog/default_file_locations.html
# /var/lib/graylog-server
# /var/log/graylog-server
# /usr/share/graylog-server
# /etc/default/graylog-server
# 

# =============================================================================
# 1. Extract .tgz and get path
if str(args.tgz).lower() == "download" :
    print("Downloading latest Graylog snapshot...")
    graylog_snapshot_tgz_file = do_download_build_from_downloads_graylog_org("graylog-enterprise-linux-x64", args.overwrite_download)

if not exists(graylog_snapshot_tgz_file):
    print(errorText + "ERROR! snapshot tgz file " + blueText + str(graylog_snapshot_tgz_file) + errorText + " does not exist!" + defText)
    exit(1)

extracted_path = extract(graylog_snapshot_tgz_file)
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

# print("Downloading latest " + blueText + "log4j2.xml" + defText + " via github")
# os.system("wget https://raw.githubusercontent.com/Graylog2/graylog2-server/master/graylog2-server/src/main/resources/log4j2.xml -O log4j2.xml")
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

# elasticsearch_hosts
print("    set elasticsearch_hosts" + blueText + "http://127.0.0.1:9200" + defText)
sedcmd = "sed -i 's/#elasticsearch_hosts = .*/elasticsearch_hosts = http\:\/\/127.0.0.1\:9200/g' /etc/graylog/server/server.conf"
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
print("create log dir: " + blueText + "/var/log/graylog-server" + defText)
os.system("mkdir -p /var/log/graylog-server/")

# jvm defaults
# /etc/default/graylog-server
print("copy jvm defaults file: " + blueText + "/etc/default/graylog-server" + defText)
os.system("cp -f graylog-server-jvm-def /etc/default/graylog-server")

# journal and data dirs
print("create journal dir: " + blueText + "/var/lib/graylog-server/journal/" + defText)
os.system("mkdir -p /var/lib/graylog-server/journal/")

# check if we are missing bundled JVM
bundled_jvm_target_path = "/usr/share/graylog-server/jvm"
bundled_jvm_tgz = "gl-jvm.tar.gz"
# NOTE: gl-jvm.tar.gz prepared with: `tar -czvf gl-jvm.tar.gz /usr/share/graylog-server/jvm`
if not exists(bundled_jvm_target_path):
    print(alertText + "WARNING! Graylog bundled JDK not found. '" + blueText + bundled_jvm_target_path + defText + "'")
    # only attempt if bundled jdk tgz file exists
    if exists(bundled_jvm_tgz):
        print("Attempting to extract an offline copy of the bundled JDK")
        # run command
        os.system("tar -xzf gl-jvm.tar.gz --directory /")
        # validate
        if exists(bundled_jvm_target_path):
            print(successText + "bundled JDK successfully extracted to '" + blueText + bundled_jvm_target_path + defText + "'")
        else:
            print(errorText + "failed to extract bundled JDK  to '" + blueText + bundled_jvm_target_path + defText + "'. Cannot continue. Fatal error.")
            exit(1)


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
os.system("systemctl restart graylog-server")

print(alertText + "waiting until graylog-server is online..." + defText)
do_wait_until_online()
print(successText + "Completed." + defText)
