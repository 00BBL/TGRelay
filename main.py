import toml
import sqlite3 as sqlite
from telethon import TelegramClient, events
import hashlib

# Load configurations
loadedConfig = toml.load("config.toml")["Config"]
strings = toml.load("config.toml")["Strings"]

# App ID and hash for authentication from the config file
destination_Id = int(loadedConfig["destinationID"])  # Ensure it's an integer
commandPrefix = loadedConfig["commandPrefix"]

# Initialize Telethon client
client = TelegramClient('relay_bot', loadedConfig["api_id"], loadedConfig["api_hash"]).start(bot_token=loadedConfig["token"])
splitter = "­⁮­⁮"

# Database setup
def create_db():
    connection, cursor = getDBC()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS BlockedUsers (
            userId INTEGER
        )''')
    connection.commit()
    connection.close()

def getDBC():
    connection = sqlite.connect('blockedUsers.db')
    cursor = connection.cursor()
    return connection, cursor

def user_is_blocked(user_id):
    _, cursor = getDBC()
    cursor.execute("SELECT userId FROM BlockedUsers WHERE userId = ?", (user_id,))
    return cursor.fetchone() is not None

def encode_chat_id(id: int):
    chars = {"zeroWidthSpace": "\u200B", "nationalDigitShapes": "\u206F"}
    encoded_parts = [
        chars['zeroWidthSpace'] * int(number) + chars['nationalDigitShapes']
        for number in str(id)
    ]
    return ''.join(encoded_parts)

def decode_chat_id(id: str):
    chars = {"zeroWidthSpace": "\u200B", "nationalDigitShapes": "\u206F"}
    split_result = id.split(chars['nationalDigitShapes'])
    split_result = split_result[:-1] if split_result[-1] == '' else split_result
    return int(''.join([str(len(number)) for number in split_result]))

# Handler for incoming messages
@client.on(events.NewMessage)
async def handle_update(event):
    sender = await event.get_sender()
    if sender.bot:  # Ignore bot messages
        return

    message_text = event.raw_text
    sender_id = sender.id
    sender_name = sender.username or sender.first_name
    uniqueIdentifierHash = hashlib.md5(str(sender_id).encode('utf-8')).hexdigest()[:6]
    encoded_chat_id = encode_chat_id(sender_id)

    # Handle incoming messages not directed to the bot owner
    if not event.is_reply and sender_id != destination_Id:
        if user_is_blocked(sender_id):
            await event.reply(f"You are currently blocked from contacting {strings['name']}.")
            return

        await client.send_message(
            destination_Id,
            f"[{sender_name}#{sender_id}] - {message_text}{splitter}{encoded_chat_id}"
        )

    # Handle replies to original messages from non-owner users
    elif event.is_reply and sender_id != destination_Id:
        if user_is_blocked(sender_id):
            await event.reply(f"You are currently blocked from contacting {strings['name']}.")
            return

        original_message = await event.get_reply_message()
        original_sender_name = original_message.sender.username or original_message.sender.first_name

        await client.send_message(
            destination_Id,
            f"[{sender_name}#{sender_id}] replied to [{original_sender_name}] - {message_text}\n"
            f"Original Message: {original_message.text}{splitter}{encoded_chat_id}"
        )

    # Handle replies from the owner to the original sender
    elif event.is_reply and event.chat_id == destination_Id and sender_id == destination_Id:
    #elif event.chat_id == destination_Id and sender_id == destination_Id:
        original_message = await event.get_reply_message()
        response_id = decode_chat_id(original_message.text.split(splitter)[-1])

        if message_text.startswith(commandPrefix):
            command = message_text[1:].strip().lower()

            if command == "help":
                await client.send_message(destination_Id, f"""Commands:
{commandPrefix}help - Shows this message
{commandPrefix}block - Blocks the user from contacting the bot
{commandPrefix}unblock - Unblocks the user from contacting the bot""")

            elif command == "block":
                connection, cursor = getDBC()
                cursor.execute("INSERT INTO BlockedUsers VALUES (?)", (response_id,))
                connection.commit()
                connection.close()
                await client.send_message(destination_Id, "User blocked.")

            elif command == "unblock":
                connection, cursor = getDBC()
                cursor.execute("DELETE FROM BlockedUsers WHERE userId = ?", (response_id,))
                connection.commit()
                connection.close()
                await client.send_message(destination_Id, "User unblocked.")

            else:
                await client.send_message(destination_Id, f"Unknown command. Use {commandPrefix}help to list available commands.")
        else:
            await client.send_message(response_id, message_text)


# Start the bot
if __name__ == "__main__":
    create_db()
    client.start()
    print("Bot is running...")
    client.run_until_disconnected()
