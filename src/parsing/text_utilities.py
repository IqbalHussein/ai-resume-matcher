from pathlib import Path
import re
import pypdf

def read_text_file(path: str) -> str:
    """
    Read and return the contents of a text file with UTF-8 encoding.
    
    Args:
        path: File path (relative or absolute) to read
        
    Returns:
        Complete file contents as a string
        
    Raises:
        FileNotFoundError: If the specified file does not exist
    """

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p.resolve()}")
    return p.read_text(encoding="utf-8")

def read_pdf_file(path: str) -> str:
    """
    Read and extract text from a PDF file using pypdf.
    
    Args:
        path: File path (relative or absolute) to read
        
    Returns:
        Extracted text content from all pages joined by newlines
        
    Raises:
        FileNotFoundError: If the specified file does not exist
        ValueError: If the file is encrypted or cannot be read
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p.resolve()}")
        
    text_content = []
    try:
        reader = pypdf.PdfReader(str(p))
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_content.append(text)
    except Exception as e:
        raise ValueError(f"Error reading PDF file: {e}")
        
    return "\n".join(text_content)

def normalize_text(text: str) -> str:
    """
    Normalize text by standardizing whitespace and removing formatting artifacts.
    
    Performs the following transformations:
    1. Standardizes all line endings to \n (handles \r\n and \r)
    2. Removes HTML entities like &nbsp;
    3. Converts tabs to spaces
    4. Strips leading/trailing whitespace from each line
    5. Collapses multiple consecutive spaces into single spaces
    6. Removes excessive blank lines (max 1 consecutive blank line)
    
    Args:
        text: Raw text to normalize
        
    Returns:
        Cleaned and normalized text with consistent formatting
    """

    # Standardize line endings
    t = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove common leftovers
    t = t.replace("&nbsp;", " ")

    # Convert tabs to spaces
    t = t.replace("\t", " ")

    # Strip each line and collapse internal whitespace
    lines = []
    for line in t.split("\n"):
        line = line.strip()
        line = re.sub(r"\s+", " ", line)
        lines.append(line)

    # Remove leading/trailing empty lines and collapse multiple blank lines
    cleaned_lines = []
    blank_run = 0
    for line in lines:
        if line == "":
            blank_run += 1
            if blank_run <= 1:
                cleaned_lines.append("")
        else:
            blank_run = 0
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()