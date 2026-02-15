#!/bin/bash
set -e

# Termux Setup Script for OpenClaw-Android
# Designed for Termux (Android)

echo "Starting OpenClaw & Athena Setup on Termux..."

# Update and install dependencies
echo "Installing system packages..."
pkg update -y
pkg install -y \
    nodejs \
    python \
    git \
    make \
    clang \
    binutils \
    rust \
    python-numpy \
    openssl-tool \
    openssh \
    libjpeg-turbo \
    libpng \
    libxml2 \
    libxslt \
    sqlite

# Verify Python version
python --version

# Setup Athena (Python backend)
echo "Setting up Athena..."
cd Athena
if [ ! -d "venv" ]; then
    python -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
# Install requirements with no-build-isolation if needed for some packages
pip install -r requirements.txt || pip install --no-build-isolation -r requirements.txt

# Initializing Athena Local DB
echo "Initializing Athena Local DB..."
python src/athena/memory/local_db.py --db ../athena_memory.db

cd ..

# Setup OpenClaw (Node.js backend)
echo "Setting up OpenClaw..."
if ! command -v pnpm &> /dev/null; then
    npm install -g pnpm
fi
pnpm install

# Build OpenClaw
echo "Building OpenClaw..."
pnpm build

# Create default config if not exists
if [ ! -f "config.json5" ]; then
    echo "Creating default config.json5..."
    cp config.json5.example config.json5 || echo "{}" > config.json5
fi

echo "------------------------------------------------"
echo "Setup Complete!"
echo "To start OpenClaw, run: ./openclaw.mjs gateway"
echo "Remember to set your API keys in config.json5 or .env"
echo "------------------------------------------------"
