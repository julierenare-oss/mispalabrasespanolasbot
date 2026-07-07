from aiogram import Router, F
from aiogram.types import CallbackQuery

from database import get_global_stats, get_hard_words
from keyboards import back_to_menu_kb

router = Router()


@router.callback_query(F.data == "stats")
async def show_stats(call: CallbackQuery):
    stats = await get_global_stats()
    hard_words = await get_hard_words(5)

    total = stats["correct_total"] + stats["wrong_total"]
    accuracy = round(stats["correct_total"] / total * 100) if total > 0 else 0

    text = (
        f"📈 <b>Общая статистика</b>\n\n"
        f"📦 Слов в словаре: <b>{stats['words_total']}</b>\n"
        f"🗓 Сессий проведено: <b>{stats['sessions_total']}</b>\n"
        f"✅ Всего верных: <b>{stats['correct_total']}</b>\n"
        f"❌ Всего неверных: <b>{stats['wrong_total']}</b>\n"
        f"🎯 Точность: <b>{accuracy}%</b>\n"
        f"📅 Последняя сессия: <b>{stats['last_session']}</b>\n"
    )

    if hard_words:
        text += f"\n🔥 <b>Топ сложных слов:</b>\n"
        for i, word in enumerate(hard_words, start=1):
            text += f"  {i}. {word['spanish']} — {word['russian']} (ошибок: {word['wrong_count']})\n"

    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_to_menu_kb())
    await call.answer()
