import asyncio
import os.path
from decimal import Decimal
import pandas as pd
from sqlalchemy import *
from sqlalchemy.orm import *
from core.database.model import *
import pymysql
import config
from loguru import logger

engine = create_engine(
    f"mysql+pymysql://{config.db_user}:{config.db_password}@{config.ip}:{config.port}/{config.database}?charset=utf8mb4")
Session = sessionmaker(bind=engine)


async def update_order(**kwargs):
    with Session() as session:
        SN = session.query(Orders).filter(Orders.chat_id == str(kwargs["chat_id"])).first()
        if SN is None:
            if len(kwargs) == len([v for k, v in kwargs.items() if v]):
                SN = Orders(**kwargs)
                session.add(SN)
        else:
            session.query(Orders).filter(Orders.chat_id == str(kwargs["chat_id"])).update(kwargs,
                                                                                          synchronize_session='fetch')
        session.commit()


async def delete_order(**kwargs):
    with Session() as session:
        orders = session.query(Orders).filter(Orders.chat_id == str(kwargs["chat_id"])).one()
        session.delete(orders)
        session.commit()


async def create_historyOrder(**kwargs):
    with Session() as session:
        session.add(HistoryOrders(**kwargs))
        session.commit()


async def get_order_info(**kwargs):
    with Session() as session:
        return session.query(Orders).filter(Orders.chat_id == str(kwargs["chat_id"])).first()


async def get_currency_name(**kwargs):
    with Session() as session:
        order = session.query(Orders).filter(Orders.chat_id == str(kwargs["chat_id"])).first()
        if order.currency == 'RUB':
            currency = 'руб'
        elif order.currency == 'USD':
            currency = '$'
        else:
            currency = ''
        return currency


async def update_client_info(**kwargs):
    with Session() as session:
        logger.info(kwargs)
        chat_id = str(kwargs["chat_id"])
        SN = session.query(Clients).filter(Clients.chat_id == chat_id).first()
        if SN is None:
            SN = Clients(**kwargs)
            session.add(SN)
        else:
            session.query(Clients).filter(Clients.chat_id == chat_id).update(kwargs, synchronize_session='fetch')
        session.commit()


async def get_client_info(**kwargs):
    with Session() as session:
        client = session.query(Clients).filter(Clients.chat_id == str(kwargs["chat_id"])).first()
        if client is None:
            return False
        return client


def create_excel(**kwargs):
    with Session() as session:
        orders = session.query(HistoryOrders).filter(HistoryOrders.chat_id == str(kwargs["chat_id"])).first()
        if not os.path.exists(os.path.join(config.dir_path, 'files')):
            os.makedirs(os.path.join(config.dir_path, 'files'))
        path_file = os.path.join(config.dir_path, 'files', f"{kwargs['chat_id']}.xlsx")
        if orders is None:
            return False
        query = text(f"SELECT * FROM {config.database}.{HistoryOrders.__table__} WHERE chat_id = {kwargs['chat_id']}"
                     f" order by date DESC")
        df = pd.read_sql(query, engine.connect())
        df = df.drop(
            columns=['chat_id', 'first_name', 'seller_id', 'order_id', 'shop_id', 'paymentGateway',
                     'product_id', 'paymentType'])
        writer = pd.ExcelWriter(path_file, engine="xlsxwriter")
        df.to_excel(writer, sheet_name='orders', index=False, na_rep='NaN')

        for column in df:
            column_length = max(df[column].astype(str).map(len).max(), len(column))
            col_idx = df.columns.get_loc(column)
            writer.sheets['orders'].set_column(col_idx, col_idx, column_length + 3)

        writer.close()

        return path_file


if __name__ == '__main__':
    order = asyncio.run(get_order_info(chat_id=5263751490))
    print(round(Decimal(order.currencyPrice) * (Decimal(order.quantity) * Decimal(order.price)) * 100))
