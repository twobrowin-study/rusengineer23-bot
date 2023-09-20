from telegram import ReplyKeyboardMarkup

from spreadsheetbot.sheets.keyboard import KeyboardAdapterClass
from spreadsheetbot.sheets.replysheet import ReplySheet

from spreadsheetbot.sheets.i18n import I18n

KeyboardAdapterClass.default_pre_async_init = KeyboardAdapterClass._pre_async_init
async def _pre_async_init(self: KeyboardAdapterClass):
    await self.default_pre_async_init()
    self.QR_CODE_FUNCTION    = I18n.qr_code
    self.EVENT_LIST_FUNCTION = I18n.event_list
KeyboardAdapterClass._pre_async_init = _pre_async_init

async def _process_df_update(self: ReplyKeyboardMarkup):
    await ReplySheet._process_df_update(self)
    self.keys = self.as_df.loc[
        self.as_df.function.isin([I18n.register, I18n.qr_code, I18n.event_list])
    ].key.values.tolist()
    self.reply_keyboard = ReplyKeyboardMarkup([
        self.keys[idx:idx+2]
        for idx in range(0,len(self.keys),2)
    ] if len(self.keys) > 2 else [[x] for x in self.keys])
    self.registration_keyboard_row = self._get(self.as_df.function == self.REGISTER_FUNCTION)
KeyboardAdapterClass._process_df_update = _process_df_update