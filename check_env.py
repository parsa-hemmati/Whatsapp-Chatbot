import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# List of required environment variables
required_vars = [
    "TWILIO_ACCOUNT_SID",
    "TWILIO_AUTH_TOKEN",
    "TWILIO_WHATSAPP_NUMBER",
    "OPENAI_API_KEY"
]

print("Checking environment variables...")
print("-" * 30)

# Check each required variable
all_present = True
for var in required_vars:
    value = os.getenv(var)
    if value:
        # Show first and last 4 characters for security
        masked_value = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "****"
        print(f"✓ {var} is set: {masked_value}")
    else:
        print(f"✗ {var} is missing!")
        all_present = False

print("-" * 30)
if all_present:
    print("All required environment variables are set!")
else:
    print("Some environment variables are missing!")
