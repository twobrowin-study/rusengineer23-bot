from spreadsheetbot.sheets.notifications import NotificationsAdapterClass

from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from spreadsheetbot.sheets.keyboard import Keyboard

def get_inline_keyboard_by_state(self: NotificationsAdapterClass, state: str) -> InlineKeyboardMarkup|None:
    key = self.get_by_state(state)
    button_text = key.button_text
    key_index = key.name
    if len(button_text) == 1:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(button_text[0],
                callback_data=self.CALLBACK_SET_STATE_TEMPLATE.format(state=key_index)
            )]
        ])
    if len(button_text) > 1:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(button_text[idx],
                callback_data=self.CALLBACK_ANSWER_TEMPLATE.format(state=key_index, answer=idx)
            )]
            for idx in range(len(button_text))
        ])
    return Keyboard.reply_keyboard
NotificationsAdapterClass.get_inline_keyboard_by_state = get_inline_keyboard_by_state

def get_button_answer_by_state(self: NotificationsAdapterClass, state_index: str, answer_idx: int = None) -> tuple[str,str]|tuple[str,str,str]:
    key_index = int(state_index)
    row = self.as_df.loc[key_index]
    if answer_idx == None:
        return row.state, row.button_answer[0]
    return row.state, row.button_answer[answer_idx], row.button_text[answer_idx]
NotificationsAdapterClass.get_button_answer_by_state = get_button_answer_by_state