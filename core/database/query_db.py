import json
import os.path
from datetime import datetime
from decimal import Decimal

import pandas as pd
from aiogram.types import Message
from sqlalchemy import select, update, text, create_engine, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker, joinedload

from core.database.model import *
from core.models_pydantic.order import Order, Product
from core.oneC.api import Api

engine = create_async_engine(
    f"postgresql+asyncpg://{config.db_user}:{config.db_password}@{config.ip}:{config.port}/{config.database}")
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def create_document(order: Order):
    async with async_session() as session:
        document = Documents(
            order_id=order.order_id,
            chat_id=str(order.tg_user.chat_id),
            agent_id=order.user.id,
            agent_name=order.user.name,
            rezident=order.rezident,
            country_code=order.shop.country_code,
            country_name=order.shop.country,
            city_code=order.shop.city_code,
            city_name=order.shop.city,
            shop_id=order.shop.id,
            shop_name=order.shop.name,
            shop_currency=order.shop.currency,
            payment_id=order.payment.id,
            payment_type=order.payment.type,
            payment_name=order.payment.name,
            tax=order.tax if order.tax == 0 else order.tax * 100,
            sum_usd=order.sum_usd,
            sum_rub=order.sum_rub,
            sum_try=order.sum_try,
            sum_kzt=order.sum_kzt,
            sum_eur=order.sum_eur,
            currency=order.currency.name,
            currency_price=order.currency.price,
            client_name=order.client_name,
            client_phone=order.client_phone,
            client_mail=order.client_mail,
            status=OrderStatus.sale
        )
        session.add(document)
        await session.commit()

        for product in order.cart:
            document_item = DocumentItems(
                document_id=document.id,
                order_id=order.order_id,
                product_id=product.id,
                product_name=product.name,
                product_groupname=product.group_name,
                product_groupid=product.group_id,
                price=product.price,
                quantity=product.quantity,
            )
            session.add(document_item)

        await session.commit()


async def create_historyOrders(order_id: str, order: Order, product: Product):
    async with async_session() as session:
        session.add(
            HistoryOrders(
                order_id=order_id,
                chat_id=str(order.tg_user.chat_id),
                city_name=order.shop.city,
                city_code=order.shop.city_code,
                country_code=order.shop.country_code,
                country_name=order.shop.country,
                paymentGateway=order.payment.id,
                paymentType=order.payment.type,
                payment_name=order.payment.name,
                tax=order.tax if order.tax == 0 else order.tax * 100,
                product_id=product.id,
                product_name=product.name,
                price=str(product.price),
                quantity=str(product.quantity),
                sum_usd=str(order.sum_usd),
                sum_rub=str(order.sum_rub),
                sum_try=str(order.sum_try),
                sum_kzt=str(order.sum_kzt),
                sum_eur=str(order.sum_eur),
                currency=order.currency.name,
                currencyPrice=str(order.currency.price),
                client_name=order.client_name,
                client_phone=order.client_phone,
                client_mail=order.client_mail,
                shop_id=order.shop.id,
                shop_name=order.shop.name,
                shop_currency=str(order.shop.currency),
                agent_id=order.user.id,
                agent_name=order.user.name,
                rezident=order.rezident,
            )
        )
        await session.commit()


async def get_history_orders_for_googleSheet(id: int) -> list[HistoryOrders]:
    async with async_session() as session:
        q = await session.execute(select(HistoryOrders)
                                  .where(HistoryOrders.id > id)
                                  .order_by(HistoryOrders.date))
        orders = q.scalars().all()
        return orders


async def get_order_by_currence_name_and_year(currency_name: str, year: int) -> list[HistoryOrders]:
    async with async_session() as session:
        q = await session.scalars(
            select(HistoryOrders)
            .where(
                (HistoryOrders.currency == currency_name) &
                (extract('year', HistoryOrders.date) == year)
            )
            .order_by(HistoryOrders.date)
        )
        orders = q.all()
        return orders


