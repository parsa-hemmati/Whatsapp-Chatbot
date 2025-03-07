import os
import traceback
import openai
from flask import Flask, request
from twilio.rest import Client

app = Flask(__name__)

def get_env_var(var_name):
    """Get environment variable with error handling."""
    val = os.getenv(var_name)
    if not val:
        raise ValueError(f"Missing required environment variable: {var_name}")
    return val

@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    """
    Handles incoming WhatsApp messages and responds using OpenAI's GPT-3.5-turbo.
    Twilio will POST to this endpoint when a new message arrives.
    """
    try:
        # Convert the incoming request form data to a dict
        request_data = request.form.to_dict()
        print("Incoming request data:", request_data)

        # Ignore Twilio status callbacks that do not contain 'Body'
        if "Body" not in request_data:
            print("Ignoring non-message request.")
            return "Ignored", 200

        # Load and verify environment variables
        OPENAI_API_KEY = get_env_var("OPENAI_API_KEY")
        TWILIO_ACCOUNT_SID = get_env_var("TWILIO_ACCOUNT_SID")
        TWILIO_AUTH_TOKEN = get_env_var("TWILIO_AUTH_TOKEN")
        TWILIO_WHATSAPP_NUMBER = get_env_var("TWILIO_WHATSAPP_NUMBER")

        # Ensure the 'From' WhatsApp number has the correct format
        if not TWILIO_WHATSAPP_NUMBER.startswith("whatsapp:"):
            TWILIO_WHATSAPP_NUMBER = f"whatsapp:{TWILIO_WHATSAPP_NUMBER}"

        incoming_msg = request_data.get("Body", "").strip()
        sender = request_data.get("From", "").strip()

        if not incoming_msg:
            raise ValueError("Received an empty message.")
        if not sender:
            raise ValueError("Missing 'From' in request.")

        print(f"Received message: {incoming_msg} from {sender}")

        # Set up OpenAI
        openai.api_key = OPENAI_API_KEY

        # Create a ChatCompletion request
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": incoming_msg}
                ]
            )
            reply = response.choices[0].message.content
            print(f"OpenAI response: {reply}")
        except Exception as e:
            print("OpenAI Error:", e)
            print("Traceback:", traceback.format_exc())
            reply = (
                "Sorry, I'm having trouble connecting to the AI service right now. "
                "Please try again later."
            )

        # Send the reply via Twilio
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        to_number = sender
        if not to_number.startswith("whatsapp:"):
            to_number = f"whatsapp:{to_number}"

        print(f"Sending message from {TWILIO_WHATSAPP_NUMBER} to {to_number}")

        try:
            message = twilio_client.messages.create(
                from_=TWILIO_WHATSAPP_NUMBER,
                body=reply,
                to=to_number
            )
            print(f"Sent message with SID: {message.sid}")
        except Exception as e:
            print("Twilio Error:", e)
            print("Traceback:", traceback.format_exc())
            return "Error sending message", 500

        return "OK", 200

    except ValueError as e:
        # Typically means a missing environment variable or config issue
        print("Configuration Error:", e)
        return str(e), 400
    except Exception as e:
        print("Unexpected Error:", e)
        print("Traceback:", traceback.format_exc())
        return "Internal server error", 500

@app.route("/", methods=["GET"])
def index():
    """Simple health-check endpoint."""
    return "WhatsApp Chatbot is running!", 200

if __name__ == "__main__":
    # Validate all required environment variables at startup
    try:
        get_env_var("OPENAI_API_KEY")
        get_env_var("TWILIO_ACCOUNT_SID")
        get_env_var("TWILIO_AUTH_TOKEN")
        get_env_var("TWILIO_WHATSAPP_NUMBER")
        print("All required environment variables are set.")
    except ValueError as e:
        print(f"Error: {e}")
        exit(1)

    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
