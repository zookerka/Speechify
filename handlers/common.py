from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.filters import ExceptionTypeFilter
from aiogram.types import ErrorEvent

from boto3 import client
import os
from datetime import datetime

import langid
from googletrans import Translator


from core.config import ACCESS_KEY, SECRET_ACCESS_KEY, REGION_NAME, LANGUAGE_MAP, ENG_VOICE_ACTORS
from states.lang_states import TTSTextState
from keyboards.reply_kb import (
    reply_settings,
    reply_yes_or_no,
    reply_user_menu,
    reply_back,
    reply_translation_languages,
    reply_text_to_speech,
)
from keyboards.inline_kb import inline_voice_actors

from db.crud import get_voice_actor, update_voice_actor
from db.connection import async_session
from core.logger import logger


# ----------------------------------------------------------General variables----------------------------------------------------------

router = Router()
translator = Translator()


# ----------------------------------------------------------Custom Exceptions----------------------------------------------------------


class LanguageError(Exception):
    """Raised when an language error occurs in text-to-speech processing. e.g. wrong language"""
    pass


class UnexpectedError(Exception):
    """Raised when an unexpected error occurs."""
    pass

# ---------------------------------------------------------Exception Handlers---------------------------------------------------------


@router.error(ExceptionTypeFilter(LanguageError), F.update.message.as_("message"))
async def handle_language_error(event: ErrorEvent, message: Message, state: FSMContext):
    logger.error(f"LanguageError encountered: {event}")
    await message.answer("I can't understand this language, please write on language that you have chosen >_<",
                         reply_markup=await reply_back())
    await state.set_state(TTSTextState.text)


@router.error(ExceptionTypeFilter(UnexpectedError), F.update.message.as_("message"))
async def handle_unexpected_error(event: ErrorEvent, message: Message, state: FSMContext):
    logger.error(f"UnexpectedError encountered: {event}")
    await message.answer(
        "An unexpected error has occurred X_X. "
        "We apologize for it and will fix it as soon as possible.",
        reply_markup=await reply_back()
    )
    print(event)
    await state.set_state(TTSTextState.text)

# ----------------------------------------------------------General functions----------------------------------------------------------


async def translate_from_one_language_to_another(text: str, languages: list[str]) -> str:
    """
    Translate text from one language to another if the language matches the expected input.

    This function first detects the language of the provided text. If the detected language
    matches the expected source language, it translates the text to the target language
    using the specified translation service.

    Args:
        text (str): The text to be translated.
        languages (list[str]): A list with the source language code at index 0
            and the target language code at index 1.

    Returns:
        str: The translated text.

    Raises:
        LanguageError: If the detected language does not match the expected source language.
        UnexpectedError: If an unexpected error occurs during language detection or translation.
    """
    try:
        logger.info(f"Attempting to translate text: '{text}' from {languages[0]} to {languages[1]}")
        detected_language, _ = langid.classify(text)
        if detected_language != languages[0]:
            logger.error(f"Language mismatch. Expected {languages[0]}, but got {detected_language}.")
            raise LanguageError(f"Incorrect language selected. Expected {languages[0]}, but got {detected_language}.")

        translated = translator.translate(text, src=languages[0], dest=languages[1])
        logger.info(f"Translation successful: {translated.text}")
        return translated.text
    except LanguageError as e:
        logger.error(f"Language error: {e}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise UnexpectedError(f"An unexpected error occurred: {e}")


async def text_to_speech(text: str, voice_actor: str) -> str:
    """
    Convert input text to speech using AWS Polly and save it as an MP3 file.

    This function connects to the AWS Polly service to synthesize speech
    from the provided text using the specified voice actor. The generated
    MP3 file is saved in an 'audios' directory with a timestamped filename.

    Args:
        text (str): The text to be converted to speech.
        voice_actor (str): The voice actor ID used by AWS Polly.

    Returns:
        str: The file path to the generated MP3 audio file.

    Raises:
        UnexpectedError: If an unexpected error occurs during the
        text-to-speech process or file handling.
    """
    try:
        logger.info(f"Converting text to speech for voice actor {voice_actor}: {text[:50]}...")
        polly_client = client(
            'polly',
            region_name=REGION_NAME,
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_ACCESS_KEY
        )

        # Declare file path and create directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file_name = f"speech_{timestamp}.mp3"
        output_directory = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'audios')
        os.makedirs(output_directory, exist_ok=True)
        output_file = os.path.join(output_directory, output_file_name)

        response = polly_client.synthesize_speech(
            Text=text,
            OutputFormat='mp3',
            VoiceId=voice_actor
        )
        if 'AudioStream' in response:
            with open(output_file, 'wb') as file:
                file.write(response['AudioStream'].read())

        logger.info(f"Audio file saved: {output_file}")
        return output_file
    except Exception as e:
        logger.error(f"Unexpected error during TTS process: {e}")
        raise UnexpectedError(f"An unexpected error occurred: {e}")

