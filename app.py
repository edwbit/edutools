import pandas as pd  # Import pandas library for data manipulation
import streamlit as st  # Import streamlit for creating the web app
from openpyxl.styles import Alignment  # Import Alignment from openpyxl for cell formatting
from io import BytesIO  # Import BytesIO for handling in-memory binary streams

# Function to read and process the quiz file
def read_quiz(file_content):
    try:
        content = file_content.read().decode('utf-8').split('\n')  # Read the file content
        print("File content read successfully:")
        for i, line in enumerate(content):
            print(f"{i}: {line.strip()}")  # Print each line with its index
        return content
    except Exception as e:
        st.error(f"An error occurred while reading the file: {e}")
        return None

# Function to format a single question
def format_question(lines, index):
    try:
        question = []
        answers = []
        correct_answer = None
        correct_index = -1
        
        # Extract the question text
        question_text = lines[index].strip()
        print(f"Processing line {index}: {question_text}")  # Debugging statement
        
        # Remove the leading number and period (e.g., "1. ", "50. ", "100. ")
        if question_text[0].isdigit():
            # Find the position of the first period
            period_index = question_text.find('.')
            if period_index != -1:
                question_text = question_text[period_index + 1:].strip()  # Strip everything before and including the period
        
        if not question_text:
            st.warning(f"Warning: Empty question found at index {index}.")
            return None
        
        question.append(question_text)
        question.append("multiple choice")
        
        # Extract answers and correct answer
        for i in range(index + 1, len(lines)):
            line = lines[i].strip()
            print(f"Processing line {i}: {line}")  # Debugging statement
            
            if line.startswith(('A)', 'B)', 'C)', 'D)')):
                answers.append(line[3:].strip())
            elif line.startswith('ANSWER:'):
                correct_answer = line.split(':')[1].strip()
                break
            elif line:  # If the line is not empty and doesn't start with an answer or correct answer
                st.warning(f"Unexpected line found at index {i}: {line}")
                return None
            else:
                continue  # Skip blank lines
        
        # Validate answers
        if len(answers) != 4:
            st.warning(f"Warning: Question at index {index} does not have exactly 4 answers.")
            return None
        
        # Determine the correct answer index
        if correct_answer:
            correct_index = ord(correct_answer) - ord('A') + 1
            if correct_index < 1 or correct_index > 4:
                st.warning(f"Warning: Invalid correct answer '{correct_answer}' for question at index {index}.")
                return None
        else:
            st.warning(f"Warning: No correct answer found for question at index {index}.")
            return None
        
        return question + answers + [correct_index]
    
    except Exception as e:
        st.error(f"An error occurred while formatting the question at index {index}: {e}")
        return None

# Main function for the Streamlit app
def main():
    st.title("Text to Excel for Quizizz 🔄")
    st.write("Upload a quiz text file and convert it into an Excel file that can be imported on Quizizz.com.")
    st.write("**Below is a sample of formatted question. Make sure to have blank line between questions and choices are uppercase as well as the answer.**")
    st.code("""
What can a robot do that helps you clean your room?
A) Cook dinner
B) Vacuum the floor
C) Wash dishes
D) Do homework
ANSWER: B

Which of the following is an example of a smart device that uses AI?
A) A toy car
B) A teddy bear
C) A smart speaker (like Alexa or Siri)
D) A pencil
ANSWER: C
""")
    # File uploader
    uploaded_file = st.file_uploader("Upload your quiz text file", type=["txt"])
    if uploaded_file is not None:
        print(f"File uploaded: {uploaded_file.name}")  # Debugging statement
        lines = read_quiz(uploaded_file)
        if lines is None:
            return
        data = []
        index = 0
        while index < len(lines):
            line = lines[index].strip()
            if line and not line.startswith(('A)', 'B)', 'C)', 'D)', 'ANSWER:')):
                formatted_question = format_question(lines, index)
                if formatted_question is not None:
                    data.append(formatted_question)
                    # Skip the lines containing answers and the correct answer
                    index += len(formatted_question) - 1
            index += 1
        if not data:
            st.error("No valid questions found in the file.")
            return
        # Create DataFrame
        df = pd.DataFrame(data, columns=['Question Text', 'Question Type', 'Option 1', 'Option 2', 'Option 3', 'Option 4', 'Correct Answer'])
        df = df.sort_values(by='Question Text')
        # Default filename
        excel_filename = "quiz.xlsx"
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
            worksheet = writer.sheets['Sheet1']
            # Set column widths
            worksheet.column_dimensions['A'].width = 60  # Question Text
            worksheet.column_dimensions['B'].width = 15  # Question Type
            worksheet.column_dimensions['C'].width = 60  # Option 1
            worksheet.column_dimensions['D'].width = 60  # Option 2
            worksheet.column_dimensions['E'].width = 60  # Option 3
            worksheet.column_dimensions['F'].width = 60  # Option 4
            worksheet.column_dimensions['G'].width = 15  # Correct Answer
            # Apply text wrapping
            for row in worksheet.iter_rows(min_row=2, max_row=worksheet.max_row, min_col=1, max_col=7):
                for cell in row:
                    cell.alignment = Alignment(wrap_text=True)
        # Provide download button
        st.success("File processed successfully! Click below to download the Excel file.")
        st.download_button(
            label="Download Excel File",
            data=output.getvalue(),
            file_name=excel_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# Run the Streamlit app
if __name__ == "__main__":
    main()
