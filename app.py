import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
import re
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from matplotlib.backends.backend_agg import FigureCanvasAgg
import matplotlib
matplotlib.use('Agg')

# Function to convert Matplotlib figure to ReportLab Image
def fig_to_image(fig):
    """Convert a Matplotlib figure to a ReportLab Image"""
    canvas = FigureCanvasAgg(fig)
    buf = io.BytesIO()
    canvas.print_png(buf)
    buf.seek(0)
    return Image(buf, width=7*inch, height=4*inch)

# Function to extract semester and program from filename
def extract_info_from_filename(filename):
    """Extract semester and program information from feedback filename"""
    info = {
        'semester': None,
        'program': None
    }
    
    # Look for pattern like 'Sem-3' in the filename
    sem_match = re.search(r'Sem-(\d+)', filename)
    if sem_match:
        info['semester'] = sem_match.group(1)
    
    # Look for program code like 'BT-AIML' in the filename
    prog_match = re.search(r'BT-([A-Z]+)', filename)
    if prog_match:
        info['program'] = prog_match.group(1)
    
    return info

# Function to generate faculty report
def generate_faculty_report(faculty_data):
    """Generate a text report with rating categories and values"""
    faculty_name = faculty_data["Faculty Name"].iloc[0]
    section = faculty_data["Section"].iloc[0] if "Section" in faculty_data.columns else ""
    
    # Include section in the header if available
    header = f"Faculty Rating Report for: {faculty_name}"
    if section:
        header = f"Faculty Rating Report for: Section {section} - {faculty_name}"
    
    report = header + "\n"
    report += f"Generated on: {datetime.now().strftime('%Y-%m-%d')}\n"
    report += "=" * 50 + "\n\n"
    
    # Add overall average
    overall_avg = faculty_data["Rating"].mean()
    report += f"OVERALL AVERAGE: {overall_avg:.2f} / 5.0\n\n"
    report += "RATINGS BY CATEGORY:\n"
    report += "-" * 50 + "\n\n"
    
    # Sort ratings from highest to lowest
    sorted_data = faculty_data.sort_values(by="Rating", ascending=False)
    
    # Add each category and its rating
    for _, row in sorted_data.iterrows():
        category = row["Rating Category"].title()
        rating = row["Rating"]
        report += f"{category}: {rating:.2f}\n"
    
    return report

def generate_pdf_report(faculty_data, course_name):
    """Generate a PDF report with ratings in table format"""
    faculty_name = faculty_data["Faculty Name"].iloc[0]
    section = faculty_data["Section"].iloc[0] if "Section" in faculty_data.columns else ""
    
    # Create buffer for PDF with reduced margins
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        rightMargin=36,  # 0.5 inch
        leftMargin=36,   # 0.5 inch
        topMargin=36,    # 0.5 inch
        bottomMargin=36  # 0.5 inch
    )
    elements = []
    styles = getSampleStyleSheet()
    
    try:
        # Add logo (adjust path as needed)
        logo = Image("REVA_logo.png", width=180, height=50)
        logo.hAlign = 'RIGHT'  # Right align the logo
        elements.append(logo)
        elements.append(Spacer(1, 10))  # Add small space after logo
    except:
        # If logo file not found, continue without it
        pass
    
    # Create custom styles for different alignments with reduced line spacing
    center_style = ParagraphStyle(
        'CenterHeader',
        parent=styles['Heading1'],
        fontSize=14,
        alignment=1,  # Center alignment
        spaceAfter=5
    )
    
    left_style = ParagraphStyle(
        'LeftAligned',
        parent=styles['Normal'],
        fontSize=12,
        alignment=0,  # Left alignment
        spaceBefore=2,  # Reduced from 5
        spaceAfter=2,   # Reduced from 5
        leading=14      # Control line height
    )
    
    right_style = ParagraphStyle(
        'RightAligned',
        parent=styles['Normal'],
        fontSize=12,
        alignment=2,  # Right alignment
        spaceBefore=2,  # Reduced from 5
        spaceAfter=2,   # Reduced from 5
        leading=14      # Control line height
    )
    
    # Clean course name for display
    clean_course_name = course_name.replace("Feedback on ", "").strip()
    
    # CENTER ALIGNED HEADERS
    # Add centered headers
    elements.append(Paragraph("School of Computing and Information Technology", center_style))
    elements.append(Paragraph(f"Academic Year {st.session_state.start_year}-{st.session_state.end_year}", center_style))
    elements.append(Paragraph(f"Feedback on {clean_course_name}", center_style))
    
    # Add program name if available - MODIFY THIS SECTION
    if st.session_state.program:
        full_program = get_full_program_name(st.session_state.program)
        elements.append(Paragraph(f"{full_program}", center_style))
    
    elements.append(Spacer(1, 10))
    
    # Create a table for the 3-column layout with tighter spacing
    data = []
    
    # Row 1: Faculty name | Empty | Semester
    row1 = [
        Paragraph(f"Name of the Faculty: {faculty_name}", left_style),
        "",
        Paragraph(f"Semester: {st.session_state.semester}" if st.session_state.semester else "", right_style)
    ]
    data.append(row1)
    
    # Row 2: Course name | Empty | Section
    row2 = [
        Paragraph(f"Course name: {clean_course_name}", left_style),
        "",
        Paragraph(f"Section: {section}" if section else "", right_style)
    ]
    data.append(row2)
    
    # Row 3: Course code | Empty | Empty
    course_code = st.session_state.course_code_mapping.get(clean_course_name, "")
    if course_code:
        row3 = [
            Paragraph(f"Course Code: {course_code}", left_style),
            "",
            ""
        ]
        data.append(row3)
    
    # Create the table with further adjusted column widths - minimize center gap
    header_table = Table(data, colWidths=[4.0*inch, 0.1*inch, 2.4*inch], rowHeights=[18]*len(data))
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Changed from TOP to MIDDLE
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 1),     # Reduced from 0
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),  # Reduced from 0
    ]))
    elements.append(header_table)
    
    elements.append(Spacer(1, 20))
    
    # Calculate overall average
    overall_avg = faculty_data["Rating"].mean().round(2)
    elements.append(Paragraph(f"Overall Average: {overall_avg:.2f} / 5.0", styles['Heading3']))
    elements.append(Spacer(1, 20))
    
    # Prepare table data
    sorted_data = faculty_data.sort_values(by="Rating", ascending=False)
    table_data = [["Rating Category", "Score"]]  # Header row
    
    for _, row in sorted_data.iterrows():
        # Split long category names into multiple lines if longer than 40 chars
        category = row["Rating Category"].title()
        if len(category) > 70:
            # Split at space nearest to middle
            mid = category[:70].rfind(' ')
            if mid == -1:  # No space found, force split
                mid = 70
            category = category[:mid] + '\n' + category[mid:].strip()
            
        table_data.append([
            category,
            f"{row['Rating']:.2f}"
        ])
    
    # Create table with increased width and automatic word wrapping
    table = Table(table_data, colWidths=[5*inch, 1*inch])
    
    # Style the table with word wrap and vertical alignment
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),    
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),  
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BOX', (0, 0), (-1, -1), 2, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('WORDWRAP', (0, 0), (-1, -1), True),  
    ])
    
    table.setStyle(style)
    elements.append(table)
    elements.append(Spacer(1, 30))

    # Create and add bar chart with increased height
    fig, ax = plt.subplots(figsize=(10, 8))  # Increased height from 6 to 8
    bars = ax.bar(faculty_data["Rating Category"], faculty_data["Rating"], color="skyblue", width=0.4)  # Reduced width for taller appearance
    ax.set_title(f"Ratings Distribution", fontsize=12)
    ax.set_xlabel("Rating Category", fontsize=10)
    ax.set_ylabel("Rating", fontsize=10)
    ax.set_ylim(0, 5.5)  # Set y-axis limit to make bars appear taller
    plt.xticks(rotation=45, ha='right')
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}',
                ha='center', va='bottom')
    
    plt.tight_layout()
    
    # Convert figure to ReportLab Image with increased height
    chart_img = fig_to_image(fig)
    chart_img.hAlign = 'CENTER'
    chart_img._height = 5*inch  # Increase image height in the PDF
    elements.append(chart_img)
    plt.close(fig)  # Close the figure to free memory
    
    # Force the footer to appear at the bottom of the page
    # First, calculate remaining space and add a spacer to push the footer down
    # A typical US Letter page is 11 inches high (minus margins)
    page_height = letter[1] - doc.topMargin - doc.bottomMargin
    
    # We already used about 7.5-8 inches (header + table + chart)
    # Add a spacer that will push the footer to the bottom
    elements.append(Spacer(1, 1.5*inch))  # Add extra space to push footer down
    
    # Add footer signatures with updated labels
    footer_data = [["IQAC", "HOD", "DIRECTOR"]]
    footer_table = Table(footer_data, colWidths=[2.0*inch, 2.0*inch, 2.0*inch])
    footer_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 30),  # Space for signature
    ])
    
    footer_table.setStyle(footer_style)
    elements.append(footer_table)
    
    # Build PDF
    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer

