# Change to script directory
cd "$(dirname "$0")"

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
    libxslt

# Verify Python version
python --version

# Setup Python environment for Athena
echo "Setting up Athena Python environment..."
if [ ! -d "Athena/venv" ]; then
    python -m venv Athena/venv
fi

source Athena/venv/bin/activate

# Install Athena dependencies
# Using pip to install requirements.
# We skip heavy ML libs if possible or let them compile.
# torch and sentence-transformers might be heavy. Termux has issues with some binary wheels.
# We might need to use --no-deps for some or rely on termux-packaged versions if available.
# But let's try standard pip first.

echo "Installing Athena requirements..."
# Removing torch/sentence-transformers from requirements if they cause issues, 
# but user wants memories so we need embeddings.
# sentence-transformers on Termux is hard.
# We used Gemini embeddings in vectors.py, so we might NOT need local sentence-transformers!
# Let's check requirements.txt again.

# Install modified requirements
pip install -r Athena/requirements.txt || echo "Warning: Some python requirements failed to install. Check errors."

# Create .env for Athena if missing
if [ ! -f "Athena/.env" ]; then
    echo "Creating Athena .env with Local DB enabled..."
    cp Athena/.env.example Athena/.env
    echo "" >> Athena/.env
    echo "# Termux Configuration" >> Athena/.env
    echo "USE_LOCAL_DB=true" >> Athena/.env
    # We still need GOOGLE_API_KEY for embeddings. User needs to provide this.
    echo "GOOGLE_API_KEY=PLACEHOLDER_KEY" >> Athena/.env
fi

# Setup OpenClaw Node environment
echo "Setting up OpenClaw Node environment..."
npm install -g pnpm

# Install dependencies
echo "Installing OpenClaw dependencies (pnpm)..."
# Skip optional dependencies that might fail build on Android
export SHARP_IGNORE_GLOBAL_LIBVIPS=1
# Force sqlite-vec to use wasm or skip if possible? No, it tries primarily native.
# If it fails, we might need to remove it manually.
pnpm install --no-frozen-lockfile || echo "Warning: pnpm install had issues, attempting to continue..."

# Build OpenClaw
echo "Building OpenClaw..."
pnpm build

echo "Setup Complete!"
echo "To run Athena/OpenClaw:"
echo "1. Activate venv: source Athena/venv/bin/activate"
echo "2. Start OpenClaw: pnpm start"
