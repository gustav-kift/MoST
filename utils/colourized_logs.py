import logging

class ColorFormatter(logging.Formatter):
    # ANSI color codes
    GREY = "\x1b[2m"
    BLUE = "\x1b[34;1m"
    GREEN = "\x1b[32;1m"
    YELLOW = "\x1b[33;1m"
    RED = "\x1b[31;1m"
    BOLD_RED = "\x1b[31;1m\x1b[1m"
    RESET = "\x1b[0m"

    LEVEL_COLORS = {
        logging.DEBUG: GREY,
        logging.INFO: GREEN,
        logging.WARNING: YELLOW,
        logging.ERROR: RED,
        logging.CRITICAL: BOLD_RED,
    }

    def format(self, record):
        color = self.LEVEL_COLORS.get(record.levelno, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        record.msg = f"{color}{record.msg}{self.RESET}"
        return super().format(record)
