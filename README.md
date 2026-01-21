# Description

**AI Resume Matcher is a project designed to pull the technical skills from a job posting and compare them against resumes to show highlights and weak points.

# Setup

```bash
git clone https://github.com/IqbalHussein/ai-resume-matcher.git
cd ai-resume-matcher
python -m venv venv
source venv/bin/activate
# Windows
# venv\Scripts\activate
pip install -r requirements.txt
```

# Usage

## CLI
Run the main script to process files in `data/`:
```bash
python main.py
```

## Web Interface
Run the Streamlit app for an interactive UI:
```bash
streamlit run streamlit_app.py
```
