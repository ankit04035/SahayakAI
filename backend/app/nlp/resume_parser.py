"""
Structured Resume Content Parser.
Extracts sections, education history, experience records,
projects, and certifications from cleaned resume text.
"""

import re
from typing import Any, Dict, List, Optional
from backend.app.nlp.skill_extractor import extract_skills

SECTION_PATTERNS = {
    "education": re.compile(
        r"^\s*(?:education|academic background|academic qualifications|academics|qualifications)\s*:?\s*$",
        re.IGNORECASE,
    ),
    "experience": re.compile(
        r"^\s*(?:work experience|professional experience|experience|employment history|work history|internships)\s*:?\s*$",
        re.IGNORECASE,
    ),
    "skills": re.compile(
        r"^\s*(?:technical skills|skills|technologies|core competencies|tools & technologies|proficiencies)\s*:?\s*$",
        re.IGNORECASE,
    ),
    "projects": re.compile(
        r"^\s*(?:projects|personal projects|academic projects|key projects)\s*:?\s*$",
        re.IGNORECASE,
    ),
    "certifications": re.compile(
        r"^\s*(?:certifications|certificates|licenses)\s*:?\s*$",
        re.IGNORECASE,
    ),
}


def parse_resume_sections(text: str) -> Dict[str, str]:
    """
    Split resume text into recognized functional sections.
    """
    if not text:
        return {}

    lines = text.splitlines()
    sections: Dict[str, List[str]] = {
        "summary": [],
        "skills": [],
        "education": [],
        "experience": [],
        "projects": [],
        "certifications": [],
    }

    current_section = "summary"

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        matched_sec = None
        for sec_name, pattern in SECTION_PATTERNS.items():
            if pattern.match(stripped):
                matched_sec = sec_name
                break

        if matched_sec:
            current_section = matched_sec
            continue

        sections[current_section].append(stripped)

    return {k: "\n".join(v) for k, v in sections.items() if v}


def extract_education(text: str) -> List[Dict[str, Any]]:
    """
    Extract structured educational credentials (degree, institution, year).
    """
    education_entries: List[Dict[str, Any]] = []
    lines = text.splitlines()

    degree_pattern = re.compile(
        r"(?<![a-zA-Z0-9])(B\.?Tech|B\.?E\.?|B\.?S\.?|B\.?Sc|M\.?Tech|M\.?E\.?|M\.?S\.?|M\.?Sc|BCA|MCA|MBA|Ph\.?D|Bachelor[^,\n]*|Master[^,\n]*|Diploma)(?![a-zA-Z0-9])",
        re.IGNORECASE,
    )
    year_pattern = re.compile(r"(?<!\d)(19\d{2}|20\d{2})(?!\d)")
    institution_pattern = re.compile(r"([A-Z][a-zA-Z\s&]+(?:University|Institute|College|Academy|School))")

    for i, line in enumerate(lines):
        degree_match = degree_pattern.search(line)
        if degree_match:
            degree_str = line.strip()
            search_block = "\n".join(lines[max(0, i - 1) : min(len(lines), i + 2)])
            inst_match = institution_pattern.search(search_block)
            years = year_pattern.findall(search_block)

            education_entries.append({
                "degree": degree_match.group(1).strip(),
                "institution": inst_match.group(1).strip() if inst_match else None,
                "year": years[-1] if years else None,
                "description": degree_str,
            })

    return education_entries


def extract_experience(text: str) -> List[Dict[str, Any]]:
    """
    Extract work experience records (role, company, duration).
    """
    experience_entries: List[Dict[str, Any]] = []
    lines = text.splitlines()

    role_pattern = re.compile(
        r"(?<![a-zA-Z0-9])(Software Engineer|Senior Developer|Lead Engineer|Backend Engineer|Frontend Developer|Backend Developer|Full Stack Developer|Data Scientist|Machine Learning Engineer|DevOps Engineer|Intern|Cloud Architect|Consultant|Analyst|System Administrator)(?![a-zA-Z0-9])",
        re.IGNORECASE,
    )
    date_pattern = re.compile(
        r"(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*)?(?:19|20)\d{2}\s*[-–—to]+\s*(?:(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*)?(?:19|20)\d{2}|Present)",
        re.IGNORECASE,
    )

    for i, line in enumerate(lines):
        role_match = role_pattern.search(line)
        if role_match:
            search_block = "\n".join(lines[i : min(len(lines), i + 3)])
            date_match = date_pattern.search(search_block)

            parts = line.split(" - ")
            company = parts[1].strip() if len(parts) > 1 else None

            experience_entries.append({
                "role": role_match.group(1).strip(),
                "company": company,
                "duration": date_match.group(0).strip() if date_match else None,
                "description": line.strip(),
            })

    return experience_entries


def parse_structured_resume(text: str) -> Dict[str, Any]:
    """
    Comprehensive structured parser converting raw resume text into normalized profile.
    """
    sections = parse_resume_sections(text)
    all_skills = extract_skills(text)
    education = extract_education(sections.get("education", text))
    experience = extract_experience(sections.get("experience", text))

    projects = []
    if "projects" in sections:
        proj_lines = [l.strip("-*• ") for l in sections["projects"].splitlines() if len(l.strip("-*• ")) > 5]
        projects = proj_lines[:5]

    certifications = []
    if "certifications" in sections:
        cert_lines = [l.strip("-*• ") for l in sections["certifications"].splitlines() if len(l.strip("-*• ")) > 5]
        certifications = cert_lines[:5]

    return {
        "skills": all_skills,
        "education": education,
        "experience": experience,
        "projects": projects,
        "certifications": certifications,
    }
