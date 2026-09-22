"""
Deterministic Skill Extraction and Normalization Module.
Provides taxonomy-based skill extraction, canonical normalization,
and exact alias resolution without hallucination.
"""

import re
from typing import Dict, List, Set

# Canonical alias mapping: maps lowercased variations/synonyms to canonical casing
SKILL_ALIAS_MAP: Dict[str, str] = {
    # Languages
    "python": "Python",
    "python3": "Python",
    "py": "Python",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "java": "Java",
    "c++": "C++",
    "cpp": "C++",
    "c#": "C#",
    "csharp": "C#",
    "golang": "Go",
    "go": "Go",
    "rust": "Rust",
    "ruby": "Ruby",
    "php": "PHP",
    "swift": "Swift",
    "kotlin": "Kotlin",
    "scala": "Scala",
    "r": "R",
    "sql": "SQL",
    "html": "HTML",
    "html5": "HTML",
    "css": "CSS",
    "css3": "CSS",
    "bash": "Bash",
    "shell": "Shell",

    # Frameworks & Libraries
    "react": "React",
    "react.js": "React",
    "reactjs": "React",
    "node": "Node.js",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "vue": "Vue",
    "vue.js": "Vue",
    "angular": "Angular",
    "fastapi": "FastAPI",
    "flask": "Flask",
    "django": "Django",
    "spring": "Spring Boot",
    "spring boot": "Spring Boot",
    "springboot": "Spring Boot",
    "express": "Express",
    "express.js": "Express",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "keras": "Keras",
    "scikit-learn": "Scikit-Learn",
    "sklearn": "Scikit-Learn",
    "pandas": "Pandas",
    "numpy": "NumPy",

    # Databases & Storage
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mysql": "MySQL",
    "sqlite": "SQLite",
    "mongodb": "MongoDB",
    "mongo": "MongoDB",
    "redis": "Redis",
    "cassandra": "Cassandra",
    "dynamodb": "DynamoDB",
    "oracle": "Oracle",
    "elasticsearch": "Elasticsearch",

    # Cloud & DevOps
    "aws": "AWS",
    "amazon web services": "AWS",
    "gcp": "GCP",
    "google cloud": "GCP",
    "google cloud platform": "GCP",
    "azure": "Azure",
    "microsoft azure": "Azure",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "terraform": "Terraform",
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",
    "git": "Git",
    "github": "Git",
    "gitlab": "GitLab",
    "linux": "Linux",
    "jenkins": "Jenkins",
    "ansible": "Ansible",

    # Concepts & Domains
    "machine learning": "Machine Learning",
    "ml": "Machine Learning",
    "deep learning": "Deep Learning",
    "dl": "Deep Learning",
    "natural language processing": "Natural Language Processing",
    "nlp": "Natural Language Processing",
    "computer vision": "Computer Vision",
    "cv": "Computer Vision",
    "data structures": "Data Structures",
    "algorithms": "Algorithms",
    "rest": "REST API",
    "restful": "REST API",
    "rest api": "REST API",
    "graphql": "GraphQL",
    "microservices": "Microservices",
    "system design": "System Design",
    "agile": "Agile",
    "scrum": "Scrum",
}

# Pre-sorted search keys: longer phrases match first
_SORTED_KEYS = sorted(SKILL_ALIAS_MAP.keys(), key=len, reverse=True)


def normalize_skill(skill: str) -> str:
    """
    Normalize a skill string to its canonical title representation.

    Examples:
        'py' -> 'Python'
        'k8s' -> 'Kubernetes'
        'react.js' -> 'React'
        'fastapi' -> 'FastAPI'
    """
    cleaned = skill.strip().lower()
    if cleaned in SKILL_ALIAS_MAP:
        return SKILL_ALIAS_MAP[cleaned]
    return skill.strip()


def extract_skills(text: str) -> List[str]:
    """
    Deterministically extract and normalize technical skills found in text.
    Uses boundary matching to prevent partial-word false positives.

    Args:
        text: Input string (resume body or job description).

    Returns:
        Sorted list of unique, canonical skill names.
    """
    if not text or not text.strip():
        return []

    lower_text = text.lower()
    matched_canonical: Set[str] = set()

    for key in _SORTED_KEYS:
        canonical = SKILL_ALIAS_MAP[key]
        if canonical in matched_canonical:
            continue

        if key in {"c++", "cpp"}:
            pattern = r"(?<![a-zA-Z0-9])(?:cpp|c\+\+)(?![a-zA-Z0-9\+])"
            if re.search(pattern, lower_text):
                matched_canonical.add(canonical)
        elif key in {"c#", "csharp"}:
            pattern = r"(?<![a-zA-Z0-9])(?:csharp|c\#)(?![a-zA-Z0-9\#])"
            if re.search(pattern, lower_text):
                matched_canonical.add(canonical)
        elif key == "c":
            # Match standalone capital C only
            if re.search(r"(?<![a-zA-Z0-9])C(?![a-zA-Z0-9\+#])", text):
                matched_canonical.add(canonical)
        elif key == "r":
            pattern = r"(?<![a-zA-Z0-9])(?:r\s+programming|r\s+language|using\s+r)(?![a-zA-Z0-9])"
            if re.search(pattern, lower_text):
                matched_canonical.add(canonical)
        elif key == "go":
            # Match Golang, go programming/language, or standalone capitalized 'Go'
            if re.search(r"(?<![a-zA-Z0-9])(?:golang|go\s+programming|go\s+language)(?![a-zA-Z0-9])", lower_text) or re.search(r"(?<![a-zA-Z0-9])Go(?![a-zA-Z0-9])", text):
                matched_canonical.add(canonical)
        elif key in {"ci/cd", "ci / cd"}:
            if re.search(r"(?<![a-zA-Z0-9])ci\s*/\s*cd(?![a-zA-Z0-9])", lower_text):
                matched_canonical.add(canonical)
        elif "/" in key:
            pattern = rf"(?<![a-zA-Z0-9]){re.escape(key)}(?![a-zA-Z0-9])"
            if re.search(pattern, lower_text):
                matched_canonical.add(canonical)
        else:
            pattern = rf"(?<![a-zA-Z0-9]){re.escape(key)}(?![a-zA-Z0-9])"
            if re.search(pattern, lower_text):
                matched_canonical.add(canonical)

    return sorted(list(matched_canonical))
