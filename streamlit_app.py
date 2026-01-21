import streamlit as st
import os
import tempfile
import shutil
from src.parsing.resume_parser import parse_resume_from_file
from src.parsing.job_parser import parse_jobs_from_file
from src.matching.matcher import match_resume_to_jobs

st.set_page_config(page_title="AI Resume Matcher", layout="wide")

# Custom CSS to reduce top padding and adjust margins
st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 1rem;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
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

def display_match_details(match):
    """Helper to display skill breakdown and evidence."""
    # Skills Visualization
    # Green for matched, Red for missing
    if match['matched_skills']:
        st.markdown(f"**✅ Matched Skills:**")
        st.markdown(", ".join([f"`{s}`" for s in match['matched_skills']]))
    else:
        st.markdown("**✅ Matched Skills:** None")

    if match['missing_skills']:
        st.markdown(f"**❌ Missing Skills:**")
        st.markdown(", ".join([f"`{s}`" for s in match['missing_skills']]))
    else:
        st.markdown("**❌ Missing Skills:** None")

    # Evidence Section in an inner expander to save space
    # Count snippets to show in label
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
                    st.text(line)
        
        if match['evidence']['resume']:
            st.markdown("#### Found in Resume")
            for skill, lines in match['evidence']['resume'].items():
                st.markdown(f"**{skill}**")
                for line in lines:
                    st.text(line)
        
        if total_evidence == 0:
            st.caption("No specific evidence snippets found.")

def main():
    st.title("AI Resume Matcher")
    st.markdown("""
    Upload your resume and a list of job postings to see how well you match!
    This tool extracts skills, performs semantic matching, and provides evidence for matches.
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("1. Upload Resume")
        resume_file = st.file_uploader("Choose a resume file", type=['txt', 'pdf'])

    with col2:
        st.subheader("2. Upload Job Postings")
        jobs_file = st.file_uploader("Choose a job postings file (.txt)", type=['txt'])

    if resume_file and jobs_file:
        with st.spinner('Parsing and Matching...'):
            # Save files temporarily
            resume_path = save_uploaded_file(resume_file)
            jobs_path = save_uploaded_file(jobs_file)

            if resume_path and jobs_path:
                try:
                    # Parse
                    resume_data = parse_resume_from_file(resume_path)
                    jobs_data = parse_jobs_from_file(jobs_path)
                    
                    # Match
                    matches = match_resume_to_jobs(
                        jobs_data, 
                        resume_data["skills_all"], 
                        resume_data=resume_data
                    )
                    
                    st.success(f"Processed {len(jobs_data)} job postings successfully!")
                    
                    st.divider()
                    st.header("Match Results")

                    # Separate Top 3 matches
                    top_matches = matches[:3]
                    other_matches = matches[3:]

                    if top_matches:
                        st.subheader("🏆 Top Recommendations")
                        # Create columns for top matches (up to 3)
                        cols = st.columns(len(top_matches))
                        
                        for i, match in enumerate(top_matches):
                            with cols[i]:
                                with st.container(border=True):
                                    st.markdown(f"### #{i+1} {match['title']}")
                                    st.caption(f"at {match['company']}")
                                    
                                    # Metrics
                                    st.metric(
                                        "Total Score", 
                                        f"{match['score']:.2f}", 
                                        delta=f"Semantic: {match['semantic_score']:.2f}"
                                    )
                                    
                                    st.divider()
                                    display_match_details(match)

                    # List the rest
                    if other_matches:
                        st.subheader("Other Matches")
                        for rank_offset, match in enumerate(other_matches, 1):
                            rank = len(top_matches) + rank_offset
                            with st.expander(f"#{rank} {match['title']} at {match['company']} (Score: {match['score']:.2f})"):
                                # Metrics Row
                                m_col1, m_col2, m_col3 = st.columns(3)
                                m_col1.metric("Total Score", f"{match['score']:.2f}")
                                m_col2.metric("Semantic Similarity", f"{match['semantic_score']:.2f}")
                                m_col3.metric("Weighted Skills", f"{match['matched_weight']}/{match['total_weight']}")
                                
                                st.divider()
                                display_match_details(match)

                except Exception as e:
                    st.error(f"An error occurred during processing: {e}")
                finally:
                    # Cleanup temp files
                    if os.path.exists(resume_path):
                        os.remove(resume_path)
                    if os.path.exists(jobs_path):
                        os.remove(jobs_path)

if __name__ == "__main__":
    main()
