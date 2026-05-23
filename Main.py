import os
import telebot
from flask import Flask, request
from openai import OpenAI

# 1. Fetch Environment Variables
# You will set these in the Render Dashboard
BOT_TOKEN = os.environ.get("BOT_TOKEN")
HF_TOKEN = os.environ.get("HF_TOKEN")

# Render automatically provides this environment variable (e.g., https://your-app-name.onrender.com)
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL") 

# 2. Initialize Telegram Bot & OpenAI Client
bot = telebot.TeleBot(BOT_TOKEN)

# Python equivalent of your JS OpenAI snippet
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

app = Flask(__name__)

# 3. Handle incoming Telegram messages
@bot.message_handler(func=lambda message: True)
def handle_chat(message):
    try:
        # Show 'typing...' status in Telegram
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Request completion from Hugging Face via OpenAI client
        chat_completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V4-Pro:novita",
            messages=[
                {
                    "role": "user",
                    "content": message.text,
                }
            ],
        )
        
        # Extract response text and reply to the user
        reply_text = chat_completion.choices[0].message.content
        bot.reply_to(message, reply_text)
        
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {str(e)}")

# 4. Flask Routes for Telegram Webhook
@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook_handler():
    # Telegram sends updates to this secure route
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Forbidden', 403

@app.route("/")
def index():
    return "Telegram Bot is running smoothly on Render!", 200

# 5. Application Startup
if __name__ == "__main__":
    # Remove any existing webhooks and set the new one pointing to Render
    bot.remove_webhook()
    
    if RENDER_EXTERNAL_URL:
        # Securely set webhook URL to https://your-app.onrender.com/BOT_TOKEN
        webhook_url = f"{RENDER_EXTERNAL_URL}/{BOT_TOKEN}"
        bot.set_webhook(url=webhook_url)
        print(f"Webhook set to: {webhook_url}")
    else:
        print("Warning: RENDER_EXTERNAL_URL not found. Webhook not set.")
        
    # Run Flask app (Render dynamically assigns a PORT environment variable)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
