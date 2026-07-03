import urllib.request # Requesting APIs
import urllib.error # Handling
import secrets # Noncing
import string # Noncing
import time # Timestamping
import hmac, hashlib, base64 # HMAC-SHA256 signing
import os # Environment variables
import logging # Lambda Logging
import json # Parsing and dumping payloads

# Set logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get ENV variables
KEY = os.environ.get("KEY")
SECRET = os.environ.get("SECRET")

# Needed for SMS Global authentication
def generateNonce():
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(32))

# Needed for SMS Global authentication
def generateMAC(ts, nonce, method, uri, host, port, extra_data=""):
    # Exact canonical string: each part separated by '\n' and ends with a final '\n'
    msg = "\n".join([
        str(ts),
        nonce,
        method,
        uri,
        host,
        str(port),
        extra_data
    ]) + "\n"

    digest = hmac.new(
        SECRET.encode("utf-8"),
        msg.encode("utf-8"),
        hashlib.sha256
    ).digest()

    return base64.b64encode(digest).decode("ascii")

def sendMessage(origin, destination, message):
    nonce = generateNonce()
    ts = int(time.time())

    method = "POST"
    uri = "/v2/sms"
    host = "api.smsglobal.com"
    port = 443
    extra_data = "" # Extra data can be anything according to SMS Global specs, just needs to exist for authentication

    mac = generateMAC(ts, nonce, method, uri, host, port, extra_data)

    headers = {
        "Authorization": f'MAC id="{KEY}", ts="{ts}", nonce="{nonce}", mac="{mac}"',
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    # Construct payload
    body_dict = {
        "origin": origin,
        "destination": destination,
        "message": message,
    }
    payload_bytes = json.dumps(body_dict, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    # Create request to SMS Global API
    req = urllib.request.Request(
        url=f"https://{host}{uri}",
        data=payload_bytes,
        headers=headers,
        method="POST",
    )

    try: # Send request
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception:
        return "Error sending SMS"

def lambda_handler(event, context):
    logger.info(f"RAW event: {event}") # Log raw event for analysis if needed

    if isinstance(event, dict) and any(k in event for k in ("from", "text", "to")):
        payload = event
    elif isinstance(event.get("body"), (str, bytes, bytearray)) and event.get("body") not in (None, b"", ""):
        body = event["body"]
        if isinstance(body, (bytes, bytearray)):
            body = body.decode("utf-8", errors="replace")
        payload = json.loads(body)
    else:
        payload = event.get("queryStringParameters") or event.get("formData") or {}

    # Extract values from payload

    msg_from = payload.get("from")
    msg_text = payload.get("text")
    msg_to = payload.get("to")

    # Send message and get response for PBX
    status, response = sendMessage(msg_from, msg_to, msg_text)
    response = json.loads(response.decode("utf-8"))
    msg_id = response["messages"][0]["outgoing_id"] # Parses SMS Global response for message ID as required by Yeastar
    logger.info(f"SMS Sent: {msg_from} to {msg_to}: \"{msg_text}\"")
    # Send response back to PBX
    return {
        "statusCode": status,
        "isBase64Encoded": False,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "data": {"id": str(msg_id)}
        }),
    }
