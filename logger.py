import logging
from datetime import datetime
from enum import Enum, auto


class LoggerLevel(Enum):
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


class SimpleLogger:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        logging.basicConfig(
            filename=f"logs/{datetime.now().strftime("%d.%m.%Y_%H-%M-%S")}.log",
            encoding="utf-8",
            level=logging.DEBUG,
            filemode="w",
            format="%(asctime)s %(message)s",
            datefmt="%d.%m.%Y_%H-%M-%S",
        )

    def log(self, message: str, level: LoggerLevel = LoggerLevel.INFO):
        if level == LoggerLevel.DEBUG:
            self.logger.debug(message)
        elif level == LoggerLevel.INFO:
            self.logger.info(message)
        elif level == LoggerLevel.WARNING:
            self.logger.warning(message)
        elif level == LoggerLevel.ERROR:
            self.logger.error(message)
        elif level == LoggerLevel.CRITICAL:
            self.logger.critical(message)


def logger() -> SimpleLogger:
    return SimpleLogger()
