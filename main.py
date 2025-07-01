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
GROUPME_ACCESS_TOKEN = os.getenv("GROUPME_ACCESS_TOKEN")  # Add this to your Railway environment variables
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
PORT = int(os.getenv("PORT", "8000"))

# GroupMe API endpoints
GROUPME_POST_URL = "https://api.groupme.com/v3/bots/post"
GROUPME_IMAGE_UPLOAD_URL = "https://image.groupme.com/pictures"

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

async def upload_image_to_groupme(image_url):
    """Download image from Discord and upload to GroupMe"""
    if not GROUPME_ACCESS_TOKEN:
        print("❌ GroupMe access token not available for image upload")
        return None
    
    async with aiohttp.ClientSession() as session:
        try:
            # Download image from Discord
            async with session.get(image_url) as resp:
                if resp.status == 200:
                    image_data = await resp.read()
                    print(f"📥 Downloaded image from Discord ({len(image_data)} bytes)")
                else:
                    print(f"❌ Failed to download image from Discord. Status: {resp.status}")
                    return None
            
            # Upload to GroupMe
            data = aiohttp.FormData()
            data.add_field('file', image_data, filename='discord_image.png', content_type='image/png')
            
            async with session.post(
                GROUPME_IMAGE_UPLOAD_URL,
                data=data,
                headers={'X-Access-Token': GROUPME_ACCESS_TOKEN}
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    groupme_image_url = result['payload']['url']
                    print(f"📤 Successfully uploaded image to GroupMe: {groupme_image_url}")
                    return groupme_image_url
                else:
                    print(f"❌ Failed to upload image to GroupMe. Status: {resp.status}")
                    error_text = await resp.text()
                    print(f"Error: {error_text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error handling image upload: {e}")
            return None

async def send_to_groupme(message_text, author_name, image_url=None):
    """Send a message to GroupMe with optional image"""
    payload = {
        "bot_id": GROUPME_BOT_ID,
        "text": f"{author_name}: {message_text}" if message_text.strip() else f"{author_name} sent an image"
    }
    
    # Add image attachment if provided
    if image_url:
        payload["attachments"] = [{
            "type": "image",
            "url": image_url
        }]
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(GROUPME_POST_URL, json=payload) as response:
                if response.status == 202:
                    image_info = " with image" if image_url else ""
                    print(f"✅ Message sent to GroupMe{image_info}: {message_text[:50]}...")
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
    print(f'🖼️ Image support: {"✅" if GROUPME_ACCESS_TOKEN else "❌ (GROUPME_ACCESS_TOKEN not set)"}')
    print(f'🚀 Bot is ready and running on Railway!')

@bot.event
async def on_message(message):
    # Don't respond to bot messages
    if message.author.bot:
        return
    
    # Only forward messages from the specified channel
    if message.channel.id == DISCORD_CHANNEL_ID:
        print(f"📨 Processing message from {message.author.display_name}...")
        
        # Handle images
        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith('image/'):
                    print(f"🖼️ Found image attachment: {attachment.filename}")
                    
                    # Upload image to GroupMe
                    groupme_image_url = await upload_image_to_groupme(attachment.url)
                    
                    if groupme_image_url:
                        # Send message with image
                        await send_to_groupme(message.content, message.author.display_name, groupme_image_url)
                    else:
                        # Send text message indicating image upload failed
                        await send_to_groupme(f"{message.content} [Image upload failed]", message.author.display_name)
                else:
                    # Non-image attachment
                    await send_to_groupme(f"{message.content} [Attached: {attachment.filename}]", message.author.display_name)
        else:
            # Regular text message
            if message.content.strip():  # Only send if there's actual content
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
        image_status = "✅" if GROUPME_ACCESS_TOKEN else "❌"
        await ctx.send(f"🟢 Bot is online and monitoring this channel!\n🔗 Connected to GroupMe: {'✅' if GROUPME_BOT_ID else '❌'}\n🖼️ Image support: {image_status}")

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
    
    if not GROUPME_ACCESS_TOKEN:
        print("⚠️ GROUPME_ACCESS_TOKEN not set - image uploads will be disabled")
    
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