# Function to generate table visualization for faculty
def generate_table_visualization(faculty_data):
    """Generate a table visualization of faculty ratings as a figure"""
    if faculty_data.empty:
        return None
    
    faculty_name = faculty_data["Faculty Name"].iloc[0]
    
    # Calculate total average
    total_avg = faculty_data['Rating'].mean().round(4)
    
    # Create new row for total average
    new_row = pd.DataFrame({
        'Faculty Name': [faculty_name],
        'Rating Category': ['Total Average'],
        'Rating': [total_avg]
    })
    
    # Append new row to faculty data
    viz_data = pd.concat([faculty_data, new_row], ignore_index=True)
    
    # Prepare data for table
    headers = ['Rating Category', 'Average Rating']
    data = viz_data[['Rating Category', 'Rating']].values.tolist()
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.axis('off')  # Hide axes
    
    # Add title
    plt.title(f"Ratings for {faculty_name}", fontsize=14, pad=20)
    
    # Create table
    table = ax.table(
        cellText=data,
        colLabels=headers,
        loc='center',
        cellLoc='left',
        colWidths=[0.7, 0.3]
    )
    
    # Set font size and padding
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1, 1.5)
    
    plt.tight_layout()
    return fig

# Function to verify data processing
def verify_data_processing(faculty_ratings_df, comments_df, course_feedback_df):
    """Print verification of data processing including course information"""
    print("\nData Processing Verification:")
    print("-" * 50)
    
    # Verify faculty ratings
    print("\nFaculty Ratings Summary:")
    print(f"Total records: {len(faculty_ratings_df)}")
    print("\nUnique courses:")
    for course in sorted(faculty_ratings_df['Course'].unique()):
        course_data = faculty_ratings_df[faculty_ratings_df['Course'] == course]
        print(f"- {course}: {len(course_data)} ratings")
    
    # Verify faculty-course combinations
    faculty_course = faculty_ratings_df.groupby(['Faculty Name', 'Course']).size().reset_index()
    print("\nFaculty-Course combinations:")
    for _, row in faculty_course.iterrows():
        print(f"- {row['Faculty Name']} - {row['Course']}")
    
    # Verify comments
    if not comments_df.empty:
        print("\nComments Summary:")
        print(f"Total comments: {len(comments_df)}")
        print("\nComments per course:")
        for course in sorted(comments_df['Course'].unique()):
            course_comments = comments_df[comments_df['Course'] == course]
            print(f"- {course}: {len(course_comments)} comments")
    
    # Verify course feedback
    if not course_feedback_df.empty:
        print("\nCourse Feedback Summary:")
        print(f"Total feedback entries: {len(course_feedback_df)}")
        print("\nFeedback per course:")
        for course in sorted(course_feedback_df['Course'].unique()):
            course_fb = course_feedback_df[course_feedback_df['Course'] == course]
            print(f"- {course}: {len(course_fb)} feedback entries")

