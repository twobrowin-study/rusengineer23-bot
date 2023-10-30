import base64, re
from telegram import Update, Message, ReplyKeyboardRemove
from telegram.ext import ContextTypes, Application
from telegram.constants import ParseMode

import pandas as pd

from spreadsheetbot.sheets.abstract import AbstractSheetAdapter
from spreadsheetbot.sheets.users import UsersAdapterClass, Users
from spreadsheetbot.sheets.settings import Settings
from spreadsheetbot.sheets.registration import Registration
from spreadsheetbot.sheets.settings import Settings
from spreadsheetbot.sheets.i18n import I18n
from spreadsheetbot.sheets.groups import Groups
from spreadsheetbot.sheets.report import Report
from spreadsheetbot.sheets.keyboard import Keyboard
from spreadsheetbot.sheets.notifications import Notifications

from ext.qr import Qr

class HasRemoveEventRegistrationStateClass(AbstractSheetAdapter.AbstractFilter):
    def filter(self, message: Message) -> bool:
        df = self.outer_obj.as_df
        return not df.loc[
            (self.outer_obj.selector(message.chat_id)) &
            (df.state == Settings.event_unregister_state)
        ].empty
HasRemoveEventRegistrationStateFilter = Users.IsRegisteredFilter & HasRemoveEventRegistrationStateClass(outer_obj=Users)

def get_state_string_fun(self: UsersAdapterClass, user, state):
    if user[state] == '':
        return I18n.data_empty
    if Registration.is_document_state(state):
        return state
    if Registration.get(state).is_main_question:
        return self.db.get_val(user[state])
    return user[state]
UsersAdapterClass.get_state_string_fun = get_state_string_fun

UsersAdapterClass.default_pre_async_init = UsersAdapterClass._pre_async_init
async def _pre_async_init(self: UsersAdapterClass):
    await self.default_pre_async_init()
    self.get_state_string = self.get_state_string_fun
UsersAdapterClass._pre_async_init = _pre_async_init

async def _process_df_update(self: UsersAdapterClass):
    self.event_registration_columns = [
        col for col in self.as_df.columns
        if col.startswith(Settings.events_registration_column_prefix)
    ]
UsersAdapterClass._process_df_update = _process_df_update

def get_by_accreditation_code(self: UsersAdapterClass, accreditation_code: str) -> pd.Series:
    return self._get(self.as_df.accreditation_code == accreditation_code)
UsersAdapterClass.get_by_accreditation_code = get_by_accreditation_code

def send_notification_to_all_users(self: UsersAdapterClass, app: Application, message: str, parse_mode: str,
                                    send_photo: str = None, state: str = None,
                                    condition: str = None):
    selector = self.selector_condition('is_active')
    if condition not in ['', None]:
        selector = self.selector_condition('is_active') & self.selector_condition(condition)
    self._send_to_all_uids(
        selector,
        app, message, parse_mode,
        send_photo,
        reply_markup=Notifications.get_inline_keyboard_by_state(state)
    )
UsersAdapterClass.send_notification_to_all_users = send_notification_to_all_users

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
        accreditation_number_offseted = user.name - Settings.accreditation_code_offset_one
        if accreditation_number_offseted > Settings.accreditation_code_offset_one_max:
            accreditation_number_offseted = user.name + Settings.accreditation_code_offset_two
        accreditation_code = Settings.accreditation_code_template.format(accreditiation_num=accreditation_number_offseted)
        registration_complete = Settings.registration_complete.format(accreditation_code=accreditation_code)
        await update.message.reply_markdown(registration_complete, reply_markup=Keyboard.reply_keyboard)
        # await update.message.reply_markdown(
        #     Settings.first_event_text_markdown,
        #     reply_markup=Keyboard.get_inline_keyboard_by_state(Settings.first_event_state)
        # )
        await self._batch_update_or_create_record(update.effective_chat.id, **{
            'accreditation_code':   accreditation_code,
            'accreditation_status': I18n.qr_not_accredited
        })
    else:
        await update.message.reply_markdown(registration_next.question, reply_markup=registration_next.reply_keyboard)

    if registration_curr.is_main_question:
        state_val = self.db.add_val(state_val)

    update_vals = {
        state: state_val
    }
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
    
