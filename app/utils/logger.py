import logging
from rich.logging import RichHandler
from rich.console import Console

console = Console()


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = RichHandler(
            console=console,
            rich_tracebacks=True,
            markup=True,
            show_path=False,
        )
        handler.setFormatter(logging.Formatter("%(message)s", datefmt="[%X]"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
