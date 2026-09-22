"""
Curated Role-to-Skill Taxonomy and Career Guidance Mapping.
Provides deterministic, explainable skill requirements, learning progressions,
portfolio projects, and interview topics for common software and AI disciplines.

Note: This is an initial curated industry taxonomy, not an exhaustive labor-market database.
"""

from typing import Any, Dict, List, Optional
from backend.app.nlp.skill_extractor import normalize_skill

ROLE_TAXONOMY: Dict[str, Dict[str, Any]] = {
    "Python Developer": {
        "required_skills": ["Python", "FastAPI", "PostgreSQL", "Git", "REST API", "Docker"],
        "recommended_skills": ["Redis", "SQLAlchemy", "CI/CD", "Linux", "PyTest", "Celery"],
        "learning_stages": [
            {
                "stage": 1,
                "title": "Python Core & Software Design",
                "description": "Master advanced Python idioms, OOP, type hinting, generators, and clean code practices.",
                "skills": ["Python", "Git", "PyTest"],
            },
            {
                "stage": 2,
                "title": "API Engineering & Databases",
                "description": "Design asynchronous RESTful APIs with FastAPI and relational data modeling in PostgreSQL.",
                "skills": ["FastAPI", "REST API", "PostgreSQL", "SQLAlchemy"],
            },
            {
                "stage": 3,
                "title": "Containerization & Background Tasks",
                "description": "Containerize applications with Docker, implement caching with Redis, and handle asynchronous job queues.",
                "skills": ["Docker", "Redis", "Celery", "Linux"],
            },
            {
                "stage": 4,
                "title": "Production Deployment & Interview Prep",
                "description": "Automate CI/CD pipelines, optimize database queries, and master system architecture interview topics.",
                "skills": ["CI/CD"],
            },
        ],
        "default_projects": [
            {
                "title": "High-Throughput Async REST API",
                "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
                "description": "Asynchronous microservice managing concurrent job processing with connection pooling and automated OpenAPI documentation.",
                "difficulty": "Intermediate",
            },
            {
                "title": "Distributed Task Queue with Redis",
                "skills": ["Python", "Redis", "Docker", "Git"],
                "description": "Background worker system executing scheduled jobs, rate limiting, and failure retry backoff.",
                "difficulty": "Intermediate",
            },
        ],
        "interview_topics": [
            "Python memory management, GIL, and garbage collection",
            "Asynchronous event loops (async/await) vs multithreading",
            "RESTful design principles, idempotency, and HTTP status codes",
            "Database indexing strategies and query execution plan optimization",
            "Docker multi-stage builds and container isolation",
        ],
    },
    "Backend Developer": {
        "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "REST API", "Microservices", "Git"],
        "recommended_skills": ["Redis", "Kubernetes", "CI/CD", "System Design", "AWS", "Kafka"],
        "learning_stages": [
            {
                "stage": 1,
                "title": "Backend Foundations & Modular Architecture",
                "description": "Build high-performance RESTful APIs, master relational databases, and enforce structured error handling.",
                "skills": ["Python", "FastAPI", "REST API", "PostgreSQL"],
            },
            {
                "stage": 2,
                "title": "Containerization & Cloud Infrastructure",
                "description": "Package applications with Docker, orchestrate deployments, and manage cloud environments.",
                "skills": ["Docker", "Git", "CI/CD", "AWS"],
            },
            {
                "stage": 3,
                "title": "Scalable Systems & Distributed Caching",
                "description": "Implement in-memory caching with Redis, design microservice boundaries, and manage event queues.",
                "skills": ["Redis", "Microservices", "Kubernetes", "Kafka"],
            },
            {
                "stage": 4,
                "title": "Enterprise System Design & Reliability",
                "description": "Study large-scale distributed patterns, fault tolerance, database sharding, and interview cases.",
                "skills": ["System Design"],
            },
        ],
        "default_projects": [
            {
                "title": "Scalable E-Commerce Order Microservice",
                "skills": ["FastAPI", "PostgreSQL", "Redis", "Docker"],
                "description": "Order processing service with inventory reservation, optimistic locking, and distributed caching.",
                "difficulty": "Advanced",
            },
            {
                "title": "Event-Driven Notification Pipeline",
                "skills": ["Python", "Docker", "Microservices", "REST API"],
                "description": "Microservice broadcasting transactional emails and webhooks with guaranteed delivery.",
                "difficulty": "Intermediate",
            },
        ],
        "interview_topics": [
            "Monolithic vs Microservices trade-offs and domain boundaries",
            "CAP theorem, ACID vs BASE consistency models",
            "Cache invalidation patterns (write-through, cache-aside)",
            "Database connection pooling and deadlock resolution",
            "System scalability: load balancing, horizontal vs vertical scaling",
        ],
    },
    "Frontend Developer": {
        "required_skills": ["JavaScript", "TypeScript", "React", "HTML", "CSS", "Git"],
        "recommended_skills": ["Next.js", "Redux", "REST API", "Tailwind CSS", "Jest", "CI/CD"],
        "learning_stages": [
            {
                "stage": 1,
                "title": "Modern JavaScript & TypeScript",
                "description": "Master ES6+ syntax, asynchronous JS, TypeScript static typing, and browser DOM performance.",
                "skills": ["HTML", "CSS", "JavaScript", "TypeScript"],
            },
            {
                "stage": 2,
                "title": "Component Architecture with React",
                "description": "Build responsive SPAs using functional components, hooks, state management, and modern CSS frameworks.",
                "skills": ["React", "Git", "REST API"],
            },
            {
                "stage": 3,
                "title": "Full-Stack React & Next.js",
                "description": "Implement Server-Side Rendering (SSR), Static Site Generation (SSG), and routing with Next.js.",
                "skills": ["Next.js", "CI/CD"],
            },
            {
                "stage": 4,
                "title": "Web Performance, Accessibility & Interview Prep",
                "description": "Optimize Core Web Vitals, implement unit and integration tests, and ace UI coding interviews.",
                "skills": ["React"],
            },
        ],
        "default_projects": [
            {
                "title": "Interactive Analytics Dashboard SPA",
                "skills": ["React", "TypeScript", "HTML", "CSS"],
                "description": "Real-time responsive dashboard visualizing complex metrics with data filtering and themes.",
                "difficulty": "Intermediate",
            },
            {
                "title": "Accessible Component Library",
                "skills": ["TypeScript", "React", "CSS"],
                "description": "Reusable UI design system complying with WCAG 2.1 AA accessibility standards.",
                "difficulty": "Intermediate",
            },
        ],
        "interview_topics": [
            "React Virtual DOM reconciliation and component lifecycle",
            "TypeScript generics, union types, and utility types",
            "State management patterns and performance optimizations (memo, useCallback)",
            "Web performance metrics: LCP, FID, CLS, and asset bundling",
            "Cross-Browser compatibility, CORS, and web security (XSS, CSRF)",
        ],
    },
    "Full Stack Developer": {
        "required_skills": ["JavaScript", "TypeScript", "React", "Python", "FastAPI", "PostgreSQL", "Git", "Docker"],
        "recommended_skills": ["Next.js", "Redis", "CI/CD", "AWS", "System Design", "REST API"],
        "learning_stages": [
            {
                "stage": 1,
                "title": "Frontend Core & Interactive UI",
                "description": "Master responsive web design, React, TypeScript, and state management.",
                "skills": ["HTML", "CSS", "JavaScript", "TypeScript", "React"],
            },
            {
                "stage": 2,
                "title": "Backend Engineering & Relational Databases",
                "description": "Develop asynchronous REST APIs using FastAPI and model data in PostgreSQL.",
                "skills": ["Python", "FastAPI", "PostgreSQL", "REST API", "Git"],
            },
            {
                "stage": 3,
                "title": "Integration, Containerization & Cloud",
                "description": "Connect frontend client to backend microservices, containerize with Docker, and configure cloud hosting.",
                "skills": ["Docker", "Redis", "CI/CD", "AWS"],
            },
            {
                "stage": 4,
                "title": "End-to-End Architecture & Portfolio Capstone",
                "description": "Design secure authentication, optimize end-to-end performance, and prepare full-stack system interviews.",
                "skills": ["System Design"],
            },
        ],
        "default_projects": [
            {
                "title": "Full-Stack SaaS Management Platform",
                "skills": ["React", "TypeScript", "FastAPI", "PostgreSQL", "Docker"],
                "description": "End-to-end SaaS web application featuring role-based access, API authentication, and dashboard analytics.",
                "difficulty": "Advanced",
            },
            {
                "title": "Real-Time Collaborative Workspace",
                "skills": ["React", "FastAPI", "Redis", "Docker"],
                "description": "Collaborative document and note-taking tool with live updates and responsive styling.",
                "difficulty": "Advanced",
            },
        ],
        "interview_topics": [
            "End-to-end request lifecycle from browser click to database query",
            "Authentication workflows: JWT, OAuth2, and secure cookie storage",
            "API design and contract management between frontend and backend",
            "Relational data consistency vs eventual consistency in UI",
            "Full-stack debugging, profiling, and observability",
        ],
    },
    "Data Analyst": {
        "required_skills": ["SQL", "Python", "Pandas", "NumPy", "Git"],
        "recommended_skills": ["PostgreSQL", "Tableau", "Power BI", "Statistics", "Data Visualization"],
        "learning_stages": [
            {
                "stage": 1,
                "title": "Advanced SQL & Database Querying",
                "description": "Write complex SQL queries, window functions, CTEs, and aggregate reporting metrics.",
                "skills": ["SQL", "PostgreSQL"],
            },
            {
                "stage": 2,
                "title": "Data Wrangling with Python & Pandas",
                "description": "Clean, transform, and analyze structured datasets using Pandas and NumPy.",
                "skills": ["Python", "Pandas", "NumPy", "Git"],
            },
            {
                "stage": 3,
                "title": "Exploratory Data Analysis & Visualization",
                "description": "Extract actionable business insights and visualize trends with interactive charts.",
                "skills": ["Data Visualization", "Statistics"],
            },
            {
                "stage": 4,
                "title": "Business Intelligence & Stakeholder Reporting",
                "description": "Synthesize data stories, build automated executive dashboards, and prepare case interviews.",
                "skills": ["SQL", "Python"],
            },
        ],
        "default_projects": [
            {
                "title": "E-Commerce Customer Cohort Retention Analysis",
                "skills": ["SQL", "Python", "Pandas"],
                "description": "Cohort analysis calculating churn rates, customer lifetime value, and purchase frequency across demographics.",
                "difficulty": "Intermediate",
            },
            {
                "title": "Financial Trends & Revenue Forecasting Dashboard",
                "skills": ["Python", "Pandas", "NumPy", "SQL"],
                "description": "Automated data pipeline summarizing monthly recurring revenue, margins, and anomaly detection.",
                "difficulty": "Intermediate",
            },
        ],
        "interview_topics": [
            "SQL window functions (RANK, DENSE_RANK, LEAD, LAG) and grouping sets",
            "Data normalization vs denormalization for analytical reporting",
            "Handling missing values, outliers, and data quality anomalies in Pandas",
            "Interpreting correlation vs causation in business metrics",
            "Communicating statistical findings clearly to non-technical stakeholders",
        ],
    },
    "Data Scientist": {
        "required_skills": ["Python", "SQL", "Pandas", "NumPy", "Scikit-Learn", "Machine Learning", "Git"],
        "recommended_skills": ["PyTorch", "TensorFlow", "Statistics", "Docker", "Feature Engineering"],
        "learning_stages": [
            {
                "stage": 1,
                "title": "Mathematics, Statistics & Exploratory Analysis",
                "description": "Probability distributions, hypothesis testing, linear algebra, and data manipulation.",
                "skills": ["Python", "SQL", "Pandas", "NumPy"],
            },
            {
                "stage": 2,
                "title": "Classical Machine Learning & Modeling",
                "description": "Supervised and unsupervised learning, hyperparameter tuning, and cross-validation.",
                "skills": ["Scikit-Learn", "Machine Learning", "Git"],
            },
            {
                "stage": 3,
                "title": "Deep Learning & Model Evaluation",
                "description": "Neural network architectures, embeddings, regularization, and model validation metrics.",
                "skills": ["PyTorch", "TensorFlow"],
            },
            {
                "stage": 4,
                "title": "Model Deployment & Interview Preparation",
                "description": "Serve models as microservice endpoints, monitor drift, and solve end-to-end ML case studies.",
                "skills": ["Docker", "Machine Learning"],
            },
        ],
        "default_projects": [
            {
                "title": "Predictive Customer Churn Classifier",
                "skills": ["Python", "Scikit-Learn", "Pandas", "Machine Learning"],
                "description": "End-to-end classification model evaluating ROC-AUC, feature importances, and SHAP explainability values.",
                "difficulty": "Intermediate",
            },
            {
                "title": "Time-Series Demand Forecasting Engine",
                "skills": ["Python", "NumPy", "Pandas", "Machine Learning"],
                "description": "Predictive modeling pipeline forecasting product demand using rolling statistics and gradient boosting.",
                "difficulty": "Advanced",
            },
        ],
        "interview_topics": [
            "Bias-variance trade-off and regularization techniques (L1, L2)",
            "Evaluation metrics for imbalanced datasets (Precision, Recall, F1, PR-AUC)",
            "Feature selection and dimensionality reduction techniques (PCA)",
            "Ensemble learning: Random Forest vs Gradient Boosting (XGBoost)",
            "A/B testing methodology, sample size determination, and p-values",
        ],
    },
    "Machine Learning Engineer": {
        "required_skills": ["Python", "PyTorch", "Scikit-Learn", "Machine Learning", "Docker", "Git", "REST API"],
        "recommended_skills": ["TensorFlow", "FastAPI", "Kubernetes", "CI/CD", "Deep Learning", "MLOps"],
        "learning_stages": [
            {
                "stage": 1,
                "title": "Machine Learning Algorithms & Frameworks",
                "description": "Master gradient descent, deep neural networks, and PyTorch model building.",
                "skills": ["Python", "Scikit-Learn", "PyTorch", "Machine Learning"],
            },
            {
                "stage": 2,
                "title": "Model Serving & Containerization",
                "description": "Package models into high-throughput API endpoints using FastAPI and Docker containers.",
                "skills": ["FastAPI", "REST API", "Docker", "Git"],
            },
            {
                "stage": 3,
                "title": "Scalable MLOps & Orchestration",
                "description": "Automate model retraining pipelines, tracking experiments, and deploying to Kubernetes.",
                "skills": ["Kubernetes", "CI/CD", "Deep Learning"],
            },
            {
                "stage": 4,
                "title": "Production Optimization & System Design",
                "description": "Quantize models, optimize inference latency, and master ML system design interview problems.",
                "skills": ["Machine Learning", "Docker"],
            },
        ],
        "default_projects": [
            {
                "title": "Low-Latency Model Inference Service",
                "skills": ["Python", "PyTorch", "FastAPI", "Docker"],
                "description": "REST API serving deep learning predictions with batching, health monitoring, and sub-50ms latency.",
                "difficulty": "Advanced",
            },
            {
                "title": "Automated MLOps Training & Deployment Pipeline",
                "skills": ["Python", "Docker", "CI/CD", "Machine Learning"],
                "description": "Continuous integration pipeline validating data quality, retraining models, and packaging artifacts.",
                "difficulty": "Advanced",
            },
        ],
        "interview_topics": [
            "Model quantization, pruning, and ONNX runtime optimization",
            "Designing scalable machine learning inference architectures",
            "Handling data drift, concept drift, and model performance decay in production",
            "Distributed training strategies: data parallelism vs model parallelism",
            "GPU vs CPU memory bounds during model batch inference",
        ],
    },
    "AI/ML Engineer": {
        "required_skills": ["Python", "PyTorch", "Deep Learning", "Natural Language Processing", "Docker", "Git"],
        "recommended_skills": ["FastAPI", "Kubernetes", "Vector Databases", "REST API", "CI/CD", "TensorFlow"],
        "learning_stages": [
            {
                "stage": 1,
                "title": "Deep Learning & Transformer Architectures",
                "description": "Study attention mechanisms, transformer encoders/decoders, and sentence embeddings.",
                "skills": ["Python", "Deep Learning", "PyTorch"],
            },
            {
                "stage": 2,
                "title": "NLP, Semantic Search & Vector Retrieval",
                "description": "Implement vector retrieval, cosine similarity indexing, and text processing pipelines.",
                "skills": ["Natural Language Processing", "Git", "REST API"],
            },
            {
                "stage": 3,
                "title": "Generative AI & LLM Systems (RAG)",
                "description": "Build Retrieval-Augmented Generation workflows, context selection, and multi-provider orchestration.",
                "skills": ["Docker", "FastAPI", "Deep Learning"],
            },
            {
                "stage": 4,
                "title": "AI System Architecture & Evaluation",
                "description": "Benchmark hallucination rates, design resilient fallback mechanisms, and ace AI architecture interviews.",
                "skills": ["Python", "Docker"],
            },
        ],
        "default_projects": [
            {
                "title": "Document Intelligence & Semantic RAG System",
                "skills": ["Python", "PyTorch", "Natural Language Processing", "Docker"],
                "description": "End-to-end RAG assistant performing vector retrieval and grounded generative answers from PDF knowledge bases.",
                "difficulty": "Advanced",
            },
            {
                "title": "Domain-Specific Text Embedding & Classification Engine",
                "skills": ["Python", "PyTorch", "Deep Learning", "Git"],
                "description": "Dense embedding encoder fine-tuned for specialized technical terminology classification.",
                "difficulty": "Advanced",
            },
        ],
        "interview_topics": [
            "Transformer self-attention mechanism and computational complexity",
            "RAG architecture: chunking strategies, dense vs sparse retrieval, and re-ranking",
            "LLM evaluation techniques, hallucination mitigation, and guardrails",
            "Embedding model distance metrics: Cosine vs Euclidean vs Dot Product",
            "Prompt engineering patterns: Few-shot, Chain-of-Thought, and ReAct",
        ],
    },
    "DevOps Engineer": {
        "required_skills": ["Linux", "Docker", "Kubernetes", "CI/CD", "Terraform", "Git"],
        "recommended_skills": ["AWS", "Python", "Bash", "Ansible", "Prometheus", "System Design"],
        "learning_stages": [
            {
                "stage": 1,
                "title": "Linux Systems & Containerization",
                "description": "Master Linux administration, shell scripting, networking, and Docker image creation.",
                "skills": ["Linux", "Docker", "Git"],
            },
            {
                "stage": 2,
                "title": "Infrastructure as Code & CI/CD",
                "description": "Automate cloud provisioning with Terraform and build robust automated CI/CD pipelines.",
                "skills": ["Terraform", "CI/CD", "AWS"],
            },
            {
                "stage": 3,
                "title": "Kubernetes Orchestration & Helm",
                "description": "Deploy, scale, and manage containerized workloads across multi-node Kubernetes clusters.",
                "skills": ["Kubernetes", "Docker", "Linux"],
            },
            {
                "stage": 4,
                "title": "Site Reliability, Observability & Security",
                "description": "Implement metrics logging, disaster recovery, zero-downtime rolling updates, and interview prep.",
                "skills": ["System Design"],
            },
        ],
        "default_projects": [
            {
                "title": "Multi-Environment GitOps Deployment Pipeline",
                "skills": ["Kubernetes", "Docker", "CI/CD", "Terraform"],
                "description": "Automated deployment pipeline deploying microservices to staging and production clusters with automated rollbacks.",
                "difficulty": "Advanced",
            },
            {
                "title": "Infrastructure as Code Cloud Provisioner",
                "skills": ["Terraform", "Linux", "AWS", "Git"],
                "description": "Modular Terraform codebase provisioning VPCs, security groups, managed databases, and compute instances.",
                "difficulty": "Intermediate",
            },
        ],
        "interview_topics": [
            "Kubernetes pod lifecycle, ingress controllers, and services (ClusterIP vs NodePort vs LoadBalancer)",
            "Terraform state management, locking, and drift detection",
            "Continuous Integration vs Continuous Delivery vs Continuous Deployment",
            "Linux troubleshooting: analyzing CPU, memory, I/O bottlenecks (top, iostat, vmstat)",
            "Zero-downtime deployment strategies (Blue-Green, Canary, Rolling)",
        ],
    },
    "Cloud Engineer": {
        "required_skills": ["AWS", "Linux", "Terraform", "Docker", "Python", "Git"],
        "recommended_skills": ["Kubernetes", "CI/CD", "GCP", "Azure", "System Design", "Networking"],
        "learning_stages": [
            {
                "stage": 1,
                "title": "Cloud Computing Fundamentals & Linux",
                "description": "Master cloud architectural principles, IAM access, compute, storage, and networking.",
                "skills": ["AWS", "Linux", "Git"],
            },
            {
                "stage": 2,
                "title": "Infrastructure Automation & Containers",
                "description": "Provision cloud resources with Terraform and containerize microservices using Docker.",
                "skills": ["Terraform", "Docker", "Python"],
            },
            {
                "stage": 3,
                "title": "Cloud Security, Networking & Orchestration",
                "description": "Configure VPC peering, routing tables, security groups, and manage container clusters.",
                "skills": ["Kubernetes", "CI/CD"],
            },
            {
                "stage": 4,
                "title": "Multi-Cloud Architecture & High Availability",
                "description": "Design resilient disaster recovery, multi-region failover, cost optimization, and ace cloud interviews.",
                "skills": ["System Design"],
            },
        ],
        "default_projects": [
            {
                "title": "Highly Available Cloud Web Architecture",
                "skills": ["AWS", "Terraform", "Docker", "Linux"],
                "description": "Auto-scaling web service deployed across multiple availability zones behind an Application Load Balancer.",
                "difficulty": "Intermediate",
            },
            {
                "title": "Automated Serverless Event Processing Pipeline",
                "skills": ["AWS", "Python", "Terraform", "Git"],
                "description": "Event-driven architecture ingesting and processing analytical events using serverless functions and storage queues.",
                "difficulty": "Intermediate",
            },
        ],
        "interview_topics": [
            "Cloud security best practices: IAM least privilege, encryption at rest and in transit",
            "VPC architecture: subnets, NAT gateways, route tables, and security groups",
            "High availability vs Fault tolerance vs Disaster recovery architectures",
            "Storage trade-offs: Block storage vs File storage vs Object storage (S3)",
            "Cloud cost governance, budgeting, and capacity planning",
        ],
    },
}


