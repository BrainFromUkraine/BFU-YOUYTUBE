# Посібник з Railway Backend

## Загальна інформація

**Railway backend** — рекомендований спосіб для виробничого використання BFU YouTube Subscriber Counter. Замість того, щоб зберігати YouTube API-ключ безпосередньо в прошивці ESP32, ви розгортаєте невеликий FastAPI-сервер на [Railway](https://railway.app/). ESP32 звертається до вашого backend URL, а backend сам викликає YouTube від його імені.

```
ESP32  ──►  https://your-app.up.railway.app/api/subscribers  ──►  YouTube Data API v3
```

**Навіщо використовувати backend?**

| Питання | Прямий API (прошивка) | Railway backend |
|---|---|---|
| Розташування API-ключа | Всередині прошивки ESP32 | Лише у змінних Railway |
| Ризик витоку ключа | Високий (будь-хто з `.py` файлом) | Відсутній (ключ ніколи не покидає сервер) |
| Кешування | Немає — кожне оновлення звертається до YouTube | Вбудоване (за замовчуванням 30 с) |
| Використання квоти | 1 одиниця на кожне оновлення ESP32 | 1 одиниця на вікно кешу |
| Надійність | Збій, якщо YouTube повільний | Повертає застарілий кеш, якщо YouTube недоступний |

> ⚠️ **Примітка:** YouTube Data API v3 повертає **публічну кількість підписників**, яку YouTube навмисно округлює для каналів з більш ніж 1 000 підписників. Це обмеження платформи YouTube і не може бути змінено ні backend, ні прошивкою.

---

## Файли backend

Усі файли backend знаходяться у папці `backend/`:

```
backend/
├── main.py            ← FastAPI-застосунок
├── requirements.txt   ← Python-залежності
├── Procfile           ← Команда запуску Railway
├── .env.example       ← Шаблон для локальної розробки
├── .gitignore         ← Виключає .env з git
└── README.md          ← README для backend
```

---

## Крок 1 — Отримайте YouTube API-ключ

1. Перейдіть до [Google Cloud Console](https://console.cloud.google.com/)
2. Створіть новий проєкт (наприклад, `BFU-Counter`)
3. Перейдіть до **APIs & Services → Library**
4. Знайдіть **YouTube Data API v3** і натисніть **Enable**
5. Перейдіть до **APIs & Services → Credentials**
6. Натисніть **Create Credentials → API key**
7. Скопіюйте згенерований ключ

> Безкоштовна квота — **10 000 одиниць/день**. З кешуванням 30 секунд навіть безперервне опитування ESP32 дає щонайбільше ~2 880 API-запитів/день — значно менше безкоштовного ліміту.

---

## Крок 2 — Розгортання на Railway

1. Завантажте цей репозиторій на GitHub (якщо ще не зроблено).
2. Перейдіть на [railway.app](https://railway.app/) і увійдіть.
3. Натисніть **New Project → Deploy from GitHub repo**.
4. Виберіть ваш репозиторій.
5. У налаштуваннях проєкту Railway встановіть **Root Directory** на `backend`.
6. Перейдіть на вкладку **Variables** і додайте:

   | Змінна | Значення |
   |---|---|
   | `YOUTUBE_API_KEY` | Ваш YouTube Data API v3 ключ |
   | `YOUTUBE_CHANNEL_ID` | ID вашого каналу (починається з `UC`) |
   | `CACHE_TTL_SECONDS` | `30` (необов'язково, за замовчуванням 30) |
   | `DEVICE_API_TOKEN` | Випадковий секретний токен (необов'язково) |

7. Railway автоматично виявить `Procfile` і розгорне застосунок.
8. Ваш endpoint буде доступний за адресою:
   ```
   https://YOUR-APP-NAME.up.railway.app/api/subscribers
   ```

---

## Крок 3 — Налаштування прошивки ESP32

Відкрийте `src/main.py` і оновіть константи URL бекенду на початку файлу:

```python
# ─── BACKEND URL (Railway proxy) ─────────────────────────────────────────────
# Встановіть URL вашого Railway бекенду.
# Залиште YOUTUBE_API_KEY як заглушку — ключ зберігається на сервері, не тут.
BACKEND_SUBSCRIBERS_URL = "https://YOUR-APP-NAME.up.railway.app/api/subscribers"
BACKEND_AVATAR_URL      = "https://YOUR-APP-NAME.up.railway.app/api/avatar-rgb565"
DEVICE_API_TOKEN        = ""   # Встановіть, якщо увімкнули токен-авторизацію на бекенді
```

> Якщо ви увімкнули `DEVICE_API_TOKEN` на backend — встановіть те саме значення в `DEVICE_API_TOKEN` у прошивці. ESP32 автоматично надсилатиме його як заголовок `X-Device-Token`.

---

## Крок 4 — Перевірка backend

Відкрийте браузер або використайте `curl` для тестування:

```
https://YOUR-APP-NAME.up.railway.app/
```

Очікувана відповідь:
```json
{
  "service": "BFU YouTube Subscriber Counter API",
  "status": "ok",
  "channel_id": "UCxxxxxxxxx",
  "cache_ttl_seconds": 30,
  "auth_enabled": false
}
```

Потім перевірте endpoint підписників:
```
https://YOUR-APP-NAME.up.railway.app/api/subscribers
```

Очікувана відповідь:
```json
{
  "ok": true,
  "channel_id": "UCxxxxxxxxx",
  "subscribers": 4590,
  "source": "youtube_data_api",
  "updated_at": "2025-01-01T12:00:00+00:00",
  "note": "Public YouTube count may be rounded",
  "stale": false
}
```

---

## Локальна розробка

Щоб запустити backend локально перед розгортанням:

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt

copy .env.example .env
# Відредагуйте .env і додайте реальні ключі

uvicorn main:app --reload --port 8000
```

Відкрийте: [http://localhost:8000/api/subscribers](http://localhost:8000/api/subscribers)

---

## Необов'язково: Авторизація через токен пристрою

Щоб захистити endpoint backend від несанкціонованого доступу:

1. Згенеруйте випадковий токен:
   ```bash
   # PowerShell
   -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | % {[char]$_})
   ```
2. Встановіть `DEVICE_API_TOKEN=your_token` у змінних Railway.
3. Встановіть `DEVICE_API_TOKEN = "your_token"` у `src/main.py`.
4. ESP32 автоматично надсилатиме `X-Device-Token: your_token` з кожним запитом.

---

## Як працює кешування

```
Запит 1 (t=0с)   → промах кешу  → запит до YouTube API → кешування → повернення свіжих даних
Запит 2 (t=10с)  → влучення     → повернення кешованих даних (без виклику YouTube)
Запит 3 (t=25с)  → влучення     → повернення кешованих даних (без виклику YouTube)
Запит 4 (t=35с)  → промах кешу  → запит до YouTube API → кешування → повернення свіжих даних
```

Якщо YouTube API тимчасово недоступний, backend повертає останнє кешоване значення з `"stale": true`. Якщо кешу немає взагалі — повертає HTTP 503 з `"ok": false`.

---

## Довідник змінних середовища

| Змінна | Обов'язкова | За замовчуванням | Опис |
|---|---|---|---|
| `YOUTUBE_API_KEY` | ✅ Так | — | YouTube Data API v3 ключ |
| `YOUTUBE_CHANNEL_ID` | ✅ Так | — | ID каналу, що починається з `UC` |
| `CACHE_TTL_SECONDS` | Ні | `30` | Тривалість кешу в секундах |
| `DEVICE_API_TOKEN` | Ні | *(вимкнено)* | Якщо встановлено, ESP32 повинен надсилати відповідний заголовок `X-Device-Token` |

---

## API Endpoints

### `GET /api/subscribers`
Повертає кількість підписників. Використовується ESP32 для основного лічильника.

### `GET /api/channel`
Повертає назву каналу, кількість підписників та URL аватара. Використовує той самий кеш, що й `/api/subscribers`.

**Відповідь:**
```json
{
  "ok": true,
  "channel_id": "UCxxxxx",
  "title": "BFU Electronics",
  "subscribers": 4670,
  "avatar_url": "https://yt3.ggpht.com/...",
  "updated_at": "2024-01-01T12:00:00+00:00",
  "stale": false
}
```

### `GET /api/avatar-rgb565`
Завантажує аватар каналу, змінює розмір до **64×64 пікселів**, конвертує кожен піксель у формат **RGB565** і повертає JSON-масив рядків у шістнадцятковому форматі. Конвертація кешується на сервері — виконується лише один раз для кожного унікального URL аватара.

**Відповідь:**
```json
{
  "ok": true,
  "width": 64,
  "height": 64,
  "pixels": ["FFFF", "0000", "F800", "..."]
}
```

Прошивка ESP32 викликає цей endpoint один раз при відкритті екрана підписників, конвертує рядки у `bytearray` і відображає аватар через `display.write_block()`. Список пікселів звільняється з RAM одразу після відображення.

### `GET /`
Перевірка стану сервісу — повертає статус і зведення конфігурації.

---

## Примітки щодо безпеки

- `YOUTUBE_API_KEY` зберігається лише у змінних Railway — ніколи в коді або на ESP32.
- Файл `.env` вказано у `backend/.gitignore` і ніколи не буде закомічений.
- Логи не виводять API-ключі або токени.
- `DEVICE_API_TOKEN` необов'язковий, але рекомендований для виробничих розгортань.
