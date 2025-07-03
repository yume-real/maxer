import logging
import os

# Optional: load variables from a local .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except ImportError:
    # Gracefully degrade if the extra dependency is not present
    pass

from maxer import Bot
from maxer.bot.button import Button
from maxer.core.enums import ChatAction

# Enable basic logging so HTTP traffic is visible
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

# Read bot token from environment (recommended) or fall back to placeholder
TOKEN = os.getenv("TOKEN", "YOUR_BOT_TOKEN_HERE")

# ---------------------------------------------------------------------------
# Bot instance and handlers
# ---------------------------------------------------------------------------

bot = Bot(TOKEN)


@bot.on("ready")
async def on_ready():
    """Fired once when long-polling loop starts."""
    me = await bot.client.bots.get_me()
    print(f"Logged in as: {me.first_name}")
    print("Send me any message – I'll echo it back with buttons!")


# ------------------------------- Commands ----------------------------------


@bot.command  # Responds to /start
async def start(ctx):
    """Welcome message for newcomers."""
    await ctx.reply("👋 Привет! Я бот на MAX. Отправь мне что-нибудь, и я постараюсь ответить ☺️")


# ---------------------------- Message handler ------------------------------


@bot.message()  # Any non-command plain-text message  # type: ignore[arg-type]
async def echo(ctx, text: str):
    # Show nice typing indicator while we 'think'
    await ctx.chat.action(ChatAction.TYPING_ON)

    # Echo back using fluent message builder + inline buttons
    await (
        ctx.chat
        .message(f"Echo: {text}")
        .buttons([
            Button("👍", callback="like"),
            Button("👎", callback="dislike"),
        ])
        .send()
    )


# --------------------------- Callback handler ------------------------------


@bot.on("callback_query")
async def on_callback_query(upd):
    """Reply to inline button presses with small toast notifications."""
    data = upd.data
    callback_id = data.get("callback_id")
    payload = data.get("callback")

    if not callback_id or not payload:
        return  # Malformed update – ignore

    if payload == "like":
        notify_text = "Спасибо за 👍!"
    elif payload == "dislike":
        notify_text = "Жаль 😢 Попробую лучше!"
    else:
        notify_text = "🤔 Неизвестное действие"

    await bot.client.messages.answer_callback(callback_id, notification=notify_text)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    bot.run() 