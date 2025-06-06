from pathlib import Path
from datetime import datetime
import pandas as pd

from core.database.query_db import get_documents_by_agent_id, get_documents_by_shop_id, \
    get_documents_by_shops
import config
from core.database.model import Documents
from typing import Generator


def data_for_df(documents: list[Documents]) -> Generator[dict, None, None]:
    for doc in documents:
        for item in doc.items:
            yield {
                'Дата': doc.date,
                'Номер заказа': doc.order_id,
                'Статус': doc.status.name,
                'Резидент': doc.rezident,
                'Имя агента': doc.agent_name,
                'Страна': doc.country_name,
                'Город': doc.city_name,
                'Название магазина': doc.shop_name,
                'Валюта магазина': doc.shop_currency,
                'Коммисия': doc.tax,
                'Название продукта': item.product_name,
                'Тип оплаты': doc.payment_name,
                'Товар': item.product_name,
                'Цена': item.price,
                'Количество': item.quantity,
                'Сумма USD': doc.sum_usd,
                'Сумма RUB': doc.sum_rub,
                'Сумма TRY': doc.sum_try,
                'Сумма KZT': doc.sum_kzt,
                'Валюта': doc.currency,
                'Цена валюты': doc.currency_price,
                'Клиент': doc.client_name,
                'Телефон': doc.client_phone,
                'Email': doc.client_mail
            }


async def correct_df(df: pd.DataFrame) -> pd.DataFrame:
    df['Дата'] = df['Дата'].dt.tz_localize(None)
    df[['Сумма USD', 'Сумма RUB', 'Сумма TRY', 'Сумма KZT', 'Цена', 'Цена валюты']] = df[
        ['Сумма USD', 'Сумма RUB', 'Сумма TRY', 'Сумма KZT', 'Цена', 'Цена валюты']].astype(float)
    df[['Количество']] = df[['Количество']].astype(int)
    sum_kzt = ((df['Цена'] * df['Количество']) * df['Цена валюты'])
    tax = df['Коммисия'].fillna(0)
    df['Сумма KZT'] = round(sum_kzt * (1 if tax.empty else tax / 100 + 1), 0)
    return df


async def write_to_excel(path_file: Path, df: pd.DataFrame):
    # Записываем данные в Excel с использованием XlsxWriter
    with pd.ExcelWriter(path_file, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name='orders', index=False, na_rep='NaN')

        # Определяем рабочий лист
        worksheet = writer.sheets['orders']

        # Устанавливаем автофильтр на диапазон данных
        max_row, max_col = df.shape
        worksheet.autofilter(0, 0, max_row, max_col - 1)

        # Устанавливаем ширину колонок на основе максимальной длины данных
        for column in df:
            column_length = max(df[column].astype(str).map(len).max(), len(column))
            col_idx = df.columns.get_loc(column)
            worksheet.set_column(col_idx, col_idx, column_length + 3)


async def create_excel_by_agent_id(agent_id: str, file_name: str, start_date=None, end_date=None):
    orders = await get_documents_by_agent_id(agent_id, start_date, end_date)
    if not orders:
        return False

    # Путь для сохранения файла
    dir_path = Path(config.dir_path, 'files', 'historyOrders')
    dir_path.mkdir(parents=True, exist_ok=True)
    path_file = dir_path / f"{file_name}.xlsx"

    # Создаем DataFrame из данных
    df = pd.DataFrame(data_for_df(orders))
    df = await correct_df(df)

    await write_to_excel(path_file, df)

    return path_file


async def create_excel_by_shop_id(shop_id: str, file_name: str, start_date=None, end_date=None):
    orders = await get_documents_by_shop_id(shop_id, start_date, end_date)
    if not orders:
        return False

    # Путь для сохранения файла
    dir_path = Path(config.dir_path, 'files', 'historyOrders')
    dir_path.mkdir(parents=True, exist_ok=True)
    path_file = dir_path / f"{file_name}.xlsx"

    # Создаем DataFrame из данных
    df = pd.DataFrame(data_for_df(orders))
    df = await correct_df(df)

    await write_to_excel(path_file, df)

    return path_file


async def create_excel_by_shops(shops: list[str], file_name: str, start_date=None, end_date=None) -> Path | None:
    orders = await get_documents_by_shops(shops, start_date, end_date)
    print(orders)
    if not orders:
        return

    # Путь для сохранения файла
    dir_path = Path(config.dir_path, 'files', 'historyOrders')
    dir_path.mkdir(parents=True, exist_ok=True)
    path_file = dir_path / f"{file_name}.xlsx"

    # Создаем DataFrame из данных
    df = pd.DataFrame(data_for_df(orders))
    df = await correct_df(df)

    await write_to_excel(path_file, df)

    return path_file


if __name__ == '__main__':
    import asyncio

    asyncio.run(create_excel_by_agent_id('7402697', 'test', '2022-11-01', '2024-11-07'))
