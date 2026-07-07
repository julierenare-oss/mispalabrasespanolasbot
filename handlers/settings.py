import csv
import io
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext

from states import SettingsStates
from database import (
    get_reminders_enabled, set_reminders_enabled,
    save_reminder_times, get_reminder_times,
    clear_words, get_all_words_for_export, get_words_count
)
from keyboards import settings_kb, confirm_kb, back_to_menu_kb

router = Router()


@router.callback_query(F.data == "settings")
async def show_settings(call: CallbackQuery, state: FSMContext):
    await state.clear()
    reminders_on = await get_reminders_enabled(call.from_user.id)
    await call.message.edit_text(
        "⚙️ Настройки",
        reply_markup=settings_kb(reminders_on)
    )
    await call.answer()


@router.callback_query(F.data == "toggle_reminders")
async def toggle_reminders(call: CallbackQuery):
    user_id = call.from_user.id
    current = await get_reminders_enabled(user_id)
    await set_reminders_enabled(user_id, not current)
    reminders_on = await get_reminders_enabled(user_id)
    status = "включены ✅" if reminders_on else "выключены ❌"
    await call.message.edit_text(
        f"🔔 Напоминания {status}",
        reply_markup=settings_kb(reminders_on)
    )
    await call.answer()


@router.callback_query(F.data == "set_reminder_times")
async def ask_reminder_times(call: CallbackQuery, state: FSMContext):
    times = await get_reminder_times(call.from_user.id)
    current = ", ".join(times) if times else "не заданы"
    await call.message.edit_text(
        f"🕐 Текущее время напоминаний: <b>{current}</b>\n\n"
        f"Введи новое время через запятую:\n"
        f"Например: <code>09:00, 14:00, 20:00</code>",
        parse_mode="HTML",
        reply_markup=back_to_menu_kb()
    )
    await state.set_state(SettingsStates.waiting_reminder_times)
    await call.answer()


@router.message(SettingsStates.waiting_reminder_times)
async def save_times(message: Message, state: FSMContext):
    raw = message.text.strip()
    parts = [p.strip() for p in raw.split(",")]

    valid_times = []
    errors = []
    for part in parts:
        try:
            h, m = part.split(":")
            if 0 <= int(h) <= 23 and 0 <= int(m) <= 59:
                valid_times.append(f"{int(h):02d}:{int(m):02d}")
            else:
                errors.append(part)
        except Exception:
            errors.append(part)

    if not valid_times:
        await message.answer(
            "⚠️ Не удалось распознать время. Введи в формате ЧЧ:ММ, например: 09:00, 20:00",
            reply_markup=back_to_menu_kb()
        )
        return

    await save_reminder_times(message.from_user.id, valid_times)
    saved = ", ".join(valid_times)

    text = f"✅ Время напоминаний сохранено: <b>{saved}</b>"
    if errors:
        text += f"\n⚠️ Не распознано: {', '.join(errors)}"

    await message.answer(text, parse_mode="HTML", reply_markup=back_to_menu_kb())
    await state.clear()


@router.callback_query(F.data == "export_words")
async def export_words(call: CallbackQuery):
    words = await get_all_words_for_export()
    if not words:
        await call.answer("Словарь пустой!", show_alert=True)
        return

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["español", "русский"])
    for word in words:
        writer.writerow([word["spanish"], word["russian"]])

    file_bytes = output.getvalue().encode("utf-8")
    file = BufferedInputFile(file_bytes, filename="my_words.csv")
    await call.message.answer_document(file, caption="📤 Твой словарь")
    await call.answer()


@router.callback_query(F.data == "clear_words")
async def ask_clear_confirm(call: CallbackQuery):
    total = await get_words_count()
    await call.message.edit_text(
        f"🗑 Ты уверена? Это удалит все <b>{total}</b> слов из словаря.",
        parse_mode="HTML",
        reply_markup=confirm_kb()
    )
    await call.answer()


@router.callback_query(F.data == "confirm_clear")
async def do_clear(call: CallbackQuery):
    await clear_words()
    await call.message.edit_text(
        "✅ Словарь очищен.",
        reply_markup=back_to_menu_kb()
    )
    await call.answer()
