import logging
from dotenv import load_dotenv
load_dotenv()
import os
import re
import paramiko
import subprocess

from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
from db import database

# Максимальное число символов в одном сообщении Telegram
MAX_MESSAGE_SIZE = 4096

# Читаем переменные окружения
TOKEN = os.getenv("TOKEN")
RM_HOST = os.getenv("RM_HOST")
RM_PORT = os.getenv("RM_PORT")
RM_USER = os.getenv("RM_USER")
RM_PASSWORD = os.getenv("RM_PASSWORD")


# Включаем логирование
logging.basicConfig( 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)

logger = logging.getLogger(__name__)


# Делим сообщение на части (из-за ограничения на количество символов) и отпраляем
def send_long_text(update: Update, context, message: str):
    splitted_text = []
    
    # Делим текст на части
    for part in range(0, len(message), MAX_MESSAGE_SIZE):
        splitted_text.append(message[part:part+MAX_MESSAGE_SIZE])
    
    # Отправляем по частям
    for part in splitted_text:
        update.message.reply_text(part)


# Выполняем команду на удалённой машине
def execute_command_by_ssh(command):

    try:
        # Создаём объект SSHClient
        client = paramiko.SSHClient()
        
        # Автоматически доверяем хосту, к которому подключаемся
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Инициируем подключение по SSH
        client.connect(hostname=RM_HOST, username=RM_USER, password=RM_PASSWORD, port=RM_PORT)

        # Выполняем команду на машинке
        stdin, stdout, stderr = client.exec_command(command)
        data = stdout.read() + stderr.read()

        # Закрываем соединение
        client.close()

        data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]

    except Exception:
        data = "Произошла ошибка при подключении к хосту."
    
    return data


# /start команда
def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f"Привет {user.full_name}")


# Вывести справку по командам
def help_command(update: Update, context):
    send_long_text(update, context,
        "/start - начать общение с ботом.\n"
        "/find_phone_number - найти телефонные номера в тексте.\n"
        "/find_email - найти Email-адреса в тексте.\n"
        "/verify_password - проверить пароль на сложность.\n"
        "/get_release - информация о релизе.\n"
        "/get_uname - информация об архитектуре процессора, имени хоста системы и версии ядра.\n"
        "/get_uptime - информация о времени работы.\n"
        "/get_df - информация о состоянии файловой системы.\n"
        "/get_free - информация о состоянии оперативной памяти.\n"
        "/get_mpstat - информация о производительности системы.\n"
        "/get_w - информация о работающих в данной системе пользователях.\n"
        "/get_auths - последние 10 входов в систему.\n"
        "/get_critical - последние 5 критических события.\n"
        "/get_ps - информация о запущенные процессах.\n"
        "/get_ss - информация об используемых портах.\n"
        "/get_apt_list [packet] - информация об установленных пакетах.\n"
        "/get_services - информация о запущенных процессах.\n"
        "/help - вывести этот список.\n"
        "/get_repl_logs - чтобы получить логи о репликации БД.\n"
        "/get_emails - вывести почтовые адреса из БД.\n"
        "/get_phone_numbers - вывести телефонные номера из БД."
    )

# Запись почтовых адресов в БД
def insert_emails(update: Update, context: CallbackContext):
    # Подключаемся к бд
    db = database()

    # Принимаем ответ пользователя
    answer = update.message.text[0]

    # Проверяем ответ пользователя, согласен ли он на добавление почты в БД
    if answer.lower() == 'д':
        for email in context.user_data.get("emails"):

            # Вставляем строку в таблицу
            if not db.insert_email(email):
                update.message.reply_text("Во время добавления почтовых адресов возникла ошибка.")
                return
        
        update.message.reply_text("E-mail-ы успешно добавлены в базу данных.")
    else:
        update.message.reply_text("Данные не будут добавлены в базу данных.")
        
    return ConversationHandler.END


