from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🚀 Начать повторение", callback_data="start_session"))
    builder.row(InlineKeyboardButton(text="📊 Моя статистика", callback_data="stats"))
    builder.row(InlineKeyboardButton(text="📂 Загрузить список слов", callback_data="upload"))
    builder.row(InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"))
    return builder.as_markup()


def direction_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🇪🇸 Испанский → Русский", callback_data="dir_es_ru"),
        InlineKeyboardButton(text="🇷🇺 Русский → Испанский", callback_data="dir_ru_es"),
    )
    builder.row(InlineKeyboardButton(text="🏠 В меню", callback_data="menu"))
    return builder.as_markup()


def count_kb(total: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=f"📚 Все ({total})", callback_data="count_all"))
    row = []
    if total >= 100:
        row.append(InlineKeyboardButton(text="100", callback_data="count_100"))
    if total >= 50:
        row.append(InlineKeyboardButton(text="50", callback_data="count_50"))
    if row:
        builder.row(*row)
    builder.row(InlineKeyboardButton(text="✏️ Своё значение", callback_data="count_custom"))
    builder.row(InlineKeyboardButton(text="🏠 В меню", callback_data="menu"))
    return builder.as_markup()


def session_stop_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⏹ Завершить сессию", callback_data="stop_session"))
    return builder.as_markup()


def after_session_kb(has_errors: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if has_errors:
        builder.row(InlineKeyboardButton(text="🔁 Повторить ошибки", callback_data="retry_errors"))
    builder.row(InlineKeyboardButton(text="🏠 В главное меню", callback_data="menu"))
    return builder.as_markup()


def settings_kb(reminders_on: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    status = "✅ ВКЛ" if reminders_on else "❌ ВЫКЛ"
    builder.row(InlineKeyboardButton(
        text=f"🔔 Напоминания: {status}",
        callback_data="toggle_reminders"
    ))
    builder.row(InlineKeyboardButton(text="🕐 Настроить время напоминаний", callback_data="set_reminder_times"))
    builder.row(InlineKeyboardButton(text="📤 Экспортировать словарь", callback_data="export_words"))
    builder.row(InlineKeyboardButton(text="🗑 Очистить словарь", callback_data="clear_words"))
    builder.row(InlineKeyboardButton(text="🏠 В меню", callback_data="menu"))
    return builder.as_markup()


def confirm_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да, удалить", callback_data="confirm_clear"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="settings"),
    )
    return builder.as_markup()


def back_to_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏠 В главное меню", callback_data="menu"))
    return builder.as_markup()
