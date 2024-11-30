from src.config import settings
from kavenegar import KavenegarAPI, APIException, HTTPException

API_KEY = settings.sms_service_api_key
SENDER_NUMBER = settings.sms_service_sender_number


class SmsService:
    def __init__(self) -> None:
        self.api_key = API_KEY
        self.sender_number = SENDER_NUMBER
        self.base_url = "https://api.kavenegar.com"
        self.url_inventory = UrlInventory()
        # self.proxy_url = settings.server_proxy_url

    def send_sms(self, receiver: str, message: str):
        try:
            api = KavenegarAPI(apikey=self.api_key)
            params = {
                "sender": self.sender_number,
                "receptor": receiver,
                "message": message,
            }
            response = api.sms_send(params)
            decoded_response = self._decode_response(response)
            return decoded_response
        except APIException as e:
            raise SendSmsError(
                f"Failed to send the SMS: {self._decode_response(str(e))}"
            )
        except HTTPException as e:
            raise SendSmsError(
                f"Failed to send the SMS: {self._decode_response(str(e))}"
            )

    def _decode_response(self, msg: str):
        try:
            # If the message contains byte-like escaped sequences (e.g., \xXX), we need to decode it
            if isinstance(msg, str) and "\\x" in msg:
                # Convert the string with escape sequences into a bytes object
                byte_data = (
                    bytes(msg, "utf-8").decode("unicode_escape").encode("latin1")
                )

                # Decode the bytes into a readable UTF-8 string
                decoded_message = byte_data.decode("utf-8")
                return decoded_message
            else:
                return msg  # If no decoding is needed, return the original message
        except Exception as e:
            return f"Error decoding message: {e}"


class UrlInventory:
    def __init__(self):
        self.api_key = API_KEY
        self.send_sms = f"/v1/{self.api_key}/sms/send.json"


class SmsServiceError(Exception):
    pass


class SendSmsError(SmsServiceError):
    pass


class EncodeError(SmsServiceError):
    pass
