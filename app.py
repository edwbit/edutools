import pandas as pd
import streamlit as st
import os
import re
from openpyxl.styles import Alignment
from io import BytesIO

st.set_page_config(page_title="EduTools", layout="centered")

# === PARSING LOGIC ===
QUESTION_NUM_PREFIX = re.compile(r'^\s*\d+\s*[.)]\s*')
ANSWER_LINE_PATTERN = re.compile(r'^\s*([A-Da-d])[\.\)]\s*(.*)', re.IGNORECASE)
ANSWER_DECL_PATTERN = re.compile(r'^\s*ANSWER\s*:\s*([A-Da-d])', re.IGNORECASE)


def read_quiz_raw_lines(file_content):
    try:
        content = file_content.read().decode('utf-8').splitlines()
        return content
    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
        return None


def split_into_blocks(lines):
    blocks = []
    current_block = []
    for line in lines:
        if line.strip() == "":
            if current_block:
                blocks.append(current_block)
                current_block = []
        else:
            current_block.append(line)
    if current_block:
        blocks.append(current_block)
    return blocks


def parse_question_block(block, block_index):
    if not block:
        return None

    try:
        question_line = block[0].strip()
        question_text = QUESTION_NUM_PREFIX.sub('', question_line).strip()
        if not question_text:
            st.warning(f"⚠️ Block {block_index+1}: Empty question line.")
            return None

        answers = {}
        i = 1
        while i < len(block):
            line = block[i].strip()
            match = ANSWER_LINE_PATTERN.match(line)
            if match:
                letter = match.group(1).upper()
                text = match.group(2).strip()
                if letter in 'ABCD':
                    answers[letter] = text
                i += 1
            else:
                break

        if set(answers.keys()) != {'A', 'B', 'C', 'D'}:
            missing = set('ABCD') - set(answers.keys())
            extra = set(answers.keys()) - set('ABCD')
            msg = f"⚠️ Block {block_index+1}: Answers must be A-D. "
            if missing:
                msg += f"Missing: {sorted(missing)}. "
            if extra:
                msg += f"Extra: {sorted(extra)}."
            st.warning(msg)
            return None

        correct_letter = None
        for j in range(i, len(block)):
            decl_match = ANSWER_DECL_PATTERN.match(block[j])
            if decl_match:
                correct_letter = decl_match.group(1).upper()
                break

        if not correct_letter:
            st.warning(f"⚠️ Block {block_index+1}: Missing 'ANSWER: X' line.")
            return None
        if correct_letter not in 'ABCD':
            st.warning(f"⚠️ Block {block_index+1}: Invalid answer '{correct_letter}'.")
            return None

        correct_index = ord(correct_letter) - ord('A') + 1

        return [
            question_text,
            "multiple choice",
            answers['A'],
            answers['B'],
            answers['C'],
            answers['D'],
            correct_index
        ]

    except Exception as e:
        st.error(f"💥 Block {block_index+1}: Parsing error — {e}")
        return None


# === STREAMLIT UI ===
def main():
    st.markdown(
        "<h1 style='text-align: center;'>🔀 Text to Excel for Quizizz</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align: center; color: #666;'>Upload a quiz → Get a Quizizz-ready Excel file</p>"
        "<p style='text-align: center; color: #666;'>Vibe code: Edwin B. Bitco</p>",
        
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
        """)

    # st.divider()

    uploaded_file = st.file_uploader("📤 Upload your `.txt` quiz file", type=["txt"], label_visibility="collapsed")

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

        df = pd.DataFrame(data, columns=[
            'Question Text', 'Question Type',
            'Option 1', 'Option 2', 'Option 3', 'Option 4',
            'Correct Answer'
        ])

        base_name = os.path.splitext(uploaded_file.name)[0]
        excel_name = f"{base_name}-QUIZIZZ.xlsx"

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
            ws = writer.sheets['Sheet1']
            ws.column_dimensions['A'].width = 70
            ws.column_dimensions['B'].width = 15
            for col in 'CDEF':
                ws.column_dimensions[col].width = 55
            ws.column_dimensions['G'].width = 15
            for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=7):
                for cell in row:
                    cell.alignment = Alignment(wrap_text=True, vertical='top')

        st.success(f"🎉 Successfully converted **{success}** questions!")
        st.download_button(
            label="📥 Download Excel for Quizizz",
            data=output.getvalue(),
            file_name=excel_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True
        )

        with st.expander("🔍 Preview (first 5 questions)"):
            preview = df.head(5).copy()
            preview['Correct Answer'] = preview['Correct Answer'].map({1: 'A', 2: 'B', 3: 'C', 4: 'D'})
            st.dataframe(
                preview[['Question Text', 'Option 1', 'Option 2', 'Correct Answer']],
                use_container_width=True,
                hide_index=True
            )


if __name__ == "__main__":
    main()
