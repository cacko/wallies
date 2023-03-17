import corelog
import os


corelog.register(os.environ.get("WALLS_LOG_LEVEL", "INFO"))
