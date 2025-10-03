import os
import discord
from dotenv import load_dotenv
import aiohttp  # async HTTP requests
import asyncio

MAX_DISCORD_LENGTH = 2000  # Discord message character limit

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
BACKEND_URL = "http://127.0.0.1:8000/api/rag-query"  # change if deployed

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}!')

async def ask_backend(query):
    """Send the query to the FastAPI backend and get the response."""
    async with aiohttp.ClientSession() as session:
        payload = {"query": query}
        async with session.post(BACKEND_URL, json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data["rag_response"]
            else:
                return f"Error: Backend returned status {resp.status}"

def split_long_text(text, chunk_size=MAX_DISCORD_LENGTH):
    """Split text into chunks small enough for Discord messages."""
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

@client.event
async def on_message(message):
    if message.author == client.user or message.author.bot:
        return

    if message.content.startswith('!ask'):
        query = message.content[len('!ask'):].strip()
        await message.channel.send(f"Processing your question: {query}")

        try:
            response = await ask_backend(query)
            response_chunks = split_long_text(response)
            for i, chunk in enumerate(response_chunks):
                bot_msg = await message.channel.send(chunk)

            # Add reactions only to the first chunk
            stars = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']
            for star in stars:
                await bot_msg.add_reaction(star)

            def check(reaction, user):
                return (
                    user == message.author and
                    str(reaction.emoji) in stars and
                    reaction.message.id == bot_msg.id
                )

            try:
                reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
                rating = stars.index(str(reaction.emoji)) + 1

                feedback_payload = {
                    "query": query,
                    "rag_response": response,
                    "rating": rating,
                    "comment": None
                }

                async with aiohttp.ClientSession() as session:
                    await session.post("http://127.0.0.1:8000/api/feedback", json=feedback_payload)

                await message.channel.send("Thanks for your feedback! ✅")

            except asyncio.TimeoutError:
                await message.channel.send("No feedback received. You can still provide it later.")

        except Exception as e:
            await message.channel.send(f"Error: {e}")

client.run(TOKEN)
