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

import tarfile, argparse, shutil, os
from os.path import exists

parser = argparse.ArgumentParser(description="Just an example",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--tgz", help="Graylog Snap .tgz file", required=True)

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

# 1. Extract .tgz and get path
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

print(successText + "Completed." + defText)
