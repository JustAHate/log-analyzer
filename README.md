# Nginx log analyzer

Скрипт парсер nginx логов с генерацией отчетов по html шаблону

## Getting Started

Запуск парсера: python3 log_analyzer.py
Запуск тестов: python3 test_log_analyzer.py

Опционально можно указать путь к конфиг файлу через параметр --config.
По умолчанию будет использован файл log_analyzer.config.json расположенный в той же директории, что и скрипт
Формат конфиг файла - json
Пример: python3 log_analyzer.py --config /some/path/to/config.json

Параметры конфига:
REPORT_SIZE - размер отчета
REPORT_DIR - путь для отчета
LOG_DIR - путь до директории с логами
LOG_FILE - путь к файлу логирования работы. Если отстутствует, логи будут выводиться в stdout