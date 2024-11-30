from src.config import settings
import httpx

API_KEY = settings.sms_service_api_key


class SmsService:
    def __init__(self) -> None:
        self.api_key = API_KEY
        self.base_url = "https://api.kavenegar.com"
        self.url_inventory = UrlInventory()
        # self.proxy_url = settings.server_proxy_url

    def send_sms(self, receptor: str, message: str):

        url = f"https://api.kavenegar.com/v1/{self.api_key}/sms/send.json"
        payload = {
            "receptor": receptor,
            "message": message,
        }

        try:
            response = httpx.post(url, json=payload, timeout=10)
            response.raise_for_status()
            decoded_response = self._decode_response(response)
            return decoded_response
        except httpx.RequestError as e:
            return {
                "error": f"An error occurred while sending the request: {self._decode_response(str(e))}"
            }
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP error occurred: {self._decode_response(str(e))}"}

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
