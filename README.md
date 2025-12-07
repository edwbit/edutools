# EduTools - Modular Quiz Converter

A modular Streamlit application that converts text-based quiz questions (TXT or DOCX) to Excel format for Quizizz.

## Project Structure

```
edutools/
├── app.py                  # Main Streamlit application
├── main.py                 # Clean entry point
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
├── parsing/
│   └── question_parser.py  # Question parsing logic
└── excel/
    └── excel_generator.py  # Excel generation functions
```

## Modules

### 1. `parsing/question_parser.py`
Handles all text parsing functionality:
- `read_quiz_raw_lines()`: Reads uploaded file content
- `split_into_blocks()`: Splits content into question blocks
- `parse_question_block()`: Parses individual question blocks

### 2. `excel/excel_generator.py`
Manages Excel file generation:
- `generate_quizizz_excel()`: Creates Quizizz-compatible Excel file
- `create_preview_dataframe()`: Generates preview data for display

### 3. `app.py`
Main Streamlit application with UI and workflow:
- Handles file uploads
- Coordinates parsing and Excel generation
- Manages user interface and display

### 4. `main.py`
Clean entry point for the application.

## Usage

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
streamlit run main.py
```

3. Upload a text file (`.txt` or `.docx`) with quiz questions in the specified format.

## Benefits of Modular Structure

- **Separation of Concerns**: Each module handles a specific responsibility
- **Easier Maintenance**: Changes to parsing logic don't affect Excel generation
- **Better Testability**: Individual modules can be tested independently
- **Improved Readability**: Smaller, focused files are easier to understand
- **Reusability**: Modules can be reused in other projects

## Example Question Format

```
What is DNS?
A. Domain Name System
B. Dynamic Host Configuration Protocol
C. Data Naming Services
D. Digital Network Security
ANSWER: A