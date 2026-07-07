import csv
import io
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from states import UploadStates
from database import add_words, get_words_count
from keyboards import back_to_menu_kb

router = Router()


@router.callback_query(F.data == "upload")
async def ask_for_file(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "📂 Отправь мне CSV файл со словами.\n\n"
        "Формат файла:\n"
        "<code>español;русский</code>\n"
        "<code>casa;дом</code>\n"
        "<code>perro;собака</code>\n\n"
        "Разделитель — точка с запятой или запятая.",
        parse_mode="HTML",
        reply_markup=back_to_menu_kb()
    )
    await state.set_state(UploadStates.waiting_for_file)
    await call.answer()


@router.message(UploadStates.waiting_for_file, F.document)
async def handle_file(message: Message, state: FSMContext):
    document = message.document

    if not document.file_name.endswith(".csv"):
        await message.answer(
            "⚠️ Нужен файл формата .csv\nПопробуй ещё раз или вернись в меню.",
            reply_markup=back_to_menu_kb()
        )
        return

    file = await message.bot.get_file(document.file_id)
    file_bytes = await message.bot.download_file(file.file_path)
    content = file_bytes.read().decode("utf-8")

    words = []
    errors = []

    reader = csv.reader(io.StringIO(content), delimiter=";")
    for i, row in enumerate(reader, start=1):
        if len(row) < 2:
            # попробуем запятую как разделитель
            row = row[0].split(",") if row else []
        if len(row) >= 2:
            spanish = row[0].strip()
            russian = row[1].strip()
            if spanish and russian:
                words.append({"spanish": spanish, "russian": russian})
        else:
            errors.append(i)

    if not words:
        await message.answer(
            "❌ Не удалось прочитать файл. Проверь формат и попробуй снова.",
            reply_markup=back_to_menu_kb()
        )
        return

    added, skipped = await add_words(words)
    total = await get_words_count()

    text = f"✅ Загружено новых слов: <b>{added}</b>\n"
    if skipped:
        text += f"⏭ Пропущено дублей: <b>{skipped}</b>\n"
    if errors:
        text += f"⚠️ Строк с ошибками: <b>{len(errors)}</b>\n"
    text += f"\n📚 Всего слов в словаре: <b>{total}</b>"

    await message.answer(text, parse_mode="HTML", reply_markup=back_to_menu_kb())
    await state.clear()


@router.message(UploadStates.waiting_for_file)
async def wrong_input(message: Message):
    await message.answer(
        "⚠️ Нужен именно файл .csv\nОтправь файл или вернись в меню.",
        reply_markup=back_to_menu_kb()
    )
  
