#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import path, listdir
import getopt
import sys
import re
from datetime import datetime
import gzip
from statistics import median
from string import Template
from collections import namedtuple
import json
import logging


config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}


def get_date_from_filename(file):
    file_name = path.basename(file)
    reg = re.search("([0-9]{8})", file_name)
    return datetime.strptime(reg.group(1), '%Y%m%d')


def get_last_logfile(logs_path):
    latest_log = None
    latest_date = None
    for file in listdir(logs_path):
        if re.match(r'nginx-access-ui\.log-[0-9]{8}(\.gz)?$', file):
            log_date = get_date_from_filename(file)
            if latest_date is None or log_date > latest_date:
                latest_date = log_date
                latest_log = file
    LogFile = namedtuple('LogFile', ['log_path', 'log_date'])
    return LogFile(path.join(logs_path, latest_log), latest_date)


def parse_log_file(log_file):
    logging.info(f'Parsing log file {log_file}')
    open_func = gzip.open if log_file.endswith('.gz') else open
    total_count = 0
    parse_errors = 0
    with open_func(log_file, 'rb') as file:
        for line in file:
            log_line = line.decode('utf-8')
            matches = re.findall(
                r'"([A-Z]{3,})\s(\S+).*\s(\d+\.\d+)', log_line)
            if not matches:
                parse_errors += 1
                continue

            matches = matches.pop()
            url = matches[1]
            time = matches[2]
            total_count += 1
            yield url, float(time)

    if parse_errors / total_count * 100 > 50:
        msg = 'Unable to parse more than 50% of log'
        logging.error(msg)
        raise Exception(msg)


def process_logs(logs, size=''):
    logging.info('Processing logs...')

    total_count = 0
    total_time = 0
    urls_dict = {}
    for log_line in logs:
        url, time = log_line
        total_count += 1
        total_time += time
        if url not in urls_dict:
            urls_dict[url] = {
                'count': 0,
                'times': []
            }
        url_dict = urls_dict.get(url)
        url_dict['count'] = url_dict['count'] + 1
        url_dict['times'].append(float(time))

    result = []
    for url in urls_dict:
        log = urls_dict[url]
        time_sum = round(sum(log['times']), 3)
        log_data = {
            'url': url,
            'count': log['count'],
            'count_perc': round(log['count'] / total_count * 100, 3),
            'time_sum': time_sum,
            'time_perc': round(time_sum / total_time * 100, 3),
            'time_avg': round(time_sum / len(log['times']), 3),
            'time_max': max(log['times']),
            'time_med': round(median(log['times']), 3)
        }
        result.append(log_data)

    return sorted(result, key=lambda k: k['time_sum'], reverse=True)[:size]


def write_report(data, report_path):
    current_dir = path.dirname(path.abspath(__file__))
    template_path = path.join(current_dir, 'report.html')
    report = None
    logging.info(f'Writing report to {report_path}')
    with open(template_path) as f:
        template = f.read()
        report = Template(template).safe_substitute({'table_json': data})
    with open(report_path, 'w') as r:
        r.write(report)


def parse_config(conf_path):
    try:
        with open(conf_path, 'r') as f:
            return(json.load(f))
    except FileNotFoundError:
        msg = 'Config file not found.'
        logging.error(msg)
        raise FileNotFoundError(msg)


def get_config(default_config):
    DEFAULT_CONFIG_PATH = './log_analyzer_config.json'
    external_config = None
    external_config_path = DEFAULT_CONFIG_PATH

    opts, args = getopt.getopt(sys.argv[1:], '', 'config=')
    for opt, arg in opts:
        if '--config' in opt:
            external_config_path = arg
    external_config = parse_config(external_config_path)

    if external_config:
        config.update(external_config)
    return default_config


def main(config_dict):
    logging.basicConfig(
        filename=config_dict.get('LOG_FILE'),
        level=logging.INFO,
        format='[%(asctime)s] %(levelname).1s %(message)s'
    )

    last_log_file = get_last_logfile(config_dict.get('LOG_DIR'))
    if last_log_file is None:
        msg = 'Logs not found'
        logging.info(msg)
        sys.exit(msg)

    log_path, log_date = last_log_file

    new_report_name = 'report-' + log_date.strftime('%Y.%m.%d' + '.html')
    new_report_path = path.join(config_dict.get('REPORT_DIR'), new_report_name)
    if path.isfile(new_report_path):
        msg = 'Report for last date already exists'
        logging.info(msg)
        sys.exit(msg)

    parse_log_gen = parse_log_file(log_path)
    data = process_logs(parse_log_gen, config_dict.get('REPORT_SIZE'))
    write_report(data, new_report_path)


if __name__ == "__main__":
    try:
        main(get_config(config))
    except KeyboardInterrupt as e:
        logging.error(e)
        raise e
    except Exception as e:
        logging.error(e)
        raise e
