# Intro

# Prerequisites

* https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES
* [winlogbeat](https://www.elastic.co/beats/winlogbeat)

# winlogbeat config example

```yaml
#.\winlogbeat.exe -e -c .\winlogbeat-evtx.yml -E EVTX_FILE=c:\backup\Security-2019.01.evtx

winlogbeat.event_logs:
  - name: ${EVTX_FILE} 
    no_more_events: stop

winlogbeat.shutdown_timeout: 1s
winlogbeat.registry_file: "${CWD}/winlogbeat/evtx-registry.yml"

output.logstash:
   hosts: ["192.168.0.86:5045"]

logging:
  #level: info
  level: info
  files:
    path: "${CWD}/winlogbeat"
    rotateonstartup: false
    keepfiles: 2
```

# Example command

`.\Winlogbeat-Bulk-Read.ps1 -Exe "C:\Users\Administrator\Downloads\winlogbeat-8.9.0-windows-x86_64\winlogbeat-8.9.0-windows-x86_64\winlogbeat.exe" -Config "C:\evtx_replay\winlogbeat_evtx_replay.yml" -Source "C:\evtx_replay\evtx" -Verbose`

NOTE: this preserves the original timestamp of the original log messages. When replayed to graylog the messages will be years in the past.