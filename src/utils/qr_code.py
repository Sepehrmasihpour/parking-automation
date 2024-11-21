import qrcode
import io


def generate_payment_qr(token_id):
    payment_url = (
        f"http://localhost:8000/pay/{token_id}"  # Replace with your payment domain
    )
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(payment_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)
    return img_byte_arr
