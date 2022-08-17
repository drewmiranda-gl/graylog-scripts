# What is this?

This is a helper file that allows collecting graylog heap usage from the
cluster stats api and outputs a prometheus formatted page so that these metrics
can be collected via prometheus.

# Why is this needed?

Currently graylog-server doesn't export jvm stats for prometheus export.

# Tested/Validated against
Graylog 4.3

# Requirements:
- Webserver
- PHP
- cURL module for PHP

# Example Setup:
- Install apache2
    - `sudo apt install apache2`
- Install PHP for apache
    - `sudo apt install php libapache2-mod-php`
- Install curl for php
    - `sudo apt install php-curl`
- Configure:
    - servername
    - server port
    - password:
        - to generate password base64 encode username:password

# Sample Output

```
jvm_memory_heap_used{node="[nodeId]"} 634080672
jvm_memory_heap_committed{node="[nodeId]"} 2040135680
jvm_memory_heap_max{node="[nodeId]"} 2040135680
org_graylog2_buffers_input_usage{node="[nodeId]"} 0
org_graylog2_buffers_input_size{node="[nodeId]"} 65536
org_graylog2_buffers_process_usage{node="[nodeId]"} 0
org_graylog2_buffers_process_size{node="[nodeId]"} 65536
org_graylog2_buffers_output_usage{node="[nodeId]"} 0
org_graylog2_buffers_output_size{node="[nodeId]"} 65536
org_graylog2_journal_append_1_sec_rate{node="[nodeId]"} 21
org_graylog2_journal_read_1_sec_rate{node="[nodeId]"} 21
org_graylog2_journal_segments{node="[nodeId]"} 1
org_graylog2_journal_entries_uncommitted{node="[nodeId]"} 0
org_graylog2_journal_utilization_ratio{node="[nodeId]"} 0.0045112855732441
org_graylog2_journal_oldest_segment{node="[nodeId]"} 2022
org_graylog2_throughput_input_1_sec_rate{node="[nodeId]"} 22
org_graylog2_throughput_output_1_sec_rate{node="[nodeId]"} 22
org_graylog_enterprise_license_status_violated{node="[nodeId]"} 0
org_graylog_enterprise_license_status_expired{node="[nodeId]"} 0
org_graylog_enterprise_license_status_expiration_upcoming{node="[nodeId]"} 0
org_graylog_enterprise_license_status_trial{node="[nodeId]"} 0
org_graylog_enterprise_license_traffic_violation_upcoming{node="[nodeId]"} 0
```