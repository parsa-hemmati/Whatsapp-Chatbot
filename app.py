import os
from flask import Flask, request
import openai
from twilio.rest import Client
import time

app = Flask(__name__)

def get_env_var(var_name):
    """Get environment variable with error handling"""
    value = os.getenv(var_name)
    if not value:
        raise ValueError(f"Missing required environment variable: {var_name}")
    return value

@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    """Handles incoming WhatsApp messages and responds using OpenAI Assistants API."""
    try:
        # Initialize clients with environment variables
        OPENAI_API_KEY = get_env_var("OPENAI_API_KEY")
        TWILIO_ACCOUNT_SID = get_env_var("TWILIO_ACCOUNT_SID")
        TWILIO_AUTH_TOKEN = get_env_var("TWILIO_AUTH_TOKEN")
        TWILIO_WHATSAPP_NUMBER = get_env_var("TWILIO_WHATSAPP_NUMBER")
        ASSISTANT_ID = get_env_var("ASSISTANT_ID")

        # Set up clients
        openai.api_key = OPENAI_API_KEY
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        # Process incoming message
        incoming_msg = request.values.get("Body", "").strip()
        sender = request.values.get("From", "")

        if not incoming_msg or not sender:
            raise ValueError("Missing required message parameters")

        # Create a new thread in OpenAI Assistant API
        thread = openai.beta.threads.create()
        thread_id = thread.id

        # Send message to OpenAI Assistant
        run = openai.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID,
            messages=[{"role": "user", "content": incoming_msg}]
        )

        # Wait for completion
        max_retries = 30  # Maximum number of retries (60 seconds total)
        retries = 0
        while retries < max_retries:
            run_status = openai.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            if run_status.status == "completed":
                break
            time.sleep(2)  # Check every 2 seconds
            retries += 1

        if retries >= max_retries:
            raise TimeoutError("OpenAI Assistant response timeout")

        # Get AI response
        messages = openai.beta.threads.messages.list(thread_id=thread_id)
        reply = messages.data[0].content[0].text.value

        # Send response via Twilio
        twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=reply,
            to=sender
        )

        return "OK", 200

    except ValueError as e:
        print(f"Configuration Error: {str(e)}")
        return str(e), 400
    except TimeoutError as e:
        print(f"Timeout Error: {str(e)}")
        return str(e), 504
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
        get_env_var("ASSISTANT_ID")
        print("All required environment variables are set")
    except ValueError as e:
        print(f"Error: {str(e)}")
        exit(1)

    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
