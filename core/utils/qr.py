import os

import qrcode

import config


async def generateQR(text, paymentType, order_id):
    dir_path = os.path.join(config.dir_path, 'files', paymentType)
    qr_path = os.path.join(dir_path, order_id)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    qr = qrcode.make(text)
    qr.save(qr_path)
    return qr_path
