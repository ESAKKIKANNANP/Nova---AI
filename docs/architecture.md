# Autonomous Data Scientist — Software Architecture

> **Version:** 1.0.0  
> **Date:** July 13, 2026  
> **Architect:** Senior Software Architect  
> **Status:** Approved for Implementation

---

## Table of Contents

1. [High-Level Architecture](#1-high-level-architecture)
2. [Component Diagram](#2-component-diagram)
3. [Agent Architecture](#3-agent-architecture)
4. [LangGraph Architecture](#4-langgraph-architecture)
5. [API Architecture](#5-api-architecture)
6. [Database Architecture](#6-database-architecture)
7. [Deployment Architecture](#7-deployment-architecture)
8. [Sequence Diagram](#8-sequence-diagram)
9. [Data Flow Diagram](#9-data-flow-diagram)
10. [Folder Structure](#10-folder-structure)

---

## 1. High-Level Architecture

The Autonomous Data Scientist (ADS) is a multi-agent AI platform that ingests raw data, autonomously plans analytical workflows, executes Python-based data science pipelines, interprets results, and delivers actionable insights — all with minimal human intervention.

```mermaid
graph TB
    subgraph CLIENT["🖥️  Client Layer"]
        UI["Next.js Web App\n(Chat + Dashboard)"]
        SDK["Python SDK\n(Programmatic Access)"]
        CLI["CLI Tool\n(agy-ds)"]
    end

    subgraph GATEWAY["🔀 API Gateway Layer"]
        GW["API Gateway\n(FastAPI + Nginx)"]
        AUTH["Auth Service\n(OAuth2 / JWT)"]
        WS["WebSocket Server\n(Real-time streaming)"]
    end

    subgraph ORCHESTRATION["🧠 Orchestration Layer"]
        OM["Orchestrator\n(LangGraph StateGraph)"]
        AR["Agent Registry"]
        TQ["Task Queue\n(Celery + Redis)"]
        ES["Event Stream\n(Kafka)"]
    end

    subgraph AGENTS["🤖 Agent Layer"]
        PA["Planner Agent"]
        DA["Data Analyst Agent"]
        FE["Feature Engineer Agent"]
        ML["ML Trainer Agent"]
        VI["Visualizer Agent"]
        IN["Insight Generator Agent"]
        CR["Critic / Verifier Agent"]
    end

    subgraph TOOLS["🔧 Tool Layer"]
        PY["Python Sandbox\n(Jupyter Kernel)"]
        DB_TOOL["DB Query Tool"]
        FS_TOOL["File System Tool"]
        WEB["Web Search Tool"]
        PLOT["Plotting Tool\n(Matplotlib/Plotly)"]
    end

    subgraph DATA["🗄️  Data Layer"]
        OBJ["Object Storage\n(S3 / MinIO)"]
        VDB["Vector DB\n(ChromaDB / Pinecone)"]
        RDB["Relational DB\n(PostgreSQL)"]
        CACHE["Cache\n(Redis)"]
        TS["Time-Series DB\n(InfluxDB)"]
    end

    subgraph LLM["🌐 LLM Provider Layer"]
        GPT["OpenAI GPT-4o"]
        GEMINI["Google Gemini 2.0"]
        OSS["Open-Source LLMs\n(Ollama / vLLM)"]
    end

    subgraph OBS["📊 Observability Layer"]
        LOG["Logging\n(Loki + Grafana)"]
        TRACE["Tracing\n(LangSmith / Jaeger)"]
        MON["Metrics\n(Prometheus)"]
    end

    CLIENT --> GATEWAY
    GATEWAY --> ORCHESTRATION
    ORCHESTRATION --> AGENTS
    AGENTS --> TOOLS
    TOOLS --> DATA
    AGENTS <--> LLM
    ORCHESTRATION --> OBS
    AGENTS --> OBS
```

---

## 2. Component Diagram

```mermaid
graph LR
    subgraph FRONTEND["Frontend Application"]
        CHAT["Chat Interface"]
        DASH["Analytics Dashboard"]
        UPLOAD["Dataset Uploader"]
        REPORT["Report Viewer"]
        EXEC["Execution Monitor"]
    end

    subgraph BACKEND["Backend Services"]
        direction TB
        API["REST API Service\n(FastAPI)"]
        WS_SVC["WebSocket Service\n(streaming events)"]
        AUTH_SVC["Authentication Service\n(JWT / OAuth2)"]
        FILE_SVC["File Ingestion Service"]
        SCHED["Scheduler Service\n(APScheduler)"]
    end

    subgraph AGENT_ENGINE["Agent Engine"]
        ORCH["LangGraph Orchestrator"]
        AGENT_POOL["Agent Pool Manager"]
        MEM["Memory Manager\n(short + long term)"]
        TOOL_REG["Tool Registry"]
        SANDBOX["Code Sandbox\n(Pyodide / local runner)"]
    end

    subgraph STORAGE["Storage Services"]
        PG["PostgreSQL\n(users, jobs, metadata)"]
        REDIS["Redis\n(sessions, cache, pub/sub)"]
        S3["S3 / MinIO\n(datasets, artifacts)"]
        CHROMA["ChromaDB\n(embeddings, memory)"]
    end

    subgraph INFRA["Infrastructure"]
        NGINX["Nginx Reverse Proxy"]
        KAFKA["Kafka Event Bus"]
        CELERY["Celery Workers"]
        RUNTIME["Local Runtime"]
    end

    FRONTEND --> NGINX
    NGINX --> API
    NGINX --> WS_SVC
    API --> AUTH_SVC
    API --> FILE_SVC
    API --> ORCH
    API --> SCHED
    ORCH --> AGENT_POOL
    ORCH --> MEM
    AGENT_POOL --> TOOL_REG
    TOOL_REG --> SANDBOX
    ORCH --> KAFKA
    KAFKA --> CELERY
    CELERY --> AGENT_POOL
    API --> PG
    API --> REDIS
    FILE_SVC --> S3
    MEM --> CHROMA
    MEM --> REDIS
    SANDBOX --> S3
```

---

## 3. Agent Architecture

```mermaid
graph TB
    subgraph SUPERVISOR["🎯 Supervisor Agent (Orchestrator)"]
        PLANNER["🗺️  Planner Agent\n─────────────────\n• Decomposes user goals\n• Creates task DAG\n• Assigns sub-agents\n• Re-plans on failure"]
        CRITIC["🔍 Critic Agent\n─────────────────\n• Validates agent outputs\n• Detects hallucinations\n• Requests re-execution\n• Quality gating"]
    end

    subgraph SPECIALIST["⚙️  Specialist Agents"]
        DATA_AGENT["📊 Data Analyst Agent\n─────────────────\n• EDA & profiling\n• Missing value analysis\n• Statistical summaries\n• Correlation analysis"]

        FEAT_AGENT["🔩 Feature Engineer Agent\n─────────────────\n• Feature creation\n• Encoding & scaling\n• Dimensionality reduction\n• Feature selection"]

        ML_AGENT["🤖 ML Trainer Agent\n─────────────────\n• Model selection\n• Hyperparameter tuning\n• Cross-validation\n• Model evaluation"]

        VIZ_AGENT["📈 Visualizer Agent\n─────────────────\n• Chart generation\n• Interactive plots\n• Dashboard assembly\n• Report formatting"]

        INSIGHT_AGENT["💡 Insight Generator Agent\n─────────────────\n• Result interpretation\n• Business recommendations\n• Narrative generation\n• Anomaly explanation"]
    end

    subgraph SUPPORT["🛠️  Support Agents"]
        CODE_AGENT["</> Code Generator Agent\n─────────────────\n• Python code generation\n• Code debugging\n• Execution management\n• Output parsing"]

        SEARCH_AGENT["🔍 Research Agent\n─────────────────\n• Web search\n• Documentation lookup\n• Library discovery\n• Context enrichment"]
    end

    subgraph MEMORY["🧠 Shared Memory Bus"]
        STM["Short-Term Memory\n(Redis / In-Context)"]
        LTM["Long-Term Memory\n(ChromaDB Embeddings)"]
        WKMEM["Working Memory\n(LangGraph State)"]
    end

    PLANNER --> DATA_AGENT
    PLANNER --> FEAT_AGENT
    PLANNER --> ML_AGENT
    PLANNER --> VIZ_AGENT
    PLANNER --> INSIGHT_AGENT
    PLANNER --> CODE_AGENT
    PLANNER --> SEARCH_AGENT

    DATA_AGENT --> CRITIC
    FEAT_AGENT --> CRITIC
    ML_AGENT --> CRITIC
    VIZ_AGENT --> CRITIC
    INSIGHT_AGENT --> CRITIC
    CODE_AGENT --> CRITIC

    CRITIC -->|"✅ Pass"| INSIGHT_AGENT
    CRITIC -->|"❌ Fail → Retry"| PLANNER

    ALL_AGENTS --- MEMORY
    DATA_AGENT & FEAT_AGENT & ML_AGENT & VIZ_AGENT & INSIGHT_AGENT & CODE_AGENT & SEARCH_AGENT --> MEMORY
```

---

## 4. LangGraph Architecture

```mermaid
stateDiagram-v2
    [*] --> UserGoalReceived : User submits query + dataset

    UserGoalReceived --> GoalClarification : Ambiguous request?
    GoalClarification --> PlannerNode : Goal clarified

    UserGoalReceived --> PlannerNode : Clear request

    PlannerNode --> DataIngestionNode : Plan created
    DataIngestionNode --> EDANode : Data loaded & validated

    EDANode --> FeatureEngNode : EDA complete
    EDANode --> InsightNode : EDA-only request

    FeatureEngNode --> ModelSelectionNode : Features ready
    ModelSelectionNode --> ModelTrainingNode : Model selected
    ModelTrainingNode --> ModelEvalNode : Training done

    ModelEvalNode --> CriticNode : Evaluation complete
    CriticNode --> VisualizationNode : ✅ Quality passed
    CriticNode --> PlannerNode : ❌ Quality failed → Re-plan

    InsightNode --> VisualizationNode : Insights generated
    VisualizationNode --> ReportNode : Charts created
    ReportNode --> [*] : Report delivered to user

    note right of PlannerNode
        Planner creates a DAG of tasks.
        Each node maps to a specialist agent.
        Conditional edges based on task type.
    end note

    note right of CriticNode
        Validates outputs.
        Max 3 retry loops before
        escalating to human.
    end note
```

### LangGraph State Schema

```mermaid
classDiagram
    class GraphState {
        +str session_id
        +str user_goal
        +str dataset_path
        +DataProfile data_profile
        +TaskPlan task_plan
        +List~AgentOutput~ agent_outputs
        +List~str~ executed_code
        +List~Artifact~ artifacts
        +str final_report
        +int retry_count
        +str current_node
        +str error_message
        +bool requires_human
    }

    class TaskPlan {
        +str plan_id
        +List~Task~ tasks
        +str dag_json
        +str status
    }

    class AgentOutput {
        +str agent_name
        +str node_id
        +Any output
        +bool validated
        +str critique
    }

    class Artifact {
        +str artifact_id
        +str type
        +str s3_path
        +str mime_type
        +datetime created_at
    }

    GraphState "1" --> "1" TaskPlan
    GraphState "1" --> "many" AgentOutput
    GraphState "1" --> "many" Artifact
```

---

## 5. API Architecture

### REST API Endpoints

```mermaid
graph LR
    subgraph AUTH_ROUTES["/auth"]
        A1["POST /login"]
        A2["POST /register"]
        A3["POST /refresh"]
        A4["POST /logout"]
    end

    subgraph SESSION_ROUTES["/sessions"]
        S1["POST /sessions — Create new analysis session"]
        S2["GET /sessions — List all sessions"]
        S3["GET /sessions/:id — Get session detail"]
        S4["DELETE /sessions/:id — Delete session"]
    end

    subgraph DATASET_ROUTES["/datasets"]
        D1["POST /datasets/upload — Upload file"]
        D2["POST /datasets/connect — Connect DB/URL"]
        D3["GET /datasets/:id/profile — Get data profile"]
        D4["DELETE /datasets/:id — Delete dataset"]
    end

    subgraph ANALYSIS_ROUTES["/analysis"]
        AN1["POST /analysis/run — Run full analysis"]
        AN2["GET /analysis/:id/status — Check job status"]
        AN3["GET /analysis/:id/results — Get results"]
        AN4["POST /analysis/:id/feedback — Submit feedback"]
    end

    subgraph ARTIFACT_ROUTES["/artifacts"]
        AR1["GET /artifacts/:id — Download artifact"]
        AR2["GET /artifacts/:id/preview — Preview artifact"]
    end

    subgraph WS_ROUTES["WebSocket /ws"]
        WS1["WS /ws/:session_id — Stream agent events"]
    end

    CLIENT --> AUTH_ROUTES
    CLIENT --> SESSION_ROUTES
    CLIENT --> DATASET_ROUTES
    CLIENT --> ANALYSIS_ROUTES
    CLIENT --> ARTIFACT_ROUTES
    CLIENT --> WS_ROUTES
```

### API Request/Response Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant GW as API Gateway
    participant AUTH as Auth Service
    participant API as FastAPI
    participant Q as Task Queue
    participant WS as WebSocket

    C->>GW: POST /analysis/run {goal, dataset_id}
    GW->>AUTH: Validate JWT
    AUTH-->>GW: Token valid
    GW->>API: Forward request
    API->>Q: Enqueue analysis job
    Q-->>API: job_id returned
    API-->>C: 202 Accepted {job_id}

    loop Streaming via WebSocket
        C->>WS: Connect WS /ws/{session_id}
        Q->>WS: Agent event published
        WS-->>C: {event_type, agent, message, artifact}
    end

    C->>API: GET /analysis/{job_id}/results
    API-->>C: 200 OK {report, artifacts, insights}
```

---

## 6. Database Architecture

### Entity-Relationship Diagram

```mermaid
erDiagram
    USERS {
        uuid id PK
        string email UK
        string name
        string hashed_password
        string role
        string plan_tier
        timestamp created_at
        timestamp updated_at
    }

    ORGANIZATIONS {
        uuid id PK
        string name
        string slug UK
        string plan_tier
        int seat_count
        timestamp created_at
    }

    SESSIONS {
        uuid id PK
        uuid user_id FK
        uuid org_id FK
        string title
        string status
        timestamp created_at
        timestamp completed_at
    }

    DATASETS {
        uuid id PK
        uuid session_id FK
        string filename
        string s3_path
        bigint size_bytes
        string mime_type
        jsonb schema_info
        jsonb profile_summary
        timestamp uploaded_at
    }

    ANALYSIS_JOBS {
        uuid id PK
        uuid session_id FK
        uuid dataset_id FK
        string status
        string user_goal
        jsonb task_plan
        jsonb langgraph_state
        int retry_count
        timestamp started_at
        timestamp completed_at
    }

    AGENT_RUNS {
        uuid id PK
        uuid job_id FK
        string agent_name
        string node_id
        string status
        jsonb input_snapshot
        jsonb output_snapshot
        int tokens_used
        float latency_ms
        timestamp started_at
        timestamp ended_at
    }

    ARTIFACTS {
        uuid id PK
        uuid job_id FK
        string artifact_type
        string s3_path
        string mime_type
        string title
        timestamp created_at
    }

    REPORTS {
        uuid id PK
        uuid job_id FK
        text markdown_content
        string pdf_s3_path
        timestamp generated_at
    }

    FEEDBACK {
        uuid id PK
        uuid job_id FK
        uuid user_id FK
        int rating
        text comment
        timestamp created_at
    }

    USERS ||--o{ SESSIONS : "owns"
    ORGANIZATIONS ||--o{ SESSIONS : "has"
    ORGANIZATIONS ||--o{ USERS : "contains"
    SESSIONS ||--o{ DATASETS : "uses"
    SESSIONS ||--o{ ANALYSIS_JOBS : "triggers"
    ANALYSIS_JOBS ||--o{ AGENT_RUNS : "contains"
    ANALYSIS_JOBS ||--o{ ARTIFACTS : "produces"
    ANALYSIS_JOBS ||--|| REPORTS : "generates"
    ANALYSIS_JOBS ||--o{ FEEDBACK : "receives"
    DATASETS ||--o{ ANALYSIS_JOBS : "analyzed by"
```

### Vector Database Schema (ChromaDB)

```mermaid
graph TB
    subgraph COLLECTIONS["ChromaDB Collections"]
        C1["📚 dataset_embeddings\n─────────────────\nid: chunk_id\nembedding: float[1536]\nmetadata: {dataset_id, row_range, col_names}\ndocument: text chunk of data"]

        C2["🧠 memory_store\n─────────────────\nid: memory_id\nembedding: float[1536]\nmetadata: {session_id, agent, timestamp}\ndocument: agent observation/result"]

        C3["📖 knowledge_base\n─────────────────\nid: doc_chunk_id\nembedding: float[1536]\nmetadata: {source, domain, version}\ndocument: DS/ML reference text"]

        C4["📋 report_index\n─────────────────\nid: report_section_id\nembedding: float[1536]\nmetadata: {job_id, section_type}\ndocument: report paragraph"]
    end
```

---

## 7. Deployment Architecture

```mermaid
graph TB
    subgraph INTERNET["🌐 Internet"]
        USER_BROWSER["User Browser"]
        MOBILE["Mobile Client"]
    end

    subgraph CDN["☁️  CDN (CloudFront / Cloudflare)"]
        STATIC["Static Assets\nNext.js Build"]
    end

    subgraph VPC["🔒 VPC — Production Region (us-east-1)"]
        subgraph DMZ["DMZ — Public Subnet"]
            LB["AWS ALB / Nginx\nLoad Balancer"]
            WAF["WAF\n(Rate limiting, DDoS)"]
        end

        subgraph APP_TIER["Application Tier — Private Subnet"]
            subgraph K8S["Kubernetes Cluster (EKS)"]
                API_POD["FastAPI Pods\n(3× replicas)"]
                WS_POD["WebSocket Pods\n(2× replicas)"]
                CELERY_POD["Celery Worker Pods\n(auto-scaled 2–20×)"]
                SANDBOX_POD["Code Sandbox Pods\n(gVisor isolated)"]
                ORCH_POD["Orchestrator Pod\n(LangGraph)"]
            end
        end

        subgraph DATA_TIER["Data Tier — Isolated Subnet"]
            RDS["AWS RDS PostgreSQL\n(Multi-AZ)"]
            ELASTICACHE["AWS ElastiCache\n(Redis Cluster)"]
            MSK["AWS MSK\n(Kafka Managed)"]
            S3_STORE["AWS S3\n(Datasets + Artifacts)"]
            OPENSEARCH["AWS OpenSearch\n(Vector + Log Search)"]
        end

        subgraph MONITORING["Monitoring Subnet"]
            GRAFANA["Grafana\n(Dashboards)"]
            PROMETHEUS["Prometheus\n(Metrics)"]
            LOKI["Loki\n(Logs)"]
            LANGSMITH["LangSmith\n(LLM Tracing)"]
        end
    end

    subgraph EXTERNAL["🔌 External Services"]
        OPENAI["OpenAI API"]
        GEMINI["Google AI API"]
        SENDGRID["SendGrid\n(Email)"]
        STRIPE["Stripe\n(Billing)"]
    end

    USER_BROWSER --> CDN
    MOBILE --> CDN
    CDN --> WAF
    WAF --> LB
    LB --> API_POD
    LB --> WS_POD
    API_POD --> CELERY_POD
    API_POD --> ORCH_POD
    ORCH_POD --> SANDBOX_POD
    API_POD --> RDS
    API_POD --> ELASTICACHE
    CELERY_POD --> MSK
    SANDBOX_POD --> S3_STORE
    API_POD --> OPENAI
    API_POD --> GEMINI
    API_POD --> SENDGRID
    API_POD --> STRIPE
    K8S --> PROMETHEUS
    PROMETHEUS --> GRAFANA
    API_POD --> LOKI
    ORCH_POD --> LANGSMITH
```

### Kubernetes Resource Overview

```mermaid
graph LR
    subgraph NS_ADS["Namespace: ads-production"]
        D1["Deployment: api-server\nreplicas: 3\nCPU: 1–2 cores\nMEM: 2–4 Gi"]
        D2["Deployment: ws-server\nreplicas: 2\nCPU: 0.5–1 core\nMEM: 1–2 Gi"]
        D3["Deployment: orchestrator\nreplicas: 2\nCPU: 2–4 cores\nMEM: 4–8 Gi"]
        D4["Deployment: celery-worker\nreplicas: 2–20 (HPA)\nCPU: 2–8 cores\nMEM: 4–16 Gi"]
        D5["Deployment: code-sandbox\nreplicas: 2–10 (HPA)\nCPU: 1–4 cores\nMEM: 2–8 Gi\nruntime: gVisor"]
        SVC1["Services: ClusterIP + LoadBalancer"]
        CM["ConfigMaps + Secrets\n(Vault integration)"]
        PVC["PersistentVolumeClaims\n(ephemeral workspace)"]
    end
```

---

## 8. Sequence Diagram

### Full Analysis Workflow

```mermaid
sequenceDiagram
    actor U as 👤 User
    participant FE as Next.js Frontend
    participant GW as API Gateway
    participant API as FastAPI
    participant ORCH as Orchestrator (LangGraph)
    participant PA as Planner Agent
    participant DA as Data Analyst Agent
    participant ML as ML Trainer Agent
    participant CR as Critic Agent
    participant VI as Visualizer Agent
    participant IG as Insight Agent
    participant SB as Code Sandbox
    participant S3 as Object Storage
    participant DB as PostgreSQL
    participant WS as WebSocket

    U->>FE: Upload dataset + enter goal
    FE->>GW: POST /datasets/upload
    GW->>API: Forward + validate JWT
    API->>S3: Store dataset
    API->>DB: Create dataset record
    API-->>FE: {dataset_id}

    U->>FE: Submit analysis goal
    FE->>GW: POST /analysis/run {goal, dataset_id}
    GW->>API: Forward request
    API->>DB: Create analysis job
    API->>ORCH: Invoke LangGraph session
    API-->>FE: 202 Accepted {job_id}

    FE->>WS: Connect /ws/{session_id}

    ORCH->>PA: Invoke Planner with goal + profile
    PA-->>ORCH: TaskPlan (DAG of tasks)
    ORCH->>WS: Event: "Plan created"
    WS-->>FE: 📋 Plan ready

    ORCH->>DA: Execute EDA node
    DA->>SB: Run EDA code
    SB-->>DA: EDA results
    DA-->>ORCH: DataProfile + summary
    ORCH->>WS: Event: "EDA complete"
    WS-->>FE: 📊 EDA results streaming

    ORCH->>ML: Execute training node
    ML->>SB: Run model training code
    SB-->>ML: Trained model + metrics
    ML-->>ORCH: ModelEvaluation
    ORCH->>WS: Event: "Model trained"

    ORCH->>CR: Validate ML outputs
    CR-->>ORCH: ✅ Quality passed

    ORCH->>VI: Generate visualizations
    VI->>SB: Render plots
    SB->>S3: Upload chart images
    SB-->>VI: S3 artifact URLs
    VI-->>ORCH: ChartArtifacts
    ORCH->>WS: Event: "Charts ready"
    WS-->>FE: 📈 Charts available

    ORCH->>IG: Generate insights + report
    IG-->>ORCH: FinalReport (markdown)
    ORCH->>DB: Save job results + report
    ORCH->>WS: Event: "Analysis complete"
    WS-->>FE: ✅ Done

    U->>FE: View results dashboard
    FE->>API: GET /analysis/{job_id}/results
    API->>DB: Fetch results
    API-->>FE: {report, charts, insights, metrics}
    FE-->>U: Render interactive report
```

---

## 9. Data Flow Diagram

### Level 0 — Context Diagram

```mermaid
graph LR
    U["👤 User"] -->|"Goal + Dataset"| ADS["🤖 Autonomous\nData Scientist\nPlatform"]
    ADS -->|"Insights + Reports + Charts"| U
    ADS <-->|"Model API calls"| LLM_EXT["🌐 LLM Providers\n(OpenAI / Gemini)"]
    ADS -->|"Billing events"| STRIPE_EXT["💳 Stripe"]
    ADS -->|"Notifications"| EMAIL_EXT["📧 Email Service"]
```

### Level 1 — Main Data Flows

```mermaid
graph TB
    subgraph INPUT["📥 Input Processing"]
        DS_IN["Raw Dataset\n(CSV, Excel, JSON, DB)"]
        GOAL_IN["User Goal\n(Natural Language)"]
        DS_PARSE["Data Parser\n& Validator"]
        GOAL_PARSE["Goal Parser\n& Clarifier"]
    end

    subgraph PLAN["📋 Planning"]
        PROFILE["Data Profiler"]
        PLANNER["Task DAG\nPlanner"]
        TASK_Q["Task Queue"]
    end

    subgraph EXEC["⚙️ Execution Pipeline"]
        EDA_FLOW["EDA Pipeline\n• Stats\n• Distributions\n• Correlations\n• Missing data"]
        FEAT_FLOW["Feature Engineering\n• Encoding\n• Scaling\n• Selection\n• Creation"]
        ML_FLOW["ML Pipeline\n• Model selection\n• Training\n• Tuning\n• Evaluation"]
        VIZ_FLOW["Visualization\n• Charts\n• Plots\n• Dashboards"]
    end

    subgraph VALIDATE["🔍 Validation"]
        CRITIC_FLOW["Critic Agent\n• Output quality\n• Hallucination check\n• Statistical validity"]
    end

    subgraph OUTPUT["📤 Output Generation"]
        INSIGHT_FLOW["Insight Generator\n• Interpretations\n• Recommendations\n• Narratives"]
        REPORT_GEN["Report Generator\n• Markdown\n• PDF\n• HTML"]
        ARTIFACT_STORE["Artifact Storage\n(S3)"]
    end

    subgraph MEMORY["🧠 Memory Systems"]
        CONTEXT["In-Context\n(LangGraph State)"]
        SHORT["Short-Term\n(Redis)"]
        LONG["Long-Term\n(ChromaDB)"]
    end

    DS_IN --> DS_PARSE --> PROFILE
    GOAL_IN --> GOAL_PARSE --> PLANNER
    PROFILE --> PLANNER
    PLANNER --> TASK_Q

    TASK_Q --> EDA_FLOW
    EDA_FLOW --> FEAT_FLOW
    FEAT_FLOW --> ML_FLOW
    ML_FLOW --> VIZ_FLOW

    EDA_FLOW --> CRITIC_FLOW
    ML_FLOW --> CRITIC_FLOW
    CRITIC_FLOW -->|"✅ Approved"| INSIGHT_FLOW
    CRITIC_FLOW -->|"❌ Retry"| TASK_Q

    INSIGHT_FLOW --> REPORT_GEN
    VIZ_FLOW --> ARTIFACT_STORE
    REPORT_GEN --> ARTIFACT_STORE

    EDA_FLOW <--> CONTEXT
    ML_FLOW <--> CONTEXT
    INSIGHT_FLOW <--> LONG
    PLANNER <--> SHORT
```

### Level 2 — Agent Internal Data Flow

```mermaid
graph LR
    subgraph AGENT_INTERNALS["Agent Internal Processing"]
        direction TB
        INPUT_CTX["Input Context\n(State + Memory)"]
        LLM_CALL["LLM Reasoning\n(GPT-4o / Gemini)"]
        CODE_GEN["Code Generation\n(Python snippet)"]
        EXEC_ENV["Execution\n(Sandbox)"]
        PARSE_OUT["Output Parsing\n(Structured)"]
        MEM_WRITE["Memory Write\n(Observation stored)"]
        OUTPUT_CTX["Output → Graph State"]

        INPUT_CTX --> LLM_CALL
        LLM_CALL --> CODE_GEN
        CODE_GEN --> EXEC_ENV
        EXEC_ENV --> PARSE_OUT
        PARSE_OUT --> MEM_WRITE
        PARSE_OUT --> OUTPUT_CTX
    end
```

---

## 10. Folder Structure

```
autonomous-data-scientist/
│
├── 📁 apps/
│   ├── 📁 web/                          # Next.js Frontend App
│   │   ├── public/
│   │   ├── src/
│   │   │   ├── app/                     # Next.js App Router
│   │   │   │   ├── (auth)/
│   │   │   │   │   ├── login/
│   │   │   │   │   └── register/
│   │   │   │   ├── (dashboard)/
│   │   │   │   │   ├── sessions/
│   │   │   │   │   ├── analysis/[id]/
│   │   │   │   │   └── datasets/
│   │   │   │   └── layout.tsx
│   │   │   ├── components/
│   │   │   │   ├── chat/
│   │   │   │   ├── dashboard/
│   │   │   │   ├── charts/
│   │   │   │   ├── report/
│   │   │   │   └── shared/
│   │   │   ├── hooks/
│   │   │   ├── lib/
│   │   │   │   ├── api-client.ts
│   │   │   │   └── ws-client.ts
│   │   │   ├── store/                   # Zustand state management
│   │   │   └── types/
│   │   ├── package.json
│   │   └── next.config.ts
│   │
│   └── 📁 cli/                          # Python CLI (agy-ds)
│       ├── ads_cli/
│       │   ├── commands/
│       │   └── main.py
│       └── pyproject.toml
│
├── 📁 services/
│   ├── 📁 api/                          # FastAPI Backend
│   │   ├── ads_api/
│   │   │   ├── main.py                  # App entrypoint
│   │   │   ├── routers/
│   │   │   │   ├── auth.py
│   │   │   │   ├── sessions.py
│   │   │   │   ├── datasets.py
│   │   │   │   ├── analysis.py
│   │   │   │   └── artifacts.py
│   │   │   ├── models/                  # SQLAlchemy models
│   │   │   │   ├── user.py
│   │   │   │   ├── session.py
│   │   │   │   ├── dataset.py
│   │   │   │   ├── analysis_job.py
│   │   │   │   └── artifact.py
│   │   │   ├── schemas/                 # Pydantic schemas
│   │   │   ├── services/
│   │   │   │   ├── auth_service.py
│   │   │   │   ├── dataset_service.py
│   │   │   │   └── analysis_service.py
│   │   │   ├── websocket/
│   │   │   │   └── event_handler.py
│   │   │   ├── middleware/
│   │   │   │   ├── auth_middleware.py
│   │   │   │   └── rate_limiter.py
│   │   │   ├── db/
│   │   │   │   ├── session.py
│   │   │   │   └── migrations/          # Alembic migrations
│   │   │   └── config/
│   │   │       └── settings.py
│   │   ├── tests/
│   │   └── pyproject.toml
│   │
│   └── 📁 worker/                       # Celery Worker Service
│       ├── ads_worker/
│       │   ├── tasks/
│       │   │   ├── analysis_task.py
│       │   │   └── report_task.py
│       │   └── celery_app.py
│       └── pyproject.toml
│
├── 📁 engine/                           # Core Agent Engine (Python)
│   ├── ads_engine/
│   │   ├── __init__.py
│   │   │
│   │   ├── 📁 orchestrator/             # LangGraph orchestration
│   │   │   ├── graph.py                 # StateGraph definition
│   │   │   ├── state.py                 # GraphState schema
│   │   │   ├── nodes.py                 # Node function mappings
│   │   │   ├── edges.py                 # Conditional edge logic
│   │   │   └── runner.py               # Graph execution runner
│   │   │
│   │   ├── 📁 agents/                   # Specialist agents
│   │   │   ├── base_agent.py            # Abstract base agent
│   │   │   ├── planner_agent.py
│   │   │   ├── data_analyst_agent.py
│   │   │   ├── feature_engineer_agent.py
│   │   │   ├── ml_trainer_agent.py
│   │   │   ├── visualizer_agent.py
│   │   │   ├── insight_generator_agent.py
│   │   │   ├── critic_agent.py
│   │   │   ├── code_generator_agent.py
│   │   │   └── research_agent.py
│   │   │
│   │   ├── 📁 tools/                    # Agent tools
│   │   │   ├── registry.py              # Tool registry
│   │   │   ├── python_sandbox.py        # Code execution tool
│   │   │   ├── data_reader.py           # Data I/O tools
│   │   │   ├── db_query.py              # SQL query tool
│   │   │   ├── chart_renderer.py        # Visualization tool
│   │   │   ├── web_search.py            # Research tool
│   │   │   └── file_manager.py          # File system tool
│   │   │
│   │   ├── 📁 memory/                   # Memory systems
│   │   │   ├── memory_manager.py        # Unified memory interface
│   │   │   ├── short_term.py            # Redis-backed STM
│   │   │   ├── long_term.py             # ChromaDB-backed LTM
│   │   │   └── working_memory.py        # In-graph working memory
│   │   │
│   │   ├── 📁 llm/                      # LLM abstraction layer
│   │   │   ├── provider.py              # LLM provider interface
│   │   │   ├── openai_provider.py
│   │   │   ├── gemini_provider.py
│   │   │   └── local_provider.py        # Ollama / vLLM
│   │   │
│   │   ├── 📁 sandbox/                  # Isolated code execution
│   │   │   ├── sandbox_manager.py
│   │   │   ├── local_sandbox.py
│   │   │   └── output_parser.py
│   │   │
│   │   ├── 📁 prompts/                  # Prompt templates
│   │   │   ├── planner_prompts.py
│   │   │   ├── analyst_prompts.py
│   │   │   ├── ml_prompts.py
│   │   │   ├── critic_prompts.py
│   │   │   └── insight_prompts.py
│   │   │
│   │   └── 📁 utils/                    # Shared utilities
│   │       ├── data_profiler.py
│   │       ├── schema_detector.py
│   │       ├── token_counter.py
│   │       └── result_serializer.py
│   │
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   └── pyproject.toml
│
├── 📁 infrastructure/                   # IaC and deployment
│   ├── 📁 k8s/                          # Kubernetes manifests
│   │   ├── namespaces/
│   │   ├── deployments/
│   │   │   ├── api-deployment.yaml
│   │   │   ├── worker-deployment.yaml
│   │   │   ├── orchestrator-deployment.yaml
│   │   │   └── sandbox-deployment.yaml
│   │   ├── services/
│   │   ├── configmaps/
│   │   ├── hpa/                         # Horizontal Pod Autoscalers
│   │   └── ingress/
│   │
│   ├── 📁 terraform/                    # AWS infrastructure
│   │   ├── modules/
│   │   │   ├── vpc/
│   │   │   ├── eks/
│   │   │   ├── rds/
│   │   │   ├── elasticache/
│   │   │   ├── s3/
│   │   │   └── msk/
│   │   ├── environments/
│   │   │   ├── dev/
│   │   │   ├── staging/
│   │   │   └── production/
│   │   └── main.tf
│   │
│   └── 📁 monitoring/                   # Observability configs
│       ├── grafana/
│       │   └── dashboards/
│       ├── prometheus/
│       │   └── prometheus.yml
│       └── loki/
│           └── loki-config.yml
│
├── 📁 packages/                         # Shared Python packages
│   ├── 📁 ads-sdk/                      # Python SDK
│   │   ├── ads_sdk/
│   │   │   ├── client.py
│   │   │   ├── async_client.py
│   │   │   └── models.py
│   │   └── pyproject.toml
│   │
│   └── 📁 ads-types/                    # Shared type definitions
│       ├── ads_types/
│       └── pyproject.toml
│
├── 📁 docs/                             # Documentation
│   ├── architecture/
│   │   └── architecture.md              # This document
│   ├── api/
│   │   └── openapi.yaml
│   ├── guides/
│   └── adr/                             # Architecture Decision Records
│
├── 📁 scripts/                          # Dev and ops scripts
│   ├── setup-dev.sh
│   ├── run-tests.sh
│   └── deploy.sh
│
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── cd-staging.yml
│       └── cd-production.yml
│
├── pyproject.toml                       # Monorepo root config
├── package.json                         # JS monorepo root
├── turbo.json                           # Turborepo config
└── README.md
```

---

## Architecture Decision Records (Key Decisions)

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | **LangGraph for orchestration** | Native support for cyclical agent workflows, conditional branching, and state persistence — essential for retry/critic loops |
| 2 | **Celery + Redis for task queue** | Decouples HTTP requests from long-running analysis jobs; supports distributed, autoscaled workers |
| 3 | **gVisor sandbox for code execution** | Provides kernel-level isolation for untrusted Python code without full VM overhead |
| 4 | **ChromaDB for vector memory** | Lightweight, embeddable, no infrastructure overhead vs Pinecone — suitable for both local and cloud deployment |
| 5 | **WebSocket for streaming** | Real-time agent event streaming improves UX for long analyses (vs polling) |
| 6 | **Monorepo structure** | Single repo with Turborepo enables atomic commits, shared types, and unified CI/CD across all services |
| 7 | **LLM provider abstraction** | Supports hot-swapping between OpenAI, Gemini, and local OSS models with zero code change in agents |
| 8 | **PostgreSQL JSONB for state** | Flexible schema for LangGraph state snapshots without full NoSQL complexity |

---

## Non-Functional Architecture Guarantees

| Attribute | Target | Mechanism |
|-----------|--------|-----------|
| **Availability** | 99.9% SLA | Multi-AZ RDS, K8s rolling deployments, ALB health checks |
| **Scalability** | 1000 concurrent sessions | HPA on Celery workers + sandbox pods; Kafka partitioning |
| **Latency (API)** | < 300ms p95 | Redis caching, async FastAPI, connection pooling |
| **Latency (Analysis)** | < 5 min for standard datasets | Parallel agent execution via task DAG |
| **Security** | SOC 2 Type II ready | JWT auth, gVisor sandbox, VPC isolation, secrets via Vault |
| **Observability** | Full trace coverage | LangSmith per-agent tracing + Prometheus/Grafana + Loki |
| **Data Privacy** | GDPR compliant | Data isolation per tenant, deletion APIs, S3 encryption at rest |

---

*Document generated by: Senior Software Architect | Autonomous Data Scientist Platform v1.0*
