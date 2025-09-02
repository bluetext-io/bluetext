import contextlib
from datetime import datetime, UTC
import logging
import os
import re

def colorize(text, color_code):
    """Wraps text with the ANSI escape code for the given color."""
    return f"\033[{color_code}m{text}\033[39m"

def bold(text):
    """Bolds the given text."""
    return f"\033[1m{text}\033[22m"

def faint(text):
    """Faints the given text."""
    return f"\033[2m{text}\033[22m"

def italic(text):
    """Italicizes the given text."""
    return f"\033[3m{text}\033[23m"

def black(text): return colorize(text, 30)
def red(text): return colorize(text, 31)
def green(text): return colorize(text, 32)
def yellow(text): return colorize(text, 33)
def blue(text): return colorize(text, 34)
def magenta(text): return colorize(text, 35)
def cyan(text): return colorize(text, 36)
def white(text): return colorize(text, 37)

CRITICAL = logging.CRITICAL
DEBUG = logging.DEBUG
ERROR = logging.ERROR
INFO = logging.INFO
TRACE = 5
WARNING = logging.WARNING

LEVEL_LABELS = {
    'CRITICAL': red(bold('CRITICAL')),
    'DEBUG': magenta('DEBUG'),
    'ERROR': red('ERROR'),
    'INFO': white('INFO'),
    'TRACE': green(faint(bold('TRACE'))),
    'WARNING': yellow('WARNING'),
}

def strip_ansi(s: str) -> str:
    """Removes ANSI escape sequences from the given string."""
    r = re.compile(r'\x1B\[.*?[a-zA-Z]')
    return r.sub('', s)

def disp_len(s: str) -> int:
    """Returns the display length of the given string."""
    return len(strip_ansi(s))

def indent_rest(input_string: str, indent: int) -> str:
    """Indents all but the first line of the given string."""
    lines = input_string.split("\n")
    return "\n".join([lines[0]] + [f"{' ' * indent}{line}" for line in lines[1:]])

class Formatter(logging.Formatter):
    """Pretty-printing log formatter."""
    def format(self, record):
        ts = (datetime
              .fromtimestamp(record.created, UTC)
              .strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z')
        level = LEVEL_LABELS.get(record.levelname, record.levelname)
        n = record.name
        color = sum([ord(x) for x in n]) % 6 + 32
        msg = record.getMessage()
        base = f"{italic(ts)} – {colorize(n, color)} – {level} – "
        ex = '\n' + self.formatException(record.exc_info) if record.exc_info else ''
        w = disp_len(base)
        return f"{base}{indent_rest(msg, w)}{indent_rest(ex, w)}"

    def formatException(self, exc_info):
        return super().formatException(exc_info)

def get_logger(name):
    """Gets a logger with the custom trace method."""
    logger = logging.getLogger(name)
    if not hasattr(logger, 'trace'):
        logger.trace = lambda msg, *args, **kwargs: logger.log(TRACE, msg, *args, **kwargs)
    return logger

def set_level(level):
    """Sets the global log level."""
    if level == 'TRACE':
        level = TRACE
    if (isinstance(level, int) and level > 0) or level in logging._nameToLevel:
        logging.getLogger().setLevel(level)
    else:
        logging.getLogger(__name__).warning('Invalid log level %s; ignoring.',
                                            red(level))

def init(level: str | int = None):
    """Initializes the logging system with TRACE support."""
    logging.addLevelName(TRACE, 'TRACE')

    def trace(self, message, *args, **kwargs):
        if self.isEnabledFor(TRACE):
            self._log(TRACE, message, args, **kwargs)
    logging.Logger.trace = trace

    logging.captureWarnings(True)
    level = level or os.environ.get('LOG_LEVEL', 'INFO').upper()
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(Formatter('%(message)s'))
    logger.handlers = [handler]
    set_level(level)

@contextlib.contextmanager
def level(level):
    """Temporarily modifies the log level.
    Usage:
    ```
    with log.level(log.DEBUG):
        ...
    ```
    """
    logger = logging.getLogger()
    old_level = logger.level
    logger.setLevel(level)
    try:
        yield  # Yield control back to the calling block
    finally:
        logger.setLevel(old_level)  # Restore the original log level
