# Advanced SMS Features Guide

Complete guide to using multi-companion SMS support with persistent mappings and commands.

## 🎯 Features Overview

### 1. **Persistent Companion Mapping** 📝
- Each phone number is mapped to a specific companion
- Mapping persists across app restarts
- First SMS from a number uses the currently selected companion
- Mapping stored in `sms_companion_mapping.json`

### 2. **SMS Commands** 📱
- Control your AI companions via text commands
- Switch companions without opening the app
- List available companions
- Get help and info

### 3. **Multi-Companion Support** 👥
- Different phone numbers can talk to different companions
- Each phone number has its own conversation history
- Switch companions mid-conversation
- Conversations are stored separately per companion

---

## 🚀 Setup

### 1. Install Flask (if not already installed)
```bash
pip install flask
```

### 2. Configure Environment Variables (.env file)
```bash
# Twilio credentials
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
USER_PHONE_NUMBER=+0987654321

# Webhook server
WEBHOOK_PORT=5000
```

### 3. Start ngrok (for local development)
```bash
ngrok http 5000
```

### 4. Configure Twilio Webhook
- Go to Twilio Console → Phone Numbers → Your Number
- Set webhook URL to: `https://your-ngrok-url.ngrok.io/sms/incoming`

### 5. Start the App
```bash
cd ai-companion-gtk4
python3 main.py
```

---

## 📋 Available SMS Commands

### Switch Companions
```
/switch [companion name]
switch to [companion name]
```
**Examples:**
- `/switch Sarah`
- `switch to girlfriend`
- `Switch to Mentor`

### List Companions
```
/list
list
list companions
show companions
```
**Shows:**
- Currently selected companion
- All available companions
- Their genders

### Who Am I Talking To?
```
/who
who are you
```
**Shows:**
- Current companion name
- Their gender
- Personality preview

### Reset Mapping
```
/reset
```
**Action:** Clears the phone-to-companion mapping. Next message will use the app's current companion.

### Help
```
/help
help
help me
commands
```
**Shows:** All available commands

---

## 💡 Usage Examples

### Example 1: First Time Setup

```
You (SMS): Hey!
Companion: Hey there! 😊 How are you doing today?

You (SMS): /list
Companion: 📱 Current companion: Sarah
          Available companions:
             1. Sarah (Female)
          👉 2. John (Male)
             3. Alex (Non-Binary)
          💡 Text 'switch to [name]' to change companions

You (SMS): switch to John
Companion: ✅ Switched to John! I'm now John.

You (SMS): Hey!
Companion: Hey! What's up? Ready to chat?
```

### Example 2: Multiple Phone Numbers

**Phone 1 (Your phone)** → Mapped to Sarah (girlfriend)
```
You: I miss you
Sarah: Aww, I miss you too! ❤️ Can't wait to see you.
```

