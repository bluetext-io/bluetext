import logging
from typing import Optional
from pydantic import BaseModel
from twilio.rest import Client as TwilioRestClient
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)


class TwilioConf(BaseModel):
    """Twilio configuration"""
    account_sid: str
    auth_token: str
    from_phone_number: str


class TwilioClient:
    """
    Twilio client for SMS and messaging operations.
    """

    def __init__(self, config: TwilioConf):
        self.config = config
        self._client: Optional[TwilioRestClient] = None

    async def initialize(self) -> None:
        """Initialize the Twilio client"""
        try:
            self._client = TwilioRestClient(
                self.config.account_sid,
                self.config.auth_token
            )
            logger.info("Twilio client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {e}")
            raise

    async def init_connection(self) -> None:
        """Verify Twilio connection by fetching account info"""
        if not self._client:
            raise RuntimeError("Twilio client not initialized")

        try:
            account = self._client.api.accounts(self.config.account_sid).fetch()
            logger.info(f"Twilio connection established for account: {account.friendly_name}")
        except TwilioRestException as e:
            logger.error(f"Failed to verify Twilio connection: {e}")
            raise

    async def close(self) -> None:
        """Close the Twilio client"""
        if self._client:
            self._client = None
            logger.info("Twilio client closed")

    @property
    def client(self) -> TwilioRestClient:
        """Get the underlying Twilio REST client"""
        if not self._client:
            raise RuntimeError("Twilio client not initialized")
        return self._client

    async def send_sms(self, to_phone_number: str, message: str) -> dict:
        """
        Send an SMS message using Twilio.

        Args:
            to_phone_number: The recipient's phone number (e.g., '+1234567890')
            message: The message content to send

        Returns:
            dict: Message details including SID, status, and other metadata

        Raises:
            TwilioRestException: If the SMS fails to send
        """
        try:
            message_obj = self.client.messages.create(
                body=message,
                from_=self.config.from_phone_number,
                to=to_phone_number
            )

            result = {
                'sid': message_obj.sid,
                'status': message_obj.status,
                'to': message_obj.to,
                'from': message_obj.from_,
                'body': message_obj.body,
                'date_created': message_obj.date_created,
                'price': message_obj.price,
                'price_unit': message_obj.price_unit
            }

            logger.info(f"SMS sent successfully to {to_phone_number}, SID: {message_obj.sid}")
            return result

        except TwilioRestException as e:
            logger.error(f"Failed to send SMS to {to_phone_number}: {e}")
            raise

    def health_check(self) -> dict:
        """Check if Twilio client is healthy"""
        if not self._client:
            return {"connected": False, "status": "not_initialized"}

        try:
            # Try to fetch account info as a health check
            account = self._client.api.accounts(self.config.account_sid).fetch()
            return {
                "connected": True,
                "status": "healthy",
                "account": account.friendly_name
            }
        except Exception as e:
            return {
                "connected": False,
                "status": "error",
                "error": str(e)
            }