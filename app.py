"""
Friday Video Studio: a web app that turns any topic into a narrated,
researched explainer video.

Run:
    pip install -r requirements.txt
    streamlit run app.py
"""

import os

import streamlit as st

from friday_video import make_video

st.set_page_config(page_title="Friday Video Studio", page_icon="🎬", layout="centered")

st.title("🎬 Friday Video Studio")
st.caption("Type a topic. Friday researches it on the web and makes a narrated explainer video.")

# --- API key ---
with st.sidebar:
    st.header("Settings")
    if os.environ.get("ANTHROPIC_API_KEY"):
        st.success("API key found")
    else:
        key = st.text_input("Anthropic API key", type="password", help="Get one at console.anthropic.com")
        if key:
            os.environ["ANTHROPIC_API_KEY"] = key
    st.markdown("Needs **ffmpeg** installed on this computer.")

# --- Input ---
topic = st.text_input("Video topic", placeholder="How black holes work")
examples = ["How black holes work", "How vaccines train the immune system", "How last-mile delivery works"]
cols = st.columns(len(examples))
for col, ex in zip(cols, examples):
    if col.button(ex, use_container_width=True):
        topic = ex
        st.session_state["auto_run"] = True

go = st.button("Create video", type="primary", disabled=not topic) or st.session_state.pop("auto_run", False)

# --- Generate ---
if go and topic:
    bar = st.progress(0.0)
    status = st.empty()

    def progress(msg, frac):
        status.info(msg)
        bar.progress(min(frac, 1.0))

    try:
        final, script = make_video(topic, progress)
        st.session_state["result"] = {
            "video": final.read_bytes(),
            "script": script,
            "name": final.parent.name,
        }
        status.success("Your video is ready.")
    except RuntimeError as err:
        status.error(str(err))
    except Exception as err:  # network, API, or gTTS problems
        status.error(f"Something went wrong: {err}")

# --- Result (kept in session so downloading doesn't reset the page) ---
result = st.session_state.get("result")
if result:
    script = result["script"]
    st.subheader(script.get("title", "Your video"))
    st.video(result["video"])
    st.download_button("Download MP4", result["video"], file_name=f"{result['name']}.mp4", mime="video/mp4")

    with st.expander("Scenes and narration"):
        for i, scene in enumerate(script["scenes"], 1):
            st.markdown(f"**{i}. {scene['heading']}**")
            st.write(scene["narration"])

    if script.get("sources"):
        with st.expander("Sources"):
            for src in script["sources"]:
                st.markdown(f"- [{src.get('title') or src.get('url')}]({src.get('url', '')})")