async def update_client_info(**kwargs):
    async with async_session() as session:
        for key, value in kwargs.items():
            kwargs[key] = str(value)
        chat_id = str(kwargs["chat_id"])
        q = await session.execute(select(Clients).filter(Clients.chat_id == chat_id))
        SN = q.scalars().first()
        if SN is None:
            SN = Clients(**kwargs)
            session.add(SN)
        else:
            await session.execute(update(Clients).where(Clients.chat_id == str(kwargs["chat_id"])).values(kwargs))
        await session.commit()


async def prepare_delete_history_order(order_id: str, order_date: datetime):
    async with async_session() as session:
        await session.execute(
            update(HistoryOrders).
            where(
                (HistoryOrders.order_id == order_id) &
                (func.to_char(HistoryOrders.date, 'YYYYMMDDHH24MI') == order_date.strftime('%Y%m%d%H%M'))
            ).
            values(
                status=OrderStatus.prepare_delete,
            ))
        await session.commit()


async def delete_document(order_id: str, order_date: datetime) -> None:
    async with async_session() as session:
        await session.execute(
            update(Documents).
            where(
                (Documents.order_id == order_id) &
                (func.to_char(Documents.date, 'YYYYMMDDHH24MI') == order_date.strftime('%Y%m%d%H%M'))
            ).
            values(
                status=OrderStatus.delete,
            ))
        await session.commit()


async def delete_history_order(order_id: str, order_date: datetime):
    async with async_session() as session:
        await session.execute(
            update(HistoryOrders).
            where(
                (HistoryOrders.order_id == order_id) &
                (func.to_char(HistoryOrders.date, 'YYYYMMDDHH24MI') == order_date.strftime('%Y%m%d%H%M'))
            ).
            values(
                status=OrderStatus.delete,
            ))
        await session.commit()


async def select_prepare_delete() -> list[HistoryOrders]:
    async with async_session() as session:
        q = await session.execute(select(HistoryOrders).where(HistoryOrders.status == OrderStatus.prepare_delete))
        return q.scalars().all()


async def update_client_language(chat_id: str, language: str):
    async with async_session() as session:
        await session.execute(update(Clients).where(Clients.chat_id == chat_id).values(language=language))
        await session.commit()


async def get_client_info(**kwargs) -> Clients | None:
    async with async_session() as session:
        q = await session.execute(select(Clients).filter(Clients.chat_id == str(kwargs["chat_id"])))
        client = q.scalars().first()
        return client


async def create_excel(chat_id: str):
    async with async_session() as session:
        q = await session.execute(select(HistoryOrders).filter(HistoryOrders.chat_id == str(chat_id)))
        orders = q.scalars().first()
        if not os.path.exists(os.path.join(config.dir_path, 'files')):
            os.makedirs(os.path.join(config.dir_path, 'files'))
        path_file = os.path.join(config.dir_path, 'files', f"{chat_id}.xlsx")
        if orders is None:
            return False
        query = text(f'SELECT * FROM public."{HistoryOrders.__table__}" WHERE chat_id = \'{chat_id}\''
                     f' order by date DESC')
        engine = create_engine(
            f"postgresql+psycopg2://{config.db_user}:{config.db_password}@{config.ip}:{config.port}/{config.database}")
        df = pd.read_sql(query, engine.connect())
        df['date'] = df['date'].dt.tz_localize(None)
        df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y %H:%M:%S')
        df = df.drop(
            columns=['chat_id', 'id', 'agent_id', 'shop_id',
                     'paymentGateway', 'product_id', 'paymentType',
                     'country_code', 'city_code'])
        # Порядок отображения столбцов
        column_order = ['date', 'order_id', 'status', 'agent_name', 'country_name', 'city_name', 'shop_name',
                        'shop_currency', 'payment_name', 'product_name', 'price',
                        'quantity', 'sum_usd', 'sum_rub', 'sum_try', 'currency', 'currencyPrice', 'client_name',
                        'client_phone', 'client_mail']
        df = df[column_order]
        writer = pd.ExcelWriter(path_file, engine="xlsxwriter")
        df.to_excel(writer, sheet_name='orders', index=False, na_rep='NaN')

        for column in df:
            column_length = max(df[column].astype(str).map(len).max(), len(column))
            col_idx = df.columns.get_loc(column)
            writer.sheets['orders'].set_column(col_idx, col_idx, column_length + 3)

        writer.close()

        return path_file