# Function to extract section information from faculty name
def extract_section_from_faculty_name(faculty_name):
    """
    Extract section information from faculty name field
    Examples:
    - "Section A - Dr. Smith" returns "A", "Dr. Smith"
    - "Dr. Smith - Section B" returns "B", "Dr. Smith"
    """
    faculty_name = str(faculty_name).strip()
    
    # Try to match "Section X - Faculty Name" pattern
    pattern1 = re.search(r'(?i)section\s+([A-Z0-9]+)\s*[-:]?\s*(.*)', faculty_name)
    if pattern1:
        section = pattern1.group(1).strip()
        name = pattern1.group(2).strip()
        return section, name
    
    # Try to match "Faculty Name - Section X" pattern - FIX: moved flag to beginning or use re.IGNORECASE
    pattern2 = re.search(r'(?i)(.*?)\s*[-:]\s*section\s+([A-Z0-9]+)', faculty_name)
    if pattern2:
        name = pattern2.group(1).strip()
        section = pattern2.group(2).strip()
        return section, name
        
    # If no section info found, return None for section
    return None, faculty_name

# Add this function before the data processing section, for example after the extract_section_from_faculty_name function

def get_columns_for_faculty(all_columns, course_columns, faculty_col_idx):
    """
    Get columns that are likely related to the faculty at faculty_col_idx.
    Uses proximity in the column layout to determine relevant columns.
    
    Parameters:
    - all_columns: List of all column names in the dataframe
    - course_columns: List of column indices for the current course
    - faculty_col_idx: Index of the specific faculty column to process
    
    Returns:
    - List of column indices relevant to this faculty
    """
    # Start with all columns in this course block
    relevant_cols = course_columns.copy()
    
    # If there's only one faculty column, return all columns
    faculty_cols = [i for i in course_columns if 'Name of the Faculty' in all_columns[i]]
    if len(faculty_cols) <= 1:
        return course_columns
    
    # Sort faculty columns
    faculty_cols.sort()
    
    # Find boundaries of this faculty's section
    # Find position of current faculty column in the sorted list
    current_idx = faculty_cols.index(faculty_col_idx)
    
    # Set start boundary (beginning of course or after previous faculty)
    start_boundary = 0 if current_idx == 0 else faculty_cols[current_idx - 1]
    
    # Set end boundary (end of course or before next faculty)
    end_boundary = float('inf') if current_idx == len(faculty_cols) - 1 else faculty_cols[current_idx + 1]
    
    # Filter to columns between boundaries
    relevant_cols = [col for col in course_columns if start_boundary <= col < end_boundary]
    
    return relevant_cols

# Add this function after the other helper functions (like extract_section_from_faculty_name)
# and before the Streamlit app initialization

def identify_course_columns(columns):
    """
    Identify which columns belong to which course/faculty block
    
    Parameters:
    - columns: List of column names in the dataframe
    
    Returns:
    - List of tuples with (course_name, [column_indices])
    """
    course_blocks = []
    current_block = []
    current_course = None

    for i, col in enumerate(columns):
        if isinstance(col, str) and col.startswith('Feedback on '):
            if current_block:
                course_blocks.append((current_course, current_block))
                current_block = []
            current_course = col
            current_block = []
        elif current_course is not None:
            current_block.append(i)

    # Add the last block
    if current_block:
        course_blocks.append((current_course, current_block))

    return course_blocks

# Add this dictionary after other helper functions but before app initialization
def get_full_program_name(program_code):
    """
    Convert program code to full program name
    """
    program_mapping = {
        "AIML": "B.Tech in Computer Science and Engineering (Artificial Intelligence and Machine Learning)",
        "CSE": "B.Tech in Computer Science and Engineering",
        "CSIT": "B.Tech in Computer Science and Information Technology",
        "CSSE": "B.Tech in Computer Science and Systems Engineering", 
        "ISE": "B.Tech in Information Science and Engineering",
        "DS": "B.Tech in Computer Science and Engineering (Data Science)",
        "CS": "B.Tech in Computer Science and Engineering",
        "ECE": "B.Tech in Electronics and Communication Engineering",
        "EEE": "B.Tech in Electrical and Electronics Engineering",
        "MECH": "B.Tech in Mechanical Engineering",
        "CIVIL": "B.Tech in Civil Engineering"
    }
    return program_mapping.get(program_code, program_code)

# Set page config
st.set_page_config(
    page_title="C&IT | REVA University", 
    page_icon="logo.ico", 
    layout="wide")

# Streamlit App Title
st.title("📊 Faculty Ratings Dashboard")

# Add app description
st.markdown("""
This app allows you to process and visualize faculty feedback data. 
You can either upload raw feedback data for processing or analyze pre-processed faculty ratings.
""")

# Initialize session state to store processed data
if 'faculty_ratings_df' not in st.session_state:
    st.session_state.faculty_ratings_df = None
if 'comments_df' not in st.session_state:
    st.session_state.comments_df = None  
if 'course_feedback_df' not in st.session_state:
    st.session_state.course_feedback_df = None
if 'avg_ratings' not in st.session_state:
    st.session_state.avg_ratings = None
if 'course_code_mapping' not in st.session_state:
    st.session_state.course_code_mapping = {}
