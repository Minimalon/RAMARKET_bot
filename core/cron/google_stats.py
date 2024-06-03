import asyncio
import datetime
from datetime import timedelta

import config
from core.cron.Spreadsheet import Spreadsheet
from core.database.model import OrderStatus
from core.database.query_db import get_history_orders_for_googleSheet, select_prepare_delete, delete_history_order


async def update_google_sheets(path):
    def update_phone_format(phone: str):
        if phone is not None:
            if len(phone) == 11:
                if phone.startswith('8'):
                    phone = '7' + phone[1:]
                phone = f'{phone[0:4]}-{phone[4:7]}-{phone[7:9]}-{phone[9:11]}'
            if len(phone) == 10:
                if phone.startswith('9'):
                    phone = '79' + phone[1:]
                phone = f'{phone[0:4]}-{phone[4:7]}-{phone[7:9]}-{phone[9:11]}'
        return phone

    if config.develope_mode:
        ss = Spreadsheet(path, 'test_sales', spreadsheetId='1dWAQdnsfXoebDNegKL6kNE77OgwOIP0Df87o4DlhF7s')
    else:
        ss = Spreadsheet(path, 'sales', spreadsheetId='1dWAQdnsfXoebDNegKL6kNE77OgwOIP0Df87o4DlhF7s')
    last_row = ss.get_last_cell_in_column('A')
    orders = await get_history_orders_for_googleSheet(last_row - 1)
    for count, order in enumerate(orders, start=last_row + 1):
        if order.status in [OrderStatus.sale, OrderStatus.change_date]:
            ss.prepare_setValues(f"A{count}:P{count}",
                                 [
                                     [
                                         (order.date + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M"),
                                         order.order_id,
                                         order.agent_name,
                                         order.country_name,
                                         order.city_name,
                                         order.shop_name,
                                         order.payment_name,
                                         order.product_name,
                                         order.price.replace('.', ','),
                                         order.quantity.replace('.', ','),
                                         order.sum_usd.replace('.', ','),
                                         order.sum_rub.replace('.', ','),
                                         order.currency,
                                         order.currencyPrice.replace('.', ','),
                                         order.client_name,
                                         update_phone_format(order.client_phone)
                                     ],
                                 ])
        else:
            ss.prepare_setValues(f"A{count}:P{count}", ss.empty_row)
        if count % 50 == 0:
            ss.runPrepared()
    ss.runPrepared()
    to_delete = await select_prepare_delete()
    deleted_rows = ss.delete_rows(to_delete)
    for order_id, row_date in deleted_rows:
        await delete_history_order(order_id, row_date)
    #
    # to_change_date = await select_prepare_change_date()
    # for tchd in to_change_date:
    #     if ss.change_date_row(tchd.order_id, tchd.date):
    #         await delete_history_order(tchd.order_id, tchd.date + timedelta(hours=3))


async def get_values(path):
    ss = Spreadsheet(path, 'sales', spreadsheetId='1dWAQdnsfXoebDNegKL6kNE77OgwOIP0Df87o4DlhF7s')
    print(ss.get_value_in_cell('A:P'))


if __name__ == '__main__':
    asyncio.run(update_google_sheets('pythonapp.json'))
    # asyncio.run(get_values('pythonapp.json'))
