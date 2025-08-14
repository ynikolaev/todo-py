from __future__ import annotations

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router(name=__name__)


class ProfileStates(StatesGroup):
    waiting_for_name = State()


@router.message(Command("profile"))
async def cmd_profile(message: types.Message, state: FSMContext) -> None:
    await state.set_state(ProfileStates.waiting_for_name)
    await message.answer(
        "Let's set your display name.\nPlease type your name (or /cancel to stop)."
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()

    allowed_prefixes = ("ProfileStates:", "TaskStates:")

    if current_state and current_state.startswith(allowed_prefixes):
        await state.clear()
        await message.answer("Cancelled. Nothing was changed.")
    else:
        await message.answer(
            "You are not in a profile setup state. Use /profile to start."
        )


@router.message(ProfileStates.waiting_for_name, F.text & ~F.via_bot)
async def got_name(message: types.Message, state: FSMContext) -> None:
    """
    Receives the name, saves it into FSM data (for the tutorial),
    and completes the flow.
    """
    if not message.text or message.text.strip() == "":
        await message.answer("Name cannot be empty. Please try again or /cancel.")
        return

    name = message.text.strip()
    await state.update_data(display_name=name)
    await state.clear()  # end FSM

    await message.answer(f"✅ Saved! Your display name is: <b>{name}</b>")


@router.message(ProfileStates.waiting_for_name)
async def name_required(message: types.Message) -> None:
    await message.answer("Please send just your name text (or /cancel).")
