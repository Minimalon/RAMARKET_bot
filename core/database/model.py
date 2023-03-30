import sqlalchemy.orm
from sqlalchemy import create_engine, Integer, String, Column, Float, DateTime, Boolean, DECIMAL
import config
from sqlalchemy.sql import func

engine = create_engine(
    f"mysql+pymysql://{config.db_user}:{config.db_password}@{config.ip}:{config.port}/{config.database}?charset=utf8mb4")
Base = sqlalchemy.orm.declarative_base()


class Currency(Base):
    __tablename__ = 'currency'
    chat_id = Column(String(50), nullable=False, primary_key=True)
    first_name = Column(String(50), nullable=False)
    type = Column(String(10), nullable=False)

    def __init__(self, chat_id, first_name, type):
        self.chat_id = chat_id
        self.first_name = first_name
        self.type = type

    def update(self, **kwargs):
        if self.chat_id != kwargs['chat_id']:
            self.chat_id = kwargs['chat_id']
        if self.first_name != kwargs['first_name']:
            self.first_name = kwargs['first_name']
        if self.type != kwargs['type']:
            self.type = kwargs['type']


class Orders(Base):
    __tablename__ = 'orders'
    chat_id = Column(String(50), nullable=False, primary_key=True)
    first_name = Column(String(50))
    shop = Column(String(50))
    seller_id = Column(String(50))
    paymentGateway = Column(String(50))
    product_id = Column(String(50))
    price = Column(DECIMAL(15, 5))
    quantity = Column(Integer)
    currency = Column(String(10))
    currencyPrice = Column(DECIMAL(15, 5))
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
    payment_name = Column(String(250))
    product_id = Column(String(50))
    product_name = Column(String(250))
    price = Column(DECIMAL(15, 5))
    quantity = Column(Integer)
    sum = Column(DECIMAL(15, 5))
    currency = Column(String(10))
    currencyPrice = Column(DECIMAL(15, 5))
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


Base.metadata.create_all(engine)
