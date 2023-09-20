import os, sys, json, dotenv
from spreadsheetbot import SpreadSheetBot, Log, DEBUG

from telegram.ext import Application

from ext.users import UsersAdapterClass
from ext.keyboard import KeyboardAdapterClass

from ext.qr import Qr
from ext.accreditation import ScheldueAccredidation

if "DOCKER_RUN" in os.environ:
    Log.info("Running in docker environment")
else:
    dotenv.load_dotenv()
    Log.info("Running in dotenv environment")

if len(sys.argv) > 1 and sys.argv[1] in ['debug', '--debug', '-D']:
    Log.setLevel(DEBUG)
    Log.debug("Starting in debug mode")

BOT_TOKEN            = os.environ.get('BOT_TOKEN')
SHEETS_ACC_JSON      = json.loads(os.environ.get('SHEETS_ACC_JSON'))
SHEETS_LINK          = os.environ.get('SHEETS_LINK')
SWITCH_UPDATE_TIME   = int(os.environ.get('SWITCH_UPDATE_TIME'))
SETTINGS_UPDATE_TIME = int(os.environ.get('SETTINGS_UPDATE_TIME'))

SpreadSheetBot.post_init_default = SpreadSheetBot.post_init
async def post_init(self: SpreadSheetBot, app: Application) -> None:
    await self.post_init_default(app)
    await Qr.async_init(self.sheets_secret, self.sheets_link)
    ScheldueAccredidation(app)
SpreadSheetBot.post_init = post_init

if __name__ == "__main__":
    bot = SpreadSheetBot(
        BOT_TOKEN,
        SHEETS_ACC_JSON,
        SHEETS_LINK,
        SWITCH_UPDATE_TIME,
        SETTINGS_UPDATE_TIME
    )
    bot.run_polling()