async def perezaliv_rub(message: Message):
    await message.answer('Начал')
    for year in range(2023, datetime.now().year + 1):
        orders = await get_order_by_currence_name_and_year('RUB', year)
        for o in orders:
            json_orders = {
                "TypeR": "Doc",
                "Data": o.date.strftime('%d.%m.%Y %H:%M:%S'),
                "Order_id": o.order_id,
                "Sklad": o.shop_id,
                "KursPrice": o.currencyPrice,
                "Valuta": o.currency,
                "SO": o.paymentGateway,
                "Sotr": o.agent_id,
                "Klient": o.client_name,
                "Telefon": o.client_phone,
                "Email": o.client_mail,
                "Itemc": [{"Tov": _.product_id, "Kol": _.quantity, "Cost": _.price,
                           'Sum': str(Decimal(_.price) * Decimal(_.quantity))} for _ in orders if
                          _.order_id == o.order_id]
            }
            await Api().post_create_order(json_orders)
    await message.answer('Заказы RUB созданы')


async def perezaliv_try(message: Message):
    await message.answer('Начал')
    for year in range(2023, datetime.now().year + 1):
        orders_try = await get_order_by_currence_name_and_year('TRY', year)
        for o in orders_try:
            json_orders = {
                "TypeR": "Doc",
                "Data": o.date.strftime('%d.%m.%Y %H:%M:%S'),
                "Order_id": o.order_id,
                "Sklad": o.shop_id,
                "KursPrice": o.currencyPrice,
                "Valuta": o.currency,
                "SO": o.paymentGateway,
                "Sotr": o.agent_id,
                "Klient": o.client_name,
                "Telefon": o.client_phone,
                "Email": o.client_mail,
                "Itemc": [{"Tov": _.product_id, "Kol": _.quantity, "Cost": _.price,
                           'Sum': str(Decimal(_.price) * Decimal(_.quantity))} for _ in orders_try if
                          _.order_id == o.order_id]
            }
            await Api().post_create_order(json_orders)
    await message.answer('Заказы TRY созданы')


async def test_perezaliv_rub(message: Message):
    await message.answer('Начал')
    orders = await get_order_by_currence_name_and_year('RUB', 2023)
    for o in orders:
        json_orders = {
            "TypeR": "Doc",
            "Data": o.date.strftime('%d.%m.%Y %H:%M:%S'),
            "Order_id": o.order_id,
            "Sklad": o.shop_id,
            "KursPrice": o.currencyPrice,
            "Valuta": o.currency,
            "SO": o.paymentGateway,
            "Sotr": o.agent_id,
            "Klient": o.client_name,
            "Telefon": o.client_phone,
            "Email": o.client_mail,
            "Itemc": [{"Tov": _.product_id, "Kol": _.quantity, "Cost": _.price,
                       'Sum': str(Decimal(_.price) * Decimal(_.quantity))} for _ in orders if _.order_id == o.order_id]
        }
        await Api().post_create_order(json_orders)
        await message.answer(json.dumps(json_orders, ensure_ascii=False, indent=4))
        return


