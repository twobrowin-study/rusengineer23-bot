from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from spreadsheetbot.sheets.users import UsersAdapterClass
from spreadsheetbot.sheets.settings import Settings
from spreadsheetbot.sheets.registration import Registration
from spreadsheetbot.sheets.settings import Settings
from spreadsheetbot.sheets.i18n import I18n
from spreadsheetbot.sheets.groups import Groups
from spreadsheetbot.sheets.report import Report
from spreadsheetbot.sheets.keyboard import Keyboard

async def proceed_registration_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        accredetation_code = Settings.accreditation_code_template.format(user=user)
        registration_complete = Settings.registration_complete.format(accredetation_code=accredetation_code)
        await update.message.reply_markdown(registration_complete, reply_markup=Keyboard.reply_keyboard)
        await self._batch_update_or_create_record(update.effective_chat.id, **{
            'accredetation_code': accredetation_code,
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