# ----------------------------------------------------------Settings-----------------------------------------------------------------


@router.message(F.text == "Settings")
async def settings(message: Message):
    """
    Handle the 'Settings' command, displaying options to change the voice actor.

    Args:
        message (Message): The message object from the user.
    Raises:
        UnexpectedError: If an unexpected error occurs during the handling of the message.
    """
    try:
        logger.info(f"User {message.from_user.id} requested settings.")
        await message.answer("Here you can change your voice actor", reply_markup=await reply_settings())
    except Exception as e:
        logger.error(f"Unexpected error in settings handler: {e}")
        raise UnexpectedError(f"An unexpected error occurred in the settings handler: {e}")


@router.message(F.text == "Change voice actor")
async def change_voice_actor(message: Message):
    """
    Handle the 'Change voice actor' command, prompting the user to select a new voice actor.

    Args:
        message (Message): The message object from the user.
    Raises:
        UnexpectedError: If an unexpected error occurs during the handling of the message.
    """
    try:
        logger.info(f"User {message.from_user.id} requested to change voice actor.")
        await message.answer("Now choose your voice actor", reply_markup=await inline_voice_actors())
    except Exception as e:
        logger.error(f"Unexpected error in change_voice_actor handler: {e}")
        raise UnexpectedError(f"An unexpected error occurred in the change_voice_actor handler: {e}")


@router.callback_query(F.data.in_(ENG_VOICE_ACTORS))
async def process_callback_button_settings(callback_query: CallbackQuery):
    """
    Process the callback query for selecting a voice actor, updating the user's preference.

    This function responds to a callback query when a user selects a voice actor from the
    inline keyboard. The selected voice actor is saved to the database, and a confirmation
    message is sent to the user.

    Args:
        callback_query (CallbackQuery): The callback query object triggered by the user.

    Raises:
        UnexpectedError: If an unexpected error occurs during the handling of the callback.
    """
    try:
        chosen_voice = callback_query.data
        user_id = callback_query.from_user.id
        logger.info(f"User {user_id} selected voice actor: {chosen_voice}")

        if chosen_voice not in ENG_VOICE_ACTORS:
            await callback_query.message.answer("Please select a valid voice actor.", reply_markup=await inline_voice_actors())
            return

        # Remove inline keyboard
        await callback_query.message.edit_reply_markup(reply_markup=None)

        async with async_session() as session:
            await update_voice_actor(session, user_id, new_voice_actor=chosen_voice)

        await callback_query.message.answer(f"You have chosen: {chosen_voice}", reply_markup=await reply_back())
    except Exception as e:
        logger.error(f"Unexpected error in process_callback_button_settings: {e}")
        raise UnexpectedError(f"An unexpected error occurred in the process_callback_button handler: {e}")

# ----------------------------------------------------------TTS Handlers-------------------------------------------------------------


