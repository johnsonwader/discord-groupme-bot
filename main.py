import discord
import aiohttp
import asyncio
import os
from discord.ext import commands
from aiohttp import web
import threading
import time

# Configuration from environment variables
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GROUPME_BOT_ID = os.getenv("GROUPME_BOT_ID")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
PORT = int(os.getenv("PORT", "8000"))

# GroupMe API endpoint
GROUPME_POST_URL = "https://api.groupme.com/v3/bots/post"

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Global variable to track bot status
bot_status = {"ready": False, "start_time": time.time()}

# Simple health check that runs in a separate thread
def run_health_server():
    """Run health check server in a separate thread"""
    async def health_check(request):
        return web.json_response({
            "status": "healthy",
            "bot_ready": bot_status["ready"],
            "uptime": time.time() - bot_status["start_time"]
        })

    async def start_server():
        app = web.Application()
        app.router.add_get('/', health_check)
        app.router.add_get('/health', health_check)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', PORT)
        await site.start()
        print(f"🏥 Health check server running on port {PORT}")
        
        # Keep the server running
        while True:
            await asyncio.sleep(60)

    # Run the server
    asyncio.new_event_loop().run_until_complete(start_server())

async def send_to_groupme(message_text, author_name):
    """Send a message to GroupMe"""
    if not message_text.strip():
        return
    
    payload = {
        "bot_id": GROUPME_BOT_ID,
        "text": f"{author_name}: {message_text}"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(GROUPME_POST_URL, json=payload) as response:
                if response.status == 202:
                    print(f"✅ Message sent to GroupMe: {message_text[:50]}...")
                else:
                    print(f"❌ Failed to send to GroupMe. Status: {response.status}")
                    error_text = await response.text()
                    print(f"Error: {error_text}")
        except Exception as e:
            print(f"❌ Error sending to GroupMe: {e}")

@bot.event
async def on_ready():
    global bot_status
    bot_status["ready"] = True
    print(f'🤖 {bot.user} has connected to Discord!')
    print(f'📺 Monitoring channel ID: {DISCORD_CHANNEL_ID}')
    print(f'🚀 Bot is ready and running on Railway!')

@bot.event
async def on_message(message):
    # Don't respond to bot messages
    if message.author.bot:
        return
    
    # Only forward messages from the specified channel
    if message.channel.id == DISCORD_CHANNEL_ID:
        print(f"📨 Forwarding message from {message.author.display_name}: {message.content[:50]}...")
        await send_to_groupme(message.content, message.author.display_name)
    
    # Process commands
    await bot.process_commands(message)

@bot.command(name='test')
async def test_bridge(ctx):
    """Test command to verify the bridge is working"""
    if ctx.channel.id == DISCORD_CHANNEL_ID:
        await send_to_groupme("🧪 Bridge test message from Railway!", "Bot Test")
        await ctx.send("✅ Test message sent to GroupMe!")
    else:
        await ctx.send("❌ This command only works in the monitored channel.")

@bot.command(name='status')
async def status(ctx):
    """Check bot status"""
    if ctx.channel.id == DISCORD_CHANNEL_ID:
        await ctx.send(f"🟢 Bot is online and monitoring this channel!\n🔗 Connected to GroupMe: {'✅' if GROUPME_BOT_ID else '❌'}")

if __name__ == "__main__":
    # Validate environment variables
    if not DISCORD_BOT_TOKEN:
        print("❌ DISCORD_BOT_TOKEN environment variable not set!")
        exit(1)
    
    if not GROUPME_BOT_ID:
        print("❌ GROUPME_BOT_ID environment variable not set!")
        exit(1)
    
    if DISCORD_CHANNEL_ID == 0:
        print("❌ DISCORD_CHANNEL_ID environment variable not set!")
        exit(1)
    
    # Start health check server in a separate thread
    print("🏥 Starting health check server...")
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    # Give the health server a moment to start
    time.sleep(2)
    
    # Start Discord bot
    print("🚀 Starting Discord to GroupMe bridge...")
    try:
        bot.run(DISCORD_BOT_TOKEN)
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
