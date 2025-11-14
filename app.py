import pandas as pd
import streamlit as st
import os
import re
from openpyxl.styles import Alignment
from io import BytesIO

st.set_page_config(page_title="EduTools")

# Regex patterns
QUESTION_NUM_PREFIX = re.compile(r'^\s*\d+\s*[.)]\s*')  # e.g., "1. ", "10) ", "5)   "
ANSWER_LINE_PATTERN = re.compile(r'^\s*([A-Da-d])[\.\)]\s*(.*)', re.IGNORECASE)
ANSWER_DECL_PATTERN = re.compile(r'^\s*ANSWER\s*:\s*([A-Da-d])', re.IGNORECASE)


def read_quiz_raw_lines(file_content):
    """Read file as raw lines (preserving blank lines)"""
    try:
        content = file_content.read().decode('utf-8').splitlines()
        return content
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None


def split_into_blocks(lines):
    """Split lines into blocks separated by ≥1 blank line"""
    blocks = []
    current_block = []
    for line in lines:
        if line.strip() == "":
            if current_block:  # end of block
                blocks.append(current_block)
                current_block = []
            # else: skip consecutive blanks
        else:
            current_block.append(line)
    if current_block:
        blocks.append(current_block)
    return blocks


def parse_question_block(block, block_index):
    """
    Parse one question block (list of non-blank lines).
    Returns:
        [question_text, 'multiple choice', A, B, C, D, correct_index (1-4)]
        or None if invalid.
    """
    if not block:
        return None

    try:
        # Step 1: First non-empty line is question (may have number prefix)
        question_line = block[0].strip()
        # Remove optional numbering like "1. " or "10) "
        question_text = QUESTION_NUM_PREFIX.sub('', question_line).strip()
        if not question_text:
            st.warning(f"Block {block_index+1}: Empty or unparseable question line: '{question_line}'")
            return None

        # Step 2: Parse answer lines (A-D)
        answers = {}
        i = 1
        while i < len(block):
            line = block[i].strip()
            # Check for answer line: A. ... or A) ...
            ans_match = ANSWER_LINE_PATTERN.match(line)
            if ans_match:
                letter = ans_match.group(1).upper()
                text = ans_match.group(2).strip()
                if letter in 'ABCD':
                    answers[letter] = text
                else:
                    st.warning(f"Block {block_index+1}: Unexpected answer letter '{letter}' in: '{line}'")
                    return None
                i += 1
            else:
                break  # Done with answers

        # Must have exactly A, B, C, D
        if set(answers.keys()) != {'A', 'B', 'C', 'D'}:
            missing = set('ABCD') - set(answers.keys())
            extra = set(answers.keys()) - set('ABCD')
            msg = f"Block {block_index+1}: Expected A-D answers. "
            if missing:
                msg += f"Missing: {sorted(missing)}. "
            if extra:
                msg += f"Extra: {sorted(extra)}."
            st.warning(msg)
            return None

        # Step 3: Find ANSWER: line in remaining lines
        correct_letter = None
        for j in range(i, len(block)):
            decl_match = ANSWER_DECL_PATTERN.match(block[j])
            if decl_match:
                correct_letter = decl_match.group(1).upper()
                break

        if not correct_letter:
            st.warning(f"Block {block_index+1}: No 'ANSWER: X' line found.")
            return None
        if correct_letter not in 'ABCD':
            st.warning(f"Block {block_index+1}: Invalid answer '{correct_letter}'. Expected A-D.")
            return None

        correct_index = ord(correct_letter) - ord('A') + 1  # A→1, B→2, etc.

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
        st.error(f"Block {block_index+1}: Error parsing: {e}")
        return None


def main():
    st.title("Text to Excel for Quizizz 🔄")
    st.write("Upload a quiz text file and convert it into an Excel file for Quizizz.com.")
    st.write("**Formatting is flexible! Supports:**")
    st.markdown("""
    - Numbered (`1.`) or unnumbered questions  
    - `A.` or `A)` style answers  
    - Blocks separated by blank lines  
    - `ANSWER: A`, `ANSWER:A`, etc.
    """)
    st.code("""\
1. What is DNS?
A. Domain Name System.
B. Dynamic Host...
C. ...
D. ...
ANSWER: A

Why use static IP?
A) So clients can find it.
B) ...
C) ...
D) ...
ANSWER: A\
""", language="text")

    uploaded_file = st.file_uploader("Upload your quiz text file", type=["txt"])
    if uploaded_file is not None:
        lines = read_quiz_raw_lines(uploaded_file)
        if lines is None:
            return

        blocks = split_into_blocks(lines)
        st.info(f"Detected {len(blocks)} question blocks (separated by blank lines).")

        data = []
        success_count = 0
        fail_count = 0

        for idx, block in enumerate(blocks):
            result = parse_question_block(block, idx)
            if result:
                data.append(result)
                success_count += 1
            else:
                fail_count += 1

        st.info(f"✅ Success: {success_count} | ❌ Failed: {fail_count}")

        if not data:
            st.error("No valid questions parsed. Please check formatting.")
            return

        df = pd.DataFrame(data, columns=[
            'Question Text', 'Question Type',
            'Option 1', 'Option 2', 'Option 3', 'Option 4',
            'Correct Answer'
        ])

        # Optional: sort by original block order (already preserved)
        # df = df.sort_index()

        # Generate Excel
        uploaded_filename = uploaded_file.name
        excel_filename = f"{os.path.splitext(uploaded_filename)[0]}-QUIZIZZ.xlsx"

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
            ws = writer.sheets['Sheet1']
            # Set widths
            ws.column_dimensions['A'].width = 70
            ws.column_dimensions['B'].width = 15
            for col in 'CDEFG':
                ws.column_dimensions[col].width = 60 if col in 'CDEF' else 15
            # Wrap text
            for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=7):
                for cell in row:
                    cell.alignment = Alignment(wrap_text=True, vertical='top')

        st.success(f"✅ Successfully parsed {success_count} questions!")
        st.download_button(
            label="📥 Download Excel for Quizizz",
            data=output.getvalue(),
            file_name=excel_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Optional: show preview
        with st.expander("🔍 Preview Parsed Questions"):
            st.dataframe(df[['Question Text', 'Option 1', 'Option 2', 'Correct Answer']].head(10))


if __name__ == "__main__":
    main()
