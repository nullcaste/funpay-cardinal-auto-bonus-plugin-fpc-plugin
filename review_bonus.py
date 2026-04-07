from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Any
from FunPayAPI.updater.events import NewMessageEvent
from FunPayAPI.types import MessageTypes
from FunPayAPI.common.utils import RegularExpressions
from datetime import datetime
import logging
import json
import os
import telebot
from telebot.types import InlineKeyboardMarkup as K, InlineKeyboardButton as B

if TYPE_CHECKING:
    from cardinal import Cardinal

logger = logging.getLogger("FPC.ReviewBonus")
LOGGER_PREFIX = "[ReviewBonus]"

NAME = "Review Bonus"
VERSION = "1.0.0"
DESCRIPTION = "Автоматическая выдача бонуса покупателю после оставленного отзыва"
CREDITS = "@wzxno // https://github.com/nullcaste"
UUID = "e8f3a9b2-4c5d-4e1a-9f2b-8d7c6e5f4a3b"
SETTINGS_PAGE = False

CONFIG_DIR = "storage/plugins/review_bonus"
CONFIG_FILE = f"{CONFIG_DIR}/config.json"
HISTORY_FILE = f"{CONFIG_DIR}/history.json"

DEFAULT_CONFIG = {
    "enabled": True,
    "bonus_message": "🎁 Спасибо за отзыв! Вот ваш бонус: {bonus}",
    "bonus_by_stars": {
        "5": "Промокод: SUPER5 на 10% скидку",
        "4": "Промокод: GOOD4 на 5% скидку",
        "3": "Спасибо за отзыв!",
        "2": "Спасибо за отзыв!",
        "1": "Спасибо за отзыв!"
    },
    "min_stars_for_bonus": 3,
    "send_only_on_new": True,
    "telegram_notify": True
}

bot = None
cardinal_instance = None

CB_MAIN = "rb_main"
CB_TOGGLE = "rb_toggle"
CB_EDIT_MESSAGE = "rb_edit_message"
CB_EDIT_BONUS = "rb_edit_bonus"
CB_MIN_STARS = "rb_min_stars"
CB_TOGGLE_NEW_ONLY = "rb_toggle_new_only"
CB_TOGGLE_TG_NOTIFY = "rb_toggle_tg_notify"
CB_SAVE = "rb_save"
CB_HISTORY = "rb_history"

current_edit_stars = None
current_chat_id = None
current_message_id = None

def ensure_config_dir():
    """Создает директорию для конфигурации"""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

def load_config() -> Dict[str, Any]:
    """Загружает конфигурацию из файла"""
    ensure_config_dir()
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"{LOGGER_PREFIX} Ошибка загрузки конфигурации: {e}")
        return DEFAULT_CONFIG

def save_config(config: Dict[str, Any]) -> bool:
    """Сохраняет конфигурацию в файл"""
    ensure_config_dir()
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        logger.error(f"{LOGGER_PREFIX} Ошибка сохранения конфигурации: {e}")
        return False

def load_history() -> Dict[str, Any]:
    """Загружает историю выданных бонусов"""
    ensure_config_dir()
    if not os.path.exists(HISTORY_FILE):
        return {}
    
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"{LOGGER_PREFIX} Ошибка загрузки истории: {e}")
        return {}

def save_history(history: Dict[str, Any]) -> bool:
    """Сохраняет историю выданных бонусов"""
    ensure_config_dir()
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        logger.error(f"{LOGGER_PREFIX} Ошибка сохранения истории: {e}")
        return False

