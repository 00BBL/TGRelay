# Telegram Relay Bot Documentation

## Overview
This bot uses **Telethon** to relay messages between users and an owner. Users can send messages to the bot, and these are forwarded to the owner's chat. The owner can reply directly through the bot to the original sender. Additionally, users can be **blocked** or **unblocked** by the owner using commands.

## Features
- **Message Relaying**: Forwards messages between users and the owner.
- **Command Handling**: Supports `/block`, `/unblock`, and `/help` commands. (Reply to a message)
- **User Blocking System**: Uses SQLite to track blocked users.
- **Encoded Chat IDs**: Uses a unique encoding mechanism for privacy.
- **TOML Configuration**: Configurable via `config.toml` file.

---

## Setup

### Prerequisites
- **Python 3.8+**
- **Telegram Bot Token**
- **API ID and API Hash** from [my.telegram.org](https://my.telegram.org/)

### Installation
1. Clone the repository or save the script to a directory.
2. Install the dependencies by running:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a config.toml file with the following structure:
   ```
   [Config]
   token = "your_bot_token"
   api_id = 123456
   api_hash = "your_api_hash"
   destinationID = 987654321  # Owner's Telegram ID
   commandPrefix = "/"
   
   [Strings]
   name = "Relay Bot"
   ```

## Usage

### Running the Bot
1. Ensure the bot token, API ID, and API hash are correctly configured in `config.toml`.
2. Start the bot by running:

   python relay_bot.py

3. The bot will display:

   Bot is running...

### Commands Available
- `/help` – Displays the list of available commands.
- `/block` – Blocks the user from communicating with the bot.
- `/unblock` – Unblocks a previously blocked user.

---

## Code Walkthrough

### 1. Configuration Loading
The bot loads the API ID, API Hash, and Bot Token from `config.toml`:

     loadedConfig = toml.load("config.toml")["Config"]
     strings = toml.load("config.toml")["Strings"]

---

### 2. Bot Initialization
The bot is initialized using Telethon. It authenticates with the bot token using:
  
     client = TelegramClient('relay_bot', api_id, api_hash).start(bot_token=loadedConfig["token"])

---

### 3. Database Setup
The SQLite database stores blocked users. If the table doesn’t exist, it’s created on startup:

     def create_db():
         connection, cursor = getDBC()
         cursor.execute('''
             CREATE TABLE IF NOT EXISTS BlockedUsers (
                 userId INTEGER
             )''')
         connection.commit()
         connection.close()

---

### 4. Event Handling
The bot uses Telethon's `@client.on(events.NewMessage)` to handle new messages.

#### Handling Incoming Messages from Users:

     @client.on(events.NewMessage)
     async def handle_update(event):
         sender = await event.get_sender()
         if sender.bot:
             return  # Ignore messages from other bots

If the user is blocked, the bot sends a warning message:

     if user_is_blocked(sender.id):
         await event.reply(f"You are currently blocked from contacting {strings['name']}.")
         return

---

### 5. Encoding Chat IDs
To maintain privacy, chat IDs are encoded before forwarding them to the owner:

     def encode_chat_id(id: int):
         chars = {"zeroWidthSpace": "\u200B", "nationalDigitShapes": "\u206F"}
         encoded_parts = [
             chars['zeroWidthSpace'] * int(number) + chars['nationalDigitShapes']
             for number in str(id)
         ]
         return ''.join(encoded_parts)

The original chat ID can be decoded with:

     def decode_chat_id(id: str):
         chars = {"zeroWidthSpace": "\u200B", "nationalDigitShapes": "\u206F"}
         split_result = id.split(chars['nationalDigitShapes'])
         return int(''.join([str(len(number)) for number in split_result[:-1]]))

---

### 6. Command Handling
The bot responds to owner commands (e.g., `/block` and `/unblock`):
  
     async def handle_command(message_text, response_id):
         command = message_text[1:].strip().lower()

       if command == "help":
           await client.send_message(destination_Id, f"""Commands:
     {commandPrefix}help - Shows this message
     {commandPrefix}block - Blocks the user from contacting the bot
     {commandPrefix}unblock - Unblocks the user""")

#### Blocking a User:

     elif command == "block":
         connection, cursor = getDBC()
         cursor.execute("INSERT INTO BlockedUsers VALUES (?)", (response_id,))
         connection.commit()
         connection.close()
         await client.send_message(destination_Id, "User blocked.")

#### Unblocking a User:

     elif command == "unblock":
         connection, cursor = getDBC()
         cursor.execute("DELETE FROM BlockedUsers WHERE userId = ?", (response_id,))
         connection.commit()
         connection.close()
         await client.send_message(destination_Id, "User unblocked.")

---

## Database Functions

- `getDBC()`: Opens a connection to the SQLite database.

       def getDBC():
           connection = sqlite.connect('blockedUsers.db')
           cursor = connection.cursor()
           return connection, cursor

- `user_is_blocked(user_id)`: Checks if a user is blocked.

       def user_is_blocked(user_id):
           _, cursor = getDBC()
           cursor.execute("SELECT userId FROM BlockedUsers WHERE userId = ?", (user_id,))
           return cursor.fetchone() is not None

---

## Full Example Flow

1. **User Message**:  
   User sends a message: `Hello!`

2. **Bot Relays Message to Owner**:
   [John#senderid] - Hello!­­­­⁮­⁮[EncodedChatID]

3. **Owner Reply**:  
   Owner replies: `Hi, how can I help?`

4. **Bot Relays Reply to User**:
   Hi, how can I help?

5. **Blocking a User**:  
   Owner sends `/block`. The user is now blocked.

---

## Error Handling

1. **Bot Token Invalid**: Ensure the correct bot token is provided in `config.toml`.
2. **Database Errors**: Make sure `blockedUsers.db` is writable.
3. **API ID/Hash Errors**: Ensure the correct API credentials are used from my.telegram.org.

---

## Conclusion
This Relay Bot provides a robust way to manage communication between users and an owner using Telethon. With message forwarding, user blocking, and configurable commands, the bot is suitable for personal or business use cases where intermediary communication is required.

