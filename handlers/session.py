import Levenshtein
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from states import SessionStates
from database import get_words_count, get_random_words, update_word_stats, create_session, finish_session
from keyboards import direction_kb, count_kb, session_stop_kb, after_session_kb

router = Router()


@router.callback_query(F.data == "start_session")
async def start_session(call: CallbackQuery, state: FSMContext):
    total = await get_words_count()
    if total == 0:
        await call.message.edit_text(
            "📭 Словарь пустой! Сначала загрузи список слов.",
            reply_markup=None
        )
        await call.answer()
        return

    await call.message.edit_text(
        "🔁 Выбери направление перевода:",
        reply_markup=direction_kb()
    )
    await state.set_state(SessionStates.choosing_direction)
    await call.answer()


@router.callback_query(SessionStates.choosing_direction, F.data.in_(["dir_es_ru", "dir_ru_es"]))
async def choose_direction(call: CallbackQuery, state: FSMContext):
    direction = call.data
    await state.update_data(direction=direction)

    total = await get_words_count()
    await call.message.edit_text(
        "📚 Сколько слов повторим?",
        reply_markup=count_kb(total)
    )
    await state.set_state(SessionStates.choosing_count)
    await call.answer()


@router.callback_query(SessionStates.choosing_count, F.data.in_(["count_all", "count_100", "count_50"]))
async def choose_count(call: CallbackQuery, state: FSMContext):
    total = await get_words_count()
    count_map = {
        "count_all": total,
        "count_100": 100,
        "count_50": 50,
    }
    count = count_map[call.data]
    count = min(count, total)
    await state.update_data(count=count)
    await call.answer()
    await launch_session(call, state)


@router.callback_query(SessionStates.choosing_count, F.data == "count_custom")
async def choose_custom(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("✏️ Введи количество слов цифрой:")
    await state.set_state(SessionStates.choosing_custom_count)
    await call.answer()


@router.message(SessionStates.choosing_custom_count)
async def handle_custom_count(message: Message, state: FSMContext):
    total = await get_words_count()
    try:
        count = int(message.text.strip())
        if count <= 0:
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Введи целое число больше 0:")
        return

    if count > total:
        await message.answer(f"⚠️ В словаре только {total} слов. Беру все!")
        count = total

    await state.update_data(count=count)
    await launch_session(message, state)


async def launch_session(target, state: FSMContext):
    data = await state.get_data()
    count = data["count"]
    direction = data["direction"]

    words = await get_random_words(count)
    session_id = await create_session(direction, count)

    await state.update_data(
        words=words,
        current_index=0,
        correct=0,
        wrong=0,
        errors=[],
        session_id=session_id
    )
    await state.set_state(SessionStates.answering)
    await send_word(target, state)


async def send_word(target, state: FSMContext):
    data = await state.get_data()
    words = data["words"]
    index = data["current_index"]
    direction = data["direction"]
    total = len(words)

    word = words[index]
    if direction == "dir_es_ru":
        question = word["spanish"]
    else:
        question = word["russian"]

    text = (
        f"🃏 Слово <b>{index + 1}</b> из <b>{total}</b>\n\n"
        f"<b>{question}</b>\n\n"
        f"Напиши перевод:"
    )

    if isinstance(target, Message):
        await target.answer(text, parse_mode="HTML", reply_markup=session_stop_kb())
    elif isinstance(target, CallbackQuery):
        await target.message.edit_text(text, parse_mode="HTML", reply_markup=session_stop_kb())


@router.message(SessionStates.answering)
async def handle_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    words = data["words"]
    index = data["current_index"]
    direction = data["direction"]
    correct_count = data["correct"]
    wrong_count = data["wrong"]
    errors = data["errors"]

    word = words[index]
    if direction == "dir_es_ru":
        correct_answer = word["russian"]
    else:
        correct_answer = word["spanish"]

    user_answer = message.text.strip().lower()
    correct_normalized = correct_answer.strip().lower()

    # Проверяем точное совпадение или через запятую
    user_variants = [v.strip() for v in user_answer.split(",")]
    exact_match = correct_normalized in user_variants

    # Проверяем опечатки (расстояние Левенштейна <= 2)
    fuzzy_match = any(
        Levenshtein.distance(v, correct_normalized) <= 2
        for v in user_variants
    )

    if exact_match:
        correct_count += 1
        await update_word_stats(word["id"], correct=True)
        response = f"✅ Правильно! +1"
    elif fuzzy_match:
        correct_count += 1
        await update_word_stats(word["id"], correct=True)
        response = f"⚠️ Почти верно! Правильно: <b>{correct_answer}</b> +1"
    else:
        wrong_count += 1
        errors.append(word)
        await update_word_stats(word["id"], correct=False)
        response = f"❌ Неверно.\nПравильный ответ: <b>{correct_answer}</b>"

    index += 1
    await state.update_data(
        current_index=index,
        correct=correct_count,
        wrong=wrong_count,
        errors=errors
    )

    # Если слова закончились
    if index >= len(words):
        await message.answer(response, parse_mode="HTML")
        await show_results(message, state)
        return

    await message.answer(response, parse_mode="HTML", reply_markup=session_stop_kb())
    await send_word(message, state)


@router.callback_query(SessionStates.answering, F.data == "stop_session")
async def stop_session(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await show_results(call.message, state)


async def show_results(target: Message, state: FSMContext):
    data = await state.get_data()
    correct = data["correct"]
    wrong = data["wrong"]
    errors = data["errors"]
    words = data["words"]
    session_id = data["session_id"]

    passed = correct + wrong
    total = len(words)
    accuracy = round(correct / passed * 100) if passed > 0 else 0

    await finish_session(session_id, correct, wrong)

    text = (
        f"📊 <b>Результаты сессии</b>\n\n"
        f"Слов пройдено: <b>{passed}</b> из <b>{total}</b>\n"
        f"✅ Правильно: <b>{correct}</b>\n"
        f"❌ Неверно: <b>{wrong}</b>\n"
        f"🎯 Точность: <b>{accuracy}%</b>"
    )

    await target.answer(
        text,
        parse_mode="HTML",
        reply_markup=after_session_kb(has_errors=len(errors) > 0)
    )
    await state.clear()


@router.callback_query(F.data == "retry_errors")
async def retry_errors(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    errors = data.get("errors", [])
    direction = data.get("direction", "dir_es_ru")

    if not errors:
        await call.answer("Ошибок нет!")
        return

    session_id = await create_session(direction, len(errors))
    await state.update_data(
        words=errors,
        current_index=0,
        correct=0,
        wrong=0,
        errors=[],
        session_id=session_id
    )
    await state.set_state(SessionStates.answering)
    await call.answer()
    await send_word(call, state)
