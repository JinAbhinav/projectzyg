# SEER - Cybersecurity Threat Intelligence Platform

SEER is an advanced cybersecurity threat intelligence platform that combines AI-powered threat analysis, web crawling capabilities, and knowledge graph visualization to provide comprehensive threat detection and analysis.

## 🏗️ Architecture

```
SEER Platform
├── Backend (FastAPI + Python)
│   ├── Web Crawler Engine
│   ├── NLP Threat Parser
│   ├── Knowledge Graph Builder
│   └── Alert System
├── Frontend (Next.js + React)
│   ├── Dashboard
│   ├── Threat Map (Graph Visualization)
│   ├── AI Analysis Tools
│   └── Alert Management
└── Database (Supabase/PostgreSQL)
    ├── Threat Intelligence Data
    ├── Crawled Content
    └── Knowledge Graph
```

## 🚀 Features

- **🕷️ Web Crawler**: Automated website crawling for threat intelligence gathering
- **🤖 AI-Powered Analysis**: NLP-based threat parsing and entity extraction
- **🕸️ Knowledge Graph**: Interactive visualization of threat relationships
- **📊 Real-time Dashboard**: Comprehensive threat intelligence overview
- **🚨 Alert System**: Automated threat detection and alerting
- **🔍 Search & Filter**: Advanced threat intelligence search capabilities

## 📋 Prerequisites

- **Python 3.8+**
- **Node.js 18+**
- **npm or yarn**
- **Supabase account** (for database)
- **Git**

## 🛠️ Installation & Setup

### 1. Clone Repository

```bash
git clone https://github.com/JinAbhinav/projectzyg.git
cd projectzyg
```

### 2. Backend Setup

#### Install Python Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements_api.txt
```

#### Environment Configuration

Create `.env` file in the root directory:

```env
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
```

#### Database Setup

Run migrations to set up the database schema:

```bash
python scripts/migrate.py
```

This will create the following tables:
- `threats` - Core threat intelligence data
- `crawl_jobs` - Web crawling job tracking
- `crawl_results` - Crawled content storage
- `alerts` - Alert management
- `graph_nodes` - Knowledge graph nodes
- `graph_edges` - Knowledge graph relationships

### 3. Frontend Setup

Navigate to the dashboard directory:

```bash
cd seer/dashboard
```

#### Install Dependencies

```bash
npm install
# or
yarn install
```

#### Environment Configuration

Create `.env.local` file in `seer/dashboard/`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

#### Build Frontend

```bash
npm run build
# or
yarn build
```

## 🏃‍♂️ Running the Application

### Development Mode

#### Start Backend API Server

```bash
# From root directory
python main.py
```

The API will be available at: `http://localhost:8000`
API Documentation: `http://localhost:8000/docs`

#### Start Frontend Development Server

```bash
# From seer/dashboard directory
cd seer/dashboard
npm run dev
# or
yarn dev
```

The dashboard will be available at: `http://localhost:3000`

### Production Mode

#### Using Docker (Recommended)

```bash
# Build and run with Docker Compose
docker-compose up --build
```

#### Manual Production Setup

```bash
# Backend
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Frontend
cd seer/dashboard
npm run build
npm start
```

## 📚 API Endpoints

### Core Endpoints

- `GET /` - Health check
- `GET /docs` - API documentation (Swagger)

### Threat Intelligence

- `GET /api/threats` - List all threats
- `POST /api/threats` - Create new threat
- `GET /api/threats/{id}` - Get specific threat
- `PUT /api/threats/{id}` - Update threat
- `DELETE /api/threats/{id}` - Delete threat

### Web Crawler

- `POST /api/crawlers/crawl` - Start crawling job
- `GET /api/crawlers/jobs` - List crawl jobs
- `GET /api/crawlers/jobs/{job_id}` - Get crawl job details
- `GET /api/crawlers/jobs/{job_id}/results` - Get crawl results

### Knowledge Graph