# Ищем e-mail в тексте
def find_email(update: Update, context: CallbackContext):
    # Принимаем пользовательский текст
    userInput = update.message.text

    # Задаём регулярное выражение и ищем шаблон по тексту
    emailRegex = re.compile(r"[a-zA-Z0-9._%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    foundEmailList = emailRegex.findall(userInput)

    # Если нет шаблона, то говорим, что нет e-mail адресов
    if not foundEmailList:
        update.message.reply_text("В вашем тексте нет e-mail адресов.")
        return
    
    # Все найденные e-mail адреса записываем в строку
    emails = ''
    for i in range(len(foundEmailList)):
        emails += f"{i+1}. {foundEmailList[i]}\n"
    
    # Отправляем пользователю e-mail-ы
    update.message.reply_text(emails)

    context.user_data["emails"] = foundEmailList
    update.message.reply_text("Хотите записать найденные почтовые адреса в базу данных? (Да/Нет)")

    return "insert_email"


# Обрабатываем команду /find_email
def find_email_command(update: Update, context):
    update.message.reply_text("Введите текст, в котором необходимо найти E-mail адреса:")

    return "find_email"


# Запись телефонных номеров в БД
def insert_phone_numbers(update: Update, context: CallbackContext):
    # Подключаемся к бд
    db = database()

    # Принимаем ответ пользователя
    answer = update.message.text[0]

    # Проверяем ответ пользователя, согласен ли он на добавление телефона в БД
    if answer.lower() == 'д':
        for phone_number in context.user_data.get("phone_numbers"):

            # Вставляем строку в таблицу
            if not db.insert_phone_numbers(phone_number):
                update.message.reply_text("Во время добавления номера возникла ошибка.")
                return
        
        update.message.reply_text("Телефонные номера успешно добавлены в базу данных.")
    else:
        update.message.reply_text("Данные не будут добавлены в базу данных.")
        
    return ConversationHandler.END


# Найти телефонный номер в тексте пользователя
def find_phone_number(update: Update, context):
    # Принимаем пользовательский ввод
    user_input = update.message.text

    # Создаём регулярное выражение и ищем шаблон в тексте пользователя
    phone_number_regex = re.compile(r'(?:\+7|8)[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}')

    found_numbers_list = phone_number_regex.findall(user_input)

    # Проверяем есть ли номера в тексте пользователя
    if not found_numbers_list:
        update.message.reply_text("В вашем тексте нет телефонных номеров.")
        return
    
    # Все номера записываем как одну строку
    phone_numbers = ''
    for i in range(len(found_numbers_list)):
        phone_numbers += f"{i+1}. {''.join(found_numbers_list[i])}\n"
    
    # Отправляем найденные номера пользователю
    update.message.reply_text(phone_numbers)

    context.user_data["phone_numbers"] = found_numbers_list
    update.message.reply_text("Хотите записать найденные номера в базу данных? (Да/Нет)")

    return "insert_phone_number"


# Обрабатываем команду /findPhoneNumber
def find_phone_number_command(update: Update, context):
    update.message.reply_text("Введите текст, в котором необходимо найти номера телефонов:")

    return "find_phone_number"


# Проверяем пароль на сложность
def verify_password(update: Update, context):
    # Принимаем пароль от пользователя
    user_input = update.message.text
    
    # Задаём регулярное выражение для проверки пароля
    password_regex = re.compile(
        r"(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()]).{8,}"
    )

    # Применяем шаблон на пароль
    found_password = password_regex.search(user_input)

    # Если пароль подходит под шаблон, то пароль сложный, иначе простой
    if not found_password:
        update.message.reply_text("Пароль простой.")
    else:
        update.message.reply_text("Пароль сложный.")
    
    return ConversationHandler.END


# Обрабатываем команду /verify_password
def verify_password_command(update: Update, context):
    update.message.reply_text("Введите пароль для проверки:")

    return "verify_password"


# Вывод информации о релизе
def get_release_command(update: Update, context):
    data = execute_command_by_ssh("lsb_release -a")
    update.message.reply_text(data)


# Вывод информации об архитектуре процессора, имени хоста системы и версии ядра
def get_uname_command(update: Update, context):
    data = execute_command_by_ssh("uname -a")
    update.message.reply_text(data)


# Вывод информации о времени работы ОС
def get_uptime_command(update: Update, context):
    data = execute_command_by_ssh("uptime")
    update.message.reply_text(data)


# Вывод информации о состоянии файловой системы
def get_df_command(update: Update, context):
    data = execute_command_by_ssh("df -h")
    update.message.reply_text(data)


# Вывод информации о состоянии оперативной памяти
def get_free_command(update: Update, context):
    data = execute_command_by_ssh("free -h")
    update.message.reply_text(data)


# Вывод информации о производительности системы
def get_mpstat_command(update: Update, context):
    data = execute_command_by_ssh("mpstat")
    update.message.reply_text(data)


# Вывод информации о работающих в системе пользователях
def get_w_command(update: Update, context):
    data = execute_command_by_ssh("w")
    update.message.reply_text(data)


# Вывод последних 10 входах в систему
def get_auths_command(update: Update, context):
    data = execute_command_by_ssh("last -n 10")
    update.message.reply_text(data)


# Вывод 5 последних критических событий
def get_critical_command(update: Update, context):
    data = execute_command_by_ssh("journalctl -p crit -n 5")
    update.message.reply_text(data)


# Вывод информации о запущенных процессах
def get_ps_command(update: Update, context):
    data = execute_command_by_ssh("ps aux")

    # Делим текст на части, чтобы отправить порциями
    send_long_text(update, context, data)


# Вывод информации об используемых портах
def get_ss_command(update: Update, context):
    data = execute_command_by_ssh("ss -tuln")
    update.message.reply_text(data)


# Вывод информации об установленных пакетах
def get_apt_list_command(update: Update, context):
    data: str
    # Проверяем указано ли имя пакета
    if len(context.args) == 0:
        data = execute_command_by_ssh("dpkg -l | head -10")
    else:
        package_name = " ".join(context.args)
        data = execute_command_by_ssh(f"dpkg -s {package_name}")
    
    send_long_text(update, context, data)


# Вывод запущенных сервисов
def get_services_command(update: Update, context):
    data = execute_command_by_ssh("service --status-all | grep '\[ + \]'")
    update.message.reply_text(data)


# Вывод логов о репликации
def get_replication_logs(update: Update, context):
    result  = subprocess.run(["cat", "/var/log/postgresql/postgresql*.log"], stdout=subprocess.PIPE, text=True)
    grepped = subprocess.run(["grep", "-i", "replica"], input=result.stdout, stdout=subprocess.PIPE, text=True)
    data    = subprocess.run(["tail", "-10"], input=grepped.stdout, stdout=subprocess.PIPE, text=True).stdout
    update.message.reply_text(data)


# Получаем почтовые адреса из БД
def get_emails(update: Update, context):
    # Подключаемся к бд
    db = database()

    emails_list = db.get_emails_list()
    if not emails_list:
        update.message.reply_text("Не удалось получить email адреса.")
    
    for id, email in emails_list:
        update.message.reply_text(str(id) + ". " + email)

# Получаем телефонные номера из БД
def get_phone_numbers(update: Update, context):
    # Подключаемся к бд
    db = database()
    
    numbers_list = db.get_phone_numbers_list()
    if not numbers_list:
        update.message.reply_text("Не удалось получить email адреса.")
    
    for id, phone_number in numbers_list:
        update.message.reply_text(str(id) + ". " + phone_number)


def main():
    # Создаём Updater и передаём ему токен бота
    updater = Updater(TOKEN, use_context=True)

    # Инициируем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Создаём обработчик диалога для поиска телефонных номеров
    conv_handler_find_phone_numbers = ConversationHandler(
        entry_points=[CommandHandler("find_phone_number", find_phone_number_command)],
        states={
            "find_phone_number": [MessageHandler(Filters.text & ~Filters.command, find_phone_number)],
            "insert_phone_number": [MessageHandler(Filters.text & ~Filters.command, insert_phone_numbers)],
        },
        fallbacks=[]
    )

    # Создаём обработчик диалога для поиска e-mail-ов
    conv_handler_find_emails = ConversationHandler(
        entry_points=[CommandHandler("find_email", find_email_command)],
        states={
            "find_email": [MessageHandler(Filters.text & ~Filters.command, find_email)],
            "insert_email": [MessageHandler(Filters.text & ~Filters.command, insert_emails)],
        },
        fallbacks=[]
    )

    # Создаём обработчик диалога для проверки пароля
    conv_handler_verify_password = ConversationHandler(
        entry_points=[CommandHandler("verify_password", verify_password_command)],
        states={
            "verify_password": [MessageHandler(Filters.text & ~Filters.command, verify_password)],
        },
        fallbacks=[]
    )

    # Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("get_release", get_release_command))
    dp.add_handler(CommandHandler("get_uname", get_uname_command))
    dp.add_handler(CommandHandler("get_uptime", get_uptime_command))
    dp.add_handler(CommandHandler("get_df", get_df_command))
    dp.add_handler(CommandHandler("get_free", get_free_command))
    dp.add_handler(CommandHandler("get_mpstat", get_mpstat_command))
    dp.add_handler(CommandHandler("get_w", get_w_command))
    dp.add_handler(CommandHandler("get_auths", get_auths_command))
    dp.add_handler(CommandHandler("get_critical", get_critical_command))
    dp.add_handler(CommandHandler("get_ps", get_ps_command))
    dp.add_handler(CommandHandler("get_ss", get_ss_command))
    dp.add_handler(CommandHandler("get_apt_list", get_apt_list_command))
    dp.add_handler(CommandHandler("get_services", get_services_command))
    dp.add_handler(CommandHandler("get_repl_logs", get_replication_logs))
    dp.add_handler(CommandHandler("get_emails", get_emails))
    dp.add_handler(CommandHandler("get_phone_numbers", get_phone_numbers))
    dp.add_handler(conv_handler_find_phone_numbers)
    dp.add_handler(conv_handler_find_emails)
    dp.add_handler(conv_handler_verify_password)

    # Запускаем бота, слушаем сообщения
    updater.start_polling()

    # Останавливаем бота при SIGINT
    updater.idle()


if __name__ == "__main__":
    main()
