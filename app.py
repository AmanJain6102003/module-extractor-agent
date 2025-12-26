import os
import time
import json
import streamlit as st
from dotenv import load_dotenv

from module_extractor import extract_from_urls
from utils.io import save_json

load_dotenv()

st.set_page_config(page_title="Pulse Module Extractor")

st.title("Pulse Module Extractor — Demo")

st.write("Paste one or more documentation base URLs (one per line).")
urls_text = st.text_area("Documentation URLs", height=150)

col1, col2, col3 = st.columns(3)
with col1:
    max_pages = st.number_input("Max pages per site", min_value=5, max_value=2000, value=200, step=5)
with col2:
    max_depth = st.number_input("Max crawl depth", min_value=0, max_value=6, value=2, step=1)
with col3:
    max_workers = st.number_input("Parallel workers", min_value=1, max_value=20, value=6, step=1)

run = st.button("Extract Modules")

if run:
    urls = [u.strip() for u in urls_text.splitlines() if u.strip()]
    if not urls:
        st.error("Please provide at least one URL.")
    else:
        progress = st.progress(0)
        status = st.empty()
        status.text("Starting extraction...")
        try:
            result = extract_from_urls(urls, progress_callback=lambda p, msg: (progress.progress(int(p*100)), status.text(msg)), max_pages=int(max_pages), max_depth=int(max_depth), max_workers=int(max_workers))
            st.success("Extraction complete.")
            st.json(result)
            # Save
            now = time.strftime("%Y%m%d_%H%M%S")
            outpath = os.path.join("output", f"modules_{now}.json")
            save_json(result, outpath)
            st.write(f"Saved output to {outpath}")

        # Output viewer
        st.markdown("---")
        st.subheader("Saved outputs")
        out_dir = "output"
        try:
            files = [f for f in os.listdir(out_dir) if f.endswith('.json')]
        except Exception:
            files = []

        files = sorted(files, key=lambda f: os.path.getmtime(os.path.join(out_dir, f)), reverse=True)
        if files:
            choice = st.selectbox("Select saved JSON to view", options=files)
            if choice:
                path = os.path.join(out_dir, choice)
                try:
                    with open(path, 'r', encoding='utf-8') as fh:
                        obj = fh.read()
                    st.code(obj, language='json')
                    st.download_button("Download JSON", data=obj, file_name=choice, mime='application/json')
                except Exception as e:
                    st.error(f"Failed to read file: {e}")
        else:
            st.info("No saved outputs yet. Run an extraction to create one.")
        except Exception as e:
            st.error(f"Extraction failed: {e}")
