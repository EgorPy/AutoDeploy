""" Logger for core """

from aiogram import Bot
import logging
import sys

# ANSI colors
RESET = "\033[0m"
RED = "\033[31m"
YELLOW = "\033[93m"
BLUE = "\033[34m"
GREEN = "\033[32m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"


class ColorFormatter(logging.Formatter):
    """ Colorful formatter for log output """

    COLORS = {
        logging.DEBUG: BLUE,
        # logging.INFO: BLUE,
        logging.WARNING: YELLOW,
        logging.ERROR: RED,
        logging.CRITICAL: RED,
    }

    def format(self, record):
        """ Formats logs """

        color = self.COLORS.get(record.levelno, RESET)
        message = super().format(record)
        return f"{color}{message}{RESET}"


async def note(self, message: str, bot: Bot = None, chat_id: int = None, *args, **kwargs):
    """ Custom NOTE log level """

    if self.isEnabledFor(NOTE_LEVEL_NUM):
        self._log(NOTE_LEVEL_NUM, message, args, **kwargs)
        if bot:
            await bot.send_message(chat_id, message)


def setup_logger():
    """ Logger setup """

    # custom log level NOTE
    logging.addLevelName(NOTE_LEVEL_NUM, "NOTE")
    logging.NOTE = NOTE_LEVEL_NUM
    logging.Logger.note = note

    logger = logging.getLogger("Core")
    logger.setLevel(logging.INFO)  # I put WARNING here to make less output in console, for hard debugging use DEBUG

    # IMPORTANT: prevent adding handlers twice
    if logger.hasHandlers():
        return logger

    handler = logging.StreamHandler(sys.stdout)
    formatter = ColorFormatter("[%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


# custom log level NOTE
NOTE_LEVEL_NUM = 35  # 5 more than WARNING, between WARNING and ERROR

logger = setup_logger()
