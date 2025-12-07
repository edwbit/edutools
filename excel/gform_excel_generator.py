"""
Google Forms Excel Generator
Specialized Excel generation for Google Forms format
"""

import pandas as pd
from openpyxl.styles import Alignment
from io import BytesIO

def generate_gform_excel(data, base_filename):
    """
    Generate a Google Forms-compatible Excel file from parsed question data.

    Args:
        data: List of parsed question data
        base_filename: Base filename for the output Excel file

    Returns:
        tuple: (excel_name, output_bytes) where excel_name is the filename string
              and output_bytes is BytesIO object containing the Excel data
    """
    # Convert parsed data to Google Forms structure
    # Parsed data format: [question_text, question_type, option_A, option_B, option_C, option_D, correct_answer_index]
    processed_data = []
    for question in data:
        # Map correct answer index (1-4) to actual choice text
        answer_choices = [question[2], question[3], question[4], question[5]]
        correct_answer_text = answer_choices[question[6] - 1]  # Convert 1-based index to 0-based

        processed_data.append({
            'Question': question[0],
            'Type': question[1],
            'Choice A': question[2],
            'Choice B': question[3],
            'Choice C': question[4],
            'Choice D': question[5],
            'Answer': correct_answer_text,  # Full answer text for Google Forms
            'Points': 1
        })

    # Create DataFrame with Google Forms structure
    df = pd.DataFrame(processed_data)

    # Sort questions alphabetically by question text
    df = df.sort_values('Question', ascending=True).reset_index(drop=True)

    # Set default points (Google Forms typically uses 1 point per question)
    # Note: Points are already set in the data processing above

    # Generate Excel file with Google Forms naming
    excel_name = f"{base_filename}-GFORM.xlsx"
    output = BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        ws = writer.sheets['Sheet1']

        # Set uniform column widths with text wrapping
        for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
            ws.column_dimensions[col].width = 20

        # Apply text wrapping and alignment
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=8):
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical='top')

    return excel_name, output

def create_gform_preview_dataframe(df):
    """
    Create a preview version of the dataframe for Google Forms display.

    Args:
        df: Original dataframe with question data

    Returns:
        DataFrame: Preview dataframe with Google Forms formatting
    """
    # For Google Forms preview, show the key columns
    preview = df.copy()
    return preview[['Question', 'Choice A', 'Choice B', 'Answer', 'Points']]