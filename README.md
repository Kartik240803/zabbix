# ZabbixDB Python Library

The `ZabbixDB` Python library is designed to interact with Zabbix monitoring system databases (MySQL or PostgreSQL). It provides a programmatic interface to query host statuses, retrieve metric data, fetch alerts, and analyze common issues. The library supports both historical and trend data queries, statistical computations, and flexible filtering by hosts, host groups, or time ranges. With robust connection management, error handling, and logging, it is ideal for building monitoring dashboards, generating reports, or automating Zabbix data analysis.

## Table of Contents

1. [Features](#features)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
   - [Initialization and Connection](#initialization-and-connection)
   - [Context Manager](#context-manager)
   - [Querying Host Status](#querying-host-status)
   - [Fetching Metric Data](#fetching-metric-data)
   - [Retrieving Alerts](#retrieving-alerts)
   - [Analyzing Common Issues](#analyzing-common-issues)
   - [Listing Hosts by Group](#listing-hosts-by-group)
   - [Retrieving Hosts by Metric](#retrieving-hosts-by-metric)
   - [Statistical Computations](#statistical-computations)
   - [Time and Duration Utilities](#time-and-duration-utilities)
6. [Function Reference](#function-reference)
7. [Examples](#examples)
8. [Error Handling](#error-handling)
9. [Logging](#logging)
10. [Contributing](#contributing)
11. [License](#license)

---

## Features

- **Database Support**: Compatible with MySQL and PostgreSQL Zabbix databases.
- **Host and Metric Queries**: Retrieve host status, metric details, and historical or trend data for specific hosts or metrics.
- **Alert Management**: Fetch and filter alerts by time range, hostname, host group, or limit, and summarize common issues.
- **Statistical Analysis**: Compute statistics such as `min`, `max`, `mean`, `median`, `stdev`, `sum`, `count`, `range`, `mad`, `last`, and `avg` on metric data.
- **Time Utilities**: Convert duration strings (e.g., `1d2h30m`) to days and calculate time differences between Unix timestamps.
- **Connection Management**: Automatic reconnection with configurable retries and timeout handling.
- **Query Building**: Safe SQL query construction via the `QueryBuilder` class to prevent SQL injection.
- **Logging**: Detailed logging with rotating file handler for debugging and monitoring.
- **Error Handling**: Custom `ZabbixDBError` for database errors and structured error responses for invalid inputs or disabled hosts/items.

---

## Requirements

- **Python**: Version 3.7 or higher
- **Dependencies**: Listed in the provided `requirements.txt` file:
  - `mysql-connector-python` (for MySQL databases)
  - `psycopg2` (for PostgreSQL databases)
  - `pandas` (for data manipulation in alert and metric queries)
- **Zabbix Database**: Access to a Zabbix database (MySQL or PostgreSQL) with appropriate credentials.
- **Zabbix Version**: Compatible with Zabbix 5.x and 6.x database schemas.

Install dependencies using pip:

```bash
pip install -r requirements.txt
```

---

## Installation

1. **Clone or Download**: Obtain the `zabbix_db.py` file and place it in your project directory.
2. **Install Dependencies**: Run the pip command above to install required libraries.
3. **Database Access**: Ensure you have valid credentials (host, port, database, user, password) for your Zabbix database.
4. **Configuration File**: Ensure the `sample-config.json` (or renamed `config.json`) is set up correctly (see [Configuration](#configuration)).
5. **Optional**: Set up a Python virtual environment to manage dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## Configuration

The library requires a configuration file (`config.json`) in the same directory as the script. A sample is provided as `sample-config.json`. Rename it to `config.json` and update the values:

```json
{
  "database_config": {
    "db_type": "mysql",  // or "postgresql"
    "host": "localhost",
    "port": 3306,  // 5432 for PostgreSQL
    "database": "zabbix",
    "user": "zabbix_user",
    "password": "zabbix_password",
    "connection_timeout": 10
  }
}
```

- **db_type**: Specify `mysql` or `postgresql`.
- **host**: Database server hostname or IP address.
- **port**: Database port (default: 3306 for MySQL, 5432 for PostgreSQL).
- **database**: Name of the Zabbix database.
- **user**: Database user with read access to Zabbix tables (`hosts`, `items`, `history*`, `trends*`, `triggers`, `events`, etc.).
- **password**: Password for the database user.
- **connection_timeout**: Timeout for connection attempts (in seconds).

Ensure the database user has appropriate permissions to read the Zabbix schema.

---

## Usage

### Initialization and Connection

Create an instance of `ZabbixDB` and establish a connection using the configuration from `config.json`:

```python
from zabbix_db import ZabbixDB
import json

with open('config.json', 'r') as f:
    config = json.load(f)
    db_config = config['database_config']

db = ZabbixDB(**db_config)
```

### Context Manager

Use a context manager to automatically manage connection opening and closing:

```python
with ZabbixDB(**db_config) as db:
    # Perform queries here
    pass
```

### Querying Host Status

Check if a host is enabled or disabled:

```python
status = db.get_host_status('server1')
print(status)  # Output: {'hostid': 123, 'hostname': 'server1', 'status': 0} or "Host 'server1' not found"
```

### Fetching Metric Data

Retrieve metric data for a specific host and time range, with optional statistical computation:

```python
result = db.get_metric_data(
    hostname='server1',
    metric_name='CPU utilization',
    time_from=1749032410,  # Unix timestamp
    time_to=1749118810,
    statistical_measure='avg'
)
print(result)
```

Output format:
```python
{
    'status': 'success',
    'hostname': 'server1',
    'metric_name': 'CPU utilization',
    'unit': '%',
    'data': 45.67,  # Average value
    'statistical_measure': 'avg'
}
```

### Retrieving Alerts

Fetch alerts filtered by time range, hostname, host group, or limit:

```python
alerts = db.get_alerts(
    time_from=1749032410,
    time_to=1749118810,
    hostname='server1',
    limit=5
)
for alert in alerts:
    print(f"Alert: {alert['event_name']}, Host: {alert['host']}")
```

Output: A list of dictionaries with columns like `host`, `trigger_name`, `event_name`, `start_time`, `duration`, etc.

### Analyzing Common Issues

Summarize the most common alerts by event name:

```python
issues = db.get_common_issues(
    time_from=1749032410,
    time_to=1749118810,
    host_group='Linux servers',
    limit=3
)
print(issues)
```

Output:
```python
{
    'status': 'success',
    'data': [
        {'event_name': 'High CPU usage', 'total_count': 10, 'acknowledged_count': 8, 'unacknowledged_count': 2},
        {'event_name': 'Low disk space', 'total_count': 7, 'acknowledged_count': 5, 'unacknowledged_count': 2},
        {'event_name': 'Service down', 'total_count': 4, 'acknowledged_count': 3, 'unacknowledged_count': 1}
    ],
    'hostname': None,
    'time_from': 1749032410,
    'time_to': 1749118810,
    'limit': 3,
    'host_group': 'Linux servers'
}
```

### Listing Hosts by Group

Retrieve all hosts in a specified host group or all monitored hosts if `host_group` is "all":

```python
hosts = db.get_host_by_group('Linux servers')
for host in hosts:
    print(f"Host: {host['host_name']}")
```

### Retrieving Hosts by Metric

List hosts sorted by a metric's value, with optional statistical measure and time range:

```python
result = db.get_host_by_metric(
    metric_name='CPU utilization',
    statistical_measure='max',
    time_from=1749032410,
    time_to=1749118810,
    limit=5
)
print(result)
```

Output:
```python
{
    'status': 'success',
    'data': [
        {'hostname': 'server1', 'unit': '%', 'clock': 1749118800, 'value': 95.5},
        {'hostname': 'server2', 'unit': '%', 'clock': 1749118700, 'value': 90.2},
        ...
    ],
    'metric_name': 'CPU utilization'
}
```

### Statistical Computations

Compute statistics on metric data:

```python
data = [{'clock': 1749032410, 'value': 10.0}, {'clock': 1749032411, 'value': 20.0}]
mean = db.compute_statistic(data, 'mean')  # Output: 15.0
max_values = db.compute_statistic(data, 'max')  # Output: [{'clock': 1749032411, 'value': 20.0}]
```

### Time and Duration Utilities

Calculate time differences or convert duration strings:

```python
days = db.time_difference(1749032410, 1749118810)  # Output: 1
days = db.convert_day('1d2h30m')  # Output: 1.1
```

---

## Function Reference

Below is a detailed reference for all public methods in the `ZabbixDB` class:

| Function | Arguments | Output | Description |
|----------|-----------|--------|-------------|
| `__init__` | `db_type` (str), `host` (str), `port` (int), `database` (str), `user` (str), `password` (str), `connection_timeout` (int, default=10), `max_retries` (int, default=3) | None | Initializes database connection parameters and establishes a connection. Validates `db_type` as 'mysql' or 'postgresql'. |
| `_connect` | None | None | Establishes a database connection with retry logic. Internal method. |
| `_ensure_connection` | None | None | Ensures the connection is active, reconnecting if necessary. Internal method. |
| `close` | None | None | Closes the active database connection. |
| `compute_statistic` | `data` (List[Dict[str, Any]]), `operation` (str: min, max, mean, median, stdev, sum, count, range, mad, last, avg) | List[Dict[str, Any]], float, or int | Computes statistical measures on metric data. Returns lists for min/max/last, numeric values for others. |
| `time_difference` | `time_from` (int), `time_to` (int) | int | Calculates the difference in days between two Unix timestamps. |
| `convert_day` | `duration` (str, e.g., '1d2h30m') | float | Converts a duration string to days (e.g., '1d2h30m' → 1.1 days). |
| `get_monitoring_status` | `hostname` (str) | int | Returns 0 (enabled) or 1 (disabled) for a host's monitoring status. |
| `get_host_by_group` | `host_group` (str) | List[Dict[str, Any]] | Retrieves hosts in a specified host group or all monitored hosts if `host_group='all'`. |
| `get_item_detail` | `item_name` (str), `hostname` (str, optional) | Dict[str, Any], List[Dict[str, Any]], or None | Fetches details for a metric (item) for a specific host or all hosts. |
| `get_trend_data` | `itemid` (str), `time_from` (int), `time_to` (int), `trend_table_name` (str), `statistical_measure` (str, optional) | List[Dict[str, Any]] or float/int | Retrieves trend data for a metric within a time range, with optional statistics. |
| `get_history_data` | `itemid` (str), `time_from` (int), `time_to` (int), `history_table_name` (str), `statistical_measure` (str, optional) | List[Dict[str, Any]] or float/int | Retrieves historical data for a metric within a time range, with optional statistics. |
| `get_function_name` | `time_from` (int), `time_to` (int), `history_days` (float), `trends_days` (float) | str | Determines whether to use `get_history_data` or `get_trend_data` based on time range and retention periods. |
| `get_metric_data` | `hostname` (str), `metric_name` (str), `time_from` (int), `time_to` (int), `statistical_measure` (str, optional) | Dict[str, Any] | Fetches metric data with automatic selection of history or trend data and optional statistics. |
| `get_all_alerts` | None | List[Dict[str, Any]] | Retrieves all alert events with details like host, trigger, and duration. |
| `get_alerts` | `time_from` (int, optional), `time_to` (int, optional), `hostname` (str, optional), `limit` (int, optional), `host_group` (str, optional) | List[Dict[str, Any]] | Filters alerts by time, host, host group, or limit. |
| `get_common_issues` | `time_from` (int, optional), `time_to` (int, optional), `hostname` (str, optional), `limit` (int, optional), `host_group` (str, optional) | Dict[str, Any] | Summarizes common alert events by frequency and acknowledgment status. |
| `get_host_by_metric` | `metric_name` (str), `statistical_measure` (str, default='last'), `time_from` (int, optional), `time_to` (int, optional), `limit` (int, optional) | Dict[str, Any] | Retrieves hosts sorted by metric values, with optional statistics. |
| `get_host_status` | `hostname` (str) | Dict[str, Any] or str | Fetches host status (enabled/disabled) with details or an error message. |

---

## Examples

### Example 1: Fetch Metric Data with Statistics

```python
from zabbix_db import ZabbixDB
import json

with open('config.json', 'r') as f:
    config = json.load(f)
    db_config = config['database_config']

with ZabbixDB(**db_config) as db:
    result = db.get_metric_data(
        hostname='server1",
        metric_name='CPU utilization',
        time_from=1749032400, #Unix timestamp
        time_to=1749118810,
        statistical_measure='avg'
    )
    print(result)
```

Output:
```json
{
    "status": "success",
    "hostname": "CPU utilization",
    "metric_name": "server1",
    "unit": "%",
    "data": 45.67,
    "statistical_measure": "avg"
}
```

### Example 2: Summarize Common Issues

```python
with ZabbixDB(**db_config) as db:
    issues = db.get_common_issues(
        time_from=1749032410,
        time_to=1749118810,
        host_group='Linux servers',
        limit=5
    )
    print(issues)
```

Output:
```json
{
    "status": "success",
    "data": [
        {"event_name": "High CPU usage", "total_count": 10, "acknowledged_count": 8, "unacknowledged_count": 2},
        {"event_name": "Low disk space", "total_count": 7, "acknowledged_count": 5, "unacknowledged_count": 2},
        ...
    ],
    "time_from": 1749032410,
    "time_to": 1749118810,
    "limit": 5,
    "host_group": "Linux servers"
}
```

### Example 3: Get Hosts by Metric

```python
with ZabbixDB(**db_config) as db:
    result = db.get_host_by_metric(
        metric_name='CPU utilization',
        statistical_measure='max',
        time_from=1749032410,
        time_to=1749118810,
        limit=3
    )
    print(result)
```

Output:
```json
{
    "status": "success",
    "data": [
        {"hostname": "server1", "unit": "%", "clock": 1749118800, "value": 95.5},
        {"hostname": "server2", "unit": "%", "clock": 1749118700, "value": 90.2},
        {"hostname": "server3", "unit": "%", "clock": 1749118600, "value": 85.1}
    ],
    "metric_name": "CPU utilization"
}
```

### Example 4: List Hosts in a Group and Check Status

```python
with ZabbixDB(**db_config) as db:
    hosts = db.get_host_by_group('Linux servers')
    for host in hosts:
        status = db.get_host_status(host['host_name'])
        print(f"Host: {host['host_name']}, Status: {status}")
```

### Example 5: Convert Duration and Compute Statistics

```python
with ZabbixDB(**db_config) as db:
    days = db.convert_day('1d2h30m')  # Output: 1.1
    result = db.get_metric_data('server1', 'CPU utilization', 1749032410, 1749118810)
    if result['status'] == 'success':
        mean = db.compute_statistic(result['data'], 'mean')
        print(f"Mean CPU utilization: {mean}")
```

---

## Error Handling

The library provides robust error handling for various scenarios:

- **Invalid Database Type**: Raises `ValueError` if `db_type` is not 'mysql' or 'postgresql'.
- **Connection Issues**: Raises `ZabbixDBError` after `max_retries` (default: 3) failed connection attempts.
- **Query Failures**: Raises `ZabbixDBError` with details for failed SQL queries.
- **Invalid Inputs**: Returns structured error responses for invalid metric names, disabled hosts/items, or unsupported statistical measures.
- **Empty Results**: Returns empty lists or appropriate error messages when no data is found.

Example error response:
```python
{
    "status": "error",
    "message": "Item 'CPU utilization' not found for host 'server1'",
    "hostname": "server1",
    "metric_name": "CPU utilization",
    "unit": "unknown",
    "data": [],
    "statistical_measure": "avg"
}
```

To handle errors in your code:

```python
result = db.get_metric_data('server1', 'Invalid metric', 1749032410, 1749118810)
if result['status'] == 'error':
    print(f"Error: {result['message']}")
else:
    print(result['data'])
```

---

## Logging

The library logs to `/var/logs/vector/vector_lib_db.log` with a rotating file handler (5MB per file, up to 5 backups). Log levels include:

- **DEBUG**: Detailed connection and query information.
- **INFO**: Successful operations (e.g., connection established, query completed).
- **WARNING**: Non-critical issues (e.g., connection retry attempts).
- **ERROR**: Critical failures (e.g., query or connection errors).

To customize logging, modify the `logger` configuration at the top of `zabbix_db.py`. For example, to change the log level or output to console:

```python
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)
```

---

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository or create a local copy of `zabbix_db.py`.
2. Add new features, fix bugs, or improve documentation.
3. Ensure code follows PEP 8 style guidelines.
4. Test changes against a Zabbix database (MySQL or PostgreSQL).
5. Submit a pull request or share your changes with the maintainer.

Please include unit tests for new functionality and update this README if necessary. For major changes, open an issue first to discuss the proposed changes.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details (if applicable, or specify your own license).

---

This README provides a comprehensive guide to using the `ZabbixDB` Python library, including setup, usage, and detailed function documentation. For further assistance, refer to the docstrings in `zabbix_db.py` or contact the maintainer.