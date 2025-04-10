import pandas as pd
import matplotlib.pyplot as plt

# Load main feedback data
feedback_df = pd.read_excel('/content/faculty_ratings (1).xlsx')

# Load course code mapping
course_codes_df = pd.read_excel('/content/course_codes.xlsx')

# Extract section and clean faculty name
feedback_df['Section'] = feedback_df['Faculty Name'].str.extract(r'^Section\s*(\w+)-', expand=False).fillna('')
feedback_df['Faculty Name'] = (
    feedback_df['Faculty Name']
    .str.replace(r'^Section\s*\w+-', '', regex=True)
    .str.strip()
)

# Standardize faculty titles (remove periods)
feedback_df['Faculty Name'] = (
    feedback_df['Faculty Name']
    .str.replace(r'\.', '', regex=True)  # Remove periods in titles (e.g., "Dr." → "Dr")
    .str.replace(r'\s+', '_', regex=True)  # Replace spaces with underscores
)

# Clean course names in both datasets
feedback_df['Course'] = feedback_df['Course'].str.replace(r'^Feedback on\s+', '', regex=True).str.strip()
course_codes_df['Course'] = course_codes_df['Course'].str.strip()

# Merge course codes into main data
merged_df = pd.merge(feedback_df, 
                     course_codes_df[['Course', 'Course Code']], 
                     on='Course', 
                     how='left')

# Handle missing course codes
merged_df['Course Code'] = merged_df['Course Code'].fillna('N/A')

# Clean rating categories
merged_df['Rating Category'] = (
    merged_df['Rating Category']
    .str.split('(', n=1, expand=True)[0]
    .str.replace(r'\.\d+$', '', regex=True)
    .str.strip()
)

# Group data by Section, Faculty Name, and Rating Category
section_faculty_data = merged_df.groupby(['Section', 'Faculty Name', 'Rating Category'])['Rating'].mean().round(4).reset_index()

# Create individual PNG images for each section-faculty combination
for (section, faculty), group in section_faculty_data.groupby(['Section', 'Faculty Name']):
    # Filter data for current section-faculty
    section_df = section_faculty_data[
        (section_faculty_data['Section'] == section) & 
        (section_faculty_data['Faculty Name'] == faculty)
    ]
    
    # Calculate total average
    total_avg = section_df['Rating'].mean().round(4)
    
    # Create new row for total average
    new_row = pd.DataFrame({
        'Rating Category': ['Total Average'],
        'Rating': [total_avg]
    })
    
    # Append total average row
    section_df = pd.concat([section_df, new_row], ignore_index=True)
    
    # Prepare table data
    headers = ['Rating Category', 'Average Rating']
    data = section_df[['Rating Category', 'Rating']].values.tolist()
    
    # Get unique courses and codes for section-faculty
    section_courses = merged_df[
        (merged_df['Section'] == section) & 
        (merged_df['Faculty Name'] == faculty)
    ]
    courses = section_courses['Course'].drop_duplicates().tolist()
    codes = section_courses['Course Code'].drop_duplicates().tolist()
    
    # Add course and code rows
    data.insert(0, ['Course Codes:', ', '.join(codes)])
    data.insert(0, ['Courses Taught:', ', '.join(courses)])
    
    # Create figure and axis with increased size
    fig, ax = plt.subplots(figsize=(20, 15))  # Larger canvas
    ax.axis('off')  # Hide axes
    
    # Create table with adjusted column widths
    table = ax.table(
        cellText=data,
        colLabels=headers,
        loc='center',
        cellLoc='left',
        colWidths=[0.7, 0.3]  # Adjusted for single-line display
    )
    
    # Set font size and padding
    table.auto_set_font_size(False)
    table.set_fontsize(16)
    table.scale(1.8, 2.2)  # Increased scaling
    
    # Generate consistent filename
    filename = f"{section}-{faculty}_ratings.png"
    plt.savefig(filename, bbox_inches='tight', dpi=300)
    plt.close()

print("PNG images created successfully!")
