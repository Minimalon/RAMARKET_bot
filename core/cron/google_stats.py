from core.cron.Spreadsheet import Spreadsheet
import asyncio
from datetime import datetime
from core.database.query_db import get_history_orders_for_googleSheet


async def update_google_sheets(path):
    """
    Asynchronously updates a Google Sheets document with sales data.

    Args:
        path (str): The path to the Google Sheets document.

    Returns:
        None
    """
    # Create an instance of the Spreadsheet class
    ss = Spreadsheet(path, 'sales', spreadsheetId='1dWAQdnsfXoebDNegKL6kNE77OgwOIP0Df87o4DlhF7s')

    # Get the last row in column A of the spreadsheet
    last_row = ss.get_last_cell_in_column('A')

    # Get the history orders for the Google Sheet
    orders = await get_history_orders_for_googleSheet(last_row - 1)

    # Iterate over the orders and update the spreadsheet
    for count, order in enumerate(orders, start=last_row + 1):
        # Convert the order to a list
        order = list(order)

        # Format the first element of the order as a datetime string
        order[0] = datetime.strftime(order[0], "%Y-%m-%d %H:%M")

        # Prepare to set the values in the spreadsheet
        ss.prepare_setValues(f"A{count}:O{count}", [order])

        # Run the prepared values every 50 orders
        if count % 50 == 0:
            ss.runPrepared()

    # Run the prepared values at the end
    ss.runPrepared()

if __name__ == '__main__':
    asyncio.run(update_google_sheets('pythonapp.json'))
