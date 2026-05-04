# Налаштування YouTube API

## Загальна інформація

Цей проєкт використовує **YouTube Data API v3** для отримання кількості підписників YouTube-каналу. API безкоштовний для типового використання (до 10 000 одиниць на день за замовчуванням).

---

## Крок 1 — Створіть проєкт у Google Cloud

1. Перейдіть на [https://console.cloud.google.com/](https://console.cloud.google.com/)
2. Увійдіть у свій обліковий запис Google.
3. Натисніть на список проєктів у верхній частині сторінки.
4. Натисніть **New Project** (Новий проєкт).
5. Введіть назву (наприклад, `BFU-Counter`) і натисніть **Create**.
6. Переконайтеся, що новий проєкт вибрано у списку.

---

## Крок 2 — Увімкніть YouTube Data API v3

1. У лівому меню перейдіть до **APIs & Services → Library**.
2. У рядку пошуку введіть `YouTube Data API v3`.
3. Натисніть на результат, потім натисніть **Enable** (Увімкнути).

---

## Крок 3 — Створіть API-ключ

1. Перейдіть до **APIs & Services → Credentials**.
2. Натисніть **Create Credentials → API key**.
3. Google згенерує ключ — скопіюйте його одразу.
4. (Необов'язково, але рекомендовано) Натисніть **Restrict Key** (Обмежити ключ):
   - У розділі **API restrictions** виберіть **Restrict key**
   - Виберіть **YouTube Data API v3** зі списку
   - Натисніть **Save**

---

## Крок 4 — Знайдіть ID вашого каналу

1. Відкрийте [YouTube Studio](https://studio.youtube.com/)
2. Перейдіть до **Settings → Channel → Advanced settings**
3. Скопіюйте **Channel ID** (починається з `UC...`)

Або відкрийте сторінку вашого YouTube-каналу в браузері та подивіться на URL:
```
https://www.youtube.com/channel/UCxxxxxxxxxxxxxxxxxx
```
Частина після `/channel/` — це ваш Channel ID.

---

## Крок 5 — Додайте ключ до прошивки або backend

### Варіант А — Railway Backend (Рекомендовано)

**Railway backend** — рекомендований спосіб для виробничого використання. Ваш API-ключ зберігається як змінна Railway і ніколи не потрапляє в прошивку ESP32.

Дивіться **[backend.md](backend.md)** для повного посібника з розгортання на Railway.

### Варіант Б — Прямий ключ у прошивці

1. Відкрийте `src/main.py` у Thonny або будь-якому текстовому редакторі.
2. Знайдіть цей рядок на початку файлу:
   ```python
   YOUTUBE_API_KEY = "PASTE_YOUR_API_KEY_HERE"
   ```
3. Замініть заглушку на ваш реальний API-ключ:
   ```python
   YOUTUBE_API_KEY = "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
   ```
4. ID каналу вже встановлено у файлі:
   ```python
   YOUTUBE_CHANNEL_ID = "UC---ig4FdhPV3bSgE9KPJhg"
   ```
   Якщо ви хочете відстежувати інший канал — замініть це значення на свій Channel ID.

5. Збережіть файл на пристрій (дивіться [installation.md](installation.md)).

---

## Як працює API-запит

Прошивка надсилає один HTTP GET-запит:

```
GET https://www.googleapis.com/youtube/v3/channels
    ?part=statistics
    &id=<CHANNEL_ID>
    &key=<API_KEY>
```

Відповідь — JSON-об'єкт. Прошивка витягує:
```json
items[0].statistics.subscriberCount
```

---

## Чому кількість підписників може відрізнятися від YouTube Studio

YouTube Data API v3 повертає **публічну кількість підписників**, яка:

- **Округлена** — YouTube округлює публічні значення до 3 значущих цифр (наприклад, 4 590 може відображатися як 4 500 або 4 600)
- **Кешована** — значення може відставати від реального на кілька хвилин або годин
- **Відрізняється від YouTube Studio** — Studio показує точну кількість у реальному часі, яка доступна лише власнику каналу через автентифікований API

Це обмеження платформи YouTube і не може бути виправлено в прошивці.

---

## Безпека

- **Ніколи не публікуйте реальний API-ключ у публічному репозиторії.**
- `YOUTUBE_API_KEY` у `src/main.py` встановлено як `"PASTE_YOUR_API_KEY_HERE"` — безпечна заглушка.
- `config.py` та `secrets.py` виключені файлом `.gitignore`.
- Якщо ви випадково розкрили ключ — перейдіть до Google Cloud Console → Credentials і негайно видаліть або перегенеруйте його.
