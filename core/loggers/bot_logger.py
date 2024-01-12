from core.loggers.make_loggers import bot_log


class BotLogger:
    def __init__(self, message):
        self.log = bot_log.bind(chat_id=message.chat.id, first_name=message.chat.first_name)

    def button(self, button_name: str):
        self.log.info(f'Нажали кнопку "{button_name}"')

    def info(self, message: str):
        self.log.info(f'{message}')

    def debug(self, message: str):
        self.log.debug(f'{message}')

    def error(self, message: str):
        self.log.error(f'{message}')

    def success(self, message: str):
        self.log.success(f'{message}')

    def exception(self, message):
        self.log.exception(f'{message}')