if 'semester' not in st.session_state:
    st.session_state.semester = None
if 'program' not in st.session_state:
    st.session_state.program = None
    
# Initialize academic year with current year
current_year = datetime.now().year
if 'start_year' not in st.session_state:
    st.session_state.start_year = current_year
if 'end_year' not in st.session_state:
    st.session_state.end_year = current_year + 1

# Academic year input
st.subheader("Set Academic Year")
col1, col2 = st.columns(2)
with col1:
    start_year = st.number_input("Starting Year", min_value=2000, max_value=2100, value=st.session_state.start_year)
    st.session_state.start_year = start_year
    
with col2:
    end_year = st.number_input("Ending Year", min_value=2000, max_value=2100, value=st.session_state.end_year)
    st.session_state.end_year = end_year

# Create tabs
tab1, tab2 = st.tabs(["Process & Visualize Data", "About"])

with tab1:
    # Course code mapping upload
    with st.expander("Upload Course Code Mapping (Optional)"):
        st.info("Upload an Excel file with columns for course names and their corresponding course codes.")
        course_mapping_file = st.file_uploader("Course Code Mapping File (Excel)", type=["xlsx", "csv"], key="course_mapping")
        
        if course_mapping_file is not None:
            try:
                if course_mapping_file.name.endswith(".csv"):
                    mapping_df = pd.read_csv(course_mapping_file)
                else:
                    mapping_df = pd.read_excel(course_mapping_file)
                
                # Check if dataframe has required columns
                required_cols = ["course_name", "course_code"]
                if not all(col.lower() in [c.lower() for c in mapping_df.columns] for col in required_cols):
                    st.warning("The mapping file should have columns for 'course_name' and 'course_code'.")
                else:
                    # Find the actual column names (case insensitive)
                    course_name_col = next(col for col in mapping_df.columns if col.lower() == "course_name")
                    course_code_col = next(col for col in mapping_df.columns if col.lower() == "course_code")
                    
                    # Create mapping dictionary
                    mapping_dict = dict(zip(mapping_df[course_name_col], mapping_df[course_code_col]))
                    st.session_state.course_code_mapping = mapping_dict
                    
                    st.success(f"✅ Course mapping loaded successfully! {len(mapping_dict)} courses mapped.")
                    
                    # Show mapping preview
                    st.write("Mapping Preview:")
                    preview_df = pd.DataFrame(list(mapping_dict.items()), columns=["Course Name", "Course Code"])
                    st.dataframe(preview_df.head(5))
            except Exception as e:
                st.error(f"⚠️ Error loading course mapping file: {e}")

    # Select processing mode
    process_mode = st.radio(
        "Select Mode:",
        ["Process Raw Feedback Data", "Analyze Processed Data"],
        horizontal=True
    )
    
    if process_mode == "Process Raw Feedback Data":
        # Upload File - Raw Data
        uploaded_file = st.file_uploader("Upload Raw Feedback Data (CSV or Excel)", type=["xlsx", "csv"])
        
        if uploaded_file is not None:
            try:
                # Extract semester and program from filename if possible
                file_info = extract_info_from_filename(uploaded_file.name)
                
                if file_info['semester']:
                    st.session_state.semester = file_info['semester']
                    st.success(f"✅ Detected Semester {file_info['semester']} from filename")
                
                if file_info['program']:
                    st.session_state.program = file_info['program']
                    st.success(f"✅ Detected Program {file_info['program']} from filename")
                
                # Read file
                if uploaded_file.name.endswith(".csv"):
                    raw_df = pd.read_csv(uploaded_file)
                else:
                    raw_df = pd.read_excel(uploaded_file)
                
                st.success("✅ Raw data file uploaded successfully!")
                
                # Display raw data sample
                with st.expander("Preview Raw Data"):
                    st.dataframe(raw_df.head())
                
                # Process button - add debug output for faculty columns
                if st.button("Process Raw Data"):
                    with st.spinner("Processing data... This may take a moment."):
                        # Add debugging information about faculty columns
                        st.write("### Faculty Columns Detection")
                        faculty_cols_debug = {}
                        
                        # Identify course blocks
                        course_blocks = identify_course_columns(raw_df.columns)
                        
                        # Process each course block to identify faculty columns
                        for course_name, column_indices in course_blocks:
                            # Use broader pattern matching for faculty columns
                            faculty_cols_in_course = [i for i in column_indices if 
                                                    any(pattern in raw_df.columns[i].lower() for pattern in 
                                                    ["name of the faculty", "faculty name", "name of faculty"])]
                            
                            if faculty_cols_in_course:
                                faculty_cols_debug[course_name] = [raw_df.columns[i] for i in faculty_cols_in_course]
                        
                        # Display detected faculty columns to the user
                        for course, faculty_cols in faculty_cols_debug.items():
                            st.write(f"**Course: {course}**")
                            for i, col in enumerate(faculty_cols, 1):
                                st.write(f"  Faculty Column {i}: {col}")
                        
                        # Show a sample row with faculty data
                        if len(raw_df) > 0:
                            st.write("### Sample Row with Faculty Names")
                            sample_row = raw_df.iloc[0]
                            
                            # Create a sample dataframe of just faculty columns
                            sample_faculty_data = {}
                            for course_name, column_indices in course_blocks:
                                faculty_cols = [i for i in column_indices if 
                                            any(pattern in raw_df.columns[i].lower() for pattern in 
                                                ["name of the faculty", "faculty name", "name of faculty"])]
                                
                                for i in faculty_cols:
                                    col_name = raw_df.columns[i]
                                    sample_faculty_data[f"{course_name}: {col_name}"] = [sample_row[col_name]]
                            
                            if sample_faculty_data:
                                sample_df = pd.DataFrame(sample_faculty_data)
                                st.dataframe(sample_df)
                        
                        # Also update the actual processing code to use broader pattern matching
                        # Initialize empty lists to store the transformed data
                        student_names = []
                        srns = []
                        sections = []
                        faculty_names = []
                        courses = []
                        rating_types = []
                        ratings = []
                        course_feedbacks = []
                        comments = []

                        # Process each row
                        for index, row in raw_df.iterrows():
                            student_name = row.get('Name of the Student', None)
                            srn = row.get('SRN', None)
                            section = row.get('Section', None)  # This stays as a backup
                            
                            if pd.isna(student_name) or pd.isna(srn):
                                continue
                                
                            # Process each course block
                            for course_name, column_indices in course_blocks:
                                # Use broader pattern matching for faculty columns
                                faculty_cols = [i for i in column_indices if 
                                            any(pattern in raw_df.columns[i].lower() for pattern in 
                                                ["name of the faculty", "faculty name", "name of faculty"])]
                                
                                # Process each faculty in this course block
                                for faculty_col_idx in faculty_cols:
                                    # Extract faculty name
                                    raw_faculty_name = str(row[raw_df.columns[faculty_col_idx]])
                                    if pd.isna(raw_faculty_name) or raw_faculty_name.strip() == '':
                                        continue
                                        
                                    # Extract section and clean faculty name
                                    section_from_faculty, faculty_name = extract_section_from_faculty_name(raw_faculty_name)
                                    
                                    # Use section from faculty name if available, otherwise use the section column
                                    effective_section = section_from_faculty if section_from_faculty else section
                                    
                                    # Find question columns related to this faculty
                                    # Use column proximity to connect questions to faculty
                                    relevant_cols = get_columns_for_faculty(raw_df.columns, column_indices, faculty_col_idx)
                                    
                                    # Extract rating questions for this faculty
                                    question_cols = [i for i in relevant_cols if 'Please give a rating' in raw_df.columns[i]]
                                    
                                    # Process each question related to this faculty
                                    for q_col in question_cols:
                                        # ...existing code to process ratings...
                                        question = raw_df.columns[q_col]
                                        rating = row[raw_df.columns[q_col]]
                                        
                                        if not pd.isna(rating):
                                            student_names.append(student_name)
                                            srns.append(srn)
                                            sections.append(effective_section)  # Use the extracted section
                                            faculty_names.append(faculty_name)  # Use the clean faculty name
                                            courses.append(course_name)
                                            rating_types.append(question)
                                            ratings.append(rating)
                                            
                                    # Get comments if available
                                    comment_col = [i for i in relevant_cols if raw_df.columns[i] == 'Comments']
                                    if comment_col:
                                        comment = row[raw_df.columns[comment_col[0]]]
                                        if not pd.isna(comment):
                                            comments.append({
                                                'Student': student_name,
                                                'SRN': srn,
                                                'Faculty': faculty_name,
                                                'Course': course_name,
                                                'Comment': comment
                                            })

                                    # Get course feedback questions
                                    course_feedback_cols = [i for i in relevant_cols if 'The course' in raw_df.columns[i]]
                                    for cf_col in course_feedback_cols:
                                        question = raw_df.columns[cf_col]
                                        rating = row[raw_df.columns[cf_col]]

                                        if not pd.isna(rating):
                                            course_feedbacks.append({
                                                'Student': student_name,
                                                'SRN': srn,
                                                'Course': course_name,
                                                'Question': question,
                                                'Rating': rating
                                            })

                        # Create the main faculty ratings DataFrame
                        faculty_ratings_df = pd.DataFrame({
                            'Student Name': student_names,
                            'SRN': srns,
                            'Section': sections,
                            'Faculty Name': faculty_names,
                            'Course': courses,
                            'Rating Category': rating_types,
                            'Rating': ratings
                        })

                        # Create the comments DataFrame
                        comments_df = pd.DataFrame(comments)

                        # Create the course feedback DataFrame
                        course_feedback_df = pd.DataFrame(course_feedbacks)
                        
                        # Clean faculty names
                        faculty_ratings_df['Faculty Name'] = faculty_ratings_df['Faculty Name'].astype(str).str.replace(r"Section[ -]?[A-Z]?[ -]?", "", regex=True).str.strip()
                        
                        # Clean the rating categories
                        faculty_ratings_df['Rating Category'] = (
                            faculty_ratings_df['Rating Category']
                            .str.strip()
                            .str.lower()
                            .str.replace(r"\s+", " ", regex=True)
                            .str.split("(").str[0]
                            .str.strip()
                        )
                        
                        # Convert rating to numeric
                        faculty_ratings_df['Rating'] = pd.to_numeric(faculty_ratings_df['Rating'], errors='coerce')
                        
                        # Save data to session state for persistence
                        st.session_state.faculty_ratings_df = faculty_ratings_df
                        st.session_state.comments_df = comments_df
                        st.session_state.course_feedback_df = course_feedback_df
                        
                        # Compute averages for visualization
                        avg_ratings = (
                            faculty_ratings_df.groupby(["Faculty Name", "Rating Category"], as_index=False)
                            .agg({"Rating": "mean"})
                        )
                        
                        # Save averages to session state
                        st.session_state.avg_ratings = avg_ratings
                        
                        # Verify data processing
                        verify_data_processing(faculty_ratings_df, comments_df, course_feedback_df)
                
                # Display processed data if available in session state
                if st.session_state.faculty_ratings_df is not None:
                    st.subheader("Processed Data")
                    
                    # Debug: Check unique sections in the dataset
                    unique_sections = st.session_state.faculty_ratings_df['Section'].unique()
                    print(f"Debug - Unique sections in data: {unique_sections}")
                    
                    # Create tabs for different datasets
                    data_tabs = st.tabs(["Faculty Ratings", "Student Comments", "Course Feedback"])
                    
                    with data_tabs[0]:
                        st.write(f"Faculty Ratings: {len(st.session_state.faculty_ratings_df)} records")
                        st.dataframe(st.session_state.faculty_ratings_df.head(10))
                        
                        # Download button for faculty ratings
                        faculty_buffer = io.BytesIO()
                        with pd.ExcelWriter(faculty_buffer, engine='openpyxl') as writer:
                            st.session_state.faculty_ratings_df.to_excel(writer, index=False)
                        faculty_buffer.seek(0)
                        
                        st.download_button(
                            label="Download Faculty Ratings Data",
                            data=faculty_buffer,
                            file_name="faculty_ratings.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    
                    with data_tabs[1]:
                        if not st.session_state.comments_df.empty:
                            st.write(f"Student Comments: {len(st.session_state.comments_df)} records")
                            st.dataframe(st.session_state.comments_df.head(10))
                            
                            # Download button for comments
                            comments_buffer = io.BytesIO()
                            with pd.ExcelWriter(comments_buffer, engine='openpyxl') as writer:
                                st.session_state.comments_df.to_excel(writer, index=False)
                            comments_buffer.seek(0)
                            
                            st.download_button(
                                label="Download Student Comments Data",
                                data=comments_buffer,
                                file_name="student_comments.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        else:
                            st.info("No student comments found in the data.")
                    
                    with data_tabs[2]:
                        if not st.session_state.course_feedback_df.empty:
                            st.write(f"Course Feedback: {len(st.session_state.course_feedback_df)} records")
                            st.dataframe(st.session_state.course_feedback_df.head(10))
                            
                            # Download button for course feedback
                            course_buffer = io.BytesIO()
                            with pd.ExcelWriter(course_buffer, engine='openpyxl') as writer:
                                st.session_state.course_feedback_df.to_excel(writer, index=False)
                            course_buffer.seek(0)
                            
                            st.download_button(
                                label="Download Course Feedback Data",
                                data=course_buffer,
                                file_name="course_feedback_ratings.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        else:
                            st.info("No course feedback found in the data.")
                    
                    # Visualization section
                    st.subheader("Visualize Faculty Ratings")
                    
                    # Group by Section and Faculty - improved logic
                    if "Section" in st.session_state.faculty_ratings_df.columns:
                        # Make sure section values are properly extracted
                        st.session_state.faculty_ratings_df['Section'] = st.session_state.faculty_ratings_df['Section'].astype(str).fillna('')
                        
                        # Create combined labels for faculty selection with clearer section extraction
                        section_faculty_groups = st.session_state.faculty_ratings_df.groupby(["Section", "Faculty Name"]).size().reset_index()
                        
                        # Debug: Show unique section-faculty combinations
                        print("Debug - Section-Faculty combinations:")
                        for _, row in section_faculty_groups.iterrows():
                            print(f"  Section: '{row['Section']}' - Faculty: '{row['Faculty Name']}'")
                            
                        # Create labels for dropdown, ensuring section is clearly shown
                        section_faculty_labels = []
                        for _, row in section_faculty_groups.iterrows():
                            section_val = row['Section']
                            # Only add "Section" prefix if section value is not empty
                            if pd.notna(section_val) and section_val.strip() != '':
                                section_faculty_labels.append(f"Section {section_val} - {row['Faculty Name']}")
                            else:
                                section_faculty_labels.append(row['Faculty Name'])
                        
                        # Select Section-Faculty combination
                        selected_combo = st.selectbox("🎓 Select a Section-Faculty Combination", section_faculty_labels)
                        
                        # Parse the selection back to section and faculty
                        if " - " in selected_combo and selected_combo.startswith("Section "):
                            section, faculty = selected_combo.replace("Section ", "", 1).split(" - ", 1)
                        else:
                            section = ""
                            faculty = selected_combo
                        
                        # Filter Data for Selected Faculty and Section
                        if section:
                            faculty_data = st.session_state.faculty_ratings_df[
                                (st.session_state.faculty_ratings_df["Faculty Name"] == faculty) &
                                (st.session_state.faculty_ratings_df["Section"] == section)
                            ].copy()
                        else:
                            faculty_data = st.session_state.faculty_ratings_df[
                                st.session_state.faculty_ratings_df["Faculty Name"] == faculty
                            ].copy()
                    else:
                        # Fall back to original faculty selection if Section is not available
                        faculties = st.session_state.avg_ratings["Faculty Name"].unique()
                        
                        if len(faculties) == 0:
                            st.error("❌ No faculty names detected! Please check your data.")
                        else:
                            selected_faculty = st.selectbox("🎓 Select a Faculty", faculties)
                            
                            # Filter Data for Selected Faculty
                            faculty_data = st.session_state.faculty_ratings_df[
                                st.session_state.faculty_ratings_df["Faculty Name"] == selected_faculty
                            ].copy()
                            section = ""
                    
                    # Get unique course name for this faculty
                    course_name = faculty_data["Course"].iloc[0].replace("Feedback on ", "") if len(faculty_data) > 0 else "N/A"
                    
                    # Update averages computation to include Section if available
                    if "Section" in faculty_data.columns:
                        avg_ratings = faculty_data.groupby(["Section", "Faculty Name", "Rating Category"], as_index=False).agg({"Rating": "mean"})
                    else:
                        avg_ratings = faculty_data.groupby(["Faculty Name", "Rating Category"], as_index=False).agg({"Rating": "mean"})
                    
                    # Select visualization type
                    viz_type = st.radio(
                        "Choose Visualization Type:",
                        ["Bar Chart", "Table"],
                        horizontal=True
                    )
                    
                    # For visualizations, update the titles to include section if available
                    if viz_type == "Bar Chart":
                        # Plot Ratings using avg_ratings
                        fig, ax = plt.subplots(figsize=(12, 8))  # Increased height from 6 to 8
                        bars = ax.bar(avg_ratings["Rating Category"], avg_ratings["Rating"], color="skyblue", width=0.6)

                        # Include section in title if available
                        if "Section" in avg_ratings.columns and avg_ratings["Section"].iloc[0]:
                            title = f"📈 Average Ratings for Section {avg_ratings['Section'].iloc[0]} - {avg_ratings['Faculty Name'].iloc[0]}"
                        else:
                            title = f"📈 Average Ratings for {avg_ratings['Faculty Name'].iloc[0]}"
                            
                        ax.set_title(title, fontsize=14)
                        ax.set_xlabel("Rating Category", fontsize=12)
                        ax.set_ylabel("Average Rating (1-5)", fontsize=12)
                        ax.set_ylim(0, 5.5)  # Keep the same y-limit
                        plt.xticks(rotation=45, ha="right", fontsize=10)
                        
                        # Add labels on bars
                        for bar, category, rating in zip(bars, avg_ratings["Rating Category"], avg_ratings["Rating"]):
                            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f"{rating:.2f}", ha="center", va="bottom", fontsize=10)
                        
                        plt.tight_layout()
                        st.pyplot(fig)
                        
                        # Save figure option
                        save_fig_buffer = io.BytesIO()
                        fig.savefig(save_fig_buffer, format='png', dpi=300, bbox_inches='tight')
                        save_fig_buffer.seek(0)
                        
                        # Create filename based on section and faculty
                        if section:
                            filename = f"Section_{section}_{faculty}_ratings_chart.png"
                        else:
                            filename = f"{faculty}_ratings_chart.png"
                        
                        st.download_button(
                            label="Download Chart",
                            data=save_fig_buffer,
                            file_name=filename,
                            mime="image/png"
                        )
                    else:  # Table visualization
                        # Generate table visualization using avg_ratings
                        table_fig = generate_table_visualization(avg_ratings)
                        if table_fig:
                            st.pyplot(table_fig)
                            
                            # Save table figure option
                            table_buffer = io.BytesIO()
                            table_fig.savefig(table_buffer, format='png', dpi=300, bbox_inches='tight')
                            table_buffer.seek(0)
                            
                            # Create filename based on section and faculty
                            if section:
                                filename = f"Section_{section}_{faculty}_ratings_table.png"
                            else:
                                filename = f"{faculty}_ratings_table.png"
                            
                            st.download_button(
                                label="Download Table Image",
                                data=table_buffer,
                                file_name=filename,
                                mime="image/png"
                            )
                    
                    # Add horizontal line for visual separation
                    st.markdown("---")
                    
                    # Generate text report for rating categories
                    faculty_report = generate_faculty_report(avg_ratings)

                    # Create columns for layout
                    report_col1, report_col2 = st.columns([1, 2])

                    with report_col1:
                        # Create report filename based on section and faculty
                        if section:
                            text_filename = f"Section_{section}_{faculty}_ratings_report.txt"
                            pdf_filename = f"Section_{section}_{faculty}_ratings_report.pdf"
                        else:
                            text_filename = f"{faculty}_ratings_report.txt"
                            pdf_filename = f"{faculty}_ratings_report.pdf"
                            
                        # Add text report download button
                        st.download_button(
                            label="Download Text Report",
                            data=faculty_report,
                            file_name=text_filename,
                            mime="text/plain"
                        )
                        
                        # Add PDF report download button
                        pdf_buffer = generate_pdf_report(avg_ratings, course_name)
                        st.download_button(
                            label="Download PDF Report",
                            data=pdf_buffer,
                            file_name=pdf_filename,
                            mime="application/pdf"
                        )

                    with report_col2:
                        # Preview the report
                        st.text("Report Preview:")
                        st.text_area("", faculty_report, height=250)
                
            except Exception as e:
                st.error(f"⚠️ Error processing the file: {e}")
                st.exception(e)
                
    else:  # Analyze Processed Data
        # Clear session state when switching to the other mode
        if st.session_state.faculty_ratings_df is not None:
            st.session_state.faculty_ratings_df = None
            st.session_state.comments_df = None
            st.session_state.course_feedback_df = None
            st.session_state.avg_ratings = None
            
        # Upload File - Processed Data
        uploaded_file = st.file_uploader("Upload Processed Faculty Ratings (CSV or Excel)", type=["xlsx", "csv"])
        
        if uploaded_file is not None:
            try:
                # Read file
                if uploaded_file.name.endswith(".csv"):
                    df = pd.read_csv(uploaded_file, encoding="utf-8")
                else:
                    df = pd.read_excel(uploaded_file, engine="openpyxl")
                
                st.success("✅ File uploaded successfully!")
                
                # Display data sample
                with st.expander("Preview Data"):
                    st.dataframe(df.head())
                
                # Identify Faculty Name Column
                faculty_col = [col for col in df.columns if "faculty" in col.lower()]
                if not faculty_col:
                    st.error("❌ No Faculty Name column found! Check your file.")
                    st.stop()
                faculty_col = faculty_col[0]
                
                # Clean Faculty Names if not already cleaned
                if "Faculty Name" not in df.columns:
                    df["Faculty Name"] = df[faculty_col].astype(str).str.replace(r"Section[ -]?[A-Z]?[ -]?", "", regex=True).str.strip()
                
                # Drop rows with missing faculty names
                df = df.dropna(subset=["Faculty Name"])
                
                # Extract Rating Columns Dynamically
                rating_cols = [col for col in df.columns if any(x in col.lower() for x in ["course", "rating", "evaluation"])]
                if not rating_cols and "Rating Category" not in df.columns:
                    st.error("❌ No Rating columns found! Check your file.")
                    st.stop()
                
                # Process data if it's not already in the right format
                if "Rating Category" not in df.columns or "Rating" not in df.columns:
                    # Melt Data for Analysis
                    melted_df = df.melt(id_vars=["Faculty Name"], value_vars=rating_cols, var_name="Rating Category", value_name="Rating")
                    
                    # Fix Duplicate Questions: Normalize Category Names
                    melted_df["Rating Category"] = (
                        melted_df["Rating Category"]
                        .str.strip()
                        .str.lower()
                        .str.replace(r"\s+", " ", regex=True)
                        .str.split("(").str[0]
                        .str.strip()
                    )
                    
                    melted_df = melted_df.dropna(subset=["Rating"])
                    
                    # Convert Rating to Numeric
                    melted_df["Rating"] = pd.to_numeric(melted_df["Rating"], errors="coerce")
                    
                    # Compute Averages
                    avg_ratings = (
                        melted_df.groupby(["Faculty Name", "Rating Category"], as_index=False)
                        .agg({"Rating": "mean"})
                    )
                else:
                    # If data is already in the right format
                    avg_ratings = df
                
                # Store in session state
                st.session_state.avg_ratings = avg_ratings
                
                # Select Faculty
                faculties = avg_ratings["Faculty Name"].unique()
                
                if len(faculties) == 0:
                    st.error("❌ No faculty names detected! Please check your data.")
                    st.stop()
                
                selected_faculty = st.selectbox("🎓 Select a Faculty", faculties)
                
                # Filter Data for Selected Faculty
                faculty_data = avg_ratings[avg_ratings["Faculty Name"] == selected_faculty]
                
                # Select visualization type
                viz_type = st.radio(
                    "Choose Visualization Type:",
                    ["Bar Chart", "Table"],
                    horizontal=True
                )
                
                if viz_type == "Bar Chart":
                    # Plot Ratings
                    fig, ax = plt.subplots(figsize=(12, 8))  # Increased height from 6 to 8
                    bars = ax.bar(faculty_data["Rating Category"], faculty_data["Rating"], color="skyblue", width=0.6)  # Added width parameter

                    ax.set_title(f"📈 Average Ratings for {selected_faculty}", fontsize=14)
                    ax.set_xlabel("Rating Category", fontsize=12)
                    ax.set_ylabel("Average Rating (1-5)", fontsize=12)
                    ax.set_ylim(0, 5.5)  # Keep the same y-limit
                    plt.xticks(rotation=45, ha="right", fontsize=10)
                    
                    # Add labels on bars
                    for bar, category, rating in zip(bars, faculty_data["Rating Category"], faculty_data["Rating"]):
                        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f"{rating:.2f}", ha="center", va="bottom", fontsize=10)
                    
                    plt.tight_layout()
                    st.pyplot(fig)
                    
                    # Save figure option
                    save_fig_buffer = io.BytesIO()
                    fig.savefig(save_fig_buffer, format='png', dpi=300, bbox_inches='tight')
                    save_fig_buffer.seek(0)
                    
                    st.download_button(
                        label="Download Chart",
                        data=save_fig_buffer,
                        file_name=f"{selected_faculty}_ratings_chart.png",
                        mime="image/png"
                    )
                else:  # Table visualization
                    # Generate table visualization
                    table_fig = generate_table_visualization(faculty_data)
                    if table_fig:
                        st.pyplot(table_fig)
                        
                        # Save table figure option
                        table_buffer = io.BytesIO()
                        table_fig.savefig(table_buffer, format='png', dpi=300, bbox_inches='tight')
                        table_buffer.seek(0)
                        
                        st.download_button(
                            label="Download Table Image",
                            data=table_buffer,
                            file_name=f"{selected_faculty}_ratings_table.png",
                            mime="image/png"
                        )
                
                # Add horizontal line for visual separation
                st.markdown("---")
                
                # Generate text report for rating categories
                faculty_report = generate_faculty_report(faculty_data)

                # Create columns for layout
                report_col1, report_col2 = st.columns([1, 2])

                with report_col1:
                    # Add text report download button
                    st.download_button(
                        label="Download Text Report",
                        data=faculty_report,
                        file_name=f"{selected_faculty}_ratings_report.txt",
                        mime="text/plain"
                    )
                    
                    # Add PDF report download button
                    pdf_buffer = generate_pdf_report(faculty_data, "N/A")
                    st.download_button(
                        label="Download PDF Report",
                        data=pdf_buffer,
                        file_name=f"{selected_faculty}_ratings_report.pdf",
                        mime="application/pdf"
                    )

                with report_col2:
                    # Preview the report
                    st.text("Report Preview:")
                    st.text_area("", faculty_report, height=250)
                
            except Exception as e:
                st.error(f"⚠️ Error processing the file: {e}")
                st.exception(e)

with tab2:
    st.header("About This App")
    st.markdown("""
    ### Faculty Ratings Dashboard
    
    This app helps analyze and visualize faculty feedback data. It offers two main functions:
    
    1. **Process Raw Feedback Data**: Upload raw feedback forms and convert them into structured data
    2. **Analyze Processed Data**: Upload already processed faculty ratings data for visualization
    
    ### Features:
    
    - Clean and transform raw feedback data
    - Generate visualizations of faculty ratings (bar charts or tables)
    - Download processed data as Excel files
    - Download visualizations as PNG images
    - Create text reports with ratings information
    
    ### How to Use:
    
    1. Select the desired mode (Process Raw Data or Analyze Processed Data)
    2. Upload your data file (CSV or Excel format)
    3. Follow the on-screen instructions to process or visualize your data
    
    For raw data processing, the app will generate three datasets:
    - Faculty ratings
    - Student comments
    - Course feedback ratings
    
    Each dataset can be downloaded separately for further analysis.
    """)