def message_handler(cardinal: Cardinal, event: NewMessageEvent) -> None:
    """Обработчик новых сообщений - отслеживает отзывы"""
    try:
        config = load_config()
        
        if not config["enabled"]:
            return
        
        if config["send_only_on_new"] and event.message.type != MessageTypes.NEW_FEEDBACK:
            return
        
        if event.message.type not in [MessageTypes.NEW_FEEDBACK, MessageTypes.FEEDBACK_CHANGED]:
            return
        
        order_id = RegularExpressions().ORDER_ID.findall(str(event.message))[0][1:]
        order = cardinal.account.get_order(order_id)
        
        if not order.review:
            return
        
        stars = order.review.stars
        
        if stars < config["min_stars_for_bonus"]:
            logger.info(f"{LOGGER_PREFIX} Отзыв {stars} звезд меньше минимума {config['min_stars_for_bonus']}, бонус не выдается")
            return
        
        history = load_history()
        if order_id in history:
            logger.info(f"{LOGGER_PREFIX} Бонус для заказа {order_id} уже был выдан")
            return
        
        bonus_text = config["bonus_by_stars"].get(str(stars), "Спасибо за отзыв!")
        message = config["bonus_message"].format(bonus=bonus_text)
        
        cardinal.account.send_message(order.chat_id, message)
        logger.info(f"{LOGGER_PREFIX} Бонус отправлен для заказа {order_id} ({stars} звезд)")
        
        history[order_id] = {
            "stars": stars,
            "bonus": bonus_text,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "buyer": order.buyer_username
        }
        save_history(history)
        
        if config["telegram_notify"] and cardinal.telegram:
            notify_text = (
                f"🎁 <b>Бонус выдан!</b>\n\n"
                f"📦 Заказ: #{order_id}\n"
                f"👤 Покупатель: {order.buyer_username}\n"
                f"⭐️ Оценка: {stars}\n"
                f"🎁 Бонус: {bonus_text}"
            )
            for user_id in cardinal.telegram.authorized_users:
                try:
                    cardinal.telegram.bot.send_message(user_id, notify_text, parse_mode="HTML")
                except Exception as e:
                    logger.error(f"{LOGGER_PREFIX} Ошибка отправки уведомления: {e}")
        
    except Exception as e:
        logger.error(f"{LOGGER_PREFIX} Ошибка обработки отзыва: {e}")
        logger.debug("TRACEBACK", exc_info=True)

