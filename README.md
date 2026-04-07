# Review Bonus Plugin для FunPay Cardinal

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## 📝 Описание

Плагин для [FunPay Cardinal](https://github.com/sidor0912/FunPayCardinal), который автоматически отправляет бонусы покупателям после оставленного отзыва.

## ✨ Возможности

- 🎁 Автоматическая выдача бонусов после отзывов
- ⭐ Настройка разных бонусов для каждой оценки (1-5 звезд)
- 🎯 Минимальный порог звезд для выдачи бонуса
- 📱 Управление через Telegram бота
- 📊 История выданных бонусов
- 🔔 Уведомления в Telegram о выданных бонусах
- 🛡️ Защита от повторной выдачи бонуса за один заказ

## 📦 Установка

1. Скачайте файл `review_bonus.py`
2. Поместите его в папку `plugins` вашего FunPay Cardinal
3. Перезапустите бота

```bash
cd FunPayCardinal/plugins
wget https://raw.githubusercontent.com/nullcaste/review-bonus-plugin/main/review_bonus.py
```

## 🚀 Использование

### Команды Telegram

- `/review_bonus` - открыть меню настроек плагина

### Настройки

В меню настроек вы можете:

- 🟢/🔴 Включить/выключить плагин
- 📝 Изменить текст сообщения с бонусом
- 🎁 Настроить бонусы для каждой оценки (1-5 звезд)
- ⭐ Установить минимальное количество звезд для выдачи бонуса
- 🔄 Выбрать режим: только новые отзывы или все
- 🔔 Включить/выключить уведомления в Telegram
- 📊 Просмотреть историю выданных бонусов

## ⚙️ Конфигурация

Плагин создает следующие файлы:

```
storage/plugins/review_bonus/
├── config.json      # Настройки плагина
└── history.json     # История выданных бонусов
```

### Пример конфигурации

```json
{
    "enabled": true,
    "bonus_message": "🎁 Спасибо за отзыв! Вот ваш бонус: {bonus}",
    "bonus_by_stars": {
        "5": "Промокод: SUPER5 на 10% скидку",
        "4": "Промокод: GOOD4 на 5% скидку",
        "3": "Спасибо за отзыв!",
        "2": "Спасибо за отзыв!",
        "1": "Спасибо за отзыв!"
    },
    "min_stars_for_bonus": 3,
    "send_only_on_new": true,
    "telegram_notify": true
}
```

## 📸 Скриншоты

### Меню настроек
```
🎁 Review Bonus v1.0.0

Статус: 🟢 Включено
Минимум звезд: 3
Только новые: Да
Уведомления: Да

Сообщение:
🎁 Спасибо за отзыв! Вот ваш бонус: {bonus}
```

### Пример уведомления
```
🎁 Бонус выдан!

📦 Заказ: #12345678
👤 Покупатель: username
⭐️ Оценка: 5
🎁 Бонус: Промокод: SUPER5 на 10% скидку
```

## 🔧 Требования

- Python 3.8+
- FunPay Cardinal
- Библиотеки:
  - `telebot` (pyTelegramBotAPI)
  - `FunPayAPI`

## 📝 Лицензия

MIT License - см. файл [LICENSE](LICENSE)

## 👤 Автор

- Telegram: [@wzxno](https://t.me/wzxno)
- GitHub: [@nullcaste](https://github.com/nullcaste)

## 🤝 Поддержка

Если у вас возникли вопросы или проблемы:

1. Создайте [Issue](https://github.com/nullcaste/review-bonus-plugin/issues)
2. Напишите в Telegram: [@wzxno](https://t.me/wzxno)

## ⭐ Поддержите проект

Если плагин вам помог, поставьте звезду на GitHub!

## 📋 Changelog

### v1.0.0 (2024)
- 🎉 Первый релиз
- ✨ Базовый функционал выдачи бонусов
- 📱 Telegram интерфейс
- 📊 История бонусов
