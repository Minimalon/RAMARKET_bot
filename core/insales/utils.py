from decimal import Decimal
from core.insales import InSalesApi
import config
import core.database.query_db as query_db

InSales = InSalesApi.from_credentials(config.account_name, config.api_key, config.api_pass)


def create_order(chat_id):
    order_info = query_db.get_order_info(chat_id=chat_id)
    order = InSales.create_order({
        'client': {
            'phone': order_info.client_phone,
            'name': order_info.client_name,
            'consent_to_personal_data': 'true',
            'subscribe': 'true',
            'messenger-subscription': 'true',
        },
        'order-lines-attributes': [{
            'product-id': order_info.product_id,
            'quantity': order_info.quantity,
        }],
        "currency-code": order_info.currency,
        'payment-gateway-id': order_info.paymentGateway,
        'delivery-variant-id': 5563162,
    })
    query_db.create_historyOrder(order_id=order['id'], chat_id=order_info.chat_id, first_name=order_info.first_name,
                                 paymentGateway=order_info.paymentGateway, product_id=order_info.product_id,
                                 price=order_info.price, quantity=order_info.quantity, currency=order_info.currency,
                                 client_name=order_info.client_name, client_phone=order_info.client_phone,
                                 client_mail=order_info.client_mail)
    return order


def get_name_paymentGateway(id):
    for payment in InSales.get_payment_gateways():
        if payment['id'] == int(id):
            return payment['title']


def get_paymentGateway(id):
    for payment in InSales.get_payment_gateways():
        if payment['id'] == int(id):
            return payment


async def convert_price(chat_id, price):
    currency = query_db.get_order_info(chat_id=chat_id).currency
    if currency == "RUR":
        return price
    if currency == "USD":
        for cur in await InSales.get_stock_currencies():
            if cur['code'] == 'USD':
                return round(price / cur['cb-rate'], 2)


async def convert_price_to_RUR(chat_id, price):
    currency = query_db.get_order_info(chat_id=chat_id).currency
    if currency == "RUR":
        return price
    if currency == "USD":
        for cur in InSales.get_stock_currencies():
            if cur['code'] == 'USD':
                return round(price * cur['cb-rate'], 2)


def update_price_on_product(product_id, price):
    for i in InSales.get_product_variants(product_id):
        InSales.update_product_variant(i['product-id'], i['id'], {'price': price})


async def get_photos(product_id):
    return [i['medium-url'] for i in InSales.get_product_images(product_id)]


def get_child_collections(collection_id):
    result = []
    for collection in InSales.get_collections():
        if collection['parent-id'] == collection_id:
            result.append(collection)
    return result


if __name__ == '__main__':
    print(InSales.get_products_by_collection(25561487))
