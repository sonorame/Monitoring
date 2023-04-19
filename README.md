# Monitoring
Программа для мониторинга системы.

## Установка
1. Запустите файл установки "setup_monitoring.exe".
2. Выберите папку для установки программы и нажмите кнопку "Install".
3. Прочитайте лицензионное соглашение.

## Использование
1. Откройте папку в которую была установлена программа.
2. В открытой папке заполните файл "monitoring.config".
3. После внесения изменений сохраните "monitoring.config" и запустите программу "monitoring.exe". При запуске программы в трее Windows будет расположена иконка с программой.
4. Для того, чтобы закрыть программу необходимо нажать правой кнопкой мыши по иконке в трее и нажать на кнопку "Выход"

## Важно!
После каждого изменения "monitoring.config" необходимо перезапускать программу Monitoring.

## Пример заполненного "monitoring.config"
[smtp]<br>
server = smtp.gmail.com<br>
port = 587<br>
username = username@gmail.com<br>
password = password<br>

[database]<br>
name = MyDB<br>
user = postgres<br>
password = 1Q2w3e4r5t<br>
host = 192.168.169.170<br>
port = 5432<br>

[time]<br>
h = 06<br>
m = 30<br>

[receiver_email]<br>
email = my_admin_mail@bars-arenda.ru

[trigger_to_send]<br>
value = 40