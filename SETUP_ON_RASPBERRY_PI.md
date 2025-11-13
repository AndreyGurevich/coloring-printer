# 🍓 Установка на Raspberry Pi

## Шаги установки

### 1. Скопируйте проект на Raspberry Pi

```bash
# Через git
cd ~
git clone <your-repo-url> coloring-printer
cd coloring-printer

# Или через scp с вашего компьютера
scp -r coloring-printer pi@raspberry-pi-ip:~/
```

### 2. Установите зависимости

```bash
cd ~/coloring-printer

# Установите Python пакеты
pip3 install -r requirements.txt

# Или используйте виртуальное окружение (рекомендуется)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Настройте .env файл

```bash
# Создайте .env из примера
cp .env.example .env

# Отредактируйте
nano .env
```

Укажите ваш OpenAI API ключ:
```bash
OPENAI_API_KEY=sk-ваш-ключ-здесь
ENABLE_PRINTING=true
PRINTER_NAME=
```

### 4. Установите и настройте CUPS

```bash
# Установка
sudo apt-get update
sudo apt-get install cups

# Добавьте пользователя в группу
sudo usermod -a -G lpadmin pi

# Перезагрузите или выйдите и войдите заново
sudo reboot
```

После перезагрузки настройте принтер:

```bash
# Откройте веб-интерфейс
# На Raspberry Pi: http://localhost:631
# С другого компьютера: http://raspberry-pi-ip:631

# Или посмотрите принтеры из командной строки
lpstat -p -d
```

### 5. Проверьте принтеры

```bash
cd ~/coloring-printer
python3 list_printers.py
```

Вы увидите список доступных принтеров.

### 6. Сделайте тестовую печать

```bash
# На принтер по умолчанию
python3 list_printers.py --test

# На конкретный принтер
python3 list_printers.py --test HP_LaserJet
```

### 7. Запустите сервер

```bash
cd ~/coloring-printer
python3 app.py
```

Сервер запустится на `http://0.0.0.0:5000`

### 8. Откройте в браузере

С любого устройства в локальной сети:
```
http://raspberry-pi-ip:5000
```

Найдите IP адрес Raspberry Pi:
```bash
hostname -I
```

---

## Настройка автозапуска

### Создайте systemd сервис

```bash
sudo nano /etc/systemd/system/coloring-printer.service
```

Вставьте:

```ini
[Unit]
Description=Coloring Printer Web Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/coloring-printer
Environment="PATH=/home/pi/coloring-printer/venv/bin"
ExecStart=/home/pi/coloring-printer/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Активируйте сервис

```bash
sudo systemctl daemon-reload
sudo systemctl enable coloring-printer
sudo systemctl start coloring-printer
```

### Проверьте статус

```bash
sudo systemctl status coloring-printer
```

### Просмотр логов

```bash
sudo journalctl -u coloring-printer -f
```

### Управление сервисом

```bash
# Остановить
sudo systemctl stop coloring-printer

# Перезапустить
sudo systemctl restart coloring-printer

# Отключить автозапуск
sudo systemctl disable coloring-printer
```

---

## Решение проблем

### Сервер не доступен из сети

Проверьте файрвол:
```bash
sudo ufw status
sudo ufw allow 5000
```

### Принтер не печатает

1. Проверьте CUPS:
```bash
sudo systemctl status cups
lpstat -p -d
```

2. Проверьте настройки в `.env`:
```bash
cat .env | grep PRINTING
```

3. Посмотрите логи приложения:
```bash
sudo journalctl -u coloring-printer -f
```

### Ошибка OpenAI API

Проверьте ключ в `.env` и баланс на аккаунте OpenAI.

---

## Полезные команды

```bash
# Узнать IP адрес
hostname -I

# Проверить открытые порты
sudo netstat -tlnp | grep 5000

# Посмотреть использование ресурсов
htop

# Перезагрузить Raspberry Pi
sudo reboot

# Выключить Raspberry Pi
sudo shutdown -h now
```

---

## Обновление

```bash
cd ~/coloring-printer

# Остановите сервис
sudo systemctl stop coloring-printer

# Обновите код
git pull

# Обновите зависимости
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Запустите сервис
sudo systemctl start coloring-printer
```

---

## Производительность

На Raspberry Pi 3/4 генерация раскрасок занимает столько же времени, сколько и на обычном компьютере, так как обработка происходит на серверах OpenAI.

Локально выполняется только:
- Веб-сервер Flask (легкий)
- Скачивание изображения (быстро)
- Отправка на печать (мгновенно)

Raspberry Pi Zero / 1 может работать медленнее при обработке веб-запросов.

---

## Бонус: Настройка доменного имени

Используйте mDNS для красивого имени:

```bash
# Установите avahi
sudo apt-get install avahi-daemon

# Теперь можно обращаться
http://raspberrypi.local:5000
```

Или настройте статический IP в роутере и используйте его.
