import base64
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import pandas as pd

from spreadsheetbot.sheets.users import UsersAdapterClass
from spreadsheetbot.sheets.settings import Settings
from spreadsheetbot.sheets.registration import Registration
from spreadsheetbot.sheets.settings import Settings
from spreadsheetbot.sheets.i18n import I18n
from spreadsheetbot.sheets.groups import Groups
from spreadsheetbot.sheets.report import Report
from spreadsheetbot.sheets.keyboard import Keyboard

from ext.qr import Qr

def get_by_accreditation_code(self: UsersAdapterClass, accreditation_code: str) -> pd.Series:
    return self._get(self.as_df.accreditation_code == accreditation_code)
UsersAdapterClass.get_by_accreditation_code = get_by_accreditation_code

async def proceed_registration_handler(self: UsersAdapterClass, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user    = self.get(update.effective_chat.id)
    state   = user.state
    save_as = user[Settings.user_document_name_field]
    registration_curr = Registration.get(state)
    registration_next = Registration.get_next(state)

    last_main_state = (state == Registration.last_main_state)
    last_state      = (state == Registration.last_state)

    state_val, save_to = self._prepare_state_to_save(update.message, registration_curr.document_link)
    if state_val == None:
        await update.message.reply_markdown(registration_curr.question, reply_markup=registration_curr.reply_keyboard)
        return

    if last_state:
        accreditation_code = Settings.accreditation_code_template.format(accreditiation_num=user.name)
        registration_complete = Settings.registration_complete.format(accreditation_code=accreditation_code)
        await update.message.reply_markdown(registration_complete, reply_markup=Keyboard.reply_keyboard)
        await self._batch_update_or_create_record(update.effective_chat.id, **{
            'accreditation_code': accreditation_code,
            'is_accredited':      I18n.no
        })
    else:
        await update.message.reply_markdown(registration_next.question, reply_markup=registration_next.reply_keyboard)

    update_vals = {state: state_val}
    if last_main_state:
        update_vals['is_active'] = I18n.yes
    
    await self._batch_update_or_create_record(update.effective_chat.id, save_to=save_to, save_as=save_as, app=context.application,
        state = '' if last_state else registration_next.state,
        **update_vals
    )

    count = self.active_user_count()
    if last_main_state and self.should_send_report(count):
        Groups.send_to_all_admin_groups(
            context.application,
            Report.currently_active_users_template.format(count=count),
            ParseMode.MARKDOWN
        )
UsersAdapterClass.proceed_registration_handler = proceed_registration_handler

async def keyboard_key_handler(self: UsersAdapterClass, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard_row = Keyboard.get(update.message.text)
    if keyboard_row.function == Keyboard.REGISTER_FUNCTION:
        user = self._get(self.selector(update.effective_chat.id))
        await update.message.reply_markdown(
            keyboard_row.text_markdown.format(user=self.user_data_markdown(user)),
            reply_markup=self.user_data_inline_keyboard(user)
        )
        return
    
    if keyboard_row.function == Keyboard.QR_CODE_FUNCTION:
        user = self.get(update.message.chat_id)
        accreditation_code = user.accreditation_code
        if user.is_accredited not in [I18n.qr_sent, I18n.yes]:
            await update.message.reply_markdown(
                Settings.qr_accreditation_failure.format(accredetation_code=accreditation_code)
            )
            return
        
        qr = Qr.get(accreditation_code)
        qr_photo = base64.standard_b64decode(qr.base64)
        await update.message.reply_photo(qr_photo, caption=Settings.qr_code_caption, parse_mode=ParseMode.MARKDOWN)

    if keyboard_row.function == Keyboard.EVENT_LIST_FUNCTION:
        await update.message.reply_markdown(
            keyboard_row.text_markdown,
            # reply_markup=reply_keyboard,
            disable_web_page_preview=True
        )
        return
UsersAdapterClass.keyboard_key_handler = keyboard_key_handler