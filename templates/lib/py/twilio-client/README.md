# Twilio Client Library

An async Twilio client library for FastAPI applications with SMS messaging support.

## Features

- Async SMS sending with Twilio
- Health check endpoint support
- Automatic error handling and logging
- Type-safe configuration with Pydantic

## Installation

This library is installed automatically when you run the `api-add-twilio-client` tool in your API service.

## Configuration

Set these environment variables in your polytope.yml:

- `TWILIO_ACCOUNT_SID`: Your Twilio Account SID
- `TWILIO_AUTH_TOKEN`: Your Twilio Auth Token
- `TWILIO_FROM_PHONE_NUMBER`: Your Twilio phone number (E.164 format, e.g., "+1234567890")

## Usage

### Using in Routes

```python
from ..routes.utils import TwilioSMS

@router.post('/send-notification')
async def send_notification(
    phone: str,
    message: str,
    twilio: TwilioSMS
):
    result = await twilio.send_sms(
        to_phone_number=phone,
        message=message
    )
    return {"success": True, "sid": result['sid']}
```

### Direct Client Access

```python
from twilio_client import TwilioClient, TwilioConf

# Get the client from FastAPI app state
client = request.app.state.twilio_client

# Send an SMS
result = await client.send_sms(
    to_phone_number="+1234567890",
    message="Hello from your API!"
)
```

### Response Format

The `send_sms` method returns a dictionary with:

- `sid`: Message SID from Twilio
- `status`: Message status (queued, sent, delivered, etc.)
- `to`: Recipient phone number
- `from`: Sender phone number
- `body`: Message content
- `date_created`: When the message was created
- `price`: Message cost (if available)
- `price_unit`: Currency of the price

## Example SMS Routes

When you add the Twilio client, example SMS routes are created at `src/backend/routes/sms.py`. These include:

- `POST /sms/send` - Send an SMS message
- `GET /sms/health` - Check Twilio service health

Register these routes in your main router:

```python
from .sms import router as sms_router
router.include_router(sms_router)
```

## Testing

Test the SMS endpoint:

```bash
curl -X POST http://localhost:3030/sms/send \
  -H 'Content-Type: application/json' \
  -d '{"to": "+1234567890", "message": "Hello from API!"}'
```