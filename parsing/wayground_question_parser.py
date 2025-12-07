import re
import streamlit as st
import zipfile
import xml.etree.ElementTree as ET
from io import BytesIO

# Regex patterns for parsing
QUESTION_NUM_PREFIX = re.compile(r'^\s*\d+\s*[.)]\s*')
ANSWER_LINE_PATTERN = re.compile(r'^\s*([A-Da-d])[\.\)]\s*(.*)', re.IGNORECASE)
ANSWER_DECL_PATTERN = re.compile(r'^\s*ANSWER\s*:\s*([A-Da-d])', re.IGNORECASE)

def read_quiz_raw_lines(file_content):
    """
    Read the uploaded file content and return lines as a list.
    Supports both TXT and DOCX file formats.

    Args:
        file_content: Uploaded file object from Streamlit

    Returns:
        list: List of lines from the file, or None if error occurs
    """
    try:
        # Check file extension to determine format
        file_name = file_content.name.lower()

        if file_name.endswith('.docx'):
            return read_docx_file(file_content)
        else:
            # Assume text file
            content = file_content.read().decode('utf-8').splitlines()
            return content
    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
        return None

def read_docx_file(file_content):
    """
    Extract text content from a DOCX file.

    Args:
        file_content: Uploaded DOCX file object

    Returns:
        list: List of lines from the DOCX file
    """
    try:
        # Read the DOCX file (which is a ZIP archive)
        docx_data = file_content.read()

        # Extract text from the DOCX
        with zipfile.ZipFile(BytesIO(docx_data)) as zip_file:
            # Find the main document XML
            with zip_file.open('word/document.xml') as doc_file:
                tree = ET.parse(doc_file)
                root = tree.getroot()

                # Extract text from paragraphs
                lines = []
                for paragraph in root.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
                    text = ''.join(paragraph.itertext()).strip()
                    if text:  # Only add non-empty lines
                        lines.append(text)

                return lines

    except Exception as e:
        st.error(f"❌ Error reading DOCX file: {e}")
        return None

def split_into_blocks(lines):
    """
    Split lines into question blocks separated by empty lines.

    Args:
        lines: List of strings representing lines from the file

    Returns:
        list: List of blocks, where each block is a list of lines
    """
    blocks = []
    current_block = []

    for line in lines:
        stripped_line = line.strip()

        if stripped_line:  # Non-empty line
            # Check if this is a new question starting (and we have content in current block)
            if (current_block and
                not stripped_line[0] in 'ABCDabc' and
                not stripped_line.lower().startswith('answer:') and
                has_answer_declaration(current_block)):
                # This looks like a new question starting, and current block is complete
                blocks.append(current_block)
                current_block = []

            current_block.append(line)

        else:  # Empty line - potential block separator
            if current_block and has_answer_declaration(current_block):
                blocks.append(current_block)
                current_block = []

    # Add the last block if it has content
    if current_block:
        blocks.append(current_block)

    return blocks

def has_answer_declaration(block):
    """Check if a block contains an ANSWER declaration"""
    return any(line.strip().lower().startswith('answer:') for line in block)

def parse_question_block(block, block_index):
    """
    Parse a single question block into structured data.

    Args:
        block: List of lines representing one question block
        block_index: Index of the block for error reporting

    Returns:
        list: Parsed question data in format [question_text, question_type,
              option_A, option_B, option_C, option_D, correct_answer_index]
              or None if parsing fails
    """
    if not block:
        return None

    try:
        # Collect all question lines (until we hit the first answer)
        question_lines = []
        i = 0
        while i < len(block):
            line = block[i].strip()
            # Stop if we hit an answer or ANSWER declaration
            if ANSWER_LINE_PATTERN.match(line) or ANSWER_DECL_PATTERN.match(line):
                break
            # Stop if line is empty and we already have question content
            if line == "" and question_lines:
                break
            # Add to question if it's not empty
            if line:
                question_lines.append(line)
            i += 1

        if not question_lines:
            st.warning(f"⚠️ Block {block_index+1}: Empty question line.")
            return None

        # Combine question lines and remove question numbers
        question_text = ' '.join(question_lines)
        question_text = QUESTION_NUM_PREFIX.sub('', question_text).strip()

        answers = {}
        # Start from where we left off after collecting question lines
        current_answer_letter = None
        current_answer_text = ""

        while i < len(block):
            line = block[i].strip()
            # Skip empty lines between answers
            if line == "":
                i += 1
                continue

            # Check if this line starts a new answer (A-D followed by . or ))
            answer_match = ANSWER_LINE_PATTERN.match(line)
            if answer_match:
                # Save previous answer if we were collecting one
                if current_answer_letter and current_answer_text:
                    answers[current_answer_letter] = current_answer_text.strip()

                # Start new answer
                current_answer_letter = answer_match.group(1).upper()
                current_answer_text = answer_match.group(2).strip()
                i += 1
            # Check if this line continues the current answer (Word line-break)
            elif current_answer_letter and line and not line[0] in 'ABCDabc' and not line.lower().startswith('answer:'):
                # This is a continuation of the current answer
                current_answer_text += " " + line
                i += 1
            else:
                # This doesn't look like an answer line
                break

        # Save the last answer if we were collecting one
        if current_answer_letter and current_answer_text:
            answers[current_answer_letter] = current_answer_text.strip()

        if set(answers.keys()) != {'A', 'B', 'C', 'D'}:
            missing = set('ABCD') - set(answers.keys())
            extra = set(answers.keys()) - set('ABCD')
            msg = f"⚠️ Block {block_index+1}: Answers must be A-D. "
            if missing:
                msg += f"Missing: {sorted(missing)}. "
            if extra:
                msg += f"Extra: {sorted(extra)}."
            msg += f"\n📝 Question: '{question_text[:50]}...'"  # Show first 50 chars of question
            st.warning(msg)
            return None

        correct_letter = None
        for j in range(i, len(block)):
            decl_match = ANSWER_DECL_PATTERN.match(block[j])
            if decl_match:
                correct_letter = decl_match.group(1).upper()
                break

        if not correct_letter:
            msg = f"⚠️ Block {block_index+1}: Missing 'ANSWER: X' line."
            msg += f"\n📝 Question: '{question_text[:50]}...'"  # Show first 50 chars of question
            st.warning(msg)
            return None
        if correct_letter not in 'ABCD':
            msg = f"⚠️ Block {block_index+1}: Invalid answer '{correct_letter}'."
            msg += f"\n📝 Question: '{question_text[:50]}...'"  # Show first 50 chars of question
            st.warning(msg)
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
        try:
            # Try to extract question text even if parsing failed
            question_line = block[0].strip() if block else "Unknown"
            question_text = QUESTION_NUM_PREFIX.sub('', question_line).strip()
            error_msg = f"💥 Block {block_index+1}: Parsing error — {e}"
            if question_text:
                error_msg += f"\n📝 Question: '{question_text[:50]}...'"
            st.error(error_msg)
        except:
            st.error(f"💥 Block {block_index+1}: Parsing error — {e}")
        return None