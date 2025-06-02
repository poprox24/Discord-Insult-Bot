import discord
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
bot = discord.Bot()

@bot.event
async def on_ready():
    print(f"{bot.user} is online.")

client = OpenAI(api_key=os.getenv("OPENAI_TOKEN"))

# Generate The Messages
def generate_messages():
    print("Attempting to generate new messages")
    response = client.chat.completions.create(
        model="gpt-4.1-mini-2025-04-14",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a bot that generates insults and reminders to drink water. "
                    "Respond only in JSON, no other text. "
                    "You can capitalize WHOLE WORDS in order to express sarcasm or disrespect. "
                    "Occasionally use obscure words."
                    "Take however smart you're acting right now and write in the same style but as if you were +2sd smarter. "
                    "Use late millenial slang not boomer slang. Mix in zoomer slang occasionally if tonally-inappropriate."
                )
            },
            {
                "role": "user",
                "content": "Generate a list of 5 insults, make them hit deep, occasionally generate messages reminding user to drink water"
            }
        ]
    )
    print("Response received successfully:")

    return response.choices[0].message.content
    
#Test generate responses
print(generate_messages())

#Go online
bot.run(os.getenv("BOT_TOKEN"))