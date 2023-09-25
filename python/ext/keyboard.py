from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

import pandas as pd

from spreadsheetbot.sheets.keyboard import KeyboardAdapterClass
from spreadsheetbot.sheets.replysheet import ReplySheet
from spreadsheetbot.sheets.settings import Settings

from spreadsheetbot.sheets.i18n import I18n

KeyboardAdapterClass.CALLBACK_ALL_EVENTS_UNREGISTER_START = 'all_events_unreg_start'

KeyboardAdapterClass.CALLBACK_EVENT_UNREGISTER_PREFIX   = 'event_unregister_'
KeyboardAdapterClass.CALLBACK_EVENT_UNREGISTER_TEMPLATE = 'event_unregister_{state}'
KeyboardAdapterClass.CALLBACK_EVENT_UNREGISTER_PATTERN  = 'event_unregister_.*'

KeyboardAdapterClass.default_pre_async_init = KeyboardAdapterClass._pre_async_init
async def _pre_async_init(self: KeyboardAdapterClass):
    await self.default_pre_async_init()
    self.QR_CODE_FUNCTION          = I18n.qr_code
    self.EVENT_LIST_FUNCTION       = I18n.event_list
    self.BACK_FUNCTION             = I18n.back
    self.ALL_MY_EVENTS_FUNCTION    = I18n.all_my_events
    self.PROGRAM_DOWNLOAD_KEY      = I18n.program_download
    self.PROGRAM_DOWNLOAD_FUNCTION = I18n.program_download
KeyboardAdapterClass._pre_async_init = _pre_async_init

async def _get_df(self) -> pd.DataFrame:
    df = pd.DataFrame(await self.wks.get_all_records())
    df = df.drop(index = 0, axis = 0)
    df = self.reply_buttons_split(df)
    df = df.loc[
        (df.key != "") &
        (df.is_active == I18n.yes)
    ]
    return df
KeyboardAdapterClass._get_df = _get_df

def _create_keyboard_markup_from_keys(self: KeyboardAdapterClass, keys: list[str], append_back_key = False) -> ReplyKeyboardMarkup:
    arr = [
        keys[idx:idx+2]
        for idx in range(0,len(keys),2)
    ] if len(keys) > 2 else [[x] for x in keys]
    if append_back_key:
        arr.append([self.back_keyboard_row.key])
    return ReplyKeyboardMarkup(arr)
KeyboardAdapterClass._create_keyboard_markup_from_keys = _create_keyboard_markup_from_keys

async def _process_df_update(self: KeyboardAdapterClass):
    await ReplySheet._process_df_update(self)
    self.keys = self.as_df.key.values.tolist()

    base_keys = self.as_df.loc[
        self.as_df.function.isin([
            self.REGISTER_FUNCTION,
            self.QR_CODE_FUNCTION,
            self.EVENT_LIST_FUNCTION,
            self.ALL_MY_EVENTS_FUNCTION,
            self.PROGRAM_DOWNLOAD_FUNCTION
        ])
    ].key.values.tolist()
    self.reply_keyboard = self._create_keyboard_markup_from_keys(base_keys)
    
    self.registration_keyboard_row = self._get(self.as_df.function == self.REGISTER_FUNCTION)
    self.back_keyboard_row = self._get(self.as_df.function == self.BACK_FUNCTION)
KeyboardAdapterClass._process_df_update = _process_df_update

def get_reply_keyboard_by_function(self: KeyboardAdapterClass, function: str) -> list[str]:
    keys = self.as_df.loc[self.as_df.function == function].key.values.tolist()
    return self._create_keyboard_markup_from_keys(keys, append_back_key = True)
KeyboardAdapterClass.get_reply_keyboard_by_function = get_reply_keyboard_by_function

def reply_buttons_split(self: KeyboardAdapterClass, df) -> pd.DataFrame:
    return df
KeyboardAdapterClass.reply_buttons_split = reply_buttons_split

def get_inline_keyboard_by_state(self: KeyboardAdapterClass, state: str) -> InlineKeyboardMarkup|None:
    key = self.get_by_state(state)
    button_text = key.button_text
    key_index = key.name
    return InlineKeyboardMarkup.from_button(
        InlineKeyboardButton(
            button_text,
            callback_data=self.CALLBACK_ANSWER_TEMPLATE.format(state=key_index, answer=0)
        )
    )
KeyboardAdapterClass.get_inline_keyboard_by_state = get_inline_keyboard_by_state

def get_button_answer_by_state(self: KeyboardAdapterClass, state_index: str) -> tuple[str,str,str]:
    key_index = int(state_index)
    row = self.as_df.loc[key_index]
    return row.state, row.button_answer, I18n.yes
KeyboardAdapterClass.get_button_answer_by_state = get_button_answer_by_state

def get_my_events_text_by_state(self: KeyboardAdapterClass, state: str) -> str:
    return self._get(self.as_df.state == state).my_events_text
KeyboardAdapterClass.get_my_events_text_by_state = get_my_events_text_by_state

def get_event_unregister_inline_button(self: KeyboardAdapterClass) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup.from_button(
        InlineKeyboardButton(
            Settings.all_my_events_event_unregister_inline_button_text,
            callback_data=self.CALLBACK_ALL_EVENTS_UNREGISTER_START
        )
    )
KeyboardAdapterClass.get_event_unregister_inline_button = get_event_unregister_inline_button

def get_unregister_inline_keyboard_by_state(self: KeyboardAdapterClass, state: str) -> InlineKeyboardMarkup|None:
    key_index = self.get_by_state(state).name
    return InlineKeyboardMarkup.from_button(
        InlineKeyboardButton(
            Settings.event_unregister_inline_button_text,
            callback_data=self.CALLBACK_EVENT_UNREGISTER_TEMPLATE.format(state=key_index)
        )
    )
KeyboardAdapterClass.get_unregister_inline_keyboard_by_state = get_unregister_inline_keyboard_by_state