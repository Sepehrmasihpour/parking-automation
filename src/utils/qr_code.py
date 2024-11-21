import qrcode


def generate_payment_qr(token_id):
    payment_url = f"http://localhost:8000/pay/{token_id}"  # Replace with payment domain
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(payment_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    qr_filename = f"qrcode_{token_id}.png"
    img.save(qr_filename)
    return qr_filename
