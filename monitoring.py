from email.mime.text import MIMEText
from datetime import datetime
from PIL import Image
import sys
import psutil
import smtplib
import psycopg2
import pystray
import threading
import atexit
import schedule
import time
import configparser
import os
import logging

log_file = os.path.join(os.path.dirname(__file__), "monitoring.log")
logging.basicConfig(filename=log_file, level=logging.ERROR)

lock_file_path = os.path.join(os.path.dirname(__file__), 'lockfile')
if os.path.isfile(lock_file_path):
    logging.error(f"Программа уже запущена, time: {datetime.now()}")
    sys.exit()

with open(lock_file_path, 'w') as lock_file:
    lock_file.write('locked')

def delete_lock_file():
    if os.path.isfile(lock_file_path):
        os.remove(lock_file_path)

atexit.register(delete_lock_file)

def read_config():
    try:
        config = configparser.ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'monitoring.config'))
        return config
    except Exception as e:
        logging.error(f"Error in read_config: {e}, time: {datetime.now()}")

def get_smtp_connection():
    try:
        config = read_config()
        smtp_server = config.get('smtp', 'server')
        smtp_port = config.getint('smtp', 'port')
        smtp_username = config.get('smtp', 'username')
        smtp_password = config.get('smtp', 'password')
        smtp_conn = smtplib.SMTP(smtp_server, smtp_port)
        smtp_conn.ehlo()
        smtp_conn.starttls()
        smtp_conn.login(smtp_username, smtp_password)
        return smtp_conn
    except Exception as e:
        logging.error(f"Error in get_smtp_connection: {e}, time: {datetime.now()}")

class EmailSender:
    def __init__(self, smtp_conn, sender_email):
        self.smtp_conn = smtp_conn
        self.sender_email = sender_email
    
    def send_email(self, recipient_email, subject, message):
        try:
            msg = MIMEText(message)
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            self.smtp_conn.sendmail(self.sender_email, recipient_email, msg.as_string())
        except Exception as e:
            logging.error(f"Error in send_email: {e}, time: {datetime.now()}")
    
    def __del__(self):
        try:
            self.smtp_conn.quit()
        except Exception as e:
            logging.error(f"Error in __del__: {e}, time: {datetime.now()}")

def get_table_size():
    try:
        config = read_config()
        db_name = config.get('database', 'name')
        db_user = config.get('database', 'user')
        db_password = config.get('database', 'password')
        db_host = config.get('database', 'host')
        db_port = config.getint('database', 'port')

        conn = psycopg2.connect(database=db_name, user=db_user, password=db_password, host=db_host, port=db_port)
        cur = conn.cursor()

        query = """
                SELECT spcname, pg_size_pretty(pg_tablespace_size(spcname)) 
                FROM pg_tablespace
                WHERE spcname<>'pg_global';
                """

        cur.execute(query)
        result = cur.fetchall()
        
        for row in result:
            print(f"Табличное пространство: {row[0]}, size: {row[1]}")

        conn.close()
        return result
    except (Exception, psycopg2.Error) as error:
        logging.error(f"Error in get_table_size: {error}, time: {datetime.now()}")

def monitor_disk_space(email_sender):
    try:
        config = read_config()
        # Получаем информацию о свободном месте на жестких дисках, использованном CPU и памяти
        disk_free = psutil.disk_usage('/').free / (1024*1024*1024) # Свободное место на диске в гигабайтах
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent
        table_size = get_table_size()

        # Отправляем уведомление по электронной почте, если свободное место на диске меньше Value ГБ
        if disk_free < int(config.get('trigger_to_send', 'value')):
            subject = 'Обратите внимание на состояние системы'
            message = f'Свободное место на диске: {disk_free:.2f} ГБ.\nЗагрузка CPU: {cpu_percent}%.\nОЗУ: {memory_percent}%.\nЗагрузка диска: {disk_percent}%.\nТабличное пространство: {table_size}'
            email_sender.send_email(config.get('receiver_email', 'email'), subject, message)
    except Exception as e:
        logging.error(f"Error in: {e}, time: {datetime.now()}")
        pass


# Устанавливаем ежедневное расписание для мониторинга дискового пространства и отправки уведомлений
config = read_config()
smtp_conn = get_smtp_connection()
email_sender = EmailSender(smtp_conn, config.get('smtp', 'username'))
schedule_time = (config.get('time', 'h') + ':' + config.get('time', 'm'))
schedule.every().day.at(schedule_time).do(lambda: monitor_disk_space(email_sender))


def on_exit(icon):
    delete_lock_file()
    icon.stop()
    os._exit(0)
    

def to_tray():
    image_path = os.path.join(os.path.dirname(__file__), "icon.ico")
    image = Image.open(image_path)
    menu = (pystray.MenuItem("Выход", on_exit),)
    icon = pystray.Icon("monitoring", image, "Monitoring", menu)
    icon.run()
    atexit.register(delete_lock_file)
    sys.exit(0)

tray_thread = threading.Thread(target=to_tray)
tray_thread.start()

while True:
    schedule.run_pending()
    time.sleep(1)