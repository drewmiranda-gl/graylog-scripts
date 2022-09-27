<?php

$curl = curl_init();

// set your server hostname
$strServerName = 'server_hostname';

// set your server port
$strServerPort = '9000';

// set auth, base64 encoded for auth basic
$strAuthBasic = 'Basic ...';

// namespace of metrics to collect (becareful as this may return a VERY LARGE result set and consume a lot of resources on your graylog cluster)
$strNamespace = 'org.graylog.plugins.pipelineprocessor.ast.Pipeline';

// build curl query
// generated via postman
// json posted was obtained from query sent via graylog web interface
curl_setopt_array($curl, array(
  CURLOPT_URL => 'http://'.$strServerName.':'.$strServerPort.'/api/system/metrics/namespace/' . $strNamespace,
  CURLOPT_RETURNTRANSFER => true,
  CURLOPT_ENCODING => '',
  CURLOPT_MAXREDIRS => 10,
  CURLOPT_TIMEOUT => 0,
  CURLOPT_FOLLOWLOCATION => true,
  CURLOPT_HTTP_VERSION => CURL_HTTP_VERSION_1_1,
  CURLOPT_CUSTOMREQUEST => 'GET',
  CURLOPT_HTTPHEADER => array(
    'Authorization: '.$strAuthBasic,
  ),
));

$response = curl_exec($curl);

curl_close($curl);

// convert json to a PHP array
$arrJson = json_decode( preg_replace('/[\x00-\x1F\x80-\xFF]/', '', $response), true );

// set header so that text is output as plaintext
header("Content-type: text/plain; version=0.0.4; charset=utf-8");

$iLines = 0;

$strNameSpaceNoDots = preg_replace("#\.|\-#i", "_", $strNamespace);

foreach ($arrJson['metrics'] as $aMetric) {
	$bInclude = true;	
	$sMetricName = $aMetric['full_name'];
	$sMetricName = preg_replace("#\.|\-#i", "_", $sMetricName);
	$sMetricValue = $aMetric['metric']['rate']['one_minute'];
	$sMetricValue = round($sMetricValue, 17);
	if (preg_match("#[a-zA-Z]#i", $sMetricValue)) {
		$bInclude = false;
	}
	if ($bInclude === true) {
		if ($i > 0) {
			echo "\n";
		}
		$strMetricName = str_replace($strNameSpaceNoDots . "_", "", $sMetricName);
		echo $strNameSpaceNoDots.'{metricname="'.$strMetricName.'"} '.$sMetricValue;
		++$i;
	}
}
