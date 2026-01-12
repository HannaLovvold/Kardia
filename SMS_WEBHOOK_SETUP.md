# Incoming SMS Setup Guide

This guide explains how to set up incoming SMS functionality so you can text your AI companion and receive responses.

## Prerequisites

1. **Install Flask** (webhook server):
   ```bash
   pip install flask
   ```

2. **Twilio account** with:
   - Account SID & Auth Token
   - Twilio phone number
   - Your verified phone number

## Configuration

### 1. Environment Variables

Add these to your `.env` file in the `ai-companion` directory:

```bash
# Twilio credentials
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
USER_PHONE_NUMBER=+0987654321

# Webhook server configuration
WEBHOOK_PORT=5000
```

### 2. Twilio Webhook Configuration

You need a **public URL** for Twilio to send webhooks to. Choose one of these options:

#### Option A: ngrok (Easiest for Development)

1. **Install ngrok**: https://ngrok.com/download

2. **Run ngrok**:
   ```bash
   ngrok http 5000
   ```

3. **Copy the forwarding URL** (e.g., `https://abc123.ngrok.io`)

4. **Configure Twilio**:
   - Go to Twilio Console → Phone Numbers → Your Twilio Number
   - Scroll to "Messaging" section
   - Set "A message comes in" webhook URL to:
     ```
     https://abc123.ngrok.io/sms/incoming
     ```

#### Option B: Deploy to Server

Deploy your app to a server with a public IP (VPS, cloud hosting, etc.)

1. **Expose port 5000** (or use nginx reverse proxy)

2. **Configure Twilio** with your public URL:
   ```
   https://your-domain.com/sms/incoming
   ```

## How It Works

```
┌─────────────┐
│ Your Phone  │
└──────┬──────┘
       │ 1. Send SMS to Twilio number
       ▼
┌─────────────┐
│   Twilio    │
└──────┬──────┘
       │ 2. Webhook POST to /sms/incoming
       ▼
┌─────────────┐
│ Flask Server│ (running on port 5000)
│ (Webhook)   │
└──────┬──────┘
       │ 3. Callback to app
       ▼
┌─────────────┐
 │ GTK4 App   │
 │ (AI Companion)         │
 └──────┬──────┘
        │ 4. Generate AI response
        ▼
┌─────────────┐
 │   Twilio   │
└──────┬──────┘
       │ 5. SMS response back
       ▼
┌─────────────┐
 │ Your Phone │
└─────────────┘
```

## Testing

1. **Start the app**:
   ```bash
   cd ai-companion-gtk4
   python3 main.py
   ```

2. **Verify webhook server started** - You should see:
   ```
   ✅ SMS webhook server started - incoming SMS enabled
   🚀 Starting SMS webhook server on port 5000
   ```

3. **Send a test SMS** from your phone to your Twilio number

4. **Check the console** - You should see:
   ```
   📩 Received SMS from +1234567890: Hello!
   📩 Processing incoming SMS from +1234567890
   ```

5. **Receive the AI response** on your phone

## Troubleshooting

### Webhook not receiving messages

1. **Check ngrok is running**: `ngrok http 5000`
2. **Verify Twilio webhook URL** is correct
3. **Check firewall** allows port 5000
4. **Test webhook health**: `curl http://localhost:5000/sms/health`

### Messages not being processed

1. **Check SMS is configured** in Settings > Twilio tab
2. **Verify companion is selected** (incoming SMS requires active companion)
3. **Check console logs** for errors

### ngrok URL changed

ngrok free tier URLs change each time you restart it. You'll need to update the Twilio webhook URL each time, or use a paid ngrok account for a static subdomain.

## Security Notes

- ⚠️ **Development only**: This setup is for personal use
- 🔒 **Production**: Add authentication to webhook endpoint
- ✅ **Validate**: Verify incoming requests are from Twilio (use Twilio signature validation)
- 🛡️ **Rate limiting**: Consider rate limiting to prevent abuse

## Features

✅ **Incoming SMS** - Text your companion from your phone
✅ **Outgoing SMS** - Receive companion responses on your phone
✅ **Conversation sync** - Messages appear in both app and phone
✅ **Memory integration** - AI remembers from SMS conversations
✅ **Multi-companion** - Works with any companion you have selected

## Limitations

- Must have the app running to receive messages
- ngrok free tier URL changes on restart
- SMS costs apply (Twilio rates)
- Requires companion to be selected in app
