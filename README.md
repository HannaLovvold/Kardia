# Kardia - AI Companion GTK4 Application

**Created by Hanna Lovvold (2025)**

A **completely standalone** modern GTK4/libadwaita AI companion application with REST API, memory management, and multi-companion support.

## 🖼️ Screenshots

### Desktop Application
![Kardia Desktop Program](/media/Kardia_program.png)

### Android App
![Kardia Android App](/media/Kardia_android_app.png)

## ✨ Standalone

Kardia is now **100% standalone** - all backend code is included. No need for the parent `ai-companion` directory!

## 🎯 Features

- **Modern GTK4/libadwaita Interface** - Beautiful GNOME-style UI
- **Multiple AI Companions** - Create custom companions with personalities
- **Proactive Messaging** - Companions send spontaneous messages throughout the day
- **REST API** - Access from your phone app or other clients
- **Push Notifications** - Webhook support for real-time updates
- **Companion Avatars** - Custom images for each character
- **Typing Indicators** - See when AI is generating a response
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
pip install python-dotenv requests flask flask-cors

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
pip install gi-gtk gi-adwaita openai anthropic groq python-dotenv requests flask flask-cors
```

### 2. Configure AI Backend

Create a `.env` file in the Kardia directory:

```bash
# API Server Configuration
API_SERVER_PORT=5000
API_BEARER_TOKEN=your-secret-token-here

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

## 📱 REST API Usage

The REST API allows external clients (like your custom phone app) to interact with Kardia.

### Authentication

All API endpoints require a Bearer token in the Authorization header:

```
Authorization: Bearer your-secret-token-here
```

Set `API_BEARER_TOKEN` in your `.env` file.

### Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check (no auth required) |
| GET | `/api/status` | Get typing indicator status |
| GET | `/api/companions` | List all companions with avatar info |
| GET | `/api/companions/<id>/avatar` | Get companion avatar image |
| POST | `/api/companions/select` | Select active companion |
| GET | `/api/companion/current` | Get current companion info |
| POST | `/api/message` | Send message to AI |
| GET | `/api/conversation` | Get conversation history |
| DELETE | `/api/conversation` | Clear conversation |
| GET | `/api/memories` | Get user memories |
| POST | `/api/memories` | Add a memory |
| GET | `/api/proactive/settings` | Get proactive messaging settings |
| PUT | `/api/proactive/settings` | Update proactive settings |
| GET | `/api/proactive/companions/<id>` | Get companion's proactive settings |
| PUT | `/api/proactive/companions/<id>` | Update companion's proactive settings |
| POST | `/api/webhook` | Register webhook for push notifications |
| DELETE | `/api/webhook` | Remove webhook |

### Example: Send Message

```bash
curl -X POST http://localhost:5000/api/message \
  -H "Authorization: Bearer your-secret-token-here" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?"}'
```

**Response:**
```json
{
  "success": true,
  "response": "I'm doing well, thank you!",
  "companion": {
    "id": "companion_1",
    "name": "Luna"
  },
  "timestamp": "2025-01-13T12:00:00"
}
```

### Example: List Companions

```bash
curl http://localhost:5000/api/companions \
  -H "Authorization: Bearer your-secret-token-here"
```

### Example: Select Companion

```bash
curl -X POST http://localhost:5000/api/companions/select \
  -H "Authorization: Bearer your-secret-token-here" \
  -H "Content-Type: application/json" \
  -d '{"companion_id": "companion_1"}'
```

### Example: Get Companion Avatar

```bash
curl http://localhost:5000/api/companions/companion_1/avatar \
  -H "Authorization: Bearer your-secret-token-here" \
  --output avatar.png
```

### Example: Check Typing Status

```bash
curl http://localhost:5000/api/status \
  -H "Authorization: Bearer your-secret-token-here"
```

**Response:**
```json
{
  "success": true,
  "typing": true,
  "companion_id": "companion_1",
  "current_companion": {
    "id": "companion_1",
    "name": "Luna"
  }
}
```

### Example: Register Webhook for Push Notifications

```bash
curl -X POST http://localhost:5000/api/webhook \
  -H "Authorization: Bearer your-secret-token-here" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-app.example.com/webhook"}'
```

**Webhook events sent to your URL:**
```json
{
  "event": "typing_started",
  "timestamp": "2025-01-13T12:00:00",
  "data": {
    "companion_id": "companion_1",
    "companion_name": "Luna"
  }
}
```

**Event types:** `typing_started`, `new_message`, `companion_selected`, `conversation_cleared`, `proactive_message`

## 🎮 Usage

### Proactive Messaging

Companions can send spontaneous messages throughout the day, even when you're not actively chatting. This simulates real companions who reach out unprompted.

**Default behavior:**
- Each companion sends ~3 messages per day
- Messages sent between 9 AM - 10 PM
- Minimum 4 hours between messages from same companion
- Messages match the companion's personality tone

**Message examples by tone:**
- Friendly: "Hey! I was just thinking about you. How's your day going?"
- Affectionate: "I was just thinking about you and wanted to say hello 💕"
- Playful: "Guess what? I was just thinking about you! 😄"
- Flirty: "Hey handsome 😉 Thinking about you..."

**Configure via API:**
```bash
# Get current settings
GET /api/proactive/settings

# Disable proactive messages
PUT /api/proactive/settings {"enabled": false}

# Change frequency (messages per day)
PUT /api/proactive/settings {"frequency": 5}

# Change time window
PUT /api/proactive/settings {"time_start": "08:00", "time_end": "23:00"}

# Disable for specific companion
PUT /api/proactive/companions/luna {"enabled": false}
```

**Webhook notification:**
When a companion sends a proactive message, your registered webhook receives:
```json
{
  "event": "proactive_message",
  "data": {
    "companion_id": "luna",
    "companion_name": "Luna",
    "message": "Hey! I was just thinking about you...",
    "type": "proactive"
  }
}
```

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
3. Or use the API: `POST /api/companions/select` with `companion_id`

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

See Settings in the app for full API endpoint reference and configuration options.

## 📄 License

Copyright (c) 2025 Hanna Lovvold. All rights reserved.

This software is provided as-is without warranty of any kind.

## 👤 Creator

**Hanna Lovvold** (2025)

Design and development of the Kardia AI Companion application.

## 🙏 Credits

- **GTK4/libadwaita** - Modern GNOME UI framework
- **GNOME HIG** - Human Interface Guidelines
- **AI Providers** - OpenAI, Groq, Anthropic, Together AI, DeepSeek, etc.
- **Python** - Programming language
- **Flask** - REST API server

---

**Version**: 1.0.0 (GTK4)
**Platform**: Linux with GTK4/libadwaita
**Language**: Python 3.8+
**Created by**: Hanna Lovvold
