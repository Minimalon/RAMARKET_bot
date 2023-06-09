import os.path

import pandas as pd
from sqlalchemy import select, update, text, create_engine, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from core.database.model import *

engine = create_async_engine(
    f"postgresql+asyncpg://{config.db_user}:{config.db_password}@{config.ip}:{config.port}/{config.database}")
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def create_historyOrder(**kwargs):
    async with async_session() as session:
        session.add(HistoryOrders(**kwargs))
        await session.commit()


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
        await session.execute(delete(HistoryOrders).where(HistoryOrders.order_id == order_id))
        await session.commit()


async def update_client_language(chat_id: str, language: str):
    async with async_session() as session:
        await session.execute(update(Clients).where(Clients.chat_id == chat_id).values(language=language))
        await session.commit()


async def get_client_info(**kwargs):
    async with async_session() as session:
        q = await session.execute(select(Clients).filter(Clients.chat_id == str(kwargs["chat_id"])))
        client = q.scalars().first()
        if client is None:
            return False
        return client


async def create_excel(**kwargs):
    async with async_session() as session:
        q = await session.execute(select(HistoryOrders).filter(HistoryOrders.chat_id == str(kwargs["chat_id"])))
        orders = q.scalars().first()
        if not os.path.exists(os.path.join(config.dir_path, 'files')):
            os.makedirs(os.path.join(config.dir_path, 'files'))
        path_file = os.path.join(config.dir_path, 'files', f"{kwargs['chat_id']}.xlsx")
        if orders is None:
            return False
        query = text(f'SELECT * FROM public."{HistoryOrders.__table__}" WHERE chat_id = \'{kwargs["chat_id"]}\''
                     f' order by date DESC')
        engine = create_engine(f"postgresql+psycopg2://{config.db_user}:{config.db_password}@{config.ip}:{config.port}/{config.database}")
        df = pd.read_sql(query, engine.connect())
        df['date'] = df['date'].dt.tz_localize(None)
        df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y %H:%M:%S')
        df = df.drop(
            columns=['chat_id', 'id', 'seller_id', 'agent_id', 'shop_id', 'paymentGateway', 'product_id', 'paymentType', 'country_code', 'city_code'])
        writer = pd.ExcelWriter(path_file, engine="xlsxwriter")
        df.to_excel(writer, sheet_name='orders', index=False, na_rep='NaN')

        for column in df:
            column_length = max(df[column].astype(str).map(len).max(), len(column))
            col_idx = df.columns.get_loc(column)
            writer.sheets['orders'].set_column(col_idx, col_idx, column_length + 3)

        writer.close()

        return path_file
