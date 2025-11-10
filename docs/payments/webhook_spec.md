# Payment Webhook Specification

## URL

POST /webhooks/payments

## Signature Header

X-Signature: <hmac-sha256>

## Body Example

```json
{
  "order_id": "uuid",
  "status": "paid"
}