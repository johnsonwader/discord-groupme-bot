import discord
import aiohttp
import asyncio
import os
from discord.ext import commands
from aiohttp import web
import threading
import time
import json
from collections import defaultdict
import re

# Configuration from environment variables
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GROUPME_BOT_ID = os.getenv("GROUPME_BOT_ID")
GROUPME_ACCESS_TOKEN = os.getenv("GROUPME_ACCESS_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
GROUPME_GROUP_ID = os.getenv("GROUPME_GROUP_ID")  # Add this to your Railway environment variables
PORT = int(os.getenv("PORT", "8000"))

# GroupMe API endpoints
GROUPME_POST_URL = "https://api.groupme.com/v3/bots/post"
GROUPME_IMAGE_UPLOAD_URL = "https://image.groupme.com/pictures"
GROUPME_GROUPS_URL = f"https://api.groupme.com/v3/groups/{GROUPME_GROUP_ID}"
GROUPME_MESSAGES_URL = f"https://api.groupme.com/v3/groups/{GROUPME_GROUP_ID}/messages"

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Global variables
bot_status = {"ready": False, "start_time": time.time()}
message_mapping = {}  # Maps Discord message IDs to GroupMe message IDs
groupme_to_discord = {}  # Maps GroupMe message IDs to Discord message IDs
recent_messages = defaultdict(list)  # Stores recent messages for threading context

# Emoji mapping for reactions
EMOJI_MAPPING = {
    const twemojiReactions = {
  // Basic smileys and emotions
  smileys: {
    '😀': { name: 'grinning', code: '1f600', category: 'smileys' },
    '😃': { name: 'smiley', code: '1f603', category: 'smileys' },
    '😄': { name: 'smile', code: '1f604', category: 'smileys' },
    '😁': { name: 'grin', code: '1f601', category: 'smileys' },
    '😆': { name: 'laughing', code: '1f606', category: 'smileys' },
    '😅': { name: 'sweat_smile', code: '1f605', category: 'smileys' },
    '🤣': { name: 'rofl', code: '1f923', category: 'smileys' },
    '😂': { name: 'joy', code: '1f602', category: 'smileys' },
    '🙂': { name: 'slightly_smiling_face', code: '1f642', category: 'smileys' },
    '😊': { name: 'blush', code: '1f60a', category: 'smileys' },
    '😇': { name: 'innocent', code: '1f607', category: 'smileys' },
    '😉': { name: 'wink', code: '1f609', category: 'smileys' },
    '😍': { name: 'heart_eyes', code: '1f60d', category: 'smileys' },
    '🥰': { name: 'smiling_face_with_hearts', code: '1f970', category: 'smileys' },
    '😘': { name: 'kissing_heart', code: '1f618', category: 'smileys' },
    '😗': { name: 'kissing', code: '1f617', category: 'smileys' },
    '😙': { name: 'kissing_smiling_eyes', code: '1f619', category: 'smileys' },
    '😚': { name: 'kissing_closed_eyes', code: '1f61a', category: 'smileys' },
    '🤗': { name: 'hugs', code: '1f917', category: 'smileys' },
    '🤔': { name: 'thinking', code: '1f914', category: 'smileys' },
    '😐': { name: 'neutral_face', code: '1f610', category: 'smileys' },
    '😑': { name: 'expressionless', code: '1f611', category: 'smileys' },
    '😶': { name: 'no_mouth', code: '1f636', category: 'smileys' },
    '😏': { name: 'smirk', code: '1f60f', category: 'smileys' },
    '😒': { name: 'unamused', code: '1f612', category: 'smileys' },
    '🙄': { name: 'roll_eyes', code: '1f644', category: 'smileys' },
    '😬': { name: 'grimacing', code: '1f62c', category: 'smileys' },
    '🤐': { name: 'zipper_mouth', code: '1f910', category: 'smileys' },
    '😔': { name: 'pensive', code: '1f614', category: 'smileys' },
    '😪': { name: 'sleepy', code: '1f62a', category: 'smileys' },
    '😴': { name: 'sleeping', code: '1f634', category: 'smileys' },
    '😷': { name: 'mask', code: '1f637', category: 'smileys' },
    '🤒': { name: 'thermometer_face', code: '1f912', category: 'smileys' },
    '😭': { name: 'sob', code: '1f62d', category: 'smileys' },
    '😢': { name: 'cry', code: '1f622', category: 'smileys' },
    '😰': { name: 'cold_sweat', code: '1f630', category: 'smileys' },
    '😱': { name: 'scream', code: '1f631', category: 'smileys' },
    '😨': { name: 'fearful', code: '1f628', category: 'smileys' },
    '😖': { name: 'confounded', code: '1f616', category: 'smileys' },
    '😞': { name: 'disappointed', code: '1f61e', category: 'smileys' },
    '😓': { name: 'sweat', code: '1f613', category: 'smileys' },
    '😤': { name: 'triumph', code: '1f624', category: 'smileys' },
    '😠': { name: 'angry', code: '1f620', category: 'smileys' },
    '😡': { name: 'rage', code: '1f621', category: 'smileys' },
  },

  // Common objects and symbols
  objects: {
    '👍': { name: 'thumbsup', code: '1f44d', category: 'objects' },
    '👎': { name: 'thumbsdown', code: '1f44e', category: 'objects' },
    '👌': { name: 'ok_hand', code: '1f44c', category: 'objects' },
    '✌️': { name: 'victory', code: '270c-fe0f', category: 'objects' },
    '🤞': { name: 'crossed_fingers', code: '1f91e', category: 'objects' },
    '🤝': { name: 'handshake', code: '1f91d', category: 'objects' },
    '👏': { name: 'clap', code: '1f44f', category: 'objects' },
    '🙌': { name: 'raised_hands', code: '1f64c', category: 'objects' },
    '👐': { name: 'open_hands', code: '1f450', category: 'objects' },
    '🤲': { name: 'palms_up', code: '1f932', category: 'objects' },
    '🙏': { name: 'pray', code: '1f64f', category: 'objects' },
    '❤️': { name: 'heart', code: '2764-fe0f', category: 'objects' },
    '💖': { name: 'sparkling_heart', code: '1f496', category: 'objects' },
    '💝': { name: 'gift_heart', code: '1f49d', category: 'objects' },
    '🔥': { name: 'fire', code: '1f525', category: 'objects' },
    '⭐': { name: 'star', code: '2b50', category: 'objects' },
    '🌟': { name: 'star2', code: '1f31f', category: 'objects' },
    '💯': { name: 'hundred', code: '1f4af', category: 'objects' },
    '✅': { name: 'white_check_mark', code: '2705', category: 'objects' },
    '❌': { name: 'x', code: '274c', category: 'objects' },
    '⚠️': { name: 'warning', code: '26a0-fe0f', category: 'objects' },
    '🎉': { name: 'tada', code: '1f389', category: 'objects' },
    '🎊': { name: 'confetti_ball', code: '1f38a', category: 'objects' },
    '💀': '💀',
    '🪩': '🪩'
  }, 
}

def run_health_server():
    """Run health check server in a separate thread"""
    async def health_check(request):
        return web.json_response({
            "status": "healthy",
            "bot_ready": bot_status["ready"],
            "uptime": time.time() - bot_status["start_time"],
            "features": {
                "image_support": bool(GROUPME_ACCESS_TOKEN),
                "reactions": bool(GROUPME_ACCESS_TOKEN and GROUPME_GROUP_ID),
                "threading": True
            }
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
        
        while True:
            await asyncio.sleep(60)

    asyncio.new_event_loop().run_until_complete(start_server())

async def get_groupme_message(message_id):
    """Fetch a specific GroupMe message by ID"""
    if not GROUPME_ACCESS_TOKEN or not GROUPME_GROUP_ID:
        return None
    
    async with aiohttp.ClientSession() as session:
        try:
            url = f"{GROUPME_MESSAGES_URL}?token={GROUPME_ACCESS_TOKEN}&limit=100"
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    messages = data.get('response', {}).get('messages', [])
                    for msg in messages:
                        if msg.get('id') == message_id:
                            return msg
                    return None
                else:
                    print(f"❌ Failed to fetch GroupMe messages. Status: {resp.status}")
                    return None
        except Exception as e:
            print(f"❌ Error fetching GroupMe message: {e}")
            return None

async def send_reaction_to_groupme(message_id, emoji, user_name):
    """Send a reaction as a message to GroupMe"""
    if not GROUPME_ACCESS_TOKEN or not GROUPME_GROUP_ID:
        print("❌ GroupMe access token or group ID not available for reactions")
        return False
    
    # Get the original message to provide context
    original_msg = await get_groupme_message(message_id)
    if original_msg:
        original_text = original_msg.get('text', '')[:50]
        original_author = original_msg.get('name', 'Unknown')
        context = f"'{original_text}...' by {original_author}" if original_text else f"message by {original_author}"
    else:
        context = "a message"
    
    reaction_text = f"{user_name} reacted {emoji} to {context}"
    
    payload = {
        "bot_id": GROUPME_BOT_ID,
        "text": reaction_text
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(GROUPME_POST_URL, json=payload) as response:
                if response.status == 202:
                    print(f"✅ Reaction sent to GroupMe: {reaction_text}")
                    return True
                else:
                    print(f"❌ Failed to send reaction to GroupMe. Status: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Error sending reaction to GroupMe: {e}")
            return False

async def upload_image_to_groupme(image_url):
    """Download image from Discord and upload to GroupMe"""
    if not GROUPME_ACCESS_TOKEN:
        print("❌ GroupMe access token not available for image upload")
        return None
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(image_url) as resp:
                if resp.status == 200:
                    image_data = await resp.read()
                    print(f"📥 Downloaded image from Discord ({len(image_data)} bytes)")
                else:
                    print(f"❌ Failed to download image from Discord. Status: {resp.status}")
                    return None
            
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
                    return None
                    
        except Exception as e:
            print(f"❌ Error handling image upload: {e}")
            return None

def detect_reply_context(message_content):
    """Detect if a message is replying to another message and extract context"""
    # Look for patterns like "Reply to @username:" or "> quoted text"
    reply_patterns = [
        r'^Reply to @(\w+):\s*(.+)',
        r'^@(\w+)\s+(.+)',
        r'^>\s*(.+?)\n(.+)',
        r'^"(.+?)"\s*(.+)'
    ]
    
    for pattern in reply_patterns:
        match = re.match(pattern, message_content, re.DOTALL)
        if match:
            if len(match.groups()) == 2:
                return match.group(1), match.group(2)
    
    return None, message_content

async def send_to_groupme(message_text, author_name, image_url=None, reply_context=None):
    """Send a message to GroupMe with optional image and reply context"""
    
    # Handle reply context
    if reply_context:
        quoted_text, reply_author = reply_context
        message_text = f"↪️ Replying to {reply_author}: \"{quoted_text[:50]}{'...' if len(quoted_text) > 50 else ''}\"\n\n{author_name}: {message_text}"
    else:
        # Check if this is a reply based on message content
        reply_author, clean_message = detect_reply_context(message_text)
        if reply_author:
            message_text = f"↪️ Replying to {reply_author}:\n\n{author_name}: {clean_message}"
        else:
            message_text = f"{author_name}: {message_text}" if message_text.strip() else f"{author_name} sent an image"
    
    payload = {
        "bot_id": GROUPME_BOT_ID,
        "text": message_text
    }
    
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
                    return True
                else:
                    print(f"❌ Failed to send to GroupMe. Status: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Error sending to GroupMe: {e}")
            return False

@bot.event
async def on_ready():
    global bot_status
    bot_status["ready"] = True
    print(f'🤖 {bot.user} has connected to Discord!')
    print(f'📺 Monitoring channel ID: {DISCORD_CHANNEL_ID}')
    print(f'🖼️ Image support: {"✅" if GROUPME_ACCESS_TOKEN else "❌ (GROUPME_ACCESS_TOKEN not set)"}')
    print(f'🔗 GroupMe Group ID: {"✅" if GROUPME_GROUP_ID else "❌ (GROUPME_GROUP_ID not set)"}')
    print(f'😀 Reaction support: {"✅" if GROUPME_ACCESS_TOKEN and GROUPME_GROUP_ID else "❌"}')
    print(f'🧵 Threading support: ✅')
    print(f'🚀 Enhanced bot is ready and running on Railway!')

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if message.channel.id == DISCORD_CHANNEL_ID:
        print(f"📨 Processing message from {message.author.display_name}...")
        
        # Store message for threading context
        recent_messages[message.channel.id].append({
            'author': message.author.display_name,
            'content': message.content,
            'timestamp': time.time(),
            'message_id': message.id
        })
        
        # Keep only last 20 messages for context
        if len(recent_messages[message.channel.id]) > 20:
            recent_messages[message.channel.id].pop(0)
        
        # Handle replies
        reply_context = None
        if message.reference and message.reference.message_id:
            try:
                replied_message = await message.channel.fetch_message(message.reference.message_id)
                reply_context = (replied_message.content[:100], replied_message.author.display_name)
            except:
                pass
        
        # Handle images
        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith('image/'):
                    print(f"🖼️ Found image attachment: {attachment.filename}")
                    groupme_image_url = await upload_image_to_groupme(attachment.url)
                    
                    if groupme_image_url:
                        await send_to_groupme(message.content, message.author.display_name, 
                                            groupme_image_url, reply_context)
                    else:
                        await send_to_groupme(f"{message.content} [Image upload failed]", 
                                            message.author.display_name, reply_context=reply_context)
                else:
                    await send_to_groupme(f"{message.content} [Attached: {attachment.filename}]", 
                                        message.author.display_name, reply_context=reply_context)
        else:
            if message.content.strip():
                await send_to_groupme(message.content, message.author.display_name, 
                                    reply_context=reply_context)
    
    await bot.process_commands(message)

@bot.event
async def on_reaction_add(reaction, user):
    """Handle reactions added to messages"""
    if user.bot:
        return
    
    if reaction.message.channel.id == DISCORD_CHANNEL_ID:
        emoji = str(reaction.emoji)
        
        # Check if this is a supported emoji
        if emoji in EMOJI_MAPPING:
            print(f"😀 Processing reaction {emoji} from {user.display_name}")
            
            # Check if this message was sent from GroupMe (stored in our mapping)
            discord_msg_id = reaction.message.id
            if discord_msg_id in message_mapping:
                groupme_msg_id = message_mapping[discord_msg_id]
                success = await send_reaction_to_groupme(groupme_msg_id, emoji, user.display_name)
                if success:
                    print(f"✅ Reaction {emoji} forwarded to GroupMe")
            else:
                # This is a reaction to a Discord-originated message
                # We can still send it as a reaction message
                original_author = reaction.message.author.display_name
                original_content = reaction.message.content[:50] if reaction.message.content else "a message"
                context = f"'{original_content}...' by {original_author}" if original_content != "a message" else f"message by {original_author}"
                
                reaction_text = f"{user.display_name} reacted {emoji} to {context}"
                
                payload = {
                    "bot_id": GROUPME_BOT_ID,
                    "text": reaction_text
                }
                
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.post(GROUPME_POST_URL, json=payload) as response:
                            if response.status == 202:
                                print(f"✅ Discord reaction sent to GroupMe: {reaction_text}")
                    except Exception as e:
                        print(f"❌ Error sending Discord reaction to GroupMe: {e}")

@bot.command(name='test')
async def test_bridge(ctx):
    """Test command to verify the bridge is working"""
    if ctx.channel.id == DISCORD_CHANNEL_ID:
        await send_to_groupme("🧪 Enhanced bridge test message from Railway!", "Bot Test")
        await ctx.send("✅ Test message sent to GroupMe!")
    else:
        await ctx.send("❌ This command only works in the monitored channel.")

@bot.command(name='status')
async def status(ctx):
    """Check bot status"""
    if ctx.channel.id == DISCORD_CHANNEL_ID:
        image_status = "✅" if GROUPME_ACCESS_TOKEN else "❌"
        reactions_status = "✅" if (GROUPME_ACCESS_TOKEN and GROUPME_GROUP_ID) else "❌"
        
        status_msg = f"""🟢 **Enhanced Bot Status**
🔗 Connected to GroupMe: {'✅' if GROUPME_BOT_ID else '❌'}
🖼️ Image support: {image_status}
😀 Reaction support: {reactions_status}
🧵 Threading support: ✅
📊 Recent messages tracked: {len(recent_messages.get(DISCORD_CHANNEL_ID, []))}

**Supported Reactions:** {', '.join(EMOJI_MAPPING.keys())}"""
        
        await ctx.send(status_msg)

@bot.command(name='react')
async def manual_react(ctx, emoji, *, message_context=None):
    """Manually send a reaction to GroupMe"""
    if ctx.channel.id != DISCORD_CHANNEL_ID:
        await ctx.send("❌ This command only works in the monitored channel.")
        return
    
    if emoji not in EMOJI_MAPPING:
        await ctx.send(f"❌ Unsupported emoji. Supported: {', '.join(EMOJI_MAPPING.keys())}")
        return
    
    context = message_context or "the last message"
    reaction_text = f"{ctx.author.display_name} reacted {emoji} to {context}"
    
    payload = {
        "bot_id": GROUPME_BOT_ID,
        "text": reaction_text
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(GROUPME_POST_URL, json=payload) as response:
                if response.status == 202:
                    await ctx.send(f"✅ Reaction sent: {reaction_text}")
                else:
                    await ctx.send("❌ Failed to send reaction to GroupMe")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

@bot.command(name='recent')
async def show_recent(ctx):
    """Show recent messages for threading context"""
    if ctx.channel.id != DISCORD_CHANNEL_ID:
        await ctx.send("❌ This command only works in the monitored channel.")
        return
    
    recent = recent_messages.get(DISCORD_CHANNEL_ID, [])
    if not recent:
        await ctx.send("📭 No recent messages tracked.")
        return
    
    message_list = []
    for i, msg in enumerate(recent[-10:], 1):  # Show last 10 messages
        content = msg['content'][:50] + "..." if len(msg['content']) > 50 else msg['content']
        message_list.append(f"**{i}.** {msg['author']}: {content}")
    
    embed = discord.Embed(title="📋 Recent Messages", description="\n".join(message_list), color=0x00ff00)
    await ctx.send(embed=embed)

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
        print("⚠️ GROUPME_ACCESS_TOKEN not set - image uploads and reactions will be disabled")
    
    if not GROUPME_GROUP_ID:
        print("⚠️ GROUPME_GROUP_ID not set - advanced features will be limited")
    
    # Start health check server
    print("🏥 Starting enhanced health check server...")
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    time.sleep(2)
    
    # Start Discord bot
    print("🚀 Starting Enhanced Discord to GroupMe bridge...")
    try:
        bot.run(DISCORD_BOT_TOKEN)
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
