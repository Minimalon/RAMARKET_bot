import sqlalchemy.orm
from sqlalchemy import create_engine, Integer, String, Column, DateTime, Boolean
import config
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker


engine = create_async_engine(
    f"postgresql+asyncpg://{config.db_user}:{config.db_password}@{config.ip}:{config.port}/{config.database}")
Base = declarative_base()


class Orders(Base):
    __tablename__ = 'orders'
    chat_id = Column(String(50), nullable=False, primary_key=True)
    first_name = Column(String(50))
    shop = Column(String(50))
    seller_id = Column(String(50))
    paymentGateway = Column(String(50))
    paymentType = Column(String(50))
    product_id = Column(String(50))
    price = Column(String(50))
    quantity = Column(String(50))
    sum = Column(String(50))
    sum_rub = Column(String(50))
    currency = Column(String(10))
    currencyPrice = Column(String(50))
    client_name = Column(String(100))
    client_phone = Column(String(20))
    client_mail = Column(String(100))


class HistoryOrders(Base):
    __tablename__ = 'historyOrders'
    date = Column(DateTime(timezone=True), server_default=func.now())
    order_id = Column(String(250), nullable=False, primary_key=True)
    chat_id = Column(String(50))
    first_name = Column(String(50))
    shop_id = Column(String(50))
    shop_name = Column(String(50))
    seller_id = Column(String(50))
    paymentGateway = Column(String(50))
    paymentType = Column(String(50))
    payment_name = Column(String(250))
    product_id = Column(String(50))
    product_name = Column(String(250))
    price = Column(String(50))
    quantity = Column(String(50))
    sum = Column(String(50))
    sum_rub = Column(String(50))
    currency = Column(String(10))
    currencyPrice = Column(String(50))
    client_name = Column(String(100))
    client_phone = Column(String(20))
    client_mail = Column(String(100))


class Clients(Base):
    __tablename__ = 'clients'
    date = Column(DateTime(timezone=True), server_default=func.now())
    phone_number = Column(String(50), nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))
    user_id = Column(String(50), nullable=False, primary_key=True)
    chat_id = Column(String(50), nullable=False)
    admin = Column(Boolean, default=False)


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
