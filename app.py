import pandas as pd  # Import pandas library for data manipulation
import streamlit as st  # Import streamlit for creating the web app
import os
from openpyxl.styles import Alignment  # Import Alignment from openpyxl for cell formatting
from io import BytesIO  # Import BytesIO for handling in-memory binary streams


#must be the first line of command
st.set_page_config(page_title="EduTools") 

# Function to read and process the quiz file
def read_quiz(file_content):
    try:
        content = file_content.read().decode('utf-8').split('\n')  # Read the file content and split into lines. This assumes the file is encoded in UTF-8.
        print("File content read successfully:") # Debugging statement to confirm the file content is read successfully
        #for i, line in enumerate(content): # Iterate over the lines with their indices to print them for debugging
            #print(f"{i}: {line.strip()}")  # Print each line with its index
        #return content # Return the list of lines from the file content to be processed further
    except Exception as e: # Handle any exceptions that occur while reading the file 
        st.error(f"An error occurred while reading the file: {e}") # Display an error message in the web app if an exception occurs
        return None # Return None if an error occurs while reading the file to indicate that the file content could not be read successfully

# Function to format a single question
def format_question(lines, index): # Function to format a single question from the list of lines and the starting index of the question
    try: # Try to format the question and handle any exceptions that may occur while processing the question
        question = [] # List to store the question and its answers
        answers = [] # List to store the answers
        correct_answer = None # Variable to store the correct answer. None is used to indicate that the correct answer has not been found yet.
        correct_index = -1 # Variable to store the index of the correct answer. -1 is used to indicate that the correct answer index has not been found yet.

        # Extract the question text
        question_text = lines[index].strip() #Get the question text from the line at the given index and remove any leading or trailing whitespace
        #print(f"Processing line {index}: {question_text}")  # # Debugging statement to print the question text being processed

        # Remove the leading number and period after item number (e.g., "1) ", "55) ", "101) ")
        if question_text[0].isdigit():  # Check if the first character is a digit
            # Find the position of the period after item number
            period_pos = question_text.find('.') # Find the position of the period after item number
            if period_pos != -1: # If a period after item number is found
                question_text = question_text[period_pos + 2:].strip()  # Remove the leading number and period after item number. 2 is added to the period position to remove the period and the space after it.

        if not question_text: # Check if the question text is empty after removing the leading number and period after item number
            st.warning(f"Warning: Empty question found at index {index}.") # Display a warning message indicating that an empty question was found
            return None # Return None to indicate that the question is invalid

        question.append(question_text) # Add the question text to the question list
        question.append("multiple choice") # Add the question type to the question list

        # Extract answers and correct answer from the following lines
        for i in range(index + 1, len(lines)): # Iterate over the lines following the question
            line = lines[i].strip() # Get the line text and remove leading/trailing whitespace
            print(f"Processing line {i}: {line}")  # Debugging statement

            if line.startswith(('A)', 'B)', 'C)', 'D)')): # Check if the line starts with an answer letter
                answers.append(line[3:].strip()) # Add the answer text to the answers list
            elif line.startswith('ANSWER:'): # Check if the line starts with the correct answer indicator
                correct_answer = line.split(':')[1].strip() # Extract the correct answer letter
                break # Exit the loop after finding the correct answer
            elif line:  # If the line is not empty and doesn't start with an answer or correct answer
                st.warning(f"Unexpected line found at index {i}: {line}") # Display a warning message
                return None # Return None to indicate that the question is invalid
            else: # If the line is empty, skip it
                continue  # Skip blank lines

        # Validate answers
        if len(answers) != 4: # Check if there are exactly 4 answers
            st.warning(f"Warning: Question at index {index} does not have exactly 4 answers.") # Display a warning message
            return None # Return None to indicate that the question is invalid

        # Determine the correct answer index
        if correct_answer: # Check if the correct answer was found
            correct_index = ord(correct_answer) - ord('A') + 1 # Convert the correct answer letter to an index
            if correct_index < 1 or correct_index > 4:  # Check if the correct answer index is valid
                st.warning(f"Warning: Invalid correct answer '{correct_answer}' for question at index {index}.") # Display a warning message
                return None # Return None to indicate that the question is invalid
        else: # If the correct answer was not found
            st.warning(f"Warning: No correct answer found for question at index {index}.") # Display a warning message
            return None # Return None to indicate that the question is invalid

        return question + answers + [correct_index] # Return the formatted question as a list

    except Exception as e: # Catch any other exceptions
        st.error(f"An error occurred while formatting the question at index {index}: {e}") # Display an error message
        return None # Return None to indicate that the question is invalid

# Main function for the Streamlit app
def main(): # Define the main function for the Streamlit app
    st.title("Text to Excel for Quizizz 🔄")
    st.write("Upload a quiz text file and convert it into an Excel file that can be imported on Quizizz.com.")
    st.write("**Below is a sample of formatted question. Make sure to have blank line between questions and choices are uppercase as well as the answer.**")
    st.code("""
1. What can a robot do that helps you clean your room?
A) Cook dinner
B) Vacuum the floor
C) Wash dishes
D) Do homework
ANSWER: B

2. Which of the following is an example of a smart device that uses AI?
A) A toy car
B) A teddy bear
C) A smart speaker (like Alexa or Siri)
D) A pencil
ANSWER: C
""")
    # File uploader
    uploaded_file = st.file_uploader("Upload your quiz text file", type=["txt"]) # Allow only .txt files to be uploaded
    if uploaded_file is not None: # Check if a file has been uploaded
        print(f"File uploaded: {uploaded_file.name}")  # Debugging statement to check the uploaded file name
        lines = read_quiz(uploaded_file) # Read the uploaded file
        if lines is None: # Check if the file was read successfully
            return # Exit the function if the file was not read successfully
        data = [] # Initialize an empty list to store the formatted questions
        index = 0 # Initialize the index to 0
        success_count = 0  # Counter for successfully processed questions
        fail_count = 0     # Counter for failed processing attempts
        
        while index < len(lines): # Loop through each line in the file
            line = lines[index].strip() # Remove leading and trailing whitespace from the line
            if line and not line.startswith(('A)', 'B)', 'C)', 'D)', 'ANSWER:')): # Check if the line is not empty and does not start with an option or answer
                formatted_question = format_question(lines, index) # Format the question and options
                if formatted_question is not None:  # Check if the question was formatted successfully
                    data.append(formatted_question)
                    success_count += 1  # Increment success counter
                    # Skip the lines containing answers and the correct answer
                    index += len(formatted_question) - 1
                else:
                    fail_count += 1  # Increment fail counter
            index += 1
        
        # Display summary
        total_items = success_count + fail_count
        st.info(f"Processing Summary:\n"
                f"- Successfully Processed: {success_count}\n"
                f"- Failed to Process: {fail_count}\n"
                f"- Total Items Processed: {total_items}")
        
        if not data:
            st.error("No valid questions found in the file.")
            return
        
        # Create DataFrame
        df = pd.DataFrame(data, columns=['Question Text', 'Question Type', 'Option 1', 'Option 2', 'Option 3', 'Option 4', 'Correct Answer'])
        df = df.sort_values(by='Question Text')
        
        # Generate Excel file name based on the uploaded file name
        uploaded_filename = uploaded_file.name
        excel_filename = f"{os.path.splitext(uploaded_filename)[0]}.xlsx"
        
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
