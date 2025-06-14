from typing import Optional, Dict, Any
import mysql.connector
import psycopg2
from mysql.connector import Error as MySQLError
from psycopg2 import Error as PostgresError
from datetime import datetime, timezone
import re
import statistics
import math
import pandas as pd
import os
import json

class ZabbixDB:
    """A class to handle Zabbix database connections and queries for host status."""
    
    def __init__(
        self,
        db_type: str,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str
    ) -> None:
        """
        Initialize the ZabbixDB connection.

        Args:
            db_type (str): Database type ('mysql' or 'postgresql').
            host (str): Database host address.
            port (int): Database port.
            database (str): Database name.
            user (str): Database user.
            password (str): Database password.

        Raises:
            ValueError: If db_type is not 'mysql' or 'postgresql'.
        """
        if db_type not in ['mysql', 'postgresql']:
            raise ValueError("db_type must be 'mysql' or 'postgresql'")
        
        self.db_type = db_type
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection = None

    def connect(self) -> None:
        """Establish a connection to the Zabbix database."""
        try:
            if self.db_type == 'mysql':
                self.connection = mysql.connector.connect(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password,
                    charset='utf8mb4',
                    use_pure=True
                )
            else:  # postgresql
                self.connection = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password
                )
        except (MySQLError, PostgresError) as e:
            raise

    def close(self) -> None:
        """Close the database connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
        self.connection = None
    
    def compute_statistic(self, data: list, operation: str):
        """
        Computes a statistical measure on a list of dicts with 'clock' and 'value'.

        Args:
            data (list): List of dicts with keys 'clock' and 'value'.
            operation (str): One of [
                'min', 'max', 'mean', 'median', 'stdev', 'sum', 'count',
                'range', 'mad', 'last'
            ]

        Returns:
            - For 'min'/'max': List[dict] with matching clock and value
            - For 'last': Single dict with latest clock and value
            - For others: Single float/int result
        """
        if not data:
            return []
        # operation = operation.lower()
        values = [round(item['value'],2) for item in data]

        if operation == 'min':
            min_value = min(values)
            return [item for item in data if item['value'] == min_value]

        elif operation == 'max':
            max_value = max(values)
            return [item for item in data if item['value'] == max_value]

        elif operation == 'last':
            return [max(data, key=lambda x: x['clock'])]

        elif operation in ('mean', 'avg'):
            return statistics.fmean(values)

        elif operation == 'median':
            return statistics.median(values)

        elif operation == 'stdev':
            return statistics.stdev(values)

        elif operation == 'sum':
            return sum(values)

        elif operation == 'count':
            return len(values)

        elif operation == 'range':
            return max(values) - min(values)

        elif operation == 'mad':
            med = statistics.median(values)
            return statistics.median([abs(x - med) for x in values])

        else:
            raise ValueError(f"Unsupported operation: {operation}")
        
    def time_difference(self, time_from: int, time_to: int) -> int:
        """
        Calculates the difference in days between two Unix timestamps.
        """
        dt_from = datetime.fromtimestamp(time_from, tz=timezone.utc)
        dt_to = datetime.fromtimestamp(time_to, tz=timezone.utc)
        delta = dt_to - dt_from
        return delta.days
    
    def convert_day(self, duration: str):
        """
        Converts a duration string like '1d', '1h', '3d', '1m' to total days.
        Supports combinations like '1d2h30m'.
        """
        # Regex to find all parts (e.g., '1d', '2h', '30m')
        matches = re.findall(r'(\d+)([dhm])', duration.lower())

        total_days = 0.0
        for value, unit in matches:
            value = int(value)
            if unit == 'd':
                total_days += value
            elif unit == 'h':
                total_days += value / 24
            elif unit == 'm':
                total_days += value / (24 * 60)

        return round(total_days, 2)
    
    def get_monitoring_Status(self, hostname: str):

        if not self.connection or not self.connection.is_connected():
            return RuntimeError("Database connection not established")

        host_status_query = """
        SELECT h.hostid, h.host, h.status
        FROM hosts h
        WHERE h.host = %s AND h.flags IN (0, 4)
        """
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(host_status_query, (hostname,))
            result = cursor.fetchone()
            cursor.close()

            if result['status'] != 1:
                return 0 # 0 = enabled, 1 = disabled
            
            else:
                return 1 # 0 = enabled, 1 = disabled
        
        except (MySQLError, PostgresError) as e:
            return RuntimeError(f"Query failed: {str(e)}")

    def get_host_by_group(self,host_group):
        """
        Function to get the host group for a given host.
        This is a placeholder function; implement the actual logic as needed.
        """
        query = """
        SELECT 
        g.name AS group_name,
        h.host AS host_name
        FROM hstgrp g
        JOIN hosts_groups hg ON g.groupid = hg.groupid
        JOIN hosts h ON hg.hostid = h.hostid
        WHERE g.name = %s
        """
        
        query_all_groups = """
        SELECT
        h.host AS host_name
        FROM hosts h
        WHERE h.status = 0 AND h.flags IN (0, 4)
        """

        try:
            cursor = self.connection.cursor(dictionary=True)
            if host_group.lower() == 'all':
                cursor.execute(query_all_groups)
            else:
                cursor.execute(query, (host_group,))
            result = cursor.fetchall()
            cursor.close()

            if result is None:
                return []
            return result
    
        except (MySQLError, PostgresError) as e:
            return RuntimeError(f"Query failed: {str(e)}")
        
    def get_item_detail(self, item_name: str, hostname: str = None):
        """
        Fetch details of a specific item. Returns one item if hostname is provided,
        otherwise returns all matching items across hosts.

        Args:
            item_name (str): The name of the item to query.
            hostname (str, optional): The hostname to query.

        Returns:
            Union[Dict[str, Any], List[Dict[str, Any]], None]: Item detail(s) or None if not found.

        Raises:
            RuntimeError: If database connection is not established or query fails.
        """
        if not self.connection or not self.connection.is_connected():
            raise RuntimeError("No active database connection")

        query_with_host = """
        SELECT i.itemid, i.hostid, i.name, i.history, i.trends, i.value_type,
            i.status, i.units, h.host
        FROM items i
        JOIN hosts h ON i.hostid = h.hostid
        WHERE h.host = %s AND i.name = %s
        """

        query_without_host = """
        SELECT i.itemid, i.hostid, i.name, i.history, i.trends, i.value_type,
            i.status, i.units, h.host
        FROM items i
        JOIN hosts h ON i.hostid = h.hostid
        WHERE i.name = %s
        AND h.status = 0 AND h.flags IN (0, 4)
        """

        table_mapping = {
            0: {'history': 'history', 'trends': 'trends'},
            1: {'history': 'history_str', 'trends': None},
            2: {'history': 'history_log', 'trends': None},
            3: {'history': 'history_uint', 'trends': 'trends_uint'},
            4: {'history': 'history_text', 'trends': None}
        }

        try:
            cursor = self.connection.cursor(dictionary=True)
            if hostname:
                cursor.execute(query_with_host, (hostname, item_name))
            else:
                cursor.execute(query_without_host, (item_name,))
            
            results = cursor.fetchall()
            cursor.close()

            if not results:
                return None

            def map_item(item):
                value_type = item['value_type']
                if value_type not in table_mapping:
                    raise RuntimeError(f"Invalid value_type {value_type} for item {item['name']}")
                return {
                    'hostname': item['host'],
                    'itemid': item['itemid'],
                    'hostid': item['hostid'],
                    'name': item['name'],
                    'history': item['history'],
                    'trends': item['trends'],
                    'value_type': value_type,
                    'status': item['status'],
                    'units': item['units'],
                    'history_table_name': table_mapping[value_type]['history'],
                    'trends_table_name': table_mapping[value_type]['trends']
                }

            if hostname:
                return map_item(results[0])
            else:
                return [map_item(item) for item in results]

        except (MySQLError, PostgresError) as e:
            raise RuntimeError(f"Failed to fetch item details: {str(e)}")

    def get_trend_data(self,itemid: str,time_from: int, time_to: int,trend_table_name: str,statistical_measure: str = None):

            if not self.connection or not self.connection.is_connected():
                    return "No active database connection"

            # Whitelist valid history tables to prevent SQL injection
            valid_tables = {'trends', 'trends_uint'}
            if trend_table_name not in valid_tables:
                return f"Invalid history table name: {trend_table_name}"
            
            # Determine the value column based on the statistical measure
            if statistical_measure not in ['min','max','all']:
                value = 'value_avg'
                query = f"""
                SELECT clock, {value} as value
                FROM {trend_table_name}
                WHERE itemid = %s
                AND clock BETWEEN %s AND %s
                ORDER BY clock DESC
                """
            elif statistical_measure == 'all':
                value = 'num, value_avg, value_min, value_max'
                query = f"""
                SELECT clock, {value}
                FROM {trend_table_name}
                WHERE itemid = %s
                AND clock BETWEEN %s AND %s
                ORDER BY clock DESC
                """
            else:
                value = 'value_max' if statistical_measure == 'max' else 'value_min'
                query = f"""
                SELECT clock, {value} as value
                FROM {trend_table_name}
                WHERE itemid = %s
                AND clock BETWEEN %s AND %s
                ORDER BY clock DESC
                """
            
            try:
                cursor = self.connection.cursor(dictionary=True)
                cursor.execute(query, (itemid, time_from, time_to))
                result = cursor.fetchall()
                cursor.close()

                if result is None:
                    return []
                if statistical_measure:
                    valid_stats = {'min', 'max', 'mean', 'median', 'stdev', 'sum', 'count', 'range', 'mad', 'last', 'avg'}
                    if statistical_measure not in valid_stats:
                        return RuntimeError(f"Invalid statistical measure: {statistical_measure}")

                # Compute the requested statistic
                    return self.compute_statistic(result, statistical_measure)
                return result            
        
            except (MySQLError, PostgresError) as e:
                return RuntimeError(f"Query failed: {str(e)}")
    
    def get_history_data(self,itemid: str,time_from: int, time_to: int,history_table_name: str,statistical_measure: str = None):

        if not self.connection or not self.connection.is_connected():
                return "No active database connection"

        # Whitelist valid history tables to prevent SQL injection
        valid_tables = {'history', 'history_str', 'history_log', 'history_uint', 'history_text'}
        if history_table_name not in valid_tables:
            return f"Invalid history table name: {history_table_name}"

        query = f"""
        SELECT clock, value
        FROM {history_table_name}
        WHERE itemid = %s
        AND clock BETWEEN %s AND %s
        ORDER BY clock DESC
        """

        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, (itemid, time_from, time_to))
            result = cursor.fetchall()
            cursor.close()

            if result is None:
                return []
            if statistical_measure:
                valid_stats = {'min', 'max', 'mean', 'median', 'stdev', 'sum', 'count', 'range', 'mad', 'last', 'avg'}
                if statistical_measure not in valid_stats:
                    return RuntimeError(f"Invalid statistical measure: {statistical_measure}")

                # Compute the requested statistic
                return self.compute_statistic(result, statistical_measure)
            return result
    
        except (MySQLError, PostgresError) as e:
            return RuntimeError(f"Query failed: {str(e)}")

    def get_function_name(self,time_from: int, time_to: int,history_days, trends_days):
        current_time = float(datetime.now().timestamp())
        seconds_in_day = float(86400)
        history_threshold = int(current_time - (history_days * seconds_in_day))
        trends_threshold = int(current_time - (trends_days * seconds_in_day))

        if time_to < trends_threshold:
            return "No data - too old"
        elif time_from >= history_threshold:
            return "get_history"
        elif time_to <= history_threshold and time_from >= trends_threshold:
            return "get_trends"
        elif time_from < history_threshold and time_to >= history_threshold:
            return "get_trends"
        else:
            return "Invalid range"

    def get_metric_data(self, hostname: str, metric_name: str, time_from: int, time_to: int, statistical_measure: str = None):
        """
        Fetch historical data for a specific metric (item) of a host within a time range.
        """
        if time_from > time_to:
            return self._error_response(
                "Invalid time range: 'time_from' must be less than 'time_to'",
                hostname, metric_name, "unknown", statistical_measure
            )

        monitoring_status = self.get_monitoring_Status(hostname)
        item_details = self.get_item_detail(metric_name,hostname)

        if item_details is None:
            message = f"Item '{metric_name}' not found for host '{hostname}'"
            return self._error_response(message, hostname, metric_name, "unknown", statistical_measure)

        if monitoring_status == 1:
            return self._error_response(f"Host '{hostname}' is disabled", hostname, metric_name, "unknown")

        if item_details['status'] != 0:
            return self._error_response(f"Item '{metric_name}' is disabled", hostname, metric_name, item_details['units'])

        history_table = item_details.get('history_table_name')
        trends_table = item_details.get('trends_table_name')
        
        if not history_table:
            return self._error_response(f"No valid history table for item '{metric_name}' with value_type {item_details['value_type']}", hostname, metric_name, item_details['units'], statistical_measure)

        if history_table not in ['history_str', 'history_log', 'history_text']:
            function_name = self.get_function_name(
                time_from, time_to,
                self.convert_day(item_details['history']),
                self.convert_day(item_details['trends'])
            )
        else:
            function_name = "get_history"
            statistical_measure = statistical_measure if statistical_measure == 'last' else None # No statistics for string/log/text history

        try:
            if statistical_measure:
                valid_stats = {'min', 'max', 'mean', 'median', 'stdev', 'sum', 'count', 'range', 'mad', 'last', 'avg'}
                if statistical_measure not in valid_stats:
                    return self._error_response(
                        f"Invalid statistical measure: {statistical_measure}",
                        hostname, metric_name, item_details['units'], statistical_measure
                    )

            itemid = item_details['itemid']

            def fetch_history():
                return self.get_history_data(itemid, time_from, time_to, history_table, statistical_measure)

            def fetch_trends():
                return self.get_trend_data(itemid, time_from, time_to, trends_table, statistical_measure)

            # Fetch function definitions
            def fetch_history_with_stats():
                data = fetch_history()
                return self.compute_statistic(data, statistical_measure) if data else []

            def fetch_trends_with_stats():
                data = fetch_trends()
                return self.compute_statistic(data, statistical_measure) if data else []

            # def fetch_both_with_stats():
            #     history_data = fetch_history()
            #     trend_data = fetch_trends()
            #     if not history_data and not trend_data:
            #         return []
            #     combined = (history_data or []) + (trend_data or [])
            #     return self.compute_statistic(combined, statistical_measure)

            # def fetch_both_raw():
            #     history_data = fetch_history()
            #     trend_data = fetch_trends()
            #     return (history_data or []) + (trend_data or [])

            fetch_func = {
                "get_history": fetch_history,
                "get_trends": fetch_trends,
                # "get_trends_and_history": fetch_both_with_stats if statistical_measure else fetch_both_raw
            }

            data = fetch_func[function_name]()

            return self._success_response(
                data=data,
                hostname=hostname,
                metric_name=metric_name,
                unit=item_details['units'],
                statistical_measure=statistical_measure
            )
        

        except (MySQLError, PostgresError) as e:
            return self._error_response(
                f"Query failed: {str(e)}", hostname, metric_name, item_details['units'], statistical_measure
            )

    def get_all_alerts(self):
        if not self.connection or not self.connection.is_connected():
            return "No active database connection"

        query = '''
            SELECT DISTINCT
                h.name AS host,
                t.description AS trigger_name,
                e.name AS event_name,
                e.eventid,
                e.acknowledged,
                e.clock AS start_time,
                COALESCE(er.clock, UNIX_TIMESTAMP()) AS end_time,
                COALESCE(er.clock, UNIX_TIMESTAMP()) - e.clock AS duration,
                er.eventid AS recovery_eventid
            FROM hosts h
            JOIN items i ON i.hostid = h.hostid AND i.status = 0
            JOIN functions f ON f.itemid = i.itemid
            JOIN triggers t ON t.triggerid = f.triggerid AND t.status = 0
            JOIN events e ON e.objectid = t.triggerid AND e.object = 0 AND e.value = 1
            LEFT JOIN event_recovery erc ON erc.eventid = e.eventid
            LEFT JOIN events er ON er.eventid = erc.r_eventid
            WHERE 
                h.status = 0
                AND h.flags IN (0, 4)
        '''

        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(query)
                result = cursor.fetchall()

            return result if result else "No alerts history found"

        except (MySQLError, PostgresError) as e:
            return f"Query failed: {str(e)}"

    def get_alerts(self,time_from: int = None, time_to: int = None, hostname: str = None, limit: int = None, host_group: str = None):
        alerts = pd.DataFrame(self.get_all_alerts())
        alerts = alerts.sort_values(by='start_time', ascending=False)
        
        if time_from is not None:
            alerts = alerts[alerts['start_time'] >= time_from]
        if time_to is not None:
            alerts = alerts[alerts['start_time'] <= time_to]
        if hostname is not None:
            alerts = alerts[alerts['host'] == hostname]
        if host_group is not None:
            host_list = self.get_host_by_group(host_group)
            host_in_group = [h['host_name'] for h in host_list]
            alerts = alerts[alerts['host'].isin(host_in_group)]

        if limit is not None:
            alerts = alerts.head(limit)

        return alerts

    def get_common_issues(self, time_from: int = None, time_to: int = None, hostname: str = None, limit: int = None, host_group: str = None):
        alerts=self.get_alerts(time_from, time_to, hostname,host_group)

        common_issues = alerts.groupby('event_name').agg(
            total_count=('eventid', 'count'),
            acknowledged_count=('acknowledged', lambda x: (x == 1).sum()),
            unacknowledged_count=('acknowledged', lambda x: (x == 0).sum())
        ).reset_index().sort_values(by='total_count', ascending=False)

        common_issues = common_issues.head(limit)

        if common_issues.empty:
            return {
                "status": "error",
                "message": "No common issues found",
                "data": []
            }
        return self._success_response(
            data=common_issues.to_dict(orient='records'),
            hostname=hostname,
            time_from=time_from,
            time_to=time_to,
            limit=limit,
            host_group=host_group
        )

    def get_host_by_metric(self, metric_name: str, statistical_measure: str = 'last', time_from: int = None, time_to: int = None, limit: int = None):
        item_details = self.get_item_detail(metric_name)
        
        if not item_details:
            return pd.DataFrame(columns=['hostname', 'unit', 'clock', 'value'])
        if not isinstance(item_details, list):
            item_details = [item_details]

        hostnames = list({item['hostname'] for item in item_details})
        
        rows = []
        for host in hostnames:
            metric_data = self.get_metric_data(
                hostname=host,
                metric_name=metric_name,
                time_from=time_from,
                time_to=time_to,
                statistical_measure=statistical_measure
            )
            
            if metric_data:
                data_points = metric_data.get("data")
                if isinstance(data_points, list) and len(data_points) > 0 and isinstance(data_points[0], dict):
                    # Expand each dict inside 'data' list into separate rows
                    for point in data_points:
                        rows.append({
                            "hostname": metric_data.get("hostname"),
                            "unit": metric_data.get("unit"),
                            "clock": point.get("clock"),
                            "value": point.get("value")
                        })
                else:
                    # Handle if data is a single value or empty list
                    rows.append({
                        "hostname": metric_data.get("hostname"),
                        "unit": metric_data.get("unit"),
                        "clock": None,
                        "value": data_points if data_points else None
                    })
    
        if limit is not None:
            rows = rows[:limit]

        df = pd.DataFrame(rows, columns=['hostname', 'unit', 'clock', 'value'])
        # Convert clock column to Int64 dtype (nullable integer) so NaNs are preserved
        df['clock'] = pd.to_numeric(df['clock'], errors='coerce').astype('Int64')
        df = df.sort_values(by='value', ascending=False, na_position='last')

        return self._success_response(
            data=df.to_dict(orient='records'),
            metric_name=metric_name
        )

    def _error_response(self, message, hostname, metric_name, unit, statistical_measure=None):
        return {
            "status": "error",
            "message": message,
            "hostname": hostname,
            "metric_name": metric_name,
            "unit": unit,
            "data": [],
            "statistical_measure": statistical_measure
        }

    def _success_response(self, data, hostname=None, metric_name=None, unit=None, statistical_measure=None,time_from=None, time_to=None, limit=None, host_group=None):
        perameter_data  = {
            "status": "success",
            "data": data,
            "hostname": hostname,
            "metric_name": metric_name,
            "unit": unit,
            "statistical_measure": statistical_measure,
            "time_from": None,
            "time_to": None,
            "limit": None,
            "host_group": None
        }
        
        return_data = {k: v for k, v in perameter_data.items() if v is not None}
        
        return return_data

    def get_host_status(self, hostname: str):
        """
        Fetch the status of a host by its hostname.

        Args:
            hostname (str): The hostname to query.

        Returns:
            Optional[Dict[str, Any]]: Dictionary containing host status details or None if not found.

        Raises:
            RuntimeError: If database connection is not established or query fails.
        """
        if not self.connection or not self.connection.is_connected():
            return RuntimeError("Database connection not established")

        host_status_query = """
        SELECT h.hostid, h.host, h.status
        FROM hosts h
        WHERE h.host = %s AND h.flags IN (0, 4)
        """
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(host_status_query, (hostname,))
            result = cursor.fetchone()
            cursor.close()

            if result['status'] != 1:
                return {
                    'hostid': result['hostid'],
                    'hostname': result['host'],
                    'status': result['status']  # 0 = enabled, 1 = disabled
                }
            
            else:
                message = f"Host '{hostname}' is disabled."
                return message
        
        except (MySQLError, PostgresError) as e:
            return RuntimeError(f"Query failed: {str(e)}")

    def __enter__(self):
        """Context manager entry to establish connection."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit to close connection."""
        self.close()


