from dotenv import load_dotenv
import logging
load_dotenv()
from os import getenv

import psycopg2
from psycopg2 import Error

# Читаем переменные окружения в локальные переменные
DB_USER = getenv("DB_USER")
DB_PASSWORD = getenv("DB_PASSWORD")
DB_HOST = getenv("DB_HOST")
DB_PORT = getenv("DB_PORT")
DB_DATABASE = getenv("DB_DATABASE")


class database:
    def __init__(self):
        try:
            self.connection = psycopg2.connect(
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT, 
                database=DB_DATABASE
            )
            self.connection.autocommit = True
            logging.info("Соединение с БД установлено")
        except (Exception, Error) as err:
            logging.error("Ошибка при подкючении к PostgreSQL: %s", err)


    def get_emails_list(self):
        results = []
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT * FROM emails;")
                results = cursor.fetchall()

            if results == [] or results[0] == []:
                results = None

            return results
        except (Exception, Error) as err:
            logging.error("Ошибка при выполнение SELECT запроса: %s", err)

        return None


    def get_phone_numbers_list(self):
        results = []
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT * FROM phone_numbers;")
                results = cursor.fetchall()

            if results == [] or results[0] == []:
                results = None

            return results
        except (Exception, Error) as err:
            logging.error("Ошибка при выполнение SELECT запроса: %s", err)

        return None


    def insert_email(self, email):
        result = None
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("INSERT INTO emails (email) VALUES (%s) RETURNING id;", (email,))
                result = cursor.fetchone()[0]
        except (Exception, Error) as err:
            logging.error("Ошибка при выполнение INSERT запроса: %s", err)

        return result


    def insert_phone_numbers(self, phone_number):
        result = None
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("INSERT INTO phone_numbers (phone_number) VALUES (%s) RETURNING id;", (phone_number,))
                result = cursor.fetchone()[0]
        except (Exception, Error) as err:
            logging.error("Ошибка при выполнение INSERT запроса: %s", err)

        return result


    def __del__(self):
        if self.connection:
            self.connection.close()
            logging.info("Соединение с БД закрыто")

