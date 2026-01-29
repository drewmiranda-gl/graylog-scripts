# set variable for script root directory
$scriptDir = $PSScriptRoot
# Import Send-Gelf function
$filePath_Send_Gelf  = Join-Path -Path $scriptDir -ChildPath "Send-Gelf.ps1"
. $filePath_Send_Gelf

# declare gelf uri var
$gelf_uri = "http://graylog.domain.tld:12201/gelf"

# declare json body var
$body = @{
    host = $env:computername
    message = "Graylog log message"
    this_is_a_field = "hello there"
    this_is_a_number = 1
} | ConvertTo-Json -Compress

# send gelf payload
Send-Gelf -uri $gelf_uri -json_body $body 
