import streamlit as st
import pandas as pd
import os
from parsing.wayground_question_parser import read_quiz_raw_lines, split_into_blocks, parse_question_block
from excel.wayground_excel_generator import generate_quizizz_excel, create_preview_dataframe
from excel.gform_excel_generator import generate_gform_excel, create_gform_preview_dataframe

st.set_page_config(page_title="EduTools", layout="centered")

def main():
    # Add CSS styling for Streamlit Cloud
    st.markdown("""
    <style>
        /* Gradient Header Card */
        .gradient-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
            text-align: center;
            margin-bottom: 20px;
            font-weight: bold;
        }

        /* Info Card Style */
        .info-card {
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            padding: 20px;
            margin: 15px 0;
            border-left: 4px solid #4CAF50;
        }

        /* Success Card Style */
        .success-card {
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            padding: 20px;
            margin: 15px 0;
            border-left: 4px solid #2196F3;
        }

        /* Sidebar Card Style */
        .sidebar-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
    </style>
    """, unsafe_allow_html=True)

    # Add sidebar menu with card styling
    with st.sidebar:
        st.markdown('''
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
            margin-bottom: 15px;
            font-size: 1.3em;
            font-weight: bold;
            text-align: center;
        ">
            🛠️ Tools
        </div>
        ''', unsafe_allow_html=True)
        # Track which tool is selected
        selected_tool = st.sidebar.radio(
            "Select Tool:",
            ["Excel file for Wayground", "Excel for G-Form"],
            label_visibility="collapsed"
        )

        # Show appropriate content based on selection
        if selected_tool == "Excel file for Wayground":
            st.sidebar.success("✅ Wayground tool selected")
        else:
            st.sidebar.success("✅ G-Form tool selected")

    # Dynamic main heading with gradient card style
    if selected_tool == "Excel file for Wayground":
        main_heading = "🔀 Excel file for Wayground"
        icon = "🔀"
    else:
        main_heading = "📋 Excel for G-Form"
        icon = "📋"

    st.markdown(f"""
    <div class="gradient-header">
        <h1 style="margin: 0; font-size: 2.5em;">{main_heading}</h1>
        <p style="margin: 5px 0 0 0; font-size: 1.1em; opacity: 0.95;">
            Convert quiz questions to Excel format
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(
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
            st.markdown('<div class="info-card" style="color: #d32f2f; background: #ffebee; padding: 15px; border-radius: 8px;">❌ No valid questions parsed. Check formatting or see guide above.</div>', unsafe_allow_html=True)
            return

        base_name = os.path.splitext(uploaded_file.name)[0]

        # Use appropriate generator based on selected tool
        if selected_tool == "Excel file for Wayground":
            excel_name, output = generate_quizizz_excel(data, base_name)
        else:  # G-Form
            excel_name, output = generate_gform_excel(data, base_name)

        # Show appropriate success message based on tool
        if selected_tool == "Excel file for Wayground":
            st.success(f"🎉 Successfully converted **{success}** questions to Wayground format!")
        else:
            st.success(f"🎉 Successfully converted **{success}** questions to G-Form format!")

        # Show appropriate download button label
        if selected_tool == "Excel file for Wayground":
            download_label = "📥 Download Excel for Wayground"
        else:
            download_label = "📥 Download Excel for G-Form"

        st.download_button(
            label=download_label,
            data=output.getvalue(),
            file_name=excel_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            width='stretch'
        )

        with st.expander("🔍 Preview (all questions)"):
            # Create appropriate preview based on selected tool
            if selected_tool == "Excel file for Wayground":
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
            else:  # G-Form preview
                # For G-Form, we need to process the data first since it has different structure
                processed_data = []
                for question in data:
                    answer_choices = [question[2], question[3], question[4], question[5]]
                    correct_answer_text = answer_choices[question[6] - 1]

                    processed_data.append({
                        'Question': question[0],
                        'Type': question[1],
                        'Choice A': question[2],
                        'Choice B': question[3],
                        'Choice C': question[4],
                        'Choice D': question[5],
                        'Answer': correct_answer_text,
                        'Points': 1
                    })

                temp_df = pd.DataFrame(processed_data)
                preview_df = create_gform_preview_dataframe(temp_df)
                st.dataframe(
                    preview_df[['Question', 'Choice A', 'Choice B', 'Answer', 'Points']],
                    width='stretch',
                    hide_index=True
                )

# Support both direct execution and Streamlit Cloud
if __name__ == "__main__":
    main()
else:
    # For Streamlit Cloud compatibility
    main()
