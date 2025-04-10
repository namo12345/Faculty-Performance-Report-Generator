import pandas as pd
import matplotlib.pyplot as plt

# Load the Excel file
df = pd.read_excel('faculty_ratings (1).xlsx', sheet_name='Sheet1')

# Split Faculty Name into Section and Faculty
df['Section'] = df['Faculty Name'].str.extract(r'^Section\s*([A-Za-z0-9]+)-', expand=False).fillna('')
df['Faculty Name'] = df['Faculty Name'].str.replace(r'^Section\s*[A-Za-z0-9]+-', '', regex=True).str.strip()

# Clean Rating Category
df['Rating Category'] = df['Rating Category'].str.split('(').str[0].str.strip()

# Calculate average ratings by Section and Faculty
avg_ratings = df.groupby(['Section', 'Faculty Name', 'Rating Category'])['Rating'].mean().reset_index()

# Generate reports for each Section-Faculty combination
for (section, faculty), group in avg_ratings.groupby(['Section', 'Faculty Name']):
    # Filter data for current section-faculty
    faculty_data = avg_ratings[
        (avg_ratings['Section'] == section) & 
        (avg_ratings['Faculty Name'] == faculty)
    ]
    
    # Create the plot
    plt.figure(figsize=(15, 8))
    bars = plt.bar(faculty_data['Rating Category'], faculty_data['Rating'], color='skyblue')
    
    # Add labels and title
    plt.title(f'Average Ratings for {section} - {faculty}', fontsize=16)
    plt.xlabel('Rating Category', fontsize=12)
    plt.ylabel('Average Rating (1-5)', fontsize=12)
    plt.ylim(0, 5.5)
    
    # Rotate x-axis labels
    plt.xticks(rotation=45, ha='right', fontsize=10)
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, height,
                 f'{height:.2f}', ha='center', va='bottom', fontsize=10)
    
    # Save and display the plot
    plt.tight_layout()
    plt.savefig(f'Section_{section}_{faculty}_ratings.png', dpi=300)
    plt.show()
