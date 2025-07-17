#!/bin/bash

# SEER Platform Setup Script
echo "🚀 Setting up SEER Cybersecurity Threat Intelligence Platform..."

# Check Python version
echo "📋 Checking Python version..."
python --version
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check Node.js version
echo "📋 Checking Node.js version..."
node --version
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt
pip install -r requirements_api.txt

# Setup environment file
echo "⚙️ Setting up environment configuration..."
if [ ! -f .env ]; then
    cat > .env << EOF
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# Database
DATABASE_URL=your_postgresql_connection_string

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Crawler Configuration
CRAWL_DELAY=1
MAX_PAGES=50
USER_AGENT=SEER-Crawler/1.0

# Security
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
EOF
    echo "✅ Created .env file. Please update with your actual values."
else
    echo "✅ .env file already exists."
fi

# Setup database
echo "🗄️ Setting up database..."
python scripts/migrate.py

# Setup frontend
echo "🎨 Setting up frontend..."
cd seer/dashboard

# Install Node.js dependencies
npm install

# Setup frontend environment
if [ ! -f .env.local ]; then
    cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
EOF
    echo "✅ Created frontend .env.local file."
else
    echo "✅ Frontend .env.local file already exists."
fi

# Build frontend
npm run build

echo "🎉 Setup complete! 

To start the application:

1. Backend API:
   python main.py

2. Frontend Dashboard:
   cd seer/dashboard
   npm run dev

3. Visit: http://localhost:3000

📚 See README.md for detailed documentation." 