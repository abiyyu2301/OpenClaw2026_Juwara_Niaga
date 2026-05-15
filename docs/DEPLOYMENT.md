# Deploying Niaga

The demo runs comfortably on a small Sumopod VPS (1 vCPU, 1 GB RAM is enough for SQLite + FastAPI + Vite static build). Estimated cost: ~Rp 36,000/month.

## What you need before deploying

- Sumopod VPS (Ubuntu 22.04 recommended) with public IPv4
- GCP service account JSON key (already at `credentials/niaga-backend-key.json` locally)
- Gmail account + app password (only required for real send/receive — dry-run mode works without)
- A domain name (optional — IP-only is fine for the demo)

## Quick deploy

```bash
# On the VPS:
ssh root@<your-ip>

# 1. Install deps
apt update && apt install -y python3.12 python3.12-venv nginx git
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

# 2. Clone repo
cd /opt
git clone https://github.com/abiyyu2301/OpenClaw2026_Juwara_Niaga.git
cd OpenClaw2026_Juwara_Niaga

# 3. Backend
cd backend
python3.12 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
cd ..

# 4. Frontend (build for static serving)
cd frontend
npm install
npm run build      # produces frontend/dist/
cd ..

# 5. Place credentials
mkdir -p credentials
# Upload niaga-backend-key.json to credentials/ via scp or paste contents
chmod 600 credentials/niaga-backend-key.json

# 6. Configure .env
cp .env.example .env
# Edit .env: set GOOGLE_APPLICATION_CREDENTIALS to the absolute path,
# GMAIL_ADDRESS + GMAIL_APP_PASSWORD if you want real email,
# PUBLIC_BASE_URL to https://your-host.

# 7. Run with systemd
cat <<'EOF' > /etc/systemd/system/niaga.service
[Unit]
Description=Niaga FastAPI backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/OpenClaw2026_Juwara_Niaga/backend
EnvironmentFile=/opt/OpenClaw2026_Juwara_Niaga/.env
ExecStart=/opt/OpenClaw2026_Juwara_Niaga/backend/venv/bin/uvicorn app:app --host 127.0.0.1 --port 8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

systemctl enable --now niaga
systemctl status niaga

# 8. Nginx reverse proxy
cat <<'EOF' > /etc/nginx/sites-available/niaga
server {
    listen 80;
    server_name your-host.example.com;   # or _ for any
    root /opt/OpenClaw2026_Juwara_Niaga/frontend/dist;
    index index.html;

    # SPA fallback
    location / { try_files $uri /index.html; }

    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $remote_addr;
    }

    # WebSocket proxy
    location /ws/ {
        proxy_pass http://127.0.0.1:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 600s;
    }
}
EOF

ln -sf /etc/nginx/sites-available/niaga /etc/nginx/sites-enabled/niaga
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# 9. (Optional) HTTPS with certbot
apt install -y certbot python3-certbot-nginx
certbot --nginx -d your-host.example.com
```

## Smoke test on the deployed instance

```bash
curl https://your-host.example.com/api/health
# → {"status":"ok","service":"niaga"}
```

Open `https://your-host.example.com/` in a browser — should see the dashboard. Create a campaign, click **Start Autonomous Run**, watch the agents work in real time.

## Troubleshooting

- **"401 Unauthorized" from Vertex AI**: the service account JSON path in `.env` is wrong or the file isn't readable by the `niaga` systemd user.
- **WebSocket disconnects**: nginx `proxy_read_timeout` too low; bump to 600s+.
- **`models.<X> not found`**: the model ID in `.env` isn't enabled on your GCP project. Check `MODEL_PROSPECTOR` etc. against the Vertex AI Model Garden, then `gcloud services enable aiplatform.googleapis.com`.
- **Email send fails with 535**: Gmail app password must be a 16-char string with NO spaces. Generate at `https://myaccount.google.com/apppasswords` (2FA required).
