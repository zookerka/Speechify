from aiogram.fsm.state import StatesGroup, State


class TTSTextState(StatesGroup):
    text = State()

    # It's going to be an array with two languages, first is from which user will translate
    # and second is to which language user will translate
    # Example: [ru, en]
    selected_languages = State()
