# 🔌 Интеграции с другими системами

Ваш сервер предоставляет простой REST API, который можно интегрировать с чем угодно.

## 📡 API Endpoints

### `POST /generate` - Генерация раскраски

**Request:**
```json
{
  "subject": "единорог",
  "style": "cartoon",           // simple, cartoon, realistic
  "detail_level": "medium",     // low, medium, high
  "print": false                // true для автопечати
}
```

**Response:**
```json
{
  "success": true,
  "image_url": "/output/coloring_unicorn_20240115_123456.png",
  "filename": "coloring_unicorn_20240115_123456.png",
  "printed": false
}
```

### `POST /print` - Печать существующего файла

**Request:**
```json
{
  "filename": "coloring_unicorn_20240115_123456.png"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Отправлено на печать!"
}
```

---

## 🏠 Home Assistant

### Добавьте REST команду

Файл: `configuration.yaml`

```yaml
rest_command:
  generate_coloring:
    url: "http://192.168.1.100:5000/generate"
    method: POST
    content_type: "application/json"
    payload: >
      {
        "subject": "{{ subject }}",
        "style": "{{ style | default('cartoon') }}",
        "detail_level": "{{ detail_level | default('medium') }}",
        "print": {{ print | default(true) }}
      }
```

### Создайте автоматизацию

```yaml
automation:
  - alias: "Генерация раскраски по кнопке"
    trigger:
      platform: state
      entity_id: input_button.generate_coloring
    action:
      service: rest_command.generate_coloring
      data:
        subject: "{{ states('input_text.coloring_subject') }}"
        style: "cartoon"
        detail_level: "medium"
        print: true
```

### Создайте input helper

```yaml
input_text:
  coloring_subject:
    name: "Что нарисовать?"
    initial: "кот"

input_button:
  generate_coloring:
    name: "Сделать раскраску"
    icon: mdi:printer
```

---

## 🔴 Node-RED

### HTTP Request Node

```json
{
  "url": "http://192.168.1.100:5000/generate",
  "method": "POST",
  "headers": {
    "content-type": "application/json"
  },
  "payload": {
    "subject": "динозавр",
    "style": "simple",
    "detail_level": "medium",
    "print": true
  }
}
```

### Пример Flow

```json
[
  {
    "id": "voice_input",
    "type": "inject",
    "name": "Голосовая команда",
    "topic": "",
    "payload": "нарисуй единорога"
  },
  {
    "id": "extract_subject",
    "type": "function",
    "name": "Извлечь тему",
    "func": "msg.payload = {\n  subject: msg.payload.replace('нарисуй ', ''),\n  style: 'cartoon',\n  print: true\n};\nreturn msg;"
  },
  {
    "id": "http_request",
    "type": "http request",
    "method": "POST",
    "url": "http://192.168.1.100:5000/generate",
    "name": "Генерация"
  }
]
```

---

## 🎤 Голосовой ассистент (Python)

### Простой пример

```python
import requests
import speech_recognition as sr

def voice_to_coloring():
    # Распознавание речи
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Скажите что нарисовать...")
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio, language='ru-RU')
        print(f"Распознано: {text}")

        # Генерация раскраски
        response = requests.post('http://192.168.1.100:5000/generate', json={
            'subject': text,
            'style': 'cartoon',
            'detail_level': 'medium',
            'print': True
        })

        if response.ok:
            print("Раскраска готова и отправлена на печать!")
        else:
            print(f"Ошибка: {response.json()}")

    except sr.UnknownValueError:
        print("Не удалось распознать речь")

if __name__ == "__main__":
    voice_to_coloring()
```

### С использованием Vosk (оффлайн)

```python
import json
import requests
from vosk import Model, KaldiRecognizer
import pyaudio

def listen_and_generate():
    model = Model("model-ru")  # Скачайте модель Vosk
    rec = KaldiRecognizer(model, 16000)

    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    frames_per_buffer=8000)

    print("Слушаю...")

    while True:
        data = stream.read(4000, exception_on_overflow=False)
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            text = result.get('text', '')

            if 'раскраска' in text or 'нарисуй' in text:
                subject = extract_subject(text)

                response = requests.post('http://localhost:5000/generate', json={
                    'subject': subject,
                    'style': 'cartoon',
                    'print': True
                })

                print(f"Создана раскраска: {subject}")

def extract_subject(text):
    # Простое извлечение темы
    words = text.split()
    if 'нарисуй' in words:
        idx = words.index('нарисуй')
        return ' '.join(words[idx+1:])
    return text
```

---

## 💬 Telegram Bot

