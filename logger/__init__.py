from logging import getLogger, basicConfig, INFO

basicConfig(
    level=INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %I:%M:%S"
)

app_logger = getLogger(__name__)