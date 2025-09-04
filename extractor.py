import pdfplumber
import docx
import re
import spacy

nlp = spacy.load("en_core_web_sm")


def extract_text_from_file(file_path: str) -> str:
    """Extract raw text from PDF or DOCX"""
    if file_path.endswith(".pdf"):
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text

    elif file_path.endswith(".docx"):
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    else:
        raise ValueError("Unsupported file format. Use PDF or DOCX.")


def clean_name(name: str) -> str:
    """Remove emails, numbers, CNIC-like patterns from extracted name"""
    if not name:
        return ""

    # Remove email if stuck in name
    name = re.sub(r"[\w\.-]+@[\w\.-]+", "", name)

    # Remove phone numbers
    name = re.sub(r"(\+92|0)?[0-9]{7,11}", "", name)

    # Remove CNIC
    name = re.sub(r"\d{5}-\d{7}-\d{1}", "", name)

    # Remove extra spaces
    return " ".join(name.split()).strip()


def extract_candidate_info(text: str) -> dict:
    """Extract candidate info using regex + heuristics + NLP"""
    info = {}
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    # ---- Full Name Heuristics ----
    if lines:
        first_line = lines[0]
        if not re.search(r"(curriculum vitae|resume)", first_line, re.IGNORECASE):
            if len(first_line.split()) <= 6:  # allow up to 6 tokens
                info["FullName"] = clean_name(first_line)

    # Regex: first line with 2–3 capitalized words
    if "FullName" not in info and lines:
        cap_match = re.match(r"^([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,3})$", lines[0])
        if cap_match:
            info["FullName"] = clean_name(cap_match.group(1))

    # Fallback: spaCy PERSON entity
    if "FullName" not in info:
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                info["FullName"] = clean_name(ent.text)
                break

    # ---- Email ----
    email_match = re.search(r"[\w\.-]+@[\w\.-]+", text)
    if email_match:
        info["Email"] = email_match.group(0)

    # ---- Phone ----
    phone_match = re.search(r"(\+92|0)?[0-9]{10,11}", text)
    if phone_match:
        info["ContactNo"] = phone_match.group(0)

    # ---- CNIC ----
    cnic_match = re.search(r"\d{5}-\d{7}-\d{1}", text)
    if cnic_match:
        info["CNIC"] = cnic_match.group(0)

    # ---- Skills ----
    skills_match = re.search(r"(Skills|Technical Skills|Key Skills)[:\-]?\s*(.+)", text, re.IGNORECASE)
    if skills_match:
        info["Skills"] = skills_match.group(2)

    return info
