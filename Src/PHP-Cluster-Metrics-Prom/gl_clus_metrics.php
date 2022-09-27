<?php

$curl = curl_init();

// set your server hostname
$strServerName = 'server_hostname';

// set your server port
$strServerPort = '9000';

// set auth, base64 encoded for auth basic
$strAuthBasic = 'Basic ....';

// build curl query
// generated via postman
// json posted was obtained from query sent via graylog web interface
curl_setopt_array($curl, array(
  CURLOPT_URL => 'http://'.$strServerName.':'.$strServerPort.'/api/cluster/metrics/multiple',
  CURLOPT_RETURNTRANSFER => true,
  CURLOPT_ENCODING => '',
  CURLOPT_MAXREDIRS => 10,
  CURLOPT_TIMEOUT => 0,
  CURLOPT_FOLLOWLOCATION => true,
  CURLOPT_HTTP_VERSION => CURL_HTTP_VERSION_1_1,
  CURLOPT_CUSTOMREQUEST => 'POST',
  CURLOPT_POSTFIELDS =>'{"metrics":["jvm.memory.heap.used","jvm.memory.heap.committed","jvm.memory.heap.max","org.graylog2.buffers.input.usage","org.graylog2.buffers.input.size","org.graylog2.buffers.process.usage","org.graylog2.buffers.process.size","org.graylog2.buffers.output.usage","org.graylog2.buffers.output.size","org.graylog2.journal.append.1-sec-rate","org.graylog2.journal.read.1-sec-rate","org.graylog2.journal.segments","org.graylog2.journal.entries-uncommitted","org.graylog2.journal.utilization-ratio","org.graylog2.journal.oldest-segment","org.graylog2.throughput.input.1-sec-rate","org.graylog2.throughput.output.1-sec-rate","org.graylog.enterprise.license.status.violated","org.graylog.enterprise.license.status.expired","org.graylog.enterprise.license.status.expiration-upcoming","org.graylog.enterprise.license.status.trial","org.graylog.enterprise.license.traffic.violation-upcoming","org.graylog.plugins.pipelineprocessor.processors.PipelineInterpreter.executionTime"]}',
  CURLOPT_HTTPHEADER => array(
    'Accept: application/json',
    'X-Requested-By: XMLHttpRequest',
    'X-Requested-With: XMLHttpRequest',
    'Authorization: '.$strAuthBasic,
    'Content-Type: application/json'
  ),
));

$response = curl_exec($curl);

curl_close($curl);

// convert json to a PHP array
$arrJson = json_decode( preg_replace('/[\x00-\x1F\x80-\xFF]/', '', $response), true );

// set header so that text is output as plaintext
header("Content-type: text/plain; version=0.0.4; charset=utf-8");

$iLines = 0;

foreach ($arrJson as $sClusterId => $aClusterMetrics) {
	foreach ($aClusterMetrics['metrics'] as $ikey => $aMetric ) {
		$bInclude = true;
		
		$sMetricName = $aMetric['full_name'];
		$sMetricName = preg_replace("#\.|\-#i", "_", $sMetricName);

		/*
		 * 	metric type?
		 */
		$sMetricType = $aMetric['type'];

		$sMetricValue = 0;
		if (strtolower($sMetricType) === 'gauge') {
		$sMetricValue = $aMetric['metric']['value'];
		$sMetricValue = round($sMetricValue, 17);
		}
		elseif (strtolower($sMetricType) === 'timer') {
			$strDurationUnit = $aMetric['metric']['duration_unit'];
			$strRateUnit	 = str_replace("/", "", $aMetric['metric']['rate_unit']);

			$strExtraAttr = ", ";
			$strExtraAttr .= "duration_unit=\"{$strDurationUnit}\"";
			$strExtraAttr .= ", ";
			$strExtraAttr .= "rate_unit=\"{$strRateUnit}\"";

			$sMetricValue = $aMetric['metric']['time']['99th_percentile'];
			$sMetricValue = round($sMetricValue, 17);
		}
		else {
			$sMetricValue = 0;
		}

		if (preg_match("#[a-zA-Z]#i", $sMetricValue)) {
			$bInclude = false;
		}

		if ($bInclude === true) {
			if ($i > 0) {
				echo "\n";
			}
			echo $sMetricName.'{node="'.$sClusterId.'"'.$strExtraAttr.'} '.$sMetricValue;
			++$i;
		}
	}
}
