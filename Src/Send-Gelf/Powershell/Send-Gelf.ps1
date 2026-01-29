function Send-Gelf {
    <#
    .SYNOPSIS
    Sends a JSON object to a specified Graylog GELF HTTP Input
    Graylog Inputs MUST be a GELF HTTP Input

    .DESCRIPTION
    This fucntion sends a JSON object to graylog using a specified Graylog GELF HTTP URI.
    This function has a connection timeout of 3 seoncds. Tweak to suite your needs.

    .PARAMETER uri
    URI to send Gelf payload to (Graylog GELF HTTP Input)
    This parameter is mandatory.

    .PARAMETER json_body
    JSON Payload to send to Graylog GELF HTTP
    This parameter is mandatory.

    Example:
        $body = @{
            host = $env:computername
            message = "Graylog log message"
        } | ConvertTo-Json -Compress
    
    Additional fields:
    Note the number is not enclosed in double quotes.
    This implies the data type is a number instead of a string
        $body = @{
            host = $env:computername
            message = "Graylog log message"
            this_is_a_field = "hello there"
            this_is_a_number = 1
        } | ConvertTo-Json -Compress

    .EXAMPLE
    $body = @{
        host = $env:computername
        message = "Graylog log message"
    } | ConvertTo-Json -Compress
    Send-Gelf -uri "http://graylog.domain.tld:12201/gelf" -json_body $body

    .NOTES
    Requires PowerShell 5.1 or later due. (only tested against 5.1 and later)

    .LINK
    https://github.com/drewmiranda-gl/graylog-scripts/tree/main/Src/Send-Gelf/Powershell
    #>
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true,
                   Position = 0,
                   HelpMessage = 'URI to send Gelf payload to (Graylog GELF HTTP Input)')]
        [string]$uri
        ,
        [Parameter(Mandatory = $true,
                   Position = 1,
                   HelpMessage = 'JSON Payload to send to Graylog GELF HTTP')]
        [string]$json_body
    )

    try {
        Invoke-RestMethod -Method Post -Uri $uri -Body $json_body -ContentType "application/json" -TimeoutSec 3
    }
    catch {
        Write-Host "`nError sent: $($_.Exception.Message)"
    }
}