@router.message(F.text == '⬅️ Main menu')
async def back_handler(message: Message, state: FSMContext):
    """
    Handle the 'Main menu' command, navigating the user back to the main menu.

    This function responds to the '⬅️ Main menu' command, displays the main menu options,
    and clears the user's current state in the finite state machine (FSM).

    Args:
        message (Message): The message object from the user.
        state (FSMContext): The finite state machine context for managing user states.

    Raises:
        UnexpectedError: If an unexpected error occurs during the handling of the message.
    """
    try:
        logger.info(f"User {message.from_user.id} requested the main menu.")
        await message.answer("Main menu", reply_markup=await reply_user_menu())
        await state.clear()
    except Exception as e:
        logger.error(f"Unexpected error in back_handler: {e}")
        raise UnexpectedError(f"An unexpected error occurred in the back_handler: {e}")


@router.message(F.text == 'Synthesize text into voice')
async def text_to_speech_handler(message: Message):
    """
    Handle the "Synthesize text into voice" command.

    If the user has selected a voice actor, prompts them to confirm if they want to
    translate their text before converting it to speech. If no voice actor is selected,
    prompts the user to select one first.

    Args:
        message (Message): Incoming Telegram message object.

    Raises:
        UnexpectedError: If an unexpected error occurs during the handling of the message.
    """
    try:
        logger.info(f"User {message.from_user.id} triggered Text to Speech.")
        user_id = message.from_user.id
        async with async_session() as session:
            voice_act = await get_voice_actor(session, user_id)
        if voice_act:
            await message.answer("Do you want to translate your speech?", reply_markup=await reply_yes_or_no())
        else:
            await message.answer(
                "First of all, you need to select a voice actor. After that, you can change it in Settings",
                reply_markup=await inline_voice_actors()
            )
    except Exception as e:
        logger.error(f"Unexpected error in text_to_speech_handler: {e}")
        raise UnexpectedError(f"An unexpected error occurred in text_to_speech_handler: {e}")


@router.callback_query(F.data.in_(ENG_VOICE_ACTORS))
async def process_callback_button(callback_query: CallbackQuery, message: Message):
    """
    Process the voice actor selection callback query.

    After the user selects a voice actor, acknowledges their choice and asks if
    they want to translate their text before converting it to speech.

    Args:
        callback_query (CallbackQuery): Incoming callback query object from Telegram.

    Raises:
        UnexpectedError: If an unexpected error occurs during the handling of the callback query.
    """
    try:
        logger.info(f"User {callback_query.from_user.id} selected voice actor: {callback_query.data}")
        chosen_voice = callback_query.data
        user_id = callback_query.from_user.id

        if chosen_voice not in ENG_VOICE_ACTORS:
            message.answer("Please select valid voice actor.", reply_markup=await inline_voice_actors())
            return

        # Removes inline keyboard
        await callback_query.message.edit_reply_markup(reply_markup=None)

        async with async_session() as session:
            await update_voice_actor(session, user_id, new_voice_actor=chosen_voice)
        await callback_query.message.answer("Great choice! Now, do you want to translate your text?",
                                            reply_markup=await reply_yes_or_no())
    except Exception as e:
        logger.error(f"Unexpected error in process_callback_button: {e}")
        raise UnexpectedError(f"An unexpected error occurred in the process_callback_button handler: {e}")


@router.message(F.text == 'No')
async def without_translation_handler(message: Message, state: FSMContext):
    """
    Handle the "No" response for translation.

    If the user does not want to translate their text, prompts them to enter
    the text they want to convert to speech.

    Args:
        message (Message): Incoming Telegram message object.
        state (FSMContext): The finite state machine context for managing user states.

    Raises:
        UnexpectedError: If an unexpected error occurs during the handling of the message.
    """
    try:
        logger.info(f"User {message.from_user.id} chose 'No' for translation.")
        await message.answer('Now type the text for speech conversion!', reply_markup=await reply_back())
        await state.set_state(TTSTextState.text)
    except Exception as e:
        logger.error(f"Unexpected error in without_translation_handler: {e}")
        raise UnexpectedError(f"An unexpected error occurred in without_translation_handler: {e}")


