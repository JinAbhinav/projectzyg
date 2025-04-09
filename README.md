# SEER - AI-Powered Cyber Threat Prediction & Early Warning System

SEER is an advanced cybersecurity tool that leverages AI, threat intelligence, and deep web crawling to detect and predict cyber threats before they escalate into attacks.

## Features

- **Deep/Dark Web Intelligence** - Crawls websites, forums, and other sources for threat data
- **AI-Powered NLP Analysis** - Uses LLMs to analyze and classify threats
- **Threat Trend Prediction** - ML models for forecasting emerging threats
- **Real-Time Notification Engine** - Alerts users about potential threats
- **Web-Based Intelligence Dashboard** - Visualizes threat data

## Architecture

```
[ Crawl4AI ] → [ NLP/LLM Pipeline ] → [ Threat Classification ] → [ ML Prediction Engine ] → [ Alert Engine ] → [ Dashboard + External Integrations ]
```

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-repo/seer.git
   cd seer
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Edit the `.env` file with your configuration (especially API keys)

## Running SEER

SEER provides a unified command-line interface for all components. The main entry point is `main.py`.

### Available Commands

- **Crawl a URL**:
  ```
  python main.py crawl https://example.com --depth 2 --max-pages 10
  ```

- **Process a crawled job**:
  ```
  python main.py process job_12345
  ```

- **Run threat prediction**:
  ```
  python main.py predict
  ```

- **Run the complete pipeline** (crawl → process → predict → alert):
  ```
  python main.py pipeline https://example.com
  ```

- **Start the API server**:
  ```
  python main.py api
  ```

## Dashboard

The dashboard is a React application located in the `seer/dashboard` directory.

To start the development server:

```
cd seer/dashboard
npm install
npm run dev
```

The dashboard will be available at `http://localhost:3000`.

## Components

- **Crawler**: Handles web crawling and content extraction
- **NLP Engine**: Processes text using OpenAI models
- **Predictor**: ML models for threat prediction
- **Alert Dispatcher**: Sends notifications via email, webhooks, etc.
- **API**: FastAPI-based backend for the dashboard

## Environment Variables

Key environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key
- `CRAWLER_OUTPUT_DIR`: Directory for crawled data
- `ALERT_EMAIL`: Email for receiving alerts

See the `.env` file for all available options.

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -am 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

[MIT License](LICENSE)

# SEER - Threat Classification Module

## Overview

This module implements the threat classification component from the SEER data flow:

```
[ Crawl4AI ] → [ NLP/LLM Pipeline ] → [ Threat Classification ] → [ ML Prediction Engine ] → [ Alert Engine ] → [ Dashboard + External Integrations ]
```

The threat classification system processes data that has been crawled by Crawl4AI and analyzed by the NLP/LLM Pipeline. It categorizes potential threats and prepares datasets for the ML Prediction Engine.

## Implementation Details

### Core Technologies

- **NLP & LLM**: OpenAI API, LangChain, Hugging Face Transformers, spaCy
- **Machine Learning**: scikit-learn, XGBoost, PyTorch (LSTM)
- **Data Processing**: pandas, NumPy
- **Backend**: Flask/FastAPI

### Classification Categories

Based on the PRD (Section 3.2), the system classifies threats into:
- Phishing
- DDoS
- Ransomware
- Exploit Trading
- Zero-day vulnerabilities
- Data breaches
- APT (Advanced Persistent Threat) campaigns

### Classification Process

1. **Input Processing**: 
   - Receives enriched data from the NLP/LLM Pipeline
   - Data includes embeddings, tagged entities, extracted keywords

2. **Feature Engineering**:
   - Transforms text features into numerical vectors
   - Implements TF-IDF and embedding-based features
   - Extracts temporal patterns and source credibility metrics

3. **Multi-label Classification**:
   - Implements ensemble models combining:
     - Transformer-based classification
     - Gradient boosting for structured features
     - Rule-based heuristics for known threat patterns

4. **Metadata Generation**:
   - Confidence score (0-1)
   - Severity rating (Low, Medium, High, Critical)
   - Potential target identification
   - Estimated timeframe

5. **Output Format**:
   - JSON structure with classification results
   - Embedded links to source material
   - Confidence intervals for predictions
   - Tagged entities for cross-referencing

## Integration Points

- **Input**: Consumes processed data from `nlp_engine.py`
- **Output**: Produces structured threat data for `predictor.py`
- **API Endpoints**: Exposes classification services for dashboard queries

## Key Files

- `threat_classifier.py`: Main classification engine
- `models/`: Pre-trained classification models
- `feature_extractors.py`: Feature engineering components
- `taxonomy.py`: Threat classification taxonomy
- `utils/`: Helper functions for data processing

## Performance Metrics

- Target classification precision: >90%
- Processing latency: <5 seconds per document
- Daily processing capacity: Up to 100,000 documents

## Future Enhancements

- Implement active learning for continuous model improvement
- Add support for additional languages beyond English
- Integrate with MITRE ATT&CK framework for enhanced classification
