# Remote Access Setup for Kardia AI Companion

This guide explains how to connect your mobile app to Kardia when you're not on the same local Wi-Fi network.

## Table of Contents

1. [Tailscale (Recommended)](#tailscale-recommended)
2. [SSH Tunneling](#ssh-tunneling)
3. [Cloudflare Tunnel](#cloudflare-tunnel)
4. [ngrok](#ngrok)
5. [Dynamic DNS with Reverse Proxy](#dynamic-dns-with-reverse-proxy)

---

## Tailscale (Recommended)

**Pros:** Free, secure, encrypted, works everywhere, no port forwarding
**Cons:** Requires installing software on both devices

### Setup

#### On Your Linux Machine

1. Install Tailscale:
   ```bash
   curl -fsSL https://tailscale.com/install.sh | sh
   ```

2. Start Tailscale:
   ```bash
   sudo tailscale up
   ```

3. Get your Tailscale IP address:
   ```bash
   tailscale ip -4
   ```
   Example output: `100.x.y.z`

#### On Your Phone

1. Download the Tailscale app:
   - **iOS**: App Store
   - **Android**: Google Play Store

2. Log in with the same account you used on your Linux machine

3. Enable the VPN in the Tailscale app

4. Find your Linux machine's Tailscale IP in the "Machines" tab

#### Connect Your App

In your mobile app settings, set the API URL to:
```
http://100.x.y.z:5000
```
Replace `100.x.y.z` with your Tailscale IP.

#### Make Kardia Accessible on Tailscale

By default, Kardia binds to `0.0.0.0:5000` which should work with Tailscale. If you have issues, check your firewall:

```bash
# Allow traffic on Tailscale interface
sudo iptables -I INPUT -i tailscale0 -p tcp --dport 5000 -j ACCEPT
```

---

## SSH Tunneling

**Pros:** Secure, uses existing SSH infrastructure
**Cons:** Requires keeping tunnel open, needs SSH access

### Setup

#### Option A: From Computer to Phone (Port Forwarding)

Run this command on your Linux machine:

```bash
ssh -R 5000:localhost:5000 user@your-remote-server.com
```

Then connect your phone app to `remote-server.com:5000`.

#### Option B: From Phone (Requires SSH Client App)

1. Install an SSH client app on your phone (Termius, JuiceSSH, etc.)

2. Create a tunnel with port forwarding:
   - Local port: `5000`
   - Remote host: `localhost`
   - Remote port: `5000`
   - Server: your machine's public IP

3. In your companion app, use: `http://localhost:5000`

#### SSH Configuration Tip

Add this to `~/.ssh/config` for easier access:

```
Host kardia-tunnel
    HostName your-public-ip
    User your-username
    LocalForward 5000 localhost:5000
```

Then simply: `ssh kardia-tunnel`

---

## Cloudflare Tunnel

**Pros:** Free, unlimited bandwidth, no public IP needed, DDoS protection
**Cons:** Slightly more complex setup

### Setup

#### 1. Install cloudflared

```bash
# Ubuntu/Debian
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Or with brew
brew install cloudflared
```

#### 2. Authenticate

```bash
cloudflared tunnel login
```

This will open a browser. Select your domain (or get a free one from Cloudflare).

#### 3. Create a Tunnel

```bash
cloudflared tunnel create kardia
```

Save the tunnel ID that's returned.

#### 4. Create Configuration File

Create `~/.cloudflared/config.yml`:

```yaml
tunnel: YOUR_TUNNEL_ID
credentials-file: /home/yourusername/.cloudflared/YOUR_TUNNEL_ID.json

ingress:
  - hostname: your-subdomain.your-domain.com
    service: http://localhost:5000
  - service: http_status:404
```

#### 5. Run the Tunnel

```bash
cloudflared tunnel run kardia
```

#### 6. Connect Your App

Use your configured URL in your mobile app:
```
https://your-subdomain.your-domain.com
```

#### 7. Run as a Service (Optional)

```bash
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

---

## ngrok

**Pros:** Very easy to set up, works instantly
**Cons:** Free tier has limitations (changes URL, limited bandwidth)

### Setup

#### 1. Install ngrok

```bash
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok
```

Or download from [ngrok.com](https://ngrok.com/download).

#### 2. Authenticate (Free Account Required)

```bash
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

Get your token from the ngrok dashboard.

#### 3. Start the Tunnel

```bash
ngrok http 5000
```

You'll see output like:
```
Forwarding  https://abcd-1234.ngrok-free.app -> http://localhost:5000
```

#### 4. Connect Your App

Use the ngrok URL in your mobile app:
```
https://abcd-1234.ngrok-free.app
```

#### 5. Keep URL Stable (Paid Feature)

The free tier changes URLs each time. For a consistent URL, upgrade to a paid plan.

---

## Dynamic DNS with Reverse Proxy

**Pros:** Permanent URL, full control
**Cons:** Most complex, requires public IP or port forwarding

### Setup

#### 1. Get a Domain and Dynamic DNS

- **Free DDNS services**: DuckDNS, No-IP, Dynu
- **Domain**: Any domain registrar

Example with DuckDNS:
1. Go to [duckdns.org](https://www.duckdns.org)
2. Create a free subdomain: `yourname.duckdns.org`

#### 2. Set Up DDNS Client

```bash
# Install ddclient
sudo apt install ddclient

# Or use a simple cron job with curl
echo "*/5 * * * * curl 'https://www.duckdns.org/update?domains=yourname&token=YOUR_TOKEN'" | crontab -
```

#### 3. Configure Your Router

- Log into your router
- Forward port 5000 to your machine's local IP
- Enable UPnP if available (automatic port forwarding)

#### 4. Set Up Reverse Proxy (Nginx)

Install Nginx:
```bash
sudo apt install nginx
```

Create config `/etc/nginx/sites-available/kardia`:

```nginx
server {
    listen 80;
    server_name yourname.duckdns.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/kardia /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 5. Add HTTPS (Recommended)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourname.duckdns.com
```

#### 6. Connect Your App

Use your domain in your mobile app:
```
https://yourname.duckdns.com
```

---

## Security Best Practices

### 1. Use a Strong API Token

Edit your `.env` file and set a secure token:

```bash
# Generate a secure token
openssl rand -base64 32
```

Update `.env`:
```
API_BEARER_TOKEN=your-generated-token-here
```

### 2. Enable HTTPS

For production use, always use HTTPS. Options:
- Cloudflare Tunnel (automatic HTTPS)
- Nginx with Let's Encrypt
- ngrok (automatic HTTPS)

### 3. Use a Firewall

Only allow necessary traffic:

```bash
# UFW example
sudo ufw allow from 100.0.0.0/8 to any port 5000  # Tailscale
sudo ufw enable
```

### 4. Keep Software Updated

```bash
sudo apt update && sudo apt upgrade
```

---

## Troubleshooting

### Connection Refused

- Check Kardia is running: `ps aux | grep python`
- Check port is listening: `netstat -tlnp | grep 5000`
- Check firewall: `sudo ufw status`

### Timeout

- Check your router has port forwarding enabled
- Verify your DDNS is up to date
- Test locally first: `curl http://localhost:5000/api/health`

### Authentication Errors

- Verify your API token matches in `.env` and your app
- Check the Authorization header format: `Bearer YOUR_TOKEN`

---

## Quick Comparison

| Method          | Difficulty | Cost | Permanent URL | Security |
|-----------------|------------|------|---------------|----------|
| Tailscale       | Easy       | Free | Yes*          | Excellent|
| SSH Tunnel      | Medium     | Free | No            | Excellent|
| Cloudflare      | Medium     | Free | Yes           | Excellent|
| ngrok           | Easy       | Free/Paid | Free: No | Good |
| DDNS + Nginx    | Hard       | Free | Yes           | Good** |

*Requires keeping Tailscale running
**Depends on HTTPS setup

---

## Recommendation

**For most users: Tailscale**

It's the easiest, most secure, and most reliable option. Works seamlessly across all networks including cellular.

**For public access: Cloudflare Tunnel**

Free, professional-grade solution with built-in DDoS protection and HTTPS.
