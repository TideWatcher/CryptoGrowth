#!/bin/bash
# Run this on a fresh Ubuntu 22.04 Vultr VPS as root
# Usage: bash setup.sh YOUR_ANTHROPIC_API_KEY

set -e

API_KEY=$1
REPO_URL="https://github.com/TideWatcher/CryptoGrowth.git"
APP_DIR="/opt/cryptowrite"

if [ -z "$API_KEY" ]; then
  echo "Usage: bash setup.sh sk-ant-xxxx"
  exit 1
fi

echo "==> Installing Docker..."
apt-get update -q
apt-get install -y -q ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list
apt-get update -q
apt-get install -y -q docker-ce docker-ce-cli containerd.io docker-compose-plugin

echo "==> Cloning repo..."
rm -rf "$APP_DIR"
git clone "$REPO_URL" "$APP_DIR"
cd "$APP_DIR"

echo "==> Writing .env..."
echo "ANTHROPIC_API_KEY=$API_KEY" > .env

echo "==> Building and starting app..."
docker compose up -d --build

echo ""
echo "✅ Done! App running at http://$(curl -s ifconfig.me):8000"
