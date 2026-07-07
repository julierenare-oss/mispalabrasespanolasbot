from aiogram.fsm.state import State, StatesGroup


class UploadStates(StatesGroup):
    waiting_for_file = State()


class SessionStates(StatesGroup):
    choosing_direction = State()
    choosing_count = State()
    choosing_custom_count = State()
    answering = State()


class SettingsStates(StatesGroup):
    main = State()
    waiting_reminder_times = State()
    confirm_clear = State()
