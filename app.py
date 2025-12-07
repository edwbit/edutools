import streamlit as st
import pandas as pd
import os
from parsing.wayground_question_parser import read_quiz_raw_lines, split_into_blocks, parse_question_block
from excel.wayground_excel_generator import generate_quizizz_excel, create_preview_dataframe

st.set_page_config(page_title="EduTools", layout="centered")

def main():
    # Add sidebar menu
    with st.sidebar:
        st.markdown("## 🛠️ Tools")
        if st.button("🔀 Excel file for Wayground"):
            st.sidebar.success("✅ Wayground Excel file generator ready!")
            st.sidebar.info("Upload your quiz file to get started")

    st.markdown(
        "<h1 style='text-align: center;'>🔀 Excel file for Wayground</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align: center; color: #666;'>Upload a quiz → Get a Wayground-ready Excel file</p>"
        "<p style='text-align: center; color: #666;'>Maintained by: <a href='https://www.facebook.com/657572656b6121/' target='_blank'>Edwin B. Bitco</a></p>",

        unsafe_allow_html=True
    )
    # st.divider()

    with st.expander("📘 Formatting Guide (click to expand)", expanded=False):
        st.markdown("""
        📝 Sample Question Format:
        ```
        What is DNS?
        A. Domain Name System
        B. Dynamic Host Configuration Protocol
        C. Data Naming Services
        D. Digital Network Security
        ANSWER: A
        ```

        ✅ **Supported File Formats**: `.txt` and `.docx`
        """)

    # st.divider()

    uploaded_file = st.file_uploader("📤 Upload your quiz file", type=["txt", "docx"], label_visibility="collapsed")

    if uploaded_file is not None:
        lines = read_quiz_raw_lines(uploaded_file)
        if lines is None:
            return

        blocks = split_into_blocks(lines)
        st.info(f"📄 Found **{len(blocks)}** question blocks.")

        data = []
        success, failed = 0, 0

        for idx, block in enumerate(blocks):
            parsed = parse_question_block(block, idx)
            if parsed:
                data.append(parsed)
                success += 1
            else:
                failed += 1

        st.divider()
        col1, col2, col3 = st.columns(3)
        col1.metric("✅ Success", success)
        col2.metric("❌ Failed", failed)
        col3.metric("📊 Total", success + failed)

        if not data:
            st.error("❌ No valid questions parsed. Check formatting or see guide above.")
            return

        base_name = os.path.splitext(uploaded_file.name)[0]
        excel_name, output = generate_quizizz_excel(data, base_name)

        st.success(f"🎉 Successfully converted **{success}** questions to Wayground format!")
        st.download_button(
            label="📥 Download Excel for Quizizz",
            data=output.getvalue(),
            file_name=excel_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            width='stretch'
        )

        with st.expander("🔍 Preview (all questions)"):
            # Create a temporary dataframe for preview
            temp_df = pd.DataFrame(data, columns=[
                'Question Text', 'Question Type',
                'Option 1', 'Option 2', 'Option 3', 'Option 4',
                'Correct Answer'
            ])
            preview_df = create_preview_dataframe(temp_df)
            st.dataframe(
                preview_df[['Question Text', 'Option 1', 'Option 2', 'Correct Answer']],
                width='stretch',
                hide_index=True
            )

# Support both direct execution and Streamlit Cloud
if __name__ == "__main__":
    main()
else:
    # For Streamlit Cloud compatibility
    main()