def init_commands(cardinal: Cardinal):
    """Инициализация команд Telegram"""
    global bot, cardinal_instance
    
    if not cardinal.telegram:
        logger.warning(f"{LOGGER_PREFIX} Telegram бот не инициализирован")
        return
    
    cardinal_instance = cardinal
    bot = cardinal.telegram.bot
    
    logger.info(f"{LOGGER_PREFIX} Инициализация команд")
    
    bot.set_my_commands([
        telebot.types.BotCommand(command='review_bonus', description='Настройка бонусов за отзывы')
    ])
    
    @bot.message_handler(commands=['review_bonus'])
    def cmd_review_bonus(message):
        if message.from_user.id not in cardinal.telegram.authorized_users:
            bot.send_message(message.chat.id, "❌ У вас нет доступа к настройкам.")
            return
        
        show_main_menu(message.chat.id)
    
    @bot.callback_query_handler(func=lambda call: call.data == CB_MAIN)
    def cb_main_menu(call):
        show_main_menu(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)
    
    @bot.callback_query_handler(func=lambda call: call.data == CB_TOGGLE)
    def cb_toggle(call):
        config = load_config()
        config["enabled"] = not config["enabled"]
        save_config(config)
        
        status = "включены" if config["enabled"] else "выключены"
        bot.answer_callback_query(call.id, f"✅ Бонусы {status}!")
        show_main_menu(call.message.chat.id, call.message.message_id)
    
    @bot.callback_query_handler(func=lambda call: call.data == CB_TOGGLE_NEW_ONLY)
    def cb_toggle_new_only(call):
        config = load_config()
        config["send_only_on_new"] = not config["send_only_on_new"]
        save_config(config)
        
        status = "только новые" if config["send_only_on_new"] else "все"
        bot.answer_callback_query(call.id, f"✅ Режим: {status}!")
        show_main_menu(call.message.chat.id, call.message.message_id)
    
    @bot.callback_query_handler(func=lambda call: call.data == CB_TOGGLE_TG_NOTIFY)
    def cb_toggle_tg_notify(call):
        config = load_config()
        config["telegram_notify"] = not config["telegram_notify"]
        save_config(config)
        
        status = "включены" if config["telegram_notify"] else "выключены"
        bot.answer_callback_query(call.id, f"✅ Уведомления {status}!")
        show_main_menu(call.message.chat.id, call.message.message_id)
    
    @bot.callback_query_handler(func=lambda call: call.data == CB_EDIT_MESSAGE)
    def cb_edit_message(call):
        config = load_config()
        kb = K()
        kb.add(B("🔙 Назад", callback_data=CB_MAIN))
        
        bot.edit_message_text(
            f"📝 Текущее сообщение:\n<pre>{config['bonus_message']}</pre>\n\n"
            f"Отправьте новое сообщение.\n"
            f"Используйте {{bonus}} для вставки текста бонуса.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb,
            parse_mode="HTML"
        )
        
        bot.register_next_step_handler(call.message, process_new_message)
        bot.answer_callback_query(call.id)
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('rb_edit_bonus_'))
    def cb_edit_bonus(call):
        global current_edit_stars, current_chat_id, current_message_id
        stars = call.data.split('_')[-1]
        current_edit_stars = stars
        current_chat_id = call.message.chat.id
        current_message_id = call.message.message_id
        
        config = load_config()
        current_bonus = config["bonus_by_stars"].get(stars, "")
        
        kb = K()
        kb.add(B("🔙 Назад", callback_data=CB_EDIT_BONUS))
        
        bot.edit_message_text(
            f"📝 Редактирование бонуса для {stars} звезд\n\n"
            f"Текущий бонус:\n<pre>{current_bonus}</pre>\n\n"
            f"Отправьте новый текст бонуса:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb,
            parse_mode="HTML"
        )
        
        bot.register_next_step_handler(call.message, process_new_bonus)
        bot.answer_callback_query(call.id)
    
    @bot.callback_query_handler(func=lambda call: call.data == CB_EDIT_BONUS)
    def cb_show_bonus_menu(call):
        config = load_config()
        kb = K(row_width=1)
        
        for stars in ["5", "4", "3", "2", "1"]:
            bonus = config["bonus_by_stars"].get(stars, "")
            short_bonus = bonus[:30] + "..." if len(bonus) > 30 else bonus
            kb.add(B(f"⭐️ {stars} звезд: {short_bonus}", callback_data=f"rb_edit_bonus_{stars}"))
        
        kb.add(B("🔙 Назад", callback_data=CB_MAIN))
        
        bot.edit_message_text(
            "📝 Выберите оценку для редактирования бонуса:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb
        )
        bot.answer_callback_query(call.id)
    
    @bot.callback_query_handler(func=lambda call: call.data == CB_MIN_STARS)
    def cb_min_stars(call):
        kb = K()
        kb.add(B("🔙 Назад", callback_data=CB_MAIN))
        
        bot.edit_message_text(
            "Введите минимальное количество звезд для выдачи бонуса (1-5):",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb
        )
        
        bot.register_next_step_handler(call.message, process_min_stars)
        bot.answer_callback_query(call.id)
    
    @bot.callback_query_handler(func=lambda call: call.data == CB_HISTORY)
    def cb_history(call):
        history = load_history()
        
        if not history:
            bot.answer_callback_query(call.id, "История пуста")
            return
        
        text = "📊 <b>История выданных бонусов:</b>\n\n"
        for order_id, data in list(history.items())[-10:]:
            text += (
                f"📦 Заказ #{order_id}\n"
                f"👤 {data.get('buyer', 'N/A')}\n"
                f"⭐️ {data.get('stars', 'N/A')} звезд\n"
                f"🎁 {data.get('bonus', 'N/A')}\n"
                f"📅 {data.get('date', 'N/A')}\n\n"
            )
        
        kb = K()
        kb.add(B("🔙 Назад", callback_data=CB_MAIN))
        
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
        bot.answer_callback_query(call.id)
    
    def process_new_message(message):
        if message.text and message.text.startswith('/'):
            show_main_menu(message.chat.id)
            return
        
        config = load_config()
        config["bonus_message"] = message.text
        save_config(config)
        
        bot.send_message(message.chat.id, "✅ Сообщение обновлено!")
        show_main_menu(message.chat.id)
    
    def process_new_bonus(message):
        global current_edit_stars
        
        if message.text and message.text.startswith('/'):
            show_main_menu(message.chat.id)
            return
        
        config = load_config()
        config["bonus_by_stars"][current_edit_stars] = message.text
        save_config(config)
        
        bot.send_message(message.chat.id, f"✅ Бонус для {current_edit_stars} звезд обновлен!")
        show_main_menu(message.chat.id)
        current_edit_stars = None
    
    def process_min_stars(message):
        if message.text and message.text.startswith('/'):
            show_main_menu(message.chat.id)
            return
        
        try:
            stars = int(message.text)
            if stars < 1 or stars > 5:
                bot.send_message(message.chat.id, "❌ Введите число от 1 до 5")
                return
            
            config = load_config()
            config["min_stars_for_bonus"] = stars
            save_config(config)
            
            bot.send_message(message.chat.id, f"✅ Минимум установлен: {stars} звезд")
            show_main_menu(message.chat.id)
        except ValueError:
            bot.send_message(message.chat.id, "❌ Введите корректное число")

