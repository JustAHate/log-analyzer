import unittest
from datetime import datetime
import tempfile
import os
from log_analyzer import *

class TestLogAnalyzer(unittest.TestCase):

    def test_get_last_logfile(self):
        temp_dir = tempfile.mkdtemp()
        temp_files = []
        for i in range(1, 4):
            path = os.path.join(temp_dir, f'nginx-access-ui.log-2020062{i}.gz')
            temp_files.append(path)
            with open(path, 'a'):
                os.utime(path, None)
        try:
            last_log_file, log_date = get_last_logfile(temp_dir)
            self.assertEqual(
                last_log_file,
                os.path.join(temp_dir, 'nginx-access-ui.log-20200623.gz')
            )

            self.assertEqual(
                log_date,
                datetime(2020, 6, 23, 0, 0)
            )
        finally:
            for file in temp_files:
                os.remove(file)
            os.rmdir(temp_dir)

    def test_parse_log_file(self):
        temp_dir = tempfile.mkdtemp()
        temp_log = os.path.join(temp_dir, f'nginx-access-ui.log-20200621')
        test_data = [
        '1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/25019354 HTTP/1.1" 200 927 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697422-2190034393-4708-9752759" "dc7161be3" 2.000',
        '1.99.174.176 3b81f63526fa8  - [29/Jun/2017:03:50:22 +0300] "GET /api/1/photogenic_banners/list/?server_name=WIN7RB4 HTTP/1.1" 200 12 "-" "Python-urllib/2.7" "-" "1498697422-32900793-4708-9752770" "-" 1.000',
        '1.169.137.128 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/16852664 HTTP/1.1" 200 19415 "-" "Slotovod" "-" "1498697422-2118016444-4708-9752769" "712e90144abee9" 3.000'
        ]
        with open(temp_log, 'w+') as f:
            for line in test_data:
                f.write(line)
                f.write("\n")
        try:
            urls = parse_log_file(temp_log)
            self.assertEqual(
                list(urls),
                [('/api/v2/banner/25019354', 2.0), ('/api/1/photogenic_banners/list/?server_name=WIN7RB4', 1.0), ('/api/v2/banner/16852664', 3.0)]
            )
        finally:
            os.remove(temp_log)
            os.rmdir(temp_dir)

    def test_process_logs(self):
        data = process_logs(
            [('/api/v2/banner/25019354', 2.0), ('/api/1/photogenic_banners/list/?server_name=WIN7RB4', 1.0), ('/api/v2/banner/16852664', 3.0)],
            3
        )
        self.assertEqual(
            data,
            [{'url': '/api/v2/banner/16852664', 'count': 1, 'count_perc': 33.333, 'time_sum': 3.0, 'time_perc': 50.0, 'time_avg': 3.0, 'time_max': 3.0, 'time_med': 3.0}, {'url': '/api/v2/banner/25019354', 'count': 1, 'count_perc': 33.333, 'time_sum': 2.0, 'time_perc': 33.333, 'time_avg': 2.0, 'time_max': 2.0, 'time_med': 2.0}, {'url': '/api/1/photogenic_banners/list/?server_name=WIN7RB4', 'count': 1, 'count_perc': 33.333, 'time_sum': 1.0, 'time_perc': 16.667, 'time_avg': 1.0, 'time_max': 1.0, 'time_med': 1.0}]
        )

    def test_write_report(self):
        temp_dir = tempfile.mkdtemp()
        report_path = os.path.join(temp_dir, 'log_analyzer_report.html')
        try:
            data = [{'url': '/api/v2/banner/16852664', 'count': 1, 'count_perc': 33.333, 'time_sum': 3.0, 'time_perc': 50.0, 'time_avg': 3.0, 'time_max': 3.0, 'time_med': 3.0}, {'url': '/api/v2/banner/25019354', 'count': 1, 'count_perc': 33.333, 'time_sum': 2.0, 'time_perc': 33.333, 'time_avg': 2.0, 'time_max': 2.0, 'time_med': 2.0}, {'url': '/api/1/photogenic_banners/list/?server_name=WIN7RB4', 'count': 1, 'count_perc': 33.333, 'time_sum': 1.0, 'time_perc': 16.667, 'time_avg': 1.0, 'time_max': 1.0, 'time_med': 1.0}]
            write_report(data, report_path)
            self.assertTrue(os.path.isfile(report_path))
        finally:
            os.remove(report_path)
            os.rmdir(temp_dir)

    def test_get_config(self):
        test_conf = {
            'REPORT_SIZE': 500,
            'REPORT_DIR': './reports',
            'LOG_DIR': './log',
            'LOG_FILE': './log_analyzer.log'
        }

        self.assertEqual(
            get_config(test_conf, './log_analyzer_config.json'),
            test_conf
        )


if __name__ == '__main__':
    unittest.main()
