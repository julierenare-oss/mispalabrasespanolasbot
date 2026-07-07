from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart

from keyboards import main_menu_kb

router = Router()


async def send_main_menu(target, text="👋 Главное меню:"):
    kb = main_menu_kb()
    if isinstance(target, Message):
        await target.answer(text, reply_markup=kb)
    elif isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=kb)
        await target.answer()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await send_main_menu(message, "👋 Привет! Я помогу тебе учить испанские слова.\n\nГлавное меню:")


@router.callback_query(F.data == "menu")
async def callback_menu(call: CallbackQuery):
    await send_main_menu(call)
