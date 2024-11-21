import sqlite3
import qrcode
from typing import Literal


def create_parking_token():
    conn = sqlite3.connect("parking.db")
    c = conn.cursor()
    c.execute("INSERT INTO parking_tokens (is_paid) VALUES (0)")
    token_id = c.lastrowid
    conn.commit()
    conn.close()
    return token_id


def cleanse_db():
    conn = sqlite3.connect("parking.db")
    c = conn.cursor()
    c.execute(
        'DELETE FROM parking_tokens WHERE created_at <= datetime("now", "-1 day")'
    )
    conn.commit()
    conn.close()
    print("Database cleansed")


# Function to update the is_paid status
def set_paid_status(token_id, status=True):
    conn = sqlite3.connect("parking.db")
    c = conn.cursor()
    c.execute("UPDATE parking_tokens SET is_paid = ? WHERE id = ?", (status, token_id))
    conn.commit()
    conn.close()


def get_paid_status(token_id: int):
    conn = sqlite3.connect("parking.db")
    c = conn.cursor()
    c.execute("SELECT is_paid FROM parking_tokens WHERE id = ?", (token_id,))
    result = c.fetchone()
    conn.close()
    if result is not None:
        return bool(result[0])
    else:
        return None  # Or raise an exception if token not found


# Function to generate a QR code linking to the payment page
def generate_payment_qr(token_id):
    payment_url = f"http://localhost:8000/pay/{token_id}"  # Replace with your domain
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(payment_url)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")
    qr_filename = f"qrcode_{token_id}.png"
    img.save(qr_filename)
    return qr_filename


def get_gate_status(name: Literal["entry", "exit"]):
    """Fetch the open status of the gate by its name."""
    conn = sqlite3.connect("parking.db")
    c = conn.cursor()
    c.execute("SELECT open FROM GATE WHERE name = ?", (name,))
    result = c.fetchone()
    conn.close()
    if result is not None:
        return bool(result[0])
    else:
        return None  # Or raise an exception if gate not found


def change_gate_status(name: Literal["entry", "exit"], status: bool):
    """Change the open status of the gate by its name."""
    conn = sqlite3.connect("parking.db")
    c = conn.cursor()
    c.execute("UPDATE GATE SET open = ? WHERE name = ?", (int(status), name))
    conn.commit()
    conn.close()
