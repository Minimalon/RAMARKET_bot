import base64
import os
import io
import qrcode

import config


async def generateQR(text: str, paymentType: str, order_id: str) -> str:
    dir_path = os.path.join(config.dir_path, 'files', paymentType)
    qr_path = os.path.join(dir_path, f'{order_id}.png')
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    qr = qrcode.make(text)
    qr.save(qr_path)
    return qr_path


async def IOgenerateQR_bytes(text: str) -> bytes:
    # Создаем QR-код
    qr = qrcode.make(text)

    # Создаем буфер в памяти
    qr_bytes_io = io.BytesIO()

    # Сохраняем QR-код в буфер (в память) - УБРАНО format='PNG'
    qr.save(qr_bytes_io)

    # Получаем байтовое содержимое из буфера
    qr_bytes_io.seek(0)
    qr_image_bytes = qr_bytes_io.read()

    # Закрываем буфер
    qr_bytes_io.close()

    return qr_image_bytes