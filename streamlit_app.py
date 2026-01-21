import streamlit as st
import os
import tempfile
import json
import re
from datetime import datetime
from src.parsing.resume_parser import parse_resume_from_file
from src.parsing.job_parser import parse_jobs_from_file
from src.matching.matcher import match_resume_to_jobs
from src.config.weights import SKILL_WEIGHTS

st.set_page_config(page_title="AI Resume Matcher", layout="wide")

# Custom CSS for Design System
st.markdown("""
    <style>
    /* ----------------------------------------------------
       Design System: Fonts & Layout
       ---------------------------------------------------- */
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
    }

    /* Adjusted Layout Margins */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 1400px;
    }

    /* ----------------------------------------------------
       Design System: Sidebar & Controls
       ---------------------------------------------------- */
    
    /* Darker Sidebar Background */
    section[data-testid="stSidebar"] {
        background-color: #0a0a0a;
        border-right: 1px solid #262626;
    }

    /* ----------------------------------------------------
       Design System: Headers & Icons
       ---------------------------------------------------- */
    
    .main-title {
        text-align: center;
        font-weight: 800;
        font-size: 2.5rem;
        margin-bottom: 8px !important;
        background: linear-gradient(90deg, #4ADE80, #60A5FA);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.03em;
    }
    
    .subtitle {
        text-align: center;
        font-size: 1.1rem;
        color: #A3A3A3;
        font-weight: 400;
        margin-bottom: 48px !important;
    }

    .upload-header {
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 16px;
        color: #F5F5F5;
        border-bottom: 1px solid #333;
        padding-bottom: 8px;
    }
    
    .upload-icon {
        width: 20px;
        height: 20px;
        stroke: #4ADE80;
    }

    /* ----------------------------------------------------
       Design System: Colors (Refined Dark Theme)
       ---------------------------------------------------- */
    
    .stApp {
        background-color: #121212;
        color: #E0E0E0;
    }

    /* Card Component Styling with Equal Height Fix */
    div[data-testid="column"] {
        display: flex;
        flex-direction: column;
    }
    
    div[data-testid="stVerticalBlockBorderWrapper"] {
        flex-grow: 1;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        background-color: #1E1E1E;
        border: 1px solid #333333;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 16px;
        height: 100%;
    }

    .job-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #F5F5F5;
        margin-bottom: 4px;
    }
    .company-name {
        font-size: 0.95rem;
        font-weight: 500;
        color: #A0A0A0;
        margin-bottom: 16px;
    }

    /* ----------------------------------------------------
       Design System: Components (Tags & Badges)
       ---------------------------------------------------- */

    .skill-tag {
        display: inline-block;
        padding: 4px 12px;
        margin: 0 6px 6px 0;
        border-radius: 6px;
        font-size: 0.85em;
        font-weight: 500;
        letter-spacing: 0.01em;
        white-space: nowrap;
        border: 1px solid transparent;
    }
    .skill-matched {
        background-color: #132E25;
        color: #4ADE80;
        border-color: #065F46;
    }
    .skill-missing {
        background-color: #3B1214;
        color: #F87171;
        border-color: #7F1D1D;
    }

    .line-badge {
        display: inline-block;
        background-color: #2D2D2D;
        color: #9CA3AF;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.75em;
        font-family: 'JetBrains Mono', monospace;
        margin-right: 8px;
        border: 1px solid #404040;
    }
    
    b {
        color: #60A5FA;
        font-weight: 600;
    }

    /* Hide MainMenu and Footer ONLY */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

def save_uploaded_file(uploaded_file):
    """Save uploaded file to a temporary file and return the path."""
    try:
        suffix = os.path.splitext(uploaded_file.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            return tmp_file.name
    except Exception as e:
        st.error(f"Error saving file: {e}")
        return None

def render_skill_tags(skills, type="matched"):
    """
    Helper to render tags as HTML with weight prioritization.
    - matched: skill + (icon if high priority)
    - missing: skill + (weight)
    """
    if not skills:
        return "<span style='color:#757575; font-style:italic; font-size:0.9em'>None</span>"
    
    tags_html = []
    
    # Sort skills by weight descending for visual hierarchy
    sorted_skills = sorted(skills, key=lambda s: SKILL_WEIGHTS.get(s, 1.0), reverse=True)

    for skill in sorted_skills:
        weight = SKILL_WEIGHTS.get(skill, 1.0)
        is_high_priority = weight >= 2.5
        
        css_class = "skill-matched" if type == "matched" else "skill-missing"
        
        display_text = skill
        
        if type == "matched":
            if is_high_priority:
                display_text = f"⭐ {skill}"
        else:
            # missing
            display_text = f"{skill} ({weight})"
            if is_high_priority:
                display_text = f"⭐ {skill} ({weight})"
        
        tags_html.append(f"<span class='skill-tag {css_class}'>{display_text}</span>")
        
    return "".join(tags_html)

def highlight_evidence(line, skill_name):
    """
    Parses 'L{num}: {content}' string.
    Returns HTML with badge for line number and bolded skill keyword.
    """
    match = re.match(r"(L\d+):\s*(.*)", line)
    if not match:
        return line 
    
    line_num_str = match.group(1)
    content = match.group(2)
    
    pattern = re.compile(rf"(?<![a-z0-9]){re.escape(skill_name)}(?![a-z0-9])", re.IGNORECASE)
    highlighted_content = pattern.sub(lambda m: f"<b>{m.group(0)}</b>", content)
    
    return f"<span class='line-badge'>{line_num_str}</span>{highlighted_content}"

def display_match_details(match):
    """Helper to display skill breakdown and evidence."""
    st.markdown(f"**✅ Matched Skills**")
    st.markdown(render_skill_tags(match['matched_skills'], "matched"), unsafe_allow_html=True)
    
    st.write("") # Spacer using standard line height

    st.markdown(f"**❌ Missing Skills**")
    st.markdown(render_skill_tags(match['missing_skills'], "missing"), unsafe_allow_html=True)

    st.write("")

    # Evidence Section
    job_evidence_count = len(match['evidence']['job'])
    resume_evidence_count = len(match['evidence']['resume'])
    total_evidence = job_evidence_count + resume_evidence_count
    
    label = f"Show Evidence ({total_evidence} snippets)"
    
    with st.expander(label, expanded=False):
        if match['evidence']['job']:
            st.markdown("#### Found in Job Posting")
            for skill, lines in match['evidence']['job'].items():
                st.markdown(f"**{skill}**")
                for line in lines:
                    st.markdown(highlight_evidence(line, skill), unsafe_allow_html=True)
        
        if match['evidence']['resume']:
            st.markdown("#### Found in Resume")
            for skill, lines in match['evidence']['resume'].items():
                st.markdown(f"**{skill}**")
                for line in lines:
                    st.markdown(highlight_evidence(line, skill), unsafe_allow_html=True)
        
        if total_evidence == 0:
            st.caption("No specific evidence snippets found.")

def main():
    # Header Section
    st.markdown("""
        <div class="main-title">AI Resume Matcher</div>
        <div class="subtitle">Intelligent skill extraction and semantic matching for modern recruitment</div>
    """, unsafe_allow_html=True)
    
    # Sidebar Filters
    st.sidebar.header("Configuration")
    min_score = st.sidebar.slider("Minimum Score", 0.0, 1.0, 0.0, 0.01)
    sort_by = st.sidebar.radio("Sort By", ["Weighted Score", "Semantic Similarity"])

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="upload-header">
            <svg class="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
            1. Upload Resume
        </div>
        """, unsafe_allow_html=True)
        resume_file = st.file_uploader("Choose a resume file", type=['txt', 'pdf'], label_visibility="collapsed")

    with col2:
        st.markdown("""
        <div class="upload-header">
            <svg class="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>
            2. Upload Job Postings
        </div>
        """, unsafe_allow_html=True)
        jobs_file = st.file_uploader("Choose a job postings file (.txt)", type=['txt'], label_visibility="collapsed")

    if resume_file and jobs_file:
        upload_id = f"{resume_file.name}_{jobs_file.name}_{resume_file.size}_{jobs_file.size}"
        
        if "upload_id" not in st.session_state or st.session_state.upload_id != upload_id:
            st.session_state.upload_id = upload_id
            st.session_state.processed_matches = None
            st.session_state.resume_data = None
            st.session_state.jobs_len = 0

        if st.session_state.processed_matches is None:
            resume_path = save_uploaded_file(resume_file)
            jobs_path = save_uploaded_file(jobs_file)

            if resume_path and jobs_path:
                try:
                    progress_bar = st.progress(0, text="Starting...")
                    
                    resume_data = parse_resume_from_file(resume_path)
                    progress_bar.progress(10, text="Parsing Resume...")
                    
                    jobs_data = parse_jobs_from_file(jobs_path)
                    progress_bar.progress(20, text="Parsing Job Postings...")
                    
                    def update_progress(p):
                        current = 30 + int(p * 70)
                        progress_bar.progress(current, text=f"Matching Job {int(p * len(jobs_data))}/{len(jobs_data)}")

                    matches = match_resume_to_jobs(
                        jobs_data, 
                        resume_data["skills_all"], 
                        resume_data=resume_data,
                        progress_callback=update_progress
                    )
                    
                    progress_bar.progress(100, text="Complete!")
                    
                    st.session_state.processed_matches = matches
                    st.session_state.resume_data = resume_data
                    st.session_state.jobs_len = len(jobs_data)

                except Exception as e:
                    st.error(f"An error occurred during processing: {e}")
                finally:
                    if os.path.exists(resume_path): os.remove(resume_path)
                    if os.path.exists(jobs_path): os.remove(jobs_path)

        matches = st.session_state.processed_matches
        resume_data = st.session_state.resume_data
        
        if matches:
            filtered_matches = [m for m in matches if m['score'] >= min_score]
            
            if sort_by == "Semantic Similarity":
                filtered_matches.sort(key=lambda x: x['semantic_score'], reverse=True)
            else:
                filtered_matches.sort(key=lambda x: x['score'], reverse=True)

            st.success(f"Processed {st.session_state.jobs_len} job postings successfully! Showing {len(filtered_matches)} matches.")
            
            match_report = {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "resume": {
                    "skills_used": resume_data["skills_all"] if resume_data else []
                },
                "results": []
            }
            for rank, r in enumerate(matches, start=1):
                match_report["results"].append({
                    "rank": rank,
                    "title": r["title"],
                    "company": r["company"],
                    "score": round(r["score"], 3),
                    "semantic_score": r.get("semantic_score", 0),
                    "matched_skills": r["matched_skills"],
                    "missing_skills": r["missing_skills"]
                })
            
            report_json = json.dumps(match_report, indent=2, ensure_ascii=False)
            st.download_button(
                label="Download Match Report (JSON)",
                data=report_json,
                file_name="match_report.json",
                mime="application/json"
            )

            st.divider()
            st.header("Match Results")

            if not filtered_matches:
                st.warning("No jobs match the current filter criteria.")
            else:
                top_matches = filtered_matches[:3]
                other_matches = filtered_matches[3:]

                if top_matches:
                    st.subheader("🏆 Top Recommendations")
                    num_cols = min(len(top_matches), 3)
                    cols = st.columns(num_cols)
                    
                    for i, match in enumerate(top_matches):
                        col_idx = i % num_cols
                        with cols[col_idx]:
                            with st.container(border=True):
                                # Typography classes applied here
                                st.markdown(f"<div class='job-title'>#{i+1} {match['title']}</div>", unsafe_allow_html=True)
                                st.markdown(f"<div class='company-name'>{match['company']}</div>", unsafe_allow_html=True)
                                
                                st.metric(
                                    "Total Score", 
                                    f"{match['score']:.2f}", 
                                    delta=f"Semantic: {match['semantic_score']:.2f}"
                                )
                                
                                st.divider()
                                display_match_details(match)

                if other_matches:
                    st.subheader("Other Matches")
                    for rank_offset, match in enumerate(other_matches, 1):
                        rank = len(top_matches) + rank_offset
                        with st.expander(f"#{rank} {match['title']} at {match['company']} (Score: {match['score']:.2f})"):
                            m_col1, m_col2, m_col3 = st.columns(3)
                            m_col1.metric("Total Score", f"{match['score']:.2f}")
                            m_col2.metric("Semantic Similarity", f"{match['semantic_score']:.2f}")
                            m_col3.metric("Weighted Skills", f"{match['matched_weight']}/{match['total_weight']}")
                            
                            st.divider()
                            display_match_details(match)

if __name__ == "__main__":
    main()