def get_role_taxonomy(target_role: str) -> Dict[str, Any]:
    """
    Look up role taxonomy matching target role with case-insensitive normalization.
    Falls back gracefully to a generic Software Engineer template if unknown.
    """
    cleaned = target_role.strip().lower()

    # Exact or alias match
    for role_name, data in ROLE_TAXONOMY.items():
        if cleaned == role_name.lower():
            return {"role": role_name, **data}

    # Partial substring match
    for role_name, data in ROLE_TAXONOMY.items():
        if role_name.lower() in cleaned or cleaned in role_name.lower():
            return {"role": role_name, **data}

    # Keyword heuristics
    if "python" in cleaned:
        return {"role": "Python Developer", **ROLE_TAXONOMY["Python Developer"]}
    if "data" in cleaned and "analyst" in cleaned:
        return {"role": "Data Analyst", **ROLE_TAXONOMY["Data Analyst"]}
    if "data" in cleaned or "scientist" in cleaned:
        return {"role": "Data Scientist", **ROLE_TAXONOMY["Data Scientist"]}
    if "devops" in cleaned or "sre" in cleaned or "infrastructure" in cleaned:
        return {"role": "DevOps Engineer", **ROLE_TAXONOMY["DevOps Engineer"]}
    if "cloud" in cleaned or "aws" in cleaned:
        return {"role": "Cloud Engineer", **ROLE_TAXONOMY["Cloud Engineer"]}
    if "front" in cleaned or "ui" in cleaned or "web" in cleaned:
        return {"role": "Frontend Developer", **ROLE_TAXONOMY["Frontend Developer"]}
    if "full" in cleaned or "stack" in cleaned:
        return {"role": "Full Stack Developer", **ROLE_TAXONOMY["Full Stack Developer"]}
    if "ai" in cleaned or "machine" in cleaned or "ml" in cleaned or "deep" in cleaned:
        return {"role": "AI/ML Engineer", **ROLE_TAXONOMY["AI/ML Engineer"]}

    # Fallback to general Software Engineer based on Backend Developer
    base = ROLE_TAXONOMY["Backend Developer"]
    return {
        "role": target_role.strip().title(),
        "required_skills": base["required_skills"],
        "recommended_skills": base["recommended_skills"],
        "learning_stages": base["learning_stages"],
        "default_projects": base["default_projects"],
        "interview_topics": base["interview_topics"],
    }