async def change_state_reply_handler(self: UsersAdapterClass, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = self.get(update.effective_chat.id)
    _,state,message_id = re.split(self.USER_CHANGE_STATE_SEPARATORS, user.state)
    save_as = user[Settings.user_document_name_field]
    registration = Registration.get(state)

    state_val, save_to = self._prepare_state_to_save(update.message, registration.document_link)
    if state_val == None:
        await update.message.reply_markdown(registration.question, reply_markup=registration.reply_keyboard)
        return

    await update.message.reply_markdown(
        Settings.user_change_message_reply_template.format(state=state),
        reply_markup=Keyboard.reply_keyboard
    )

    if registration.is_main_question:
        state_val = self.db.add_val(state_val)

    await self._batch_update_or_create_record(update.effective_chat.id, save_to=save_to, save_as=save_as, app=context.application,
        state = '',
        **{
            state: state_val
        }
    )
    await self._change_message_after_callback(update.effective_chat.id, message_id, context.application)
UsersAdapterClass.change_state_reply_handler = change_state_reply_handler

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
        if user.accreditation_status == I18n.qr_not_accredited:
            await update.message.reply_markdown(
                Settings.qr_accreditation_not_yet.format(accreditation_code=accreditation_code)
            )
            return
        
        if user.accreditation_status in [I18n.qr_is_accredited_sent, I18n.qr_is_accredited_not_sent]:
            qr = Qr.get(accreditation_code)
            qr_photo = base64.standard_b64decode(qr.base64)
            await update.message.reply_photo(qr_photo, caption=Settings.qr_code_caption, parse_mode=ParseMode.MARKDOWN)
            return

        if user.accreditation_status == I18n.qr_not_needed:
            await update.message.reply_markdown(
                Settings.qr_accreditation_no_need.format(accreditation_code=accreditation_code)
            )
            return

        await update.message.reply_markdown(
            Settings.qr_accreditation_error.format(accreditation_code=accreditation_code)
        )
        return

    if keyboard_row.function == Keyboard.BACK_FUNCTION:
        await update.message.reply_markdown(
            keyboard_row.text_markdown,
            reply_markup=Keyboard.reply_keyboard
        )
        return

    if keyboard_row.function == Keyboard.EVENT_LIST_FUNCTION:
        reply_keyboard = Keyboard.get_reply_keyboard_by_function(keyboard_row.key)
        await update.message.reply_markdown(
            keyboard_row.text_markdown,
            reply_markup=reply_keyboard
        )
        return

    if keyboard_row.function == Keyboard.ALL_MY_EVENTS_FUNCTION:
        user = self.get(update.message.chat_id)
        my_events = [
            Keyboard.get_my_events_text_by_state(state)
            for state in self.event_registration_columns
            if user[state] == I18n.yes
        ]
        if len(my_events) == 0:
            await update.message.reply_markdown(Settings.all_my_events_list_empty_text)
            return

        my_events_message = keyboard_row.text_markdown.format(template="\n\n".join(my_events))
        my_events_messages = [
            my_events_message[idx:idx+4096]
            for idx in range(0, len(my_events_message), 4096)
        ]

        if len(my_events_messages) > 1:
            for idx in range(1,len(my_events_messages)):
                newline_last_index = my_events_messages[idx-1].rfind("\n\n")
                postfix_of_last_index = my_events_messages[idx-1][newline_last_index:]
                my_events_messages[idx-1] = my_events_messages[idx-1].removesuffix(postfix_of_last_index)
                my_events_messages[idx]   = f"{postfix_of_last_index}{my_events_messages[idx]}"
        
        for idx in range(len(my_events_messages)):
            reply_markup=None
            if idx == len(my_events_messages)-1:
                reply_markup=Keyboard.get_event_unregister_inline_button()
            await update.message.reply_markdown(
                my_events_messages[idx],
                reply_markup=reply_markup
            )
        return
    
    user = self.get(update.effective_chat.id)
    is_registered = False
    reply_markup  = None
    if keyboard_row.state not in [None, '']:
        is_registered = (user[keyboard_row.state] == I18n.yes)
        reply_markup = Keyboard.get_inline_keyboard_by_state(keyboard_row.state)
        if is_registered:
            reply_markup = Keyboard.get_unregister_inline_keyboard_by_state(keyboard_row.state)
    
    if keyboard_row.key.endswith(Keyboard.PROGRAM_DOWNLOAD_KEY) or keyboard_row.function == Keyboard.PROGRAM_DOWNLOAD_KEY:
        if keyboard_row.send_document not in [None, '']:
            await update.message.reply_document(
                keyboard_row.send_document,
                caption=keyboard_row.text_markdown,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            return
        await update.message.reply_markdown(keyboard_row.text_markdown, reply_markup=reply_markup)
        return
    
    await update.message.reply_markdown(
        keyboard_row.text_markdown,
        reply_markup=reply_markup
    )
UsersAdapterClass.keyboard_key_handler = keyboard_key_handler

async def keyboard_answer_callback_handler(self: UsersAdapterClass, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    state_index,_ = update.callback_query.data\
        .removeprefix(Keyboard.CALLBACK_ANSWER_PREFIX)\
        .split(Keyboard.CALLBACK_ANSWER_SEPARATOR)
    state,text,answer = Keyboard.get_button_answer_by_state(state_index)
    await context.bot.send_message(
        update.effective_chat.id,
        text,
        parse_mode=ParseMode.MARKDOWN,
    )
    await update.callback_query.message.edit_reply_markup(Keyboard.get_unregister_inline_keyboard_by_state(state))
    await self._update_record(update.effective_chat.id, state, answer)
UsersAdapterClass.keyboard_answer_callback_handler = keyboard_answer_callback_handler
    
async def notification_answer_callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    state_index,answer_idx = update.callback_query.data\
        .removeprefix(Notifications.CALLBACK_ANSWER_PREFIX)\
        .split(Notifications.CALLBACK_ANSWER_SEPARATOR)
    state,text,answer = Notifications.get_button_answer_by_state(state_index, int(answer_idx))
    await context.bot.send_message(
        update.effective_chat.id,
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=Keyboard.reply_keyboard
    )
    await self._update_record(update.effective_chat.id, state, answer)
UsersAdapterClass.notification_answer_callback_handler = notification_answer_callback_handler
    
async def notification_set_state_callback_handler(self: UsersAdapterClass, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    state_idx = update.callback_query.data.removeprefix(Notifications.CALLBACK_SET_STATE_PREFIX)
    state, text = Notifications.get_button_answer_by_state(state_idx)
    await context.bot.send_message(
        update.effective_chat.id,
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardRemove()
    )
    await self._update_record(update.effective_chat.id, 'state', state)
UsersAdapterClass.notification_set_state_callback_handler = notification_set_state_callback_handler
    
async def my_events_unregister_start_callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()

    user = self.get(update.effective_chat.id)
    my_events_keys = [
        Keyboard.get_by_state(state).key
        for state in self.event_registration_columns
        if user[state] == I18n.yes
    ]

    await context.bot.send_message(
        update.effective_chat.id,
        Settings.event_unregister_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=Keyboard._create_keyboard_markup_from_keys(my_events_keys, append_back_key=True)
    )
    await self._update_record(update.effective_chat.id, 'state', Settings.event_unregister_state)
UsersAdapterClass.my_events_unregister_start_callback_handler = my_events_unregister_start_callback_handler

async def remove_event_registration_key_handler(self: UsersAdapterClass, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard_row = Keyboard.get(update.message.text)
    if keyboard_row.function == Keyboard.BACK_FUNCTION:
        await update.message.reply_markdown(
            keyboard_row.text_markdown,
            reply_markup=Keyboard.reply_keyboard
        )
        await self._update_record(update.effective_chat.id, 'state', '')
        return

    user = self.get(update.effective_chat.id)

    if keyboard_row.state not in user.index.to_list():
        await self.keyboard_key_handler(update, context)
        await self._update_record(update.effective_chat.id, 'state', '')
        return

    is_not_registered = (user[keyboard_row.state] != I18n.yes)
    if is_not_registered:
        reply_markup = Keyboard.get_inline_keyboard_by_state(keyboard_row.state)
        await update.message.reply_markdown(
            keyboard_row.text_markdown,
            reply_markup=reply_markup
        )
        return
    
    reply_markup = Keyboard.get_unregister_inline_keyboard_by_state(keyboard_row.state)
    await update.message.reply_markdown(
        keyboard_row.text_markdown,
        reply_markup=reply_markup
    )
UsersAdapterClass.remove_event_registration_key_handler = remove_event_registration_key_handler
    
async def event_unregister_callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    key_index = update.callback_query.data.removeprefix(Keyboard.CALLBACK_EVENT_UNREGISTER_PREFIX)
    keyboard_row = Keyboard.as_df.loc[int(key_index)]
    state = keyboard_row.state
    event_title = keyboard_row.text_markdown.split('\n')[0]

    await update.callback_query.message.reply_markdown(
        Settings.event_unregister_done_text.format(event_title=event_title)
    )
    await update.callback_query.message.edit_reply_markup(Keyboard.get_inline_keyboard_by_state(state))
    await self._update_record(update.effective_chat.id, state, I18n.no)
UsersAdapterClass.event_unregister_callback_handler = event_unregister_callback_handler