@router.message(F.text == 'Yes')
async def with_translation_handler(message: Message, state: FSMContext):
    """
    Handle the "Yes" response for translation.

    Prompts the user to select a language for translation.

    Args:
        message (Message): Incoming Telegram message object.

    Raises:
        UnexpectedError: If an unexpected error occurs during the handling of the message.
    """
    try:
        logger.info(f"User {message.from_user.id} chose 'Yes' for translation.")
        await message.answer('Select the language you want to translate <i>from</i>',
                             reply_markup=await reply_translation_languages(),
                             parse_mode='HTML')
        await state.set_state(TTSTextState.selected_languages.state)
        await state.update_data(selected_languages=[])

    except Exception as e:
        logger.error(f"Unexpected error in with_translation_handler: {e}")
        raise UnexpectedError(f"An unexpected error occurred in with_translation_handler: {e}")


@router.message(TTSTextState.selected_languages)
async def process_language_selection(message: Message, state: FSMContext):
    """
    Process the language selection from the user.

    Args:
        message (Message): Incoming message with selected language.
        state (FSMContext): The FSM context used to store selected languages.
    """
    try:
        selected_language = message.text

        if selected_language not in LANGUAGE_MAP:
            print(selected_language)
            print(LANGUAGE_MAP)
            await message.answer("Please select a valid language.", reply_markup=await reply_translation_languages())
            return

        language_code = LANGUAGE_MAP[selected_language]

        current_state = await state.get_data()
        selected_languages = current_state['selected_languages']
        selected_languages.append(language_code)

        await state.update_data(selected_languages=selected_languages)
        if len(selected_languages) == 1:
            await message.answer('Now, select the language to translate <i>into</i>',
                                 reply_markup=await reply_translation_languages(exclude_language=selected_language),
                                 parse_mode="HTML")
        else:
            await message.answer("Now type text for speech conversion", reply_markup=await reply_back())
            await state.set_state(TTSTextState.text)
    except Exception as e:
        logger.error(f"Unexpected error in language_translation_handler_en_to_ru: {e}")
        raise UnexpectedError(f"An unexpected error occurred in language_translation_handler_en_to_ru: {e}")


@router.message(F.text == 'From english to russian')
async def language_translation_handler_en_to_ru(message: Message, state: FSMContext):
    """
    Handle the "From English to Russian" translation command.

    Sets the source language to English and the target language to Russian, then prompts
    the user to enter text for speech conversion.

    Args:
        message (Message): Incoming Telegram message object.
        state (FSMContext): The finite state machine context for managing user states.

    Raises:
        UnexpectedError: If an unexpected error occurs during the handling of the message.
    """
    try:
        logger.info(f"User {message.from_user.id} selected 'From English to Russian' translation.")
        languages = ['en', 'ru']
        await state.update_data(selected_languages=languages)
        await message.answer('Now type text for speech conversion', reply_markup=await reply_back())
        await state.set_state(TTSTextState.text)
    except Exception as e:
        logger.error(f"Unexpected error in language_translation_handler_en_to_ru: {e}")
        raise UnexpectedError(f"An unexpected error occurred in language_translation_handler_en_to_ru: {e}")


@router.message(F.text == 'From russian to english')
async def language_translation_handler_ru_to_en(message: Message, state: FSMContext):
    """
    Handle the "From Russian to English" translation command.

    Sets the source language to Russian and the target language to English, then prompts
    the user to enter text for speech conversion.

    Args:
        message (Message): Incoming Telegram message object.
        state (FSMContext): The finite state machine context for managing user states.

    Raises:
        UnexpectedError: If an unexpected error occurs during the handling of the message.
    """
    try:
        logger.info(f"User {message.from_user.id} selected 'From Russian to English' translation.")
        languages = ['ru', 'en']
        await state.update_data(selected_languages=languages)
        await message.answer('Now type text for speech conversion', reply_markup=await reply_back())
        await state.set_state(TTSTextState.text)
    except Exception as e:
        logger.error(f"Unexpected error in language_translation_handler_ru_to_en: {e}")
        raise UnexpectedError(f"An unexpected error occurred in language_translation_handler_ru_to_en: {e}")