def show_main_menu(chat_id, message_id=None):
    """Показывает главное меню настроек"""
    config = load_config()
    
    kb = K(row_width=2)
    
    status = "🟢" if config["enabled"] else "🔴"
    kb.add(B(f"{status} Бонусы", callback_data=CB_TOGGLE))
    
    kb.add(
        B("📝 Сообщение", callback_data=CB_EDIT_MESSAGE),
        B("🎁 Бонусы", callback_data=CB_EDIT_BONUS)
    )
    
    kb.add(B(f"⭐️ Минимум: {config['min_stars_for_bonus']} звезд", callback_data=CB_MIN_STARS))
    
    new_only_status = "🟢" if config["send_only_on_new"] else "🔴"
    kb.add(B(f"{new_only_status} Только новые отзывы", callback_data=CB_TOGGLE_NEW_ONLY))
    
    tg_notify_status = "🟢" if config["telegram_notify"] else "🔴"
    kb.add(B(f"{tg_notify_status} Уведомления в TG", callback_data=CB_TOGGLE_TG_NOTIFY))
    
    kb.add(B("📊 История", callback_data=CB_HISTORY))
    
    kb.add(
        B("💎 GitHub", url="https://github.com/nullcaste"),
        B("💬 Telegram", url="https://t.me/wzxno")
    )
    
    text = (
        f"🎁 <b>Review Bonus v{VERSION}</b>\n\n"
        f"<b>Статус:</b> {'🟢 Включено' if config['enabled'] else '🔴 Выключено'}\n"
        f"<b>Минимум звезд:</b> {config['min_stars_for_bonus']}\n"
        f"<b>Только новые:</b> {'Да' if config['send_only_on_new'] else 'Нет'}\n"
        f"<b>Уведомления:</b> {'Да' if config['telegram_notify'] else 'Нет'}\n\n"
        f"<b>Сообщение:</b>\n<pre>{config['bonus_message']}</pre>\n\n"
        f"<i>Используйте кнопки для настройки</i>\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👨‍💻 <b>Разработчик:</b> <a href='https://t.me/wzxno'>@wzxno</a>\n"
        f"💎 <b>GitHub:</b> <a href='https://github.com/nullcaste'>nullcaste</a>"
    )
    
    if message_id:
        try:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=kb, parse_mode="HTML")
        except:
            bot.send_message(chat_id, text, reply_markup=kb, parse_mode="HTML")
    else:
        bot.send_message(chat_id, text, reply_markup=kb, parse_mode="HTML")

load_config()

BIND_TO_NEW_MESSAGE = [message_handler]
BIND_TO_PRE_INIT = [init_commands]
BIND_TO_DELETE = None
