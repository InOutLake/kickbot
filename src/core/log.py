import logging
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
    force=True,
)
file_handler = logging.FileHandler("logs.txt")
logging.root.addHandler(file_handler)

mail_logger = logging.getLogger("aioimaplib.aioimaplib")
mail_logger.setLevel(logging.DEBUG)