async def test_perezaliv_try(message: Message):
    await message.answer('Начал')
    orders_try = await get_order_by_currence_name_and_year('TRY', 2023)
    for o in orders_try:
        json_orders = {
            "TypeR": "Doc",
            "Data": o.date.strftime('%d.%m.%Y %H:%M:%S'),
            "Order_id": o.order_id,
            "Sklad": o.shop_id,
            "KursPrice": o.currencyPrice,
            "Valuta": o.currency,
            "SO": o.paymentGateway,
            "Sotr": o.agent_id,
            "Klient": o.client_name,
            "Telefon": o.client_phone,
            "Email": o.client_mail,
            "Itemc": [{"Tov": _.product_id, "Kol": _.quantity, "Cost": _.price,
                       'Sum': str(Decimal(_.price) * Decimal(_.quantity))} for _ in orders_try if
                      _.order_id == o.order_id]
        }
        await Api().post_create_order(json_orders)
        await message.answer(json.dumps(json_orders, ensure_ascii=False, indent=4))
        return

async def get_documents_by_agent_id(agent_id: str, start_date: str = None, end_date: str = None) -> list[Documents]:
    async with async_session() as session:
        if start_date and end_date:
            start_date = datetime.fromisoformat(start_date)
            end_date = datetime.fromisoformat(end_date)
            query = select(Documents).options(joinedload(Documents.items)).where(Documents.agent_id == agent_id).where(
                Documents.date >= start_date, Documents.date < end_date)
        else:
            query = select(Documents).options(joinedload(Documents.items)).where(Documents.agent_id == agent_id)
        result = await session.execute(query)
        return result.scalars().unique().all()

async def get_documents_by_shop_id(
        shop_id: str, start_date: str = None, end_date: str = None
) -> list[Documents]:
    async with async_session() as session:
        if start_date and end_date:
            start_date_parsed = datetime.fromisoformat(start_date)
            end_date_parsed = datetime.fromisoformat(end_date)

            query = (
                select(Documents)
                .options(joinedload(Documents.items))
                .where(Documents.shop_id == shop_id)
                .where(
                    Documents.date >= start_date_parsed,
                    Documents.date < end_date_parsed,
                )
            )
        else:
            query = (
                select(Documents)
                .options(joinedload(Documents.items))
                .where(Documents.shop_id == shop_id)
            )
        result = await session.execute(query)
        return result.scalars().unique().all()

async def get_documents_by_shops(shops: list[str], start_date: str = None, end_date: str = None) -> list[Documents]:
    async with async_session() as session:
        if start_date and end_date:
            start_date = datetime.fromisoformat(start_date)
            end_date = datetime.fromisoformat(end_date)
            query = select(Documents).options(joinedload(Documents.items)).where(Documents.shop_id.in_(shops)).where(
                Documents.date >= start_date, Documents.date < end_date)
        else:
            query = select(Documents).options(joinedload(Documents.items)).where(Documents.shop_id.in_(shops))
        result = await session.execute(query)
        return result.scalars().unique().all()

async def kosyc_klyiner(message: Message):
    """Пересоздовали заказы, потому что в 1С не передовалась валюта заказа"""

    # with open(os.path.join(config.dir_path, 'core', 'database', 'orders.json'), 'w', encoding="utf8") as orders:
    #     orders.write(json.dumps(json_orders, ensure_ascii=False, indent=4) + '\n')

# if __name__ == '__main__':
#     orders = asyncio.run(get_order_by_currence_name_and_year('RUB', 2022))
#     for o in orders:
#         json_orders = {
#             "TypeR": "Doc",
#             "Data": o.date.strftime('%d.%m.%Y %H:%M:%S'),
#             "Order_id": o.order_id,
#             "Sklad": o.shop_id,
#             "KursPrice": o.currencyPrice,
#             "Valuta": o.currency,
#             "SO": o.paymentGateway,
#             "Sotr": o.agent_id,
#             "Klient": o.client_name,
#             "Telefon": o.client_phone,
#             "Email": o.client_mail,
#             "Itemc": [{"Tov": _.product_id, "Kol": _.quantity, "Cost": _.price, 'Sum': str(Decimal(_.price) * Decimal(_.quantity))} for _ in orders if _.order_id == o.order_id]
#         }
#         print(json_orders)
