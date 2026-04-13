"""quick test to see if twilio whatsapp is working"""
from twilio.rest import Client
import json

with open("alert_config.json") as f:
    c = json.load(f)

print("SID:", c["twilio_sid"][:10] + "...")
print("From:", c.get("twilio_whatsapp", "not set"))
print("To:", c["alert_phones"][0])

try:
    client = Client(c["twilio_sid"], c["twilio_token"])

    to_num = c["alert_phones"][0]
    if not to_num.startswith("whatsapp:"):
        to_num = "whatsapp:" + to_num

    msg = client.messages.create(
        body="HERMES test - WhatsApp alerts working",
        from_=c.get("twilio_whatsapp", "whatsapp:+14155238886"),
        to=to_num
    )
    print("SUCCESS:", msg.sid)
except Exception as e:
    print("ERROR:", e)
