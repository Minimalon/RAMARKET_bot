import enum

from sqlalchemy import String, Column, DateTime, Boolean, BigInteger, Enum, Float, ForeignKey, Integer, Numeric
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

import config

engine = create_async_engine(
    f"postgresql+asyncpg://{config.db_user}:{config.db_password}@{config.ip}:{config.port}/{config.database}")
Base = declarative_base()


class OrderStatus(enum.Enum):
    sale = 1  # Продали
    prepare_delete = 2  # Подготовка к удалению
    delete = 3  # Удалён в лукере
    cancel = 4  # Отменили
    change_date = 5  # Изменили дату в лукере и в бд


class Documents(Base):
    __tablename__ = 'document'
    id = Column(BigInteger, nullable=False, primary_key=True)
    date = Column(DateTime(timezone=True), server_default=func.now())
    order_id = Column(String(250), nullable=False)
    chat_id = Column(String(50))
    agent_id = Column(String(50))
    agent_name = Column(String(250))
    rezident = Column(String(50))
    country_code = Column(String(50))
    country_name = Column(String(250))
    city_code = Column(String(50))
    city_name = Column(String(250))
    shop_id = Column(String(50))
    shop_name = Column(String(250))
    shop_currency = Column(String(50))
    payment_id = Column(String(50))
    payment_type = Column(String(50))
    payment_name = Column(String(250))
    tax = Column(Float(10))
    sum_usd = Column(Numeric(10, 2))
    sum_rub = Column(Numeric(10, 2))
    sum_try = Column(Numeric(20, 2))
    sum_kzt = Column(Numeric(20, 2))
    currency = Column(String(10))
    currency_price = Column(Numeric(10, 4))
    client_name = Column(String(100))
    client_phone = Column(String(20))
    client_mail = Column(String(100))
    status = Column(Enum(OrderStatus, native_enum=False), default=OrderStatus.sale)

    items = relationship("DocumentItems", back_populates="document", uselist=True, cascade="all, delete, delete-orphan",
                         foreign_keys="[DocumentItems.document_id]")

class DocumentItems(Base):
    __tablename__ = 'documentitems'
    id = Column(BigInteger, nullable=False, primary_key=True)
    document_id = Column(BigInteger, ForeignKey('document.id'), nullable=False)
    order_id = Column(String(250), ForeignKey('document.order_id'), nullable=False)
    product_id = Column(String(50))
    product_name = Column(String(250))
    product_groupname = Column(String(250))
    product_groupid = Column(String(50))
    price = Column(Numeric(10, 2))
    quantity = Column(Integer)

    document = relationship("Documents", back_populates="items", uselist=False, foreign_keys=[document_id])


class HistoryOrders(Base):
    __tablename__ = 'historyOrders'
    id = Column(BigInteger, nullable=False, primary_key=True)
    date = Column(DateTime(timezone=True), server_default=func.now())
    order_id = Column(String(250), nullable=False)
    chat_id = Column(String(50))
    agent_id = Column(String(50))
    agent_name = Column(String(250))
    rezident = Column(String(50))
    country_code = Column(String(50))
    country_name = Column(String(250))
    city_code = Column(String(50))
    city_name = Column(String(250))
    shop_id = Column(String(50))
    shop_name = Column(String(50))
    shop_currency = Column(String(50))
    paymentGateway = Column(String(50))
    paymentType = Column(String(50))
    payment_name = Column(String(250))
    tax = Column(Float(10))
    product_id = Column(String(50))
    product_name = Column(String(250))
    price = Column(String(50))
    quantity = Column(String(50))
    sum_usd = Column(String(50))
    sum_rub = Column(String(50))
    sum_try = Column(String(50))
    sum_kzt = Column(String(50))
    currency = Column(String(10))
    currencyPrice = Column(String(50))
    client_name = Column(String(100))
    client_phone = Column(String(20))
    client_mail = Column(String(100))
    status = Column(Enum(OrderStatus, native_enum=False), default=OrderStatus.sale)


class Clients(Base):
    __tablename__ = 'clients'
    date = Column(DateTime(timezone=True), server_default=func.now())
    phone_number = Column(String(50), nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))
    user_id = Column(String(50), nullable=False, primary_key=True)
    chat_id = Column(String(50), nullable=False)
    admin = Column(Boolean, default=False)
    language = Column(String(3), default='ru')


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
