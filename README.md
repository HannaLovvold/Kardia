# Kardia - AI Companion GTK4 Application

**Created by Hanna Lovvold (2025)**

A **completely standalone** modern GTK4/libadwaita AI companion application with SMS integration, memory management, and multi-companion support.

## ✨ Standalone

Kardia is now **100% standalone** - all backend code is included. No need for the parent `ai-companion` directory!

## 🎯 Features

- **Modern GTK4/libadwaita Interface** - Beautiful GNOME-style UI
- **Multiple AI Companions** - Create custom companions with personalities
- **SMS Integration** - Send/receive SMS via Twilio
- **Multi-Companion SMS** - Different companions for different phone numbers
- **SMS Commands** - Control companions via text commands
- **Memory System** - AI remembers details about you
- **Conversation History** - All conversations saved
- **Customizable** - Create your own companions with traits, goals, and backstories

## 📋 Requirements

### System Requirements
- Python 3.8 or higher
- Linux (GTK4/libadwaita)
- GNOME 42+ or GTK4 environment

### Python Dependencies
```bash
# Required packages
pip install gi-gtk gi-adwaita

# Backend dependencies
pip install openai anthropic groq
pip install python-dotenv requests twilio flask

# Optional: for Ollama (local AI)
# Install Ollama separately from https://ollama.ai
```

### System Dependencies (Ubuntu/Debian)
```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adwaita-1
```

### System Dependencies (Fedora)
```bash
sudo dnf install python3-gobject gtk4 libadwaita
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Install Python packages
pip install -r requirements.txt

# Or install individually
pip install gi-gtk gi-adwaita openai anthropic groq python-dotenv requests twilio flask
```

### 2. Configure AI Backend

Create a `.env` file in the Kardia directory:

```bash
# For Groq (FREE, recommended)
AI_BACKEND=groq
API_KEY=gsk_your_api_key_here
API_URL=https://api.groq.com/openai/v1
API_MODEL=llama-3.3-70b-versatile

# For OpenAI
# AI_BACKEND=openai
# API_KEY=sk-your_api_key_here
# API_URL=https://api.openai.com/v1
# API_MODEL=gpt-3.5-turbo

# For Ollama (local, free)
# AI_BACKEND=ollama
# OLLAMA_URL=http://localhost:11434
# OLLAMA_MODEL=mistral

# Additional Parameters (JSON format, optional)
API_PARAMS={"thinking": {"type": "enabled", "clear_thinking": "true"}, "do_sample": "true"}
```

### 3. Run the Application
```bash
cd /home/hanna/PythonProjects/Kardia
python3 main.py
```

## 📱 SMS Setup (Optional)

### For Incoming/Outgoing SMS:

1. **Install Flask**:
   ```bash
   pip install flask
   ```

2. **Configure Twilio** in `.env`:
   ```bash
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_PHONE_NUMBER=+1234567890
   USER_PHONE_NUMBER=+0987654321
   WEBHOOK_PORT=5000
   ```

3. **Setup ngrok** (for local development):
   ```bash
   ngrok http 5000
   ```

4. **Configure Twilio Webhook**:
   - Go to Twilio Console → Your Phone Number → Messaging
   - Set webhook URL to: `https://your-ngrok-url.ngrok.io/sms/incoming`

See `SMS_FEATURES_GUIDE.md` in parent directory for details.

## 🎮 Usage

### Creating a Companion

1. Click **"+ Create Companion"** button
2. Fill in basic info:
   - Name
   - Gender/Pronouns
3. Select personality traits (use quick-select presets or custom)
4. Set relationship goal and communication tone
5. Add background story (optional)
6. Click **"Save"**

### Switching Companions

1. Click **"Change Companion"** button
2. Select from available companions
3. Or use SMS commands: `/switch [name]`

### Deleting a Chat

1. Click the trash icon in the chat header
2. Confirm to delete all messages and start fresh

### Managing Memories

1. Go to **Settings** → **Memory** tab
2. View recent memories
3. Add memories manually
4. Search memories
5. Export/Import memories
6. Clear all memories

### User Profile

1. Go to **Settings** → **Your Profile** (or click profile button in header)
2. Fill in your personal information
3. Add interests, likes, dislikes
4. Set goals
5. Save to create shared memories

## 🔧 Configuration Files

All data is stored in the Kardia directory:
```
Kardia/
├── companion_data/
│   ├── companions.json    # Preset companions
│   └── presets/            # Custom companions (created by you)
├── conversations/         # Conversation history
├── memories/              # Memory storage
├── config                 # App configuration
└── .env                   # Environment variables (create this)
```

## ⌨️ Keyboard Shortcuts

- **Ctrl+Q** - Quit application
- **Escape** - Go back to companion selection

## 🎨 Customization

### CSS Styling

Edit `style.css` to customize the appearance:
- Message bubble colors
- Chat input styling
- Personality trait chips
- And more...

### Creating Custom Companions

Companion data structure:
```python
{
    "id": "unique_id",
    "name": "Companion Name",
    "gender": "Female/Male/Non-Binary/etc",
    "pronouns": "she/her",
    "personality": "Detailed personality description",
    "interests": ["interest1", "interest2"],
    "greeting": "Initial greeting message",
    "relationship_goal": "Being a supportive friend",
    "tone": "Warm and affectionate",
    "background": "Backstory",
    "image_path": "/path/to/image.png"
}
```

## 🐛 Troubleshooting

### App won't start

**Error**: `ModuleNotFoundError: No module named 'gi'`

**Solution**:
```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adwaita-1
```

### CSS Warnings

**Error**: Theme parser errors in style.css

**Solution**: GTK4 CSS has limited properties. The included CSS has been validated for GTK4.

### SMS not working

**Solution**:
1. Check Flask is installed: `pip install flask`
2. Verify Twilio credentials in `.env`
3. Ensure ngrok is running
4. Check webhook URL in Twilio Console

### Companions not loading

**Solution**:
1. Check backend configuration in `.env`
2. Verify API key is valid
3. Test connection in Settings → AI Backend

## 📚 Documentation

See parent directory for detailed guides:
- `SMS_WEBHOOK_SETUP.md` - SMS webhook setup guide
- `SMS_FEATURES_GUIDE.md` - Advanced SMS features guide

## 📄 License

Copyright (c) 2025 Hanna Lovvold. All rights reserved.

This software is provided as-is without warranty of any kind.

## 👤 Creator

**Hanna Lovvold** (2025)

Design and development of the Kardia AI Companion application.

## 🙏 Credits

- **GTK4/libadwaita** - Modern GNOME UI framework
- **GNOME HIG** - Human Interface Guidelines
- **Twilio** - SMS services infrastructure
- **AI Providers** - OpenAI, Groq, Anthropic, Together AI, DeepSeek, etc.
- **Python** - Programming language
- **Flask** - Webhook server for incoming SMS

---

**Version**: 1.0.0 (GTK4)
**Platform**: Linux with GTK4/libadwaita
**Language**: Python 3.8+
**Created by**: Hanna Lovvold
