<div align="center">

# ₿ FX Portal

### Валютный монитор в реальном времени

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-24%2F24%20%E2%9C%85-34d399?style=for-the-badge)

</div>

---

## 🌍 О проекте

**FX Portal** — веб-приложение для мониторинга курсов валют в реальном времени.  
Получает актуальные данные с публичного API, отображает графики истории, позволяет конвертировать валюты и экспортировать отчёты.

> Учебный проект команды из 3 студентов по дисциплине «Проектирование программных продуктов»

---

## ✨ Возможности

| Функция | Описание |
|---|---|
| 📊 **Курсы валют** | 18 валютных пар в реальном времени относительно USD |
| 💱 **Конвертер** | Мгновенный перевод между любыми валютами |
| 📈 **История курсов** | Реальные данные ЕЦБ за 1 нед / 1 мес / 3 мес / 6 мес / 1 год |
| 📥 **Экспорт CSV** | Скачать таблицу курсов в формате CSV |
| 📗 **Экспорт Excel** | Скачать таблицу курсов в формате XLSX |
| 🔐 **Авторизация** | Регистрация, вход, система ролей admin/user |
| ⚙️ **Админ-панель** | Управление пользователями системы |
| 🐳 **Docker** | Запуск одной командой в любой среде |

---

## 🖥️ Скриншоты

### Главная страница
> Таблица курсов, конвертер, мини-график тренда

### История курса
> Реальные данные от ЕЦБ с фильтром периода

---

## 🚀 Быстрый старт

### Вариант 1 — Docker (рекомендуется)

```bash
# Клонировать репозиторий
git clone https://github.com/chekuringleb-collab/currency-portal.git
cd currency-portal

# Запустить
docker-compose up --build
```

Открыть в браузере: **http://localhost:5000**

---

### Вариант 2 — Локально

```bash
# Клонировать репозиторий
git clone https://github.com/chekuringleb-collab/currency-portal.git
cd currency-portal

# Создать виртуальное окружение
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# Установить зависимости
pip install -r requirements.txt

# Запустить
python app.py
```

Открыть в браузере: **http://localhost:5000**

---

## 🔐 Безопасность

- Пароли хешируются через `pbkdf2:sha256` с 600 000 итерациями
- `SECRET_KEY` читается из переменной окружения
- Защита от открытых редиректов
- `SESSION_COOKIE_HTTPONLY` и `SAMESITE=Lax`
- Раздельные роли: `admin` и `user`
- Первый зарегистрированный автоматически получает права администратора

---

## 🗂️ Структура проекта

```
currency-portal/
├── app.py                  # Основное Flask-приложение
├── tests.py                # Тесты (24 теста)
├── requirements.txt        # Зависимости Python
├── Dockerfile              # Docker-образ
├── docker-compose.yml      # Docker Compose
├── .env.example            # Пример переменных окружения
└── templates/
    ├── base.html           # Базовый шаблон
    ├── index.html          # Главная страница
    ├── login.html          # Вход
    ├── register.html       # Регистрация
    ├── history.html        # История курса
    ├── admin.html          # Админ-панель
    └── error.html          # Страницы ошибок
```

---

## 🧪 Тесты

```bash
python tests.py
```

```
Ran 24 tests in 25s — OK ✅
```

| Модуль | Тестов | Статус |
|---|---|---|
| Авторизация | 10 | ✅ |
| Доступ к страницам | 5 | ✅ |
| API курсов | 5 | ✅ |
| Экспорт CSV/Excel | 2 | ✅ |
| Безопасность | 2 | ✅ |

---

## 🛠️ Технологии

- **Backend:** Python 3.12, Flask 3.0, SQLAlchemy, Flask-Login
- **Frontend:** HTML5, CSS3, JavaScript, Chart.js
- **База данных:** SQLite
- **API:** ExchangeRate API, Frankfurter (ЕЦБ)
- **Контейнеризация:** Docker, Docker Compose
- **Шрифты:** Syne, DM Sans (Google Fonts)

---

## 👥 Команда

Учебный проект — 3 студента

---

<div align="center">

Сделано с ❤️ в 2026

</div>
