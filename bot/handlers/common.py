from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards import main_menu


router = Router()


@router.message(F.text == "❌ Отмена")
async def cancel_handler(
    message: Message,
    state: FSMContext,
):
    await state.clear()

    await message.answer(
        "❌ Действие отменено.",
        reply_markup=main_menu(),
    )