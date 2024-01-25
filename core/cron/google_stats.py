import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import config
from core.cron.Spreadsheet import Spreadsheet
from core.database.query_db import get_history_orders_for_googleSheet, select_prepare_delete, delete_history_order


async def update_google_sheets(path):
    if config.develope_mode:
        ss = Spreadsheet(path, 'test_sales', spreadsheetId='1dWAQdnsfXoebDNegKL6kNE77OgwOIP0Df87o4DlhF7s')
    else:
        ss = Spreadsheet(path, 'sales', spreadsheetId='1dWAQdnsfXoebDNegKL6kNE77OgwOIP0Df87o4DlhF7s')
    last_row = ss.get_last_cell_in_column('A')
    orders = await get_history_orders_for_googleSheet(last_row - 1)
    for count, order in enumerate(orders, start=last_row + 1):
        order = list(order)
        order[0] = datetime.strftime(order[0], "%Y-%m-%d %H:%M")
        ss.prepare_setValues(f"A{count}:P{count}", [order])
        if count % 50 == 0:
            ss.runPrepared()
    ss.runPrepared()

    to_delete = await select_prepare_delete()
    for td in to_delete:
        if ss.delete_row(td.order_id, td.date):
            await delete_history_order(td.order_id, td.date + timedelta(hours=3))




async def get_values(path):
    ss = Spreadsheet(path, 'sales', spreadsheetId='1dWAQdnsfXoebDNegKL6kNE77OgwOIP0Df87o4DlhF7s')
    print(ss.get_value_in_cell('A:P'))


if __name__ == '__main__':
    asyncio.run(update_google_sheets('pythonapp.json'))
    # asyncio.run(get_values('pythonapp.json'))
