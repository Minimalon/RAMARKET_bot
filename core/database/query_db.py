import asyncio
import json
import os.path

import pandas as pd
from sqlalchemy import select, update, text, create_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from core.database.model import *
from core.models_pydantic.order import Order, Product

engine = create_async_engine(
    f"postgresql+asyncpg://{config.db_user}:{config.db_password}@{config.ip}:{config.port}/{config.database}")
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def create_historyOrder(order_id: str, order: Order, product: Product):
    async with async_session() as session:
        session.add(
            HistoryOrders(
                order_id=order_id, chat_id=str(order.tg_user.chat_id),
                city_name=order.shop.city, city_code=order.shop.city_code,
                country_code=order.shop.country_code,
                country_name=order.shop.country,
                paymentGateway=order.payment.id, paymentType=order.payment.type,
                payment_name=order.payment.name,
                product_id=product.id, product_name=product.name,
                price=str(product.price), quantity=str(product.quantity),
                sum_usd=str(order.sum_usd), sum_rub=str(order.sum_rub), sum_try=str(order.sum_try),
                currency=order.currency.name, currencyPrice=str(order.currency.price),
                client_name=order.client_name, client_phone=order.client_phone,
                client_mail=order.client_mail, shop_id=order.shop.id,
                shop_name=order.shop.name, shop_currency=str(order.shop.currency),
                agent_id=order.user.id, agent_name=order.user.name,
            )
        )
        await session.commit()


async def get_history_orders_for_googleSheet(id: int):
    async with async_session() as session:
        q = await session.execute(
            select(HistoryOrders.date, HistoryOrders.agent_name, HistoryOrders.country_name,
                   HistoryOrders.city_name, HistoryOrders.shop_name, HistoryOrders.payment_name,
                   HistoryOrders.product_name, HistoryOrders.price, HistoryOrders.quantity,
                   HistoryOrders.sum_usd, HistoryOrders.sum_rub, HistoryOrders.currency,
                   HistoryOrders.currencyPrice, HistoryOrders.client_name, HistoryOrders.client_phone)
            .where(HistoryOrders.id > id, HistoryOrders.status == OrderStatus.sale).order_by(HistoryOrders.date))
        orders = q.all()
        return orders


async def get_order_by_currence_name(currency_name: str) -> list[HistoryOrders]:
    async with async_session() as session:
        q = await session.scalars(
            select(HistoryOrders)
            .where(HistoryOrders.currency == currency_name).order_by(HistoryOrders.date))
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


async def delete_history_order(order_id: str):
    async with async_session() as session:
        await session.execute(update(HistoryOrders).where(HistoryOrders.order_id == order_id).values(
            status=OrderStatus.delete
        ))
        await session.commit()


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
        engine = create_engine(f"postgresql+psycopg2://{config.db_user}:{config.db_password}@{config.ip}:{config.port}/{config.database}")
        df = pd.read_sql(query, engine.connect())
        df['date'] = df['date'].dt.tz_localize(None)
        df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y %H:%M:%S')
        df = df.drop(
            columns=['chat_id', 'id', 'agent_id', 'shop_id',
                     'paymentGateway', 'product_id', 'paymentType',
                     'country_code', 'city_code'])
        # Порядок отображения столбцов
        column_order = ['date', 'order_id', 'status', 'agent_name', 'country_name', 'city_name', 'shop_name', 'shop_currency', 'payment_name', 'product_name', 'price',
                        'quantity', 'sum_usd', 'sum_rub', 'sum_try', 'currency', 'currencyPrice', 'client_name', 'client_phone', 'client_mail']
        df = df[column_order]
        writer = pd.ExcelWriter(path_file, engine="xlsxwriter")
        df.to_excel(writer, sheet_name='orders', index=False, na_rep='NaN')

        for column in df:
            column_length = max(df[column].astype(str).map(len).max(), len(column))
            col_idx = df.columns.get_loc(column)
            writer.sheets['orders'].set_column(col_idx, col_idx, column_length + 3)

        writer.close()

        return path_file


async def kosyc_klyiner():
    with open(os.path.join(config.dir_path, 'core', 'database', 'orders.json'), 'r', encoding="utf8") as orders:
        orders = json.loads(orders.read())
    for count, order in enumerate(orders, start=1):
        order_id = f'RECOVER-{count}'
        print(count, order)
        # await create_historyOrder()


if __name__ == '__main__':
    orders = asyncio.run(get_order_by_currence_name('RUB'))
    json_orders = [{
        "TypeR": "Doc",
        "Sklad": o.shop_id,
        "KursPrice": o.currencyPrice,
        "Valuta": o.currency,
        "SO": o.paymentGateway,
        "Sotr": o.agent_id,
        "Klient": o.client_name,
        "Telefon": o.client_phone,
        "Email": o.client_mail,
        "Itemc": [{"Tov": o.product_id, "Kol": o.quantity, "Cost": o.price, 'Sum': o.sum_rub}]
    } for o in orders]
    with open(os.path.join(config.dir_path, 'core', 'database', 'orders.json'), 'w', encoding="utf8") as orders:
        orders.write(json.dumps(json_orders) + '\n')
