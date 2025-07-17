@echo off
echo 🚀 Setting up SEER Cybersecurity Threat Intelligence Platform...

REM Check Python version
echo 📋 Checking Python version...
python --version
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8+ first.
    pause
    exit /b 1
)

REM Check Node.js version
echo 📋 Checking Node.js version...
node --version
if errorlevel 1 (
    echo ❌ Node.js is not installed. Please install Node.js 18+ first.
    pause
    exit /b 1
)

REM Install Python dependencies
echo 📦 Installing Python dependencies...
pip install -r requirements.txt
pip install -r requirements_api.txt

REM Setup environment file
echo ⚙️ Setting up environment configuration...
if not exist .env (
    (
    echo # Supabase Configuration
    echo SUPABASE_URL=your_supabase_project_url
    echo SUPABASE_KEY=your_supabase_anon_key
    echo SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
    echo.
    echo # Database
    echo DATABASE_URL=your_postgresql_connection_string
    echo.
    echo # API Configuration
    echo API_HOST=0.0.0.0
    echo API_PORT=8000
    echo DEBUG=True
    echo.
    echo # Crawler Configuration
    echo CRAWL_DELAY=1
    echo MAX_PAGES=50
    echo USER_AGENT=SEER-Crawler/1.0
    echo.
    echo # Security
    echo SECRET_KEY=your_secret_key_here
    echo ALGORITHM=HS256
    echo ACCESS_TOKEN_EXPIRE_MINUTES=30
    ) > .env
    echo ✅ Created .env file. Please update with your actual values.
) else (
    echo ✅ .env file already exists.
)

REM Setup database
echo 🗄️ Setting up database...
python scripts/migrate.py

REM Setup frontend
echo 🎨 Setting up frontend...
cd seer\dashboard

REM Install Node.js dependencies
npm install

REM Setup frontend environment
if not exist .env.local (
    (
    echo NEXT_PUBLIC_API_URL=http://localhost:8000
    echo NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
    echo NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
    ) > .env.local
    echo ✅ Created frontend .env.local file.
) else (
    echo ✅ Frontend .env.local file already exists.
)

REM Build frontend
npm run build

echo.
echo 🎉 Setup complete! 
echo.
echo To start the application:
echo.
echo 1. Backend API:
echo    python main.py
echo.
echo 2. Frontend Dashboard:
echo    cd seer\dashboard
echo    npm run dev
echo.
echo 3. Visit: http://localhost:3000
echo.
echo 📚 See README.md for detailed documentation.
echo.
pause 