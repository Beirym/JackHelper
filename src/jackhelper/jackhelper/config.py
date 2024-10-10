import os
from dotenv import load_dotenv


load_dotenv()


DJANGO_SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")

WHITE_LIST = list(map(int, os.environ.get("WHITE_LIST").split(',')))