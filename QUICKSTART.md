# Quick Start Guide - Kardia

## 🚀 Installation (5 minutes)

### 1. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adwaita-1 python3-pip
```

**Fedora:**
```bash
sudo dnf install python3-gobject gtk4 libadwaita python3-pip
```

### 2. Install Python Dependencies
```bash
cd /home/hanna/PythonProjects/Kardia
pip install -r requirements.txt
```

### 3. Configure AI Backend

Create/edit `.env` file in `/home/hanna/PythonProjects/Kardia/`:

```bash
# Get a free API key from https://console.groq.com/
AI_BACKEND=groq
API_KEY=gsk_your_api_key_here
API_URL=https://api.groq.com/openai/v1
API_MODEL=llama-3.3-70b-versatile

# Additional Parameters (for thinking mode)
API_PARAMS={"thinking": {"type": "enabled", "clear_thinking": "true"}, "do_sample": "true"}
```

### 4. Run Kardia

```bash
cd /home/hanna/PythonProjects/Kardia
./run.sh
```

Or:
```bash
python3 main.py
```

## ✅ Verify It Works

1. **App opens** with GTK4 interface
2. **Select a companion** from the list
3. **Send a message** - should get a response!
4. **Try creating a companion** - Click "+ Create Companion"

## 🎯 First Steps

1. **Create Your Profile**
   - Click "Your Profile" button (top right)
   - Add your name, interests, likes/dislikes
   - Click "Save Profile"

2. **Create a Custom Companion**
   - Click "+ Create Companion"
   - Give them a name, gender, personality
   - Use quick-select presets (Romantic, Best Friend, etc.)
   - Click "Save"

3. **Start Chatting!**
   - Select your companion
   - Type a message
   - Have fun!

## 📱 Optional: SMS Setup

Want to text with your AI companion?

1. **Install Flask**:
   ```bash
   pip install flask
   ```

2. **Get Twilio account** (free trial available)

3. **Add to `.env`**:
   ```bash
   TWILIO_ACCOUNT_SID=your_sid
   TWILIO_AUTH_TOKEN=your_token
   TWILIO_PHONE_NUMBER=+1234567890
   USER_PHONE_NUMBER=+0987654321
   ```

4. **Setup webhook** (see `SMS_WEBHOOK_SETUP.md` in parent directory)

## 🆘 Troubleshooting

**"ModuleNotFoundError: No module named 'gi'"**
```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adwaita-1
```

**"Backend not found"**
- All backend code is now included in Kardia
- Make sure you're in the Kardia directory

**"Connection error"**
- Check your API key in `.env`
- Verify internet connection
- Try Settings → AI Backend → Test Connection

## 💡 Tips

- **Groq is FREE** and fast - recommended for testing
- **Multiple companions** - Create different friends/partners
- **Memories** - AI remembers what you share
- **SMS commands** - Switch companions via text: `/switch [name]`

## 📚 Learn More

- `README.md` - Full documentation
- `SMS_FEATURES_GUIDE.md` (parent dir) - Advanced SMS features
- `SMS_WEBHOOK_SETUP.md` (parent dir) - SMS setup guide

---

**Enjoy Kardia! 🎉**
