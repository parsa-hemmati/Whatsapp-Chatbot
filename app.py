from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import os
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize Twilio client
twilio_client = Client(
    os.getenv('TWILIO_ACCOUNT_SID'),
    os.getenv('TWILIO_AUTH_TOKEN')
)

# Initialize OpenAI client
openai.api_key = os.getenv('OPENAI_API_KEY')

@app.route("/webhook", methods=['POST'])
def webhook():
    # Get the message from the request
    incoming_msg = request.values.get('Body', '').lower()
    sender = request.values.get('From', '')
    
    # Create a response object
    resp = MessagingResponse()
    
    try:
        # Get response from OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": incoming_msg}
            ]
        )
        
        # Get the assistant's response
        bot_response = response.choices[0].message.content
        
        # Send the response back
        resp.message(bot_response)
        
    except Exception as e:
        resp.message("I apologize, but I encountered an error. Please try again later.")
        print(f"Error: {str(e)}")
    
    return str(resp)

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 