import asyncio

from sqlalchemy import *
from sqlalchemy.orm import *
from core.database.model import *
import pymysql
import config
from loguru import logger

engine = create_engine(
    f"mysql+pymysql://{config.db_user}:{config.db_password}@{config.ip}:{config.port}/{config.database}?charset=utf8mb4")
Session = sessionmaker(bind=engine)


async def get_currency(chat_id):
    with Session() as session:
        return session.query(Currency).filter(Currency.chat_id == str(chat_id)).first().type


async def set_currency(**kwargs):
    with Session() as session:
        SN = session.query(Currency).filter(Currency.chat_id == str(kwargs["chat_id"])).first()
        if SN is None:
            if len(kwargs) == len([v for k, v in kwargs.items() if v]):
                SN = Currency(**kwargs)
                session.add(SN)
        else:
            session.query(Currency).filter(Currency.chat_id == str(kwargs["chat_id"])) \
                .update({"type": kwargs["type"]}, synchronize_session='fetch')
        session.commit()


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
