import pandas as pd
from openpyxl.styles import Alignment
from io import BytesIO

def generate_quizizz_excel(data, base_filename):
    """
    Generate a Quizizz-compatible Excel file from parsed question data.

    Args:
        data: List of parsed question data
        base_filename: Base filename for the output Excel file

    Returns:
        tuple: (excel_name, output_bytes) where excel_name is the filename string
              and output_bytes is BytesIO object containing the Excel data
    """
    # Add Time in seconds column (default 60 seconds)
    for row in data:
        row.append(60)  # Add time value

    df = pd.DataFrame(data, columns=[
        'Question Text', 'Question Type',
        'Option 1', 'Option 2', 'Option 3', 'Option 4',
        'Correct Answer', 'Time in seconds'
    ])

    # Sort questions alphabetically by question text
    df = df.sort_values('Question Text', ascending=True).reset_index(drop=True)

    excel_name = f"{base_filename}-QUIZIZZ.xlsx"
    output = BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        ws = writer.sheets['Sheet1']

        # Set column widths
        ws.column_dimensions['A'].width = 70  # Question Text
        ws.column_dimensions['B'].width = 15  # Question Type
        ws.column_dimensions['C'].width = 55  # Option 1
        ws.column_dimensions['D'].width = 55  # Option 2
        ws.column_dimensions['E'].width = 55  # Option 3
        ws.column_dimensions['F'].width = 55  # Option 4
        ws.column_dimensions['G'].width = 15  # Correct Answer
        ws.column_dimensions['H'].width = 15  # Time in seconds

        # Apply text wrapping and alignment
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=8):
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical='top')

    return excel_name, output

def create_preview_dataframe(df):
    """
    Create a preview version of the dataframe for display.

    Args:
        df: Original dataframe with question data

    Returns:
        DataFrame: Preview dataframe with formatted correct answers
    """
    preview = df.copy()  # Show all questions instead of just 5
    preview['Correct Answer'] = preview['Correct Answer'].map({1: 'A', 2: 'B', 3: 'C', 4: 'D'})
    return preview