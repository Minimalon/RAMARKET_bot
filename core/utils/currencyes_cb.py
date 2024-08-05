import asyncio

import httpx as httpx
from decimal import Decimal


async def get_price_valute_by_one(valute: str = 'USD'):
    async with httpx.AsyncClient() as client:
        response = await client.get('https://www.cbr-xml-daily.ru/daily_json.js')
        r_json = response.json()
        price_by_one = r_json['Valute'][valute]['Value'] / r_json['Valute'][valute]['Nominal']
        return round(Decimal(price_by_one), 4)
