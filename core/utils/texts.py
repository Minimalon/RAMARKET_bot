import re

from funcy import str_join

from config import __, _
from core.models_pydantic.order import Order

# region ERRORS
error_head = __("➖➖🚨ОШИБКА🚨➖➖\n")
error_fakeContact = __(f'{error_head}Ты отправил <u><b>не свой</b></u> контакт')
error_cancel = __("{error_head}Не найдено текущего заказа").format(error_head=error_head)
error_price_double_comma = __("{error_head}Вы написали больше одной запятой\nПример как надо: <b>10.12</b>").format(
    error_head=error_head)

error_price_not_decimal = __(
    "{error_head}Цена содержит не нужные символы\nПопробуйте снова\nПример как надо: <u><b>10.12</b></u>").format(
    error_head=error_head)

error_article_not_decimal = __("{error_head}Разрешено вводить только цифры\nПопробуйте снова").format(
    error_head=error_head)

error_not_found_order = __("{error_head}Не найдено заказа\nПопробуйте снова создать заказ.").format(
    error_head=error_head)


def error_full_name(name):
    return __(
        "{error_head}ФИО состоит из 3 слов, а ваше состоит из {count} слов\n<b>Попробуйте снова.</b>").format(
        error_head=error_head, count=len(name.split()))


def error_article_not_found(article):
    return __.format(
        error_head=error_head)


def error_server(response):
    return __("{error_head}Сервер недоступен, его код ответа '{response}'\nПопробуйте создать заказ снова.").format(error_head=error_head, response=response.status)


# endregion

menu = __('<u><b>Заказ</b></u> - Оформить заказ покупателю\n'
          '<u><b>Личный кабинет</b></u> - Личные регистрационные данные\n'
          '<u><b>История заказов</b></u> - Получить Excel файл с историями заказов')

succes_registration = __('Регистрация успешна пройдена')
need_reg = __(
    'Вы зашли впервые, нажмите кнопку Регистрация'
)


def menu_new_language(language='ru'):
    return __('<u><b>Заказ</b></u> - Оформить заказ покупателю\n'
              '<u><b>Личный кабинет</b></u> - Личные регистрационные данные\n'
              '<u><b>История заказов</b></u> - Получить Excel файл с историями заказов', locale=language)


def cart(order: Order) -> str:
    text = ''
    for index, product in enumerate(order.cart, 1):
        text += _('ℹ️<b>Товар №{index}:</b>\n'
                  '      <b>Название товара</b>: <code>{product_name}</code>\n'
                  '      <b>Цена товара</b>: <code>{price} {currency_symbol}</code>\n'
                  '      <b>Количество</b>: <code>{quantity}</code>\n'). \
            format(index=index, product_name=product.name, quantity=product.quantity,
                   price=product.price, currency_symbol=order.currency.symbol)
    if order.currency.name == 'RUB':
        text += _('<b>Общая сумма</b>: <code>{sum_rub} {currency_symbol} / {sum_usd} $</code>'). \
            format(sum_usd=order.sum_usd, sum_rub=order.sum_rub, currency_symbol=order.currency.symbol)
    elif order.currency.name == 'USD':
        text += _('<b>Общая сумма</b>: <code>{sum_usd} {currency_symbol} / {sum_rub} ₽</code>'). \
            format(sum_usd=order.sum_usd, sum_rub=order.sum_rub, currency_symbol=order.currency.symbol)
    elif order.currency.name == 'TRY':
        text += _('<b>Общая сумма</b>: <code>{sum_try} {currency_symbol} / {sum_rub} ₽</code>'). \
            format(sum_try=order.sum_try, sum_rub=order.sum_rub, currency_symbol=order.currency.symbol)
    return text


async def createOrder(order: Order) -> str:
    if order.client_phone is not None:
        mail_or_phone = order.client_phone
        message = __("Сотовый")
    else:
        mail_or_phone = order.client_mail
        message = __("Почта")

    text = __(
        'ℹ️ <b>Информация о заказе:</b>\n'
        '➖➖➖➖➖➖➖➖➖➖➖\n'
        '<b>ФИО клиента</b>: <code>{client_name}</code>\n'
        '<b>{message} клиента</b>: <code>{mail_or_phone}</code>\n'
        '<b>Название магазина</b>: <code>{shop_name}</code>\n'
        '<b>Тип оплаты</b>: <code>{payment_name}</code>\n'
        '<b>Валюта</b>: <code>{currency}</code>\n'
        '<b>Курс валюты</b>: <code>{currencyPrice}</code>\n'
    ).format(client_name=order.client_name, message=message,
             mail_or_phone=mail_or_phone, shop_name=order.shop.name,
             payment_name=order.payment.name,
             currencyPrice=order.currency.price,
             currency=order.currency.name)

    text += cart(order)
    return text


async def qr(order_id: str, order: Order) -> str:
    text = _('<b><u>Заказ успешно создан</u></b>✅\n')
    text += _('<b>Номер заказа</b>: <code>{order_id}</code>\n'.format(order_id=order_id))
    text += await createOrder(order)
    return text


def phone(phone):
    phone = str_join(sep="", seq=re.findall(r'[0-9]*', phone))
    if re.findall(r'^89', phone):
        return re.sub(r'^89', '79', phone)
    return phone


def phoneNotReg(phone):
    text = error_head + \
           __(f'Ваш сотовый "{phone}" не зарегистрирован в системе\n'
              f'Уточните вопрос и попробуйте снова.')
    return text
