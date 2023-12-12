from core.cron.Spreadsheet import Spreadsheet
import asyncio
from datetime import datetime
from core.database.query_db import get_history_orders_for_googleSheet


async def update_google_sheets(path):
    ss = Spreadsheet(path, 'sales', spreadsheetId='1dWAQdnsfXoebDNegKL6kNE77OgwOIP0Df87o4DlhF7s')
    last_row = ss.get_last_cell_in_column('A')
    orders = await get_history_orders_for_googleSheet(last_row - 1)
    for count, order in enumerate(orders, start=last_row + 1):
        order = list(order)
        order[0] = datetime.strftime(order[0], "%Y-%m-%d %H:%M")
        ss.prepare_setValues(f"A{count}:O{count}",[order])
        if count % 50 == 0:
            ss.runPrepared()
    ss.runPrepared()

if __name__ == '__main__':
    asyncio.run(update_google_sheets('pythonapp.json'))
