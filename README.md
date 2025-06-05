

# ZabbixDB Python Library

The `ZabbixDB` class is a Python library designed to interact with a Zabbix monitoring system's database (MySQL or PostgreSQL). It provides a programmatic interface to query host statuses, metric data, alerts, and common issues, enabling users to retrieve and analyze monitoring data efficiently. The library supports both historical and trend data queries, statistical computations, and filtering by hosts, host groups, or time ranges.

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
   - [Statistical Computations](#statistical-computations)
   - [Time and Duration Utilities](#time-and-duration-utilities)
6. [Function Reference](#function-reference)
7. [Examples](#examples)
8. [Error Handling](#error-handling)
9. [Contributing](#contributing)
10. [License](#license)

---

## Features

- **Database Support**: Compatible with MySQL and PostgreSQL Zabbix databases.
- **Host and Metric Queries**: Retrieve host status, metric details, and historical/trend data for specific hosts or metrics.
- **Alert Management**: Fetch and filter alerts by time, host, or host group, and summarize common issues.
- **Statistical Analysis**: Compute statistics (e.g., min, max, mean, median) on metric data.
- **Time Utilities**: Convert duration strings (e.g., `1d2h30m`) to days and calculate time differences between Unix timestamps.
- **Context Manager**: Automatically manage database connections using Python's `with` statement.
- **Flexible Data Retrieval**: Query data by host, metric, or host group, with optional statistical measures and time ranges.
- **Error Handling**: Robust error responses for invalid inputs, database errors, or disabled hosts/items.

---

## Requirements

- **Python**: Version 3.6 or higher
- **Dependencies**:
  - `mysql-connector-python` (for MySQL databases)
  - `psycopg2` (for PostgreSQL databases)
  - `pandas` (for data manipulation in alert and metric queries)
- **Zabbix Database**: Access to a Zabbix database (MySQL or PostgreSQL) with appropriate credentials.
- **Zabbix Version**: Compatible with Zabbix 5.x and 6.x database schemas.

Install dependencies using pip:

```bash
pip install mysql-connector-python psycopg2 pandas
```

---

## Installation

1. **Clone or Download**: Obtain the `zabbix_db.py` file and place it in your project directory.
2. **Install Dependencies**: Run the pip command above to install required libraries.
3. **Database Access**: Ensure you have valid credentials (host, port, database, user, password) for your Zabbix database.
4. **Optional**: Set up a Python virtual environment to manage dependencies.

---

## Configuration

To use the `ZabbixDB` class, configure the database connection parameters:

```python
db_config = {
    'db_type': 'mysql',  # or 'postgresql'
    'host': 'localhost',  # Database host
    'port': 3306,         # Database port (3306 for MySQL, 5432 for PostgreSQL)
    'database': 'zabbix', # Database name
    'user': 'your_username',
    'password': 'your_password'
}
```

Replace the values with your Zabbix database details. Ensure the database user has read access to the necessary tables (`hosts`, `items`, `history*`, `trends*`, `triggers`, `events`, etc.).

---

## Usage

### Initialization and Connection

Create an instance of `ZabbixDB` and establish a connection:

```python
from zabbix_db import ZabbixDB

db = ZabbixDB(**db_config)
db.connect()
```

### Context Manager

Use a context manager to automatically handle connection opening and closing:

```python
with ZabbixDB(**db_config) as db:
    # Perform queries here
    pass
```

### Querying Host Status

Check if a host is enabled or disabled:

```python
status = db.get_host_status('Zabbix server')
print(status)  # Output: {'hostid': 123, 'hostname': 'Zabbix server', 'status': 0} or 'Host is disabled.'
```

### Fetching Metric Data

Retrieve metric data for a specific host and time range:

```python
result = db.get_metric_data(
    hostname='Zabbix server',
    metric_name='CPU utilization',
    time_from=1749032410,  # Unix timestamp
    time_to=1749118810,
    statistical_measure='max'
)
print(result)
```

Output format:
```python
{
    'status': 'success',
    'hostname': 'Zabbix server',
    'metric_name': 'CPU utilization',
    'unit': 'percent',
    'data': [{'clock': 1749032410, 'value': 75.5}, ...],
    'statistical_measure': 'max'
}
```

### Retrieving Alerts

Fetch alerts filtered by time, host, or host group:

```python
alerts = db.get_alerts(
    time_from=1749032410,
    time_to=1749118810,
    hostname='Zabbix server',
    limit=5
)
print(alerts)
```

Output: A pandas DataFrame with columns like `host`, `trigger_name`, `event_name`, `start_time`, etc.

### Analyzing Common Issues

Summarize the most common alerts:

```python
issues = db.get_common_issues(
    time_from=1749032410,
    limit=3,
    host_group='Linux servers'
)
print(issues)
```

Output:
```python
{
    'status': 'success',
    'message': 'Common issues retrieved successfully',
    'data': [
        {'event_name': 'High CPU usage', 'total_count': 10, 'acknowledged_count': 8, 'unacknowledged_count': 2},
        ...
    ]
}
```

### Statistical Computations

Compute statistics on metric data:

```python
data = [{'clock': 1749032410, 'value': 10}, {'clock': 1749032411, 'value': 20}]
mean = db.compute_statistic(data, 'mean')  # Output: 15.0
max_values = db.compute_statistic(data, 'max')  # Output: [{'clock': 1749032411, 'value': 20}]
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
| `__init__` | `db_type` (str), `host` (str), `port` (int), `database` (str), `user` (str), `password` (str) | None | Initializes database connection parameters. Validates `db_type` as 'mysql' or 'postgresql'. |
| `connect` | None | None | Establishes a connection to the Zabbix database using the configured parameters. |
| `close` | None | None | Closes the active database connection if open. |
| `compute_statistic` | `data` (list of dicts with `clock` and `value`), `operation` (str: min, max, mean, median, stdev, sum, count, range, mad, last) | List[dict], dict, or float/int | Computes statistical measures on metric data. Returns lists for min/max, single dict for last, or numeric values for others. |
| `time_difference` | `time_from` (int), `time_to` (int) | int | Calculates the difference in days between two Unix timestamps. |
| `convert_day` | `duration` (str, e.g., '1d2h30m') | float | Converts a duration string to days (e.g., '1d2h30m' → 1.1 days). |
| `get_monitoring_Status` | `hostname` (str) | int or RuntimeError | Returns 0 (enabled) or 1 (disabled) for a host's monitoring status. |
| `get_host_by_group` | `host_group` (str) | list of dicts or RuntimeError | Retrieves hosts in a specified host group or all hosts if `host_group='all'`. |
| `get_item_detail` | `item_name` (str), `hostname` (str, optional) | dict, list of dicts, or None | Fetches details for a metric (item) for a specific host or all hosts. |
| `get_trend_data` | `itemid` (str), `time_from` (int), `time_to` (int), `trend_table_name` (str), `statistical_measure` (str, optional) | list of dicts or error | Retrieves trend data for a metric within a time range. |
| `get_history_data` | `itemid` (str), `time_from` (int), `time_to` (int), `history_table_name` (str), `statistical_measure` (str, optional) | list of dicts or error | Retrieves historical data for a metric within a time range. |
| `get_function_name` | `time_from` (int), `time_to` (int), `history_days` (float), `trends_days` (float) | str | Determines whether to use history, trends, or both based on time range and retention periods. |
| `get_metric_data` | `hostname` (str), `metric_name` (str), `time_from` (int), `time_to` (int), `statistical_measure` (str, optional) | dict | Fetches metric data with optional statistical computation. |
| `get_all_alerts` | None | list of dicts or error | Retrieves all alert events with details like host, trigger, and duration. |
| `get_alerts` | `time_from` (int, optional), `time_to` (int, optional), `hostname` (str, optional), `limit` (int, optional), `host_group` (str, optional) | pandas DataFrame | Filters alerts by time, host, host group, or limit. |
| `get_common_issues` | `time_from` (int, optional), `time_to` (int, optional), `hostname` (str, optional), `limit` (int, optional), `host_group` (str, optional) | dict | Summarizes common alert events by frequency and acknowledgment status. |
| `get_host_by_metric` | `metric_name` (str), `statistical_measure` (str, default='last'), `time_from` (int, optional), `time_to` (int, optional), `limit` (int, optional) | pandas DataFrame | Retrieves metric values across all hosts, sorted by value. |
| `get_host_status` | `hostname` (str) | dict or str | Fetches host status (enabled/disabled) with details. |
| `__enter__` / `__exit__` | None | None | Context manager methods for automatic connection management. |

---

## Examples

### Example 1: Fetch Metric Data with Statistics

```python
from zabbix_db import ZabbixDB

db_config = {
    'db_type': 'mysql',
    'host': '140.238.230.93',
    'port': 3306,
    'database': 'zabbix',
    'user': 'kartik',
    'password': 'Kartik@24082003'
}

with ZabbixDB(**db_config) as db:
    result = db.get_metric_data(
        hostname='Zabbix server',
        metric_name='CPU utilization',
        time_from=1749032410,
        time_to=1749118810,
        statistical_measure='mean'
    )
    print(result)
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

### Example 3: Get Hosts by Metric

```python
with ZabbixDB(**db_config) as db:
    df = db.get_host_by_metric(
        metric_name='CPU utilization',
        statistical_measure='max',
        time_from=1749032410,
        time_to=1749118810,
        limit=10
    )
    print(df)
```

### Example 4: Convert Duration and Compute Statistics

```python
with ZabbixDB(**db_config) as db:
    days = db.convert_day('1d2h30m')  # Output: 1.1
    data = db.get_metric_data('Zabbix server', 'CPU utilization', 1749032410, 1749118810)['data']
    mean = db.compute_statistic(data, 'mean')
    print(f"Mean CPU utilization: {mean}")
```

---

## Error Handling

The library includes robust error handling for:

- **Invalid Database Type**: Raises `ValueError` if `db_type` is not 'mysql' or 'postgresql'.
- **Connection Issues**: Raises `MySQLError` or `PostgresError` for database connection failures.
- **Query Failures**: Returns `RuntimeError` with details for failed SQL queries.
- **Invalid Inputs**: Returns structured error responses for invalid metric names, disabled hosts/items, or unsupported statistical measures.
- **Empty Results**: Returns empty lists or appropriate error messages when no data is found.

Example error response:
```python
{
    'status': 'error',
    'message': 'Item "CPU utilization" not found for host "Zabbix server"',
    'hostname': 'Zabbix server',
    'metric_name': 'CPU utilization',
    'unit': 'unknown',
    'data': [],
    'statistical_measure': None
}
```

---

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository or create a local copy of `zabbix_db.py`.
2. Add new features, fix bugs, or improve documentation.
3. Ensure code follows PEP 8 style guidelines.
4. Test changes against a Zabbix database (MySQL or PostgreSQL).
5. Submit a pull request or share your changes with the maintainer.

Please include unit tests for new functionality and update the README if necessary.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details (if applicable, or specify your own license).

---

This README provides a comprehensive guide to using the `ZabbixDB` class, including setup, usage, and detailed function documentation. For further assistance, refer to the docstrings in `zabbix_db.py` or contact the maintainer.