- `GET /api/graph/data` - Get graph nodes and edges
- `POST /api/graph/populate` - Populate graph from existing threats
- `GET /api/graph/stats` - Get graph statistics

### Alerts

- `GET /api/alerts` - List all alerts
- `POST /api/alerts` - Create new alert
- `GET /api/alerts/{id}` - Get specific alert
- `PUT /api/alerts/{id}/status` - Update alert status

## 🧠 AI Analysis Features

### Threat Text Analyzer

Upload or paste threat intelligence text for AI-powered analysis:

```bash
curl -X POST "http://localhost:8000/api/threats/analyze" \
     -H "Content-Type: application/json" \
     -d '{"text": "APT29 threat actor using Cobalt Strike..."}'
```

### Knowledge Graph Population

Automatically extract entities and relationships from existing threats:

```bash
curl -X POST "http://localhost:8000/api/graph/populate"
```

## 📊 Dashboard Features

### Main Dashboard
- Threat statistics overview
- Recent alerts
- Crawl job status
- System health metrics

### Threat Map
- Interactive knowledge graph visualization
- Node filtering by type
- Relationship exploration
- Export capabilities

### AI Knowledge Tools
- Manual threat text analysis
- Bulk graph population
- Knowledge graph statistics

## 🔧 Configuration

### Crawler Settings

Edit `seer/utils/config.py`:

```python
CRAWLER_CONFIG = {
    "max_pages": 50,
    "delay": 1,
    "timeout": 30,
    "user_agent": "SEER-Crawler/1.0"
}
```

### Alert Rules

Configure alert rules in `seer/alert_dispatcher/dispatcher.py`:

```python
ALERT_RULES = {
    "high_severity_keywords": ["APT", "zero-day", "ransomware"],
    "threat_actor_patterns": ["APT[0-9]+", "FIN[0-9]+"],
    "malware_families": ["Cobalt Strike", "Metasploit"]
}
```

## 🧪 Testing

### Run Backend Tests

```bash
python -m pytest tests/
```

### Run Frontend Tests

```bash
cd seer/dashboard
npm test
# or
yarn test
```

### Manual Testing

Test the threat parser:

```bash
python test_threat_parser.py
```

Test crawler functionality:

```bash
python test_crawl4ai.py
```

## 📝 Development Workflow

### Adding New Features

1. **Backend**: Add new endpoints in `seer/api/routers/`
2. **Frontend**: Add new pages in `seer/dashboard/src/pages/`
3. **Database**: Create migrations in `migrations/`
4. **Tests**: Add tests in `tests/`

### Code Structure

```
seer/
├── api/                 # FastAPI application
│   ├── routers/        # API route handlers
│   └── services/       # Business logic
├── crawler/            # Web crawling engine
├── nlp_engine/         # AI/NLP processing
├── db/                 # Database models and connections
├── dashboard/          # Next.js frontend
└── utils/              # Shared utilities
```

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check Supabase credentials in `.env`
   - Verify database URL format
   - Run migrations: `python scripts/migrate.py`

2. **Frontend Build Errors**
   - Clear `.next` directory: `rm -rf .next`
   - Reinstall dependencies: `npm install`
   - Check Node.js version (18+ required)

3. **API Errors**
   - Check Python version (3.8+ required)
   - Verify all dependencies installed
   - Check logs: `tail -f logs/api.log`

4. **Crawler Issues**
   - Verify network connectivity
   - Check user agent restrictions
   - Review crawl delay settings

### Logs Location

- API logs: `logs/api.log`
- Crawler logs: `logs/crawler.log`
- Frontend logs: Browser console

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation: `/docs`
- Review API documentation: `http://localhost:8000/docs`

## 🚀 Roadmap

- [ ] Advanced ML threat prediction models
- [ ] Real-time threat feed integration
- [ ] Mobile application
- [ ] Advanced visualization options
- [ ] Multi-tenant support
- [ ] API rate limiting
- [ ] Advanced search capabilities
- [ ] Threat intelligence sharing

---

**Built with ❤️ for cybersecurity professionals**