# --------------------------------------------------------------TTS State--------------------------------------------------------------


@router.message(F.text == 'Convert it', TTSTextState.text)
async def convert_text_to_speech(message: Message, state: FSMContext):
    """
    Handle the "Convert it" command to convert the accumulated text to speech.

    Retrieves user data from the state, including text and selected languages. If translation
    is needed, the text is translated before converting to speech. The resulting audio is sent
    back to the user as a voice message.

    Args:
        message (Message): Incoming Telegram message object.
        state (FSMContext): The finite state machine context for managing user states.

    Raises:
        UnexpectedError: If an unexpected error occurs during the handling of the message.
    """
    try:
        logger.info(f"User {message.from_user.id} triggered 'Convert it' for TTS.")
        user_id = message.from_user.id
        data = await state.get_data()
        full_text = data.get("text", "")

        if not full_text:
            await message.answer("There is nothing to convert")
            return

        async with async_session() as session:
            voice_actor = await get_voice_actor(session, user_id)

        languages = data.get("selected_languages", [])
        if languages:
            full_text = await translate_from_one_language_to_another(full_text, languages)
            if languages[1] == 'ru':
                voice_actor = 'Tatyana'

        voice_file_path = await text_to_speech(full_text, voice_actor)
        voice_file = FSInputFile(voice_file_path)
        await message.answer_voice(voice=voice_file, reply_markup=await reply_back())
    except LanguageError as e:
        logger.error(f"Language error in convert_text_to_speech: {e}")
        raise LanguageError(f"Language error, {e}")
    except Exception as e:
        logger.error(f"Unexpected error in convert_text_to_speech: {e}")
        raise UnexpectedError(f"An unexpected error occurred in convert_text_to_speech: {e}")
    finally:
        await state.clear()


@router.message(TTSTextState.text)
async def text_for_speech_handler(message: Message, state: FSMContext):
    """
    Collect text for speech conversion.

    Verifies that the text is in the expected language and appends it to any previously collected
    text. Prompts the user to add more text or press "Convert it" when ready for conversion.

    Args:
        message (Message): Incoming Telegram message object.
        state (FSMContext): The finite state machine context for managing user states.

    Raises:
        LanguageError: If the detected language of the text does not match the expected language.
        UnexpectedError: If an unexpected error occurs during the handling of the message.
    """
    try:
        logger.info(f"User {message.from_user.id} is adding text for speech conversion.")
        data = await state.get_data()
        languages = data.get("selected_languages", [])
        previous_text = data.get("text", "")
        new_text = message.text

        detected_language, _ = langid.classify(new_text)
        if languages and detected_language != languages[0]:
            raise LanguageError(f"Incorrect language selected. Expected {languages[0]}, but got {detected_language}.")

        updated_text = previous_text + (" " if previous_text else "") + new_text
        await state.update_data(text=updated_text)

        await message.answer(
            "If you want to add more text, you can just type it in. "
            "When you are ready, press 'Convert it' to convert the text to speech.",
            reply_markup=await reply_text_to_speech()
        )
    except LanguageError as e:
        logger.error(f"Language error in text_for_speech_handler: {e}")
        raise LanguageError(f"Language error, {e}")
    except Exception as e:
        logger.error(f"Unexpected error in text_for_speech_handler: {e}")
        raise UnexpectedError(f"An unexpected error occurred in text_for_speech_handler: {e}")

# -----------------------------------------------------------------------------------------------------------------------------------


@router.message()
async def handle_unknown_message(message: Message):
    """
    Handle unknown messages.
    """
    try:
        logger.warning(f"User {message.from_user.id} sent an unknown message.")
        await message.answer("I can't understand you. =(", reply_markup=await reply_back())
    except Exception as e:
        logger.error(f"Unexpected error in handle_unknown_message: {e}")
        await message.answer("An unexpected error occurred, please try again later.")
