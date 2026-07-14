import json # Parsing and dumping payloads
import logging # Logging for CloudWatch
import ssl # Required for urllib SSL
import urllib.request # Requesting APIs
import urllib.error # Handling
import hashlib # Generating signature/hashing for authentication
import hmac # ^
import uuid # Generating ID's
from datetime import datetime, timezone
import os

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# These should be set as Lambda Environment Variables. Ensure Yeastar host does NOT have http/https schema
yeastar_host = os.environ.get('HOST')
path = os.environ.get('PATH') # Set as trailing webhook endpoint on PBX
secret = os.environ.get('SECRET')

def getTime():
    now = datetime.now(timezone.utc).astimezone()  # local time with offset
    s = now.isoformat(timespec="milliseconds")
    return s

def send_webhook(
    host,
    path,
    timeout,
    msg_to,
    msg_from,
    msg_text,
    msg_date,
    msg_id,):
    body = {
        "data": {
            "event_type": "message.received",
            "id": msg_id,
            "payload": {
                "id": msg_id,
                "from": {
                    "phone_number": msg_from,
                },
                "to": [
                    {
                        "phone_number": msg_to,
                    }
                ],
                "text": msg_text,
                "received_at": str(getTime()),
            },
            "record_type": "message",
        },
    }

    payload_bytes = json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    signature = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

    url = f"https://{host}{path}"
    req = urllib.request.Request(
        url=url,
        data=payload_bytes,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Signature-256": f"sha256={signature}",
        },
    )

    context = ssl.create_default_context()

    try:
        with urllib.request.urlopen(req, timeout=timeout, context=context) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    

def lambda_handler(event, context):
    logger.info(f"RAW event: {event}")

    # Extract fields from query string (this matches your logged event)
    qsp = event.get("queryStringParameters") or {}

    msg_from = qsp.get("from")
    msg_to = qsp.get("to")
    msg_text = qsp.get("msg")
    msg_date = qsp.get("date")
    msg_id = qsp.get("msgid")

    resp = {
        "ok": True,
        "from": msg_id,
        "to": msg_to,
        "msg": msg_text,
        "date": msg_date,
        "msgid": msg_id,
    }

    logger.info(f"{msg_from} to {msg_to}: {msg_text} -- ID: {msg_id}")

    status, response = send_webhook(
        yeastar_host,
        path,
        10,
        msg_to,
        msg_from,
        msg_text,
        msg_date,
        msg_id,
    )


    if status == 400 or status == "400":
        raise Exception(f"Webhook failed: {status}: {response.decode('utf-8', errors='replace')}")
    else:
        logger.info(f"Message ID {msg_id} forwarded to {yeastar_host}")

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(resp),
    }
