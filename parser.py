from typing import Dict
from pypdf import PdfReader


SECTION_HEADERS = {
    "education": ["education", "academic background"],
    "experience": ["experience", "work experience", "employment"],
    "skills": ["skills", "technical skills", "core competencies"],
    "projects": ["projects"],
    "certifications": ["certifications", "certificates"],
}


def extract_text_from_pdf(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    pages = []

    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)

    return "\n".join(pages)


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ").replace("\t", " ")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def split_sections(text: str) -> Dict[str, str]:
    lines = text.splitlines()
    sections = {"other": []}
    current_section = "other"

    for line in lines:
        lower = line.lower()
        matched = False

        for section, headers in SECTION_HEADERS.items():
            if any(h in lower for h in headers):
                current_section = section
                sections[current_section] = []
                matched = True
                break

        if not matched:
            sections.setdefault(current_section, []).append(line)

    return {
        key: "\n".join(value).strip()
        for key, value in sections.items()
        if value
    }


def parse_resume(pdf_path: str) -> Dict[str, str]:
    raw_text = extract_text_from_pdf(pdf_path)
    cleaned = clean_text(raw_text)
    sections = split_sections(cleaned)

    return {
        "education": sections.get("education", ""),
        "experience": sections.get("experience", ""),
        "skills": sections.get("skills", ""),
        "projects": sections.get("projects", ""),
        "certifications": sections.get("certifications", ""),
        "other": sections.get("other", "")
    }


if __name__ == "__main__":
    import json
    import os

    # Path to the resume file
    resume_path = "resume.pdf"
    
    if os.path.exists(resume_path):
        print(f"Parsing {resume_path}...\n")
        data = parse_resume(resume_path)
        print(json.dumps(data, indent=2))
    else:
        print(f"Error: {resume_path} not found in the current directory.")