```python
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import requests

def generate_coloring(update: Update, context: CallbackContext):
    subject = ' '.join(context.args)

    if not subject:
        update.message.reply_text("Использование: /coloring единорог")
        return

    update.message.reply_text(f"Генерирую раскраску: {subject}... ⏳")

    response = requests.post('http://192.168.1.100:5000/generate', json={
        'subject': subject,
        'style': 'cartoon',
        'detail_level': 'medium',
        'print': False
    })

    if response.ok:
        data = response.json()
        image_url = f"http://192.168.1.100:5000{data['image_url']}"

        # Отправляем изображение
        update.message.reply_photo(photo=image_url)
        update.message.reply_text("Готово! ✅ Хотите напечатать? /print")
    else:
        update.message.reply_text(f"Ошибка: {response.json()['error']}")

def main():
    updater = Updater("YOUR_BOT_TOKEN", use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("coloring", generate_coloring))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
```

---

## 🌐 cURL примеры

### Генерация раскраски

```bash
curl -X POST http://192.168.1.100:5000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "дракон",
    "style": "cartoon",
    "detail_level": "medium",
    "print": false
  }'
```

### Печать

```bash
curl -X POST http://192.168.1.100:5000/print \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "coloring_dragon_20240115_123456.png"
  }'
```

---

## 🐍 Python Script

```python
import requests

def create_coloring(subject, style='cartoon', detail='medium', print_now=False):
    """Создать раскраску"""
    url = 'http://192.168.1.100:5000/generate'

    response = requests.post(url, json={
        'subject': subject,
        'style': style,
        'detail_level': detail,
        'print': print_now
    })

    if response.ok:
        data = response.json()
        print(f"✅ Раскраска готова: {data['filename']}")
        print(f"📥 URL: http://192.168.1.100:5000{data['image_url']}")
        return data
    else:
        print(f"❌ Ошибка: {response.json()['error']}")
        return None

# Использование
if __name__ == "__main__":
    # Создать и напечатать
    create_coloring("космический корабль", style="realistic", print_now=True)

    # Только создать
    result = create_coloring("пират", style="cartoon", detail="high")

    # Напечатать позже
    if result:
        requests.post('http://192.168.1.100:5000/print', json={
            'filename': result['filename']
        })
```

---

## 📱 iOS Shortcuts

1. Создайте новый Shortcut
2. Добавьте действие "Get Contents of URL"
3. Настройте:
   - **URL**: `http://192.168.1.100:5000/generate`
   - **Method**: POST
   - **Headers**: `Content-Type: application/json`
   - **Request Body**: JSON
   ```json
   {
     "subject": "Ask When Run",
     "style": "cartoon",
     "detail_level": "medium",
     "print": true
   }
   ```
4. Добавьте в виджеты или попросите Siri: "Hey Siri, generate coloring"

---

## 🤖 IFTTT / Zapier

### IFTTT Webhook

**Trigger**: Что угодно (кнопка, время, геолокация)

**Action**: Webhooks
- **URL**: `http://192.168.1.100:5000/generate`
- **Method**: POST
- **Content Type**: `application/json`
- **Body**:
```json
{
  "subject": "{{EventName}}",
  "style": "cartoon",
  "print": true
}
```

---

## 🎮 Пример расписания (cron)

Автоматическая генерация раскраски каждый день в 8:00

```bash
crontab -e
```

Добавьте:
```bash
0 8 * * * curl -X POST http://localhost:5000/generate -H "Content-Type: application/json" -d '{"subject":"случайное животное","style":"cartoon","print":true}'
```

---

## 🔐 Добавление авторизации (опционально)

Если хотите защитить API, добавьте в `app.py`:

```python
from functools import wraps
from flask import request, jsonify

API_KEY = os.getenv('API_KEY', 'your-secret-key')

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        key = request.headers.get('X-API-Key')
        if key != API_KEY:
            return jsonify({'error': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Применить к endpoint'ам
@app.route('/generate', methods=['POST'])
@require_api_key
def generate():
    # ...
```

Использование:
```bash
curl -X POST http://localhost:5000/generate \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"subject":"кот"}'
```

---

## 💡 Идеи для интеграций

- **Детский будильник**: Раскраска печатается каждое утро
- **Система наград**: После выполнения задач ребенком
- **Образовательные проекты**: Генерация раскрасок по темам уроков
- **Праздничные открытки**: Автоматически к дням рождения
- **QR-коды**: Раскраска печатается при сканировании QR-кода
- **NFC-метки**: Приложил карточку → распечаталась раскраска

---

Любая система, которая умеет отправлять HTTP запросы, может работать с вашим сервером! 🚀
