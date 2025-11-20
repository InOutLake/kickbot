import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
    force=True,
)

mail_logger = logging.getLogger("aioimaplib.aioimaplib")
mail_logger.setLevel(logging.INFO)
