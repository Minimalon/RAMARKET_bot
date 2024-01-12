import os

from loguru import logger

import config

MAIN_FORMAT = "{time} | {level} | {message} | {extra}"


# Фильтер для логов
def make_filters(name):
    def filter(record):
        return record["extra"].get("filter") == name

    return filter


# region Создание директорий для логов
main_log_dir = os.path.join(config.dir_path, 'logs')
if not os.path.exists(main_log_dir):
    os.makedirs(main_log_dir)

curl_dir = os.path.join(main_log_dir, 'curl')
if not os.path.exists(curl_dir):
    os.makedirs(curl_dir)
# endregion

# region Создаёт пути для лога файлов
bot_path = os.path.join(main_log_dir, 'bot.log')
api_path = os.path.join(curl_dir, 'api.log')


# endregion

# region Создание лог файлов
async def create_loggers():
    logger.add(bot_path, format=MAIN_FORMAT, filter=make_filters('bot'))
    logger.add(api_path, format=MAIN_FORMAT, filter=make_filters('api'))


# endregion

# region Переменные для логирования
api_log = logger.bind(filter='api')
bot_log = logger.bind(filter='bot')
# endregion
