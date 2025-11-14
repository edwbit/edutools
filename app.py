import pandas as pd
import streamlit as st
import os
import re
from openpyxl.styles import Alignment
from io import BytesIO

# Page config
st.set_page_config(page_title="EduTools", layout="centered")

# === PARSING LOGIC ===
QUESTION_NUM_PREFIX = re.compile(r'^\s*\d+\s*[.)]\s*')
ANSWER_LINE_PATTERN = re.compile(r'^\s*([A-Da-d])[\.\)]\s*(.*)', re.IGNORECASE)
ANSWER_DECL_PATTERN = re.compile(r'^\s*ANSWER\s*:\s*([A-Da-d])', re.IGNORECASE)


def read_quiz_raw_lines(file_content):
    """Read file as raw lines (preserving blank lines)"""
    try:
        content = file_content.read().decode('utf-8').splitlines()
        return content
    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
        return None


def split_into_blocks(lines):
    """Split lines into blocks separated by ≥1 blank line"""
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
    """
    Parse one question block.
    Returns: [question, type, A, B, C, D, correct_index (1-4)] or None
    """
    if not block:
        return None

    try:
        # Question line (strip optional numbering)
        question_line = block[0].strip()
        question_text = QUESTION_NUM_PREFIX.sub('', question_line).strip()
        if not question_text:
            st.warning(f"⚠️ Block {block_index+1}: Empty question line.")
            return None

        # Parse answers A-D
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
            missing = set('ABCD') - answers.keys()
            extra = answers.keys() - set('ABCD')
            msg = f"⚠️ Block {block_index+1}: Answers must be A-D. "
            if missing:
                msg += f"Missing: {sorted(missing)}. "
            if extra:
                msg += f"Extra: {sorted(extra)}."
            st.warning(msg)
            return None

        # Find ANSWER: line
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
    # Modern title
    st.markdown(
        "<h1 style='text-align: center;'>🔀 Text to Excel for Quizizz</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align: center; color: #666;'>Upload a quiz → Get a Quizizz-ready Excel file</p>",
        unsafe_allow_html=True
    )
    st.divider()

    # Collapsible instructions
    with st.expander("📘 Formatting Guide (click to expand)", expanded=False):
        st.markdown("""
        ✅ Supports **all** of these styles:
        - `1. Question?` or just `Question?`
        - `A. Answer` or `A) Answer`
        - Blocks separated by **blank lines**
        - `ANSWER: A`, `ANSWER:A`, case-insensitive

        📝 Example:
        ```
        What is DNS?
        A. Domain Name System.
        B. Dynamic Host...
        C. Windows Update...
        D. Server Manager...
        ANSWER: A
        ```

        💡 Tip: Blank lines between questions help the parser group them correctly.
        """)
    
    st.divider()

    # File uploader
    uploaded_file = st.file_uploader(
        "📤 Upload your `.txt` quiz file",
        type=["txt"],
        label_visibility="collapsed"
    )

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

        if not 
            st.error("❌ No valid questions parsed. Check formatting or see guide above.")
            return

        # Create DataFrame
        df = pd.DataFrame(data, columns=[
            'Question Text', 'Question Type',
            'Option 1', 'Option 2', 'Option 3', 'Option 4',
            'Correct Answer'
        ])

        # Excel export
        base_name = os.path.splitext(uploaded_file.name)[0]
        excel_name = f"{base_name}-QUIZIZZ.xlsx"

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
            ws = writer.sheets['Sheet1']
            # Column widths
            ws.column_dimensions['A'].width = 70  # Question
            ws.column_dimensions['B'].width = 15  # Type
            for col in 'CDEF': ws.column_dimensions[col].width = 55
            ws.column_dimensions['G'].width = 15  # Correct Answer
            # Wrap text
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

        # Preview
        with st.expander("🔍 Preview (first 5 questions)"):
            preview = df.head(5).copy()
            preview['Correct Answer'] = preview['Correct Answer'].map({1:'A', 2:'B', 3:'C', 4:'D'})
            st.dataframe(
                preview[['Question Text', 'Option 1', 'Option 2', 'Correct Answer']],
                use_container_width=True,
                hide_index=True
            )


# Run app
if __name__ == "__main__":
    main()