if __name__ == "__main__":

    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
        db_config = config['database_config']
        db_config.pop('connection_timeout', None)

    # Sample hostname to query
    hostname = 'Zabbix server'
    metric_name = 'CPU utilization'  # Example metric name
    # metric_name = 'Host name of Zabbix agent running'

    try:
        with ZabbixDB(**db_config) as zbx:
            # result = zbx.get_metric_data(
            #     hostname=hostname,
            #     metric_name=metric_name,
            #     time_from=1749032410,  # Example start time (Unix timestamp)
            #     time_to=1749118810,  # Example statistical measure
            #     statistical_measure='last'  # Example statistical measure
            # )
            # print(result)
            result = zbx.get_host_by_metric(metric_name=metric_name,time_from=1749032410, time_to=1749118810, statistical_measure='avg')
            # result = zbx.get_trend_data(itemid=42269,time_from=1746793913,time_to=1749639488,trend_table_name='trends',statistical_measure='all')
            # result = zbx.get_item_detail(item_name='CPU nice time', hostname=hostname)
            print(result)

            # print(zbx.time_difference(1747751299, 1747837706))
            # print(zbx.convert_day('1h'))

            # print(zbx.compute_statistic(result['data'], 'mean'))
            # print(zbx.compute_statistic(result['data'], 'median'))
            # print(zbx.compute_statistic(result['data'], 'min'))
            # print(zbx.compute_statistic(result['data'], 'max'))
            # print(zbx.compute_statistic(result['data'], 'stdev'))
            # print(zbx.compute_statistic(result['data'], 'sum'))
            # print(zbx.compute_statistic(result['data'], 'count'))

    except (RuntimeError, ValueError) as e:
        print(f"Error: {str(e)}")