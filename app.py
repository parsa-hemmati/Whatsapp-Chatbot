import os
from flask import Flask, request
import openai
from twilio.rest import Client
from openai import OpenAI

app = Flask(__name__)

def get_env_var(var_name):
    """Get environment variable with error handling"""
    value = os.getenv(var_name)
    if not value:
        raise ValueError(f"Missing required environment variable: {var_name}")
    return value

@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    """Handles incoming WhatsApp messages and responds using ChatGPT."""
    try:
        # Initialize clients with environment variables
        OPENAI_API_KEY = get_env_var("OPENAI_API_KEY")
        TWILIO_ACCOUNT_SID = get_env_var("TWILIO_ACCOUNT_SID")
        TWILIO_AUTH_TOKEN = get_env_var("TWILIO_AUTH_TOKEN")
        TWILIO_WHATSAPP_NUMBER = get_env_var("TWILIO_WHATSAPP_NUMBER")

        # Set up clients
        client = OpenAI(api_key=OPENAI_API_KEY)
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        # Process incoming message
        incoming_msg = request.values.get("Body", "").strip()
        sender = request.values.get("From", "")

        if not incoming_msg or not sender:
            raise ValueError("Missing required message parameters")

        # Get response from ChatGPT
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": incoming_msg}
            ]
        )

        # Extract the response text
        reply = response.choices[0].message.content

        # Send response via Twilio
        twilio_client.messages.create(
            from_=f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
            body=reply,
            to=sender
        )

        return "OK", 200

    except ValueError as e:
        print(f"Configuration Error: {str(e)}")
        return str(e), 400
    except Exception as e:
        print(f"Unexpected Error: {str(e)}")
        return "Internal server error", 500

if __name__ == "__main__":
    # Verify environment variables on startup
    try:
        get_env_var("OPENAI_API_KEY")
        get_env_var("TWILIO_ACCOUNT_SID")
        get_env_var("TWILIO_AUTH_TOKEN")
        get_env_var("TWILIO_WHATSAPP_NUMBER")
        print("All required environment variables are set")
    except ValueError as e:
        print(f"Error: {str(e)}")
        exit(1)

    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