**Phone 2 (Friend's phone)** → Mapped to Alex (best friend)
```
Friend: Yo what's up
Alex: Hey! Not much, just chillin. You?
```

Each phone number has its own companion and conversation history!

### Example 3: Switching Companions

```
You: Can we talk about something serious?
Sarah (playful): Sure! What's on your mind? 😊

You: /switch mentor
Companion: ✅ Switched to Mentor! I'm now Mentor.

You: Can we talk about something serious?
Mentor: Of course. I'm here to help. What would you like to discuss?
```

---

## 🔧 How It Works

### First Message from a New Number

1. **App is open** with "Sarah" selected
2. **You send SMS**: "Hello!"
3. **System**:
   - Sees no mapping for your number
   - Uses current companion (Sarah)
   - Creates mapping: Your Number → Sarah
   - Saves to `sms_companion_mapping.json`
4. **Sarah responds**: "Hey! Great to hear from you! 😊"

### Subsequent Messages

1. **You send SMS**: "How are you?"
2. **System**:
   - Checks mapping: Your Number → Sarah
   - Loads Sarah's conversation history
   - Processes message with Sarah's personality
   - Updates conversation
3. **Sarah responds** with full context

### Switching Companions

1. **You send**: `/switch John`
2. **System**:
   - Detects command
   - Finds John in companions
   - Updates mapping: Your Number → John
   - Saves new mapping
3. **Response**: "✅ Switched to John! I'm now John."
4. **Next message** will be from John!

### Multiple Phone Numbers

The mapping file structure:
```json
{
  "mappings": {
    "15551234567": {
      "companion_id": "sarah_girlfriend",
      "companion_name": "Sarah",
      "phone_number": "+15551234567",
      "assigned_at": "2025-01-13T10:00:00",
      "last_interaction": "2025-01-13T12:30:00"
    },
    "15559876543": {
      "companion_id": "john_best_friend",
      "companion_name": "John",
      "phone_number": "+15559876543",
      "assigned_at": "2025-01-13T11:00:00",
      "last_interaction": "2025-01-13T12:00:00"
    }
  }
}
```

---

## 📊 Conversation Storage

Each companion has their own conversation file:
```
conversations/
├── sarah_girlfriend.json      # Sarah's conversations
├── john_best_friend.json       # John's conversations
├── alex_mentor.json            # Alex's conversations
└── sms_companion_mapping.json  # Phone number mappings
```

**Per-companion features:**
- ✅ Separate conversation history
- ✅ Separate memory extraction
- ✅ Separate context and personality
- ✅ Phone number can switch between companions

---

## 🎨 Natural Language Commands

You don't always need to use `/` commands. Natural language works too:

| Command | Natural Language Variations |
|---------|----------------------------|
| `/switch [name]` | "switch to [name]", "change to [name]" |
| `/list` | "list companions", "show companions", "who can I talk to?" |
| `/who` | "who are you?", "who am I talking to?" |
| `/help` | "help", "help me", "what can you do?", "commands" |

---

## 🔐 Security & Privacy

### Phone Number Privacy
- Phone numbers are normalized (digits only)
- Stored locally in `sms_companion_mapping.json`
- Never transmitted except to Twilio

### Multiple Users
- Each phone number can have its own companion
- Useful for:
  - Multiple people in household
  - Testing different companions
  - Separate conversations

### Data Isolation
- Each companion has separate conversation files
- Memories are shared across companions (if marked as shared)
- Private memories stay with specific companion

---

## ⚠️ Troubleshooting

### Command Not Working
**Problem**: Command is being processed as regular message

**Solution**: Make sure to use exact command format:
- `/switch Sarah` (not "/switch to Sarah")
- Or use natural language: `switch to Sarah`

### Wrong Companion Responding
**Problem**: Different companion than expected is responding

**Solution**:
1. Check current companion: `/who`
2. Reset mapping: `/reset`
3. Select companion in app
4. Send message to create new mapping

### Mapping Not Saving
**Problem**: Mapping is lost after app restart

**Solution**: Check file permissions:
```bash
ls -la conversations/sms_companion_mapping.json
```

### Companion Not Found
**Problem**: "Companion not found" error

**Solution**:
1. List companions: `/list`
2. Use exact name from list
3. Check for typos

---

## 🚀 Advanced Usage

### Creating Companion Shortcuts

Create speed-dial-like shortcuts:

```
/s  → switch to Sarah
/j  → switch to John
/a  → switch to Alex
```

Wait, these aren't implemented yet! But you can use full names:
```
/switch Sarah
/switch John
/switch Alex
```

### Context Switching

Switch companions based on conversation context:

```
You: I need relationship advice
Companion: [Current companion responds]

You: /switch mentor
Companion: ✅ Switched to Mentor! I'm now Mentor.

You: I need relationship advice
Mentor: Of course! I'd be happy to help with relationship advice...
```

### Testing Multiple Companions

Use multiple phone numbers (or have friends test):

1. **Your phone** → Test with Sarah
2. **Friend's phone** → Test with John
3. **Work phone** → Test with Alex

Each maintains separate conversation!

---

## 📝 Best Practices

### 1. **Name Your Companions Clearly**
Use distinct names to avoid confusion:
- ✅ "Sarah", "John", "Alex"
- ❌ "Companion1", "Companion2", "Best Friend"

### 2. **Set Up Initial Mapping**
Open the app, select a companion, then send first SMS to create mapping.

### 3. **Use Commands to Verify**
After switching, verify with `/who` to confirm correct companion.

### 4. **Test Before Deploying**
Test all commands with ngrok before relying on them.

### 5. **Backup Mappings**
The `sms_companion_mapping.json` file is your backup:
```bash
cp conversations/sms_companion_mapping.json ~/backup/
```

---

## 🎉 Summary

You now have:
- ✅ **Persistent mapping** - Phone numbers remember their companions
- ✅ **SMS commands** - Control companions via text
- ✅ **Multi-companion** - Different companions for different numbers
- ✅ **Separate conversations** - Each companion has own history
- ✅ **Full context** - Personality, memories, and conversation history per companion

Enjoy chatting with your AI companions via SMS! 📱🤖
