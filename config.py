import pymysql

class Config:
    SECRET_KEY = 'skportal_secret_key'

    DB_HOST = 'localhost'
    DB_USER = 'root'
    DB_PASSWORD = ''
    DB_NAME = 'sk_portal'
    DB_CURSORCLASS = pymysql.cursors.DictCursor