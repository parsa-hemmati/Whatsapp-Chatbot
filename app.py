import os
from flask import Flask, request
from openai import OpenAI
from twilio.rest import Client
import traceback

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
        # Log the full request payload for debugging
        request_data = request.form.to_dict()
        print("Incoming request data:", request_data)

        # Ignore status update requests (they don't contain a Body field)
        if "Body" not in request_data:
            print("Ignoring status update request.")
            return "Ignored", 200

        # Initialize clients with environment variables
        OPENAI_API_KEY = get_env_var("OPENAI_API_KEY")
        TWILIO_ACCOUNT_SID = get_env_var("TWILIO_ACCOUNT_SID")
        TWILIO_AUTH_TOKEN = get_env_var("TWILIO_AUTH_TOKEN")
        TWILIO_WHATSAPP_NUMBER = get_env_var("TWILIO_WHATSAPP_NUMBER")
        
        # Ensure the WhatsApp number has the correct format
        if not TWILIO_WHATSAPP_NUMBER.startswith("whatsapp:"):
            TWILIO_WHATSAPP_NUMBER = f"whatsapp:{TWILIO_WHATSAPP_NUMBER}"

        # Extract message details
        incoming_msg = request_data.get("Body", "").strip()
        sender = request_data.get("From", "")

        if not incoming_msg:
            raise ValueError("Received an empty message.")
        if not sender:
            raise ValueError("Missing 'From' parameter in request.")

        print(f"Received message: {incoming_msg} from {sender}")

        # Fix OpenAI API usage
        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
            
            # Use the correct OpenAI API format
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": incoming_msg}
                ]
            )
            
            # Extract the response text
            reply = response.choices[0].message.content
            print(f"ChatGPT response: {reply}")

        except Exception as e:
            print(f"OpenAI Error: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            reply = "I apologize, but I'm having trouble connecting to my AI service right now. Please try again later."

        # Fix Twilio WhatsApp number format
        try:
            twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            
            # Ensure the recipient number has the correct format
            to_number = sender
            if not to_number.startswith("whatsapp:"):
                to_number = f"whatsapp:{to_number}"
            
            print(f"Sending message from {TWILIO_WHATSAPP_NUMBER} to {to_number}")

            # Send message via Twilio
            message = twilio_client.messages.create(
                from_=TWILIO_WHATSAPP_NUMBER,
                body=reply,
                to=to_number
            )
            print(f"Sent message with SID: {message.sid}")
        except Exception as e:
            print(f"Twilio Error: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return "Error sending message", 500

        return "OK", 200

    except ValueError as e:
        print(f"Configuration Error: {str(e)}")
        return str(e), 400
    except Exception as e:
        print(f"Unexpected Error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return "Internal server error", 500

@app.route("/", methods=["GET"])
def index():
    """Simple health check endpoint"""
    return "WhatsApp Chatbot is running!", 200

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
