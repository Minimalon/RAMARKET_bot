from datetime import datetime

from pydantic import BaseModel


class Client(BaseModel):
    date: datetime
    phone_number: str
    first_name: str
    last_name: str
    user_id: str
    chat_id: int
    admin: bool
    language: str
