import asyncio, base64
from telegram import Bot
from telegram.ext import Application
from telegram.constants import ParseMode

from spreadsheetbot.sheets.settings import Settings
from spreadsheetbot.sheets.users import Users
from spreadsheetbot.sheets.i18n import I18n

from spreadsheetbot.basic.log import Log

from ext.qr import Qr

def ScheldueAccredidation(app: Application) -> None:
    app.create_task(
        _scheldue_and_perform_accredidation(app),
        {
            'action': 'Perform accredatations'
        }
    )

async def _scheldue_and_perform_accredidation(app: Application) -> None:
    await asyncio.sleep(Settings.accreditation_update_time)
    ScheldueAccredidation(app)
    await _perform_accredidation(app)

async def _perform_accredidation(app: Application) -> None:
    bot: Bot = app.bot

    Log.info("Start performing accredidation")

    accredidation_values = await Users.wks.col_values(Settings.accredidation_column_num)
    Log.info("Got whole accredidation column")

    to_accreditate_codes = []
    for num, state in enumerate(accredidation_values[1:]):
        if state == I18n.qr_is_accredited_not_sent:
            accreditation_number_offseted = num - Settings.accreditation_code_offset_one
            if accreditation_number_offseted > Settings.accreditation_code_offset_one_max:
                accreditation_number_offseted = num + Settings.accreditation_code_offset_two
            to_accreditate_codes += [Settings.accreditation_code_template.format(accreditiation_num=accreditation_number_offseted)]

    for accreditation_code in to_accreditate_codes:
        user = Users.get_by_accreditation_code(accreditation_code)
        qr   = Qr.get(accreditation_code)

        chat_id  = user.chat_id
        qr_photo = base64.standard_b64decode(qr.base64)

        await bot.send_photo(chat_id, qr_photo, caption=Settings.qr_code_caption, parse_mode=ParseMode.MARKDOWN)
        await Users._update_record(chat_id, 'accreditation_status', I18n.qr_is_accredited_sent)

        Log.info(f"Sent accredidation message to user {chat_id}")

    Log.info("Done performing accredidation")