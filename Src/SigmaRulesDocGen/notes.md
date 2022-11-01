# Graylog API

## Import Sigma Rules using Github repo

`/api/plugins/org.graylog.plugins.securityapp.sigma/sigma/rules/import`

POST

```
{"keys":["rules/application/antivirus/av_exploiting.yml"]}
```

## View rules

/api/plugins/org.graylog.plugins.securityapp.sigma/sigma/rules?page=1&per_page=15&sort=parsed_rule.title&direction=asc

# Workflow proof of concept for auto importing sigma rules

1. Generate a list of sigma files with paths
    * can be done by `git clone` of sigma repo
2. Post list of files to graylog API
    * Assuming there is a limit on bulk import, will test