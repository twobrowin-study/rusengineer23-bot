import pandas as pd
from spreadsheetbot.sheets.abstract import AbstractSheetAdapter

from spreadsheetbot.sheets.i18n import I18n

class QrAdapterClass(AbstractSheetAdapter):
    def __init__(self) -> None:
        super().__init__('qr', 'qr', initialize_as_df=True)
    
    async def _pre_async_init(self):
        self.sheet_name = I18n.qr_codes

    async def _get_df(self) -> pd.DataFrame:
        df = pd.DataFrame(await self.wks.get_all_records())
        df = df.drop(index = 0, axis = 0)
        return df

Qr = QrAdapterClass()