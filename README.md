# Yeastar-PBX_to_SMSGlobal-API
Acts as middleware between the Yeastar PBX General SMS provider system and the SMS Global API, which would otherwise be incompatible. Requires 2 AWS Lambda functions with a HTTP API Gateway each.

## Prerequisites

1. Your SMS Global account must have a virtual number, and valid REST API credentials (key + secret)
2. Two AWS Lambda functions - One for `PBX -> SMS Global`, the other for `SMS Global -> PBX`.
3. An *open* HTTP API Gateway on each function

## Setup

### PBX Configuration

1. Create a new SMS Channel under `Messaging -> Message Channel -> Add -> SMS`
2. Set your desired channel name
3. Set ITSP to "General"
4. Set "API Address for Sending Messages" to your Lambda `PBX -> SMS Global` function's open HTTP API Gateway
5. Set key and secret to your SMS Global API credentials - While the PBX does not directly authenticate with SMS Global, the outbound SMS Lambda function will verify the Bearer token so that bad actors can't run up your SMS bill :)

### SMS Global Configuration

1. Ensure your virtual number/s are enabled for SMS
2. Set the callback URL for replies to your `SMS Global -> PBX` function

### PBX -> SMS Global (Outbound SMS)

1. Paste the contents of `pbx-to-smsglobal.py` into your `PBX -> SMS Global` function
2. Ensure the environment variables are set as below

| Key    | Value        |
|--------|--------------|
| KEY    | \<api-key\>    |
| SECRET | \<api-secret\> |

### SMS Global -> PBX (Inbound SMS)

1. Paste the contents of `smsglobal-to-pbx.py` into your `SMS Global -> PBX` function
2. Ensure the environment variables are set as below

| Key    | Value                                                                   |
|--------|-------------------------------------------------------------------------|
| SECRET | \<api-secret\>                                                            |
| HOST   | \<pbx-domain e.g mypbx.au.ycmcloud.com\>                                  |
| PATH   | \<pbx-webhook e.g /api/v1.0/webhook/general/abcdefghijklmnop1234567890\> |
