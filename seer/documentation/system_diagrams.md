# SEER System Diagrams

This document contains various diagrams representing the SEER cybersecurity monitoring system's architecture, components, and user flows.

## System Architecture Diagram

```mermaid
flowchart TD
    subgraph "Frontend"
        UI[Dashboard UI]
        Pages[Pages Components]
        Services[Frontend Services]
    end

    subgraph "Backend API"
        API[FastAPI Server]
        Routers[API Routers]
        APIServices[API Services]
    end

    subgraph "Data Processing"
        NLP[NLP Engine]
        Parser[Threat Parser]
        AlertEval[Alert Evaluator]
    end

    subgraph "Data Storage"
        Supabase[(Supabase Database)]
        LocalStorage[(Local Storage)]
    end

    UI --> Services
    Services --> API
    Pages --> Services
    
    API --> Routers
    Routers --> APIServices
    APIServices --> NLP
    APIServices --> AlertEval
    NLP --> Parser
    
    Parser --> Supabase
    AlertEval --> LocalStorage
    AlertEval --> Supabase
    
    Routers --> Supabase
```

## Component Diagram

```mermaid
classDiagram
    class Dashboard {
        +displayThreats()
        +displayAlerts()
        +displayStatistics()
    }
    
    class ThreatService {
        +getThreats()
        +getThreat(id)
    }
    
    class AlertService {
        +getAlerts()
        +getHistory()
        +createRule()
        +updateRule()
    }
    
    class ThreatsRouter {
        +GET /api/threats
        +GET /api/threats/:id
        +POST /api/parse
    }
    
    class AlertsRouter {
        +GET /api/alerts
        +POST /api/alerts
        +GET /api/alerts/local_history
    }
    
    class ThreatParser {
        +extract_threat_info()
        +save_threat_to_supabase()
    }
    
    class AlertEvaluator {
        +evaluate_data_against_rules()
        +add_to_alert_history()
    }
    
    class SupabaseClient {
        +getClient()
    }
    
    Dashboard --> ThreatService
    Dashboard --> AlertService
    ThreatService --> ThreatsRouter
    AlertService --> AlertsRouter
    ThreatsRouter --> ThreatParser
    ThreatsRouter --> SupabaseClient
    AlertsRouter --> AlertEvaluator
    AlertsRouter --> SupabaseClient
    ThreatParser --> SupabaseClient
    AlertEvaluator --> SupabaseClient
```

## Database Schema

```mermaid
erDiagram
    THREATS {
        uuid id PK
        string title
        string description
        string severity
        float confidence
        timestamp created_at
        jsonb threat_actors
        jsonb indicators
        jsonb affected_systems
        jsonb tactics
        jsonb techniques
        jsonb mitigations
        jsonb references
    }
    
    ALERT_RULES {
        uuid id PK
        string name
        string type
        jsonb conditions
        string[] notification_channels
        boolean enabled
        timestamp created_at
    }
    
    ALERT_HISTORY {
        uuid id PK
        uuid rule_id FK
        string rule_name
        timestamp triggered_at
        jsonb matched_data
    }
    
    CRAWL_JOBS {
        uuid id PK
        string url
        string status
        timestamp created_at
        timestamp completed_at
    }
    
    ALERT_RULES ||--o{ ALERT_HISTORY : "triggers"
```

## User Flow Diagram

```mermaid
sequenceDiagram
    actor User
    participant Dashboard
    participant API
    participant Parser
    participant Evaluator
    participant DB as Supabase

    User->>Dashboard: View Dashboard
    Dashboard->>API: GET /api/threats
    API->>DB: Query threats
    DB-->>API: Return threats
    API-->>Dashboard: Return threat data
    Dashboard->>User: Display threat stats & recent threats
    
    User->>Dashboard: Upload threat intelligence
    Dashboard->>API: POST /api/parse
    API->>Parser: Process intelligence
    Parser->>Parser: Extract threat info
    Parser->>DB: Save threat
    Parser-->>API: Return extracted info
    API->>Evaluator: Evaluate against alert rules
    Evaluator->>Evaluator: Check matched rules
    Evaluator->>DB: Save matched alerts
    Evaluator-->>API: Return matched rules
    API-->>Dashboard: Return results
    Dashboard->>User: Display processing results
    
    User->>Dashboard: Create Alert Rule
    Dashboard->>API: POST /api/alerts
    API->>DB: Save alert rule
    DB-->>API: Confirm save
    API-->>Dashboard: Return success
    Dashboard->>User: Display confirmation
```

## Data Flow Diagram

```mermaid
flowchart TD
    User((User))
    
    subgraph Input
        Upload[Upload Intelligence]
        ManageRules[Manage Alert Rules]
    end
    
    subgraph Processing
        Parser[Threat Parser]
        Evaluator[Alert Evaluator]
    end
    
    subgraph Storage
        DB[(Supabase Database)]
        LocalFiles[(Local Files)]
    end
    
    subgraph Output
        Dashboard[Dashboard]
        Alerts[Alert Notifications]
    end
    
    User --> Upload
    User --> ManageRules
    
    Upload --> Parser
    Parser --> DB
    Parser --> Evaluator
    
    Evaluator --> DB
    Evaluator --> LocalFiles
    Evaluator --> Alerts
    
    DB --> Dashboard
    LocalFiles --> Dashboard
    
    Dashboard --> User
    Alerts --> User
    
    ManageRules --> DB
```

## Deployment Architecture

```mermaid
flowchart TD
    subgraph Client
        Browser[Web Browser]
    end
    
    subgraph "Server (Production)"
        NextJS[Next.js Frontend]
        FastAPI[FastAPI Backend]
        NLPEngine[NLP Processing Engine]
    end
    
    subgraph "External Services"
        Supabase[(Supabase)]
        Email[Email Service]
    end
    
    Browser <--> NextJS
    NextJS <--> FastAPI
    FastAPI <--> NLPEngine
    FastAPI <--> Supabase
    NLPEngine <--> Supabase
    FastAPI <--> Email
```

## Alert Evaluation Flow

```mermaid
stateDiagram-v2
    [*] --> IncomingData
    
    IncomingData --> RuleMatching: New threat data
    
    state RuleMatching {
        [*] --> CheckRules
        CheckRules --> RuleMatch: Condition met
        CheckRules --> NoMatch: No match
        RuleMatch --> [*]: Return matched rules
        NoMatch --> [*]: Return empty
    }
    
    RuleMatching --> AlertGeneration: Rules matched
    RuleMatching --> [*]: No rules matched
    
    state AlertGeneration {
        [*] --> CreateAlert
        CreateAlert --> SaveAlert
        SaveAlert --> Notify
        Notify --> [*]
    }
    
    AlertGeneration --> [*]
``` 