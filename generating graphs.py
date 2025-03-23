import pandas as pd
import matplotlib.pyplot as plt

# Load the Excel file
df = pd.read_excel('faculty_ratings.xlsx', sheet_name='Sheet1')

# Clean the "Faculty Name" column to remove section details
df['Faculty Name'] = df['Faculty Name'].str.replace(r'^Section[ -]A[ -]', '', regex=True)

# Clean the "Rating Category" column (remove text after parentheses)
df['Rating Category'] = df['Rating Category'].str.split('(').str[0].str.strip()

# Calculate average ratings for each faculty and category
avg_ratings = df.groupby(['Faculty Name', 'Rating Category'])['Rating'].mean().reset_index()

# Get unique faculty names
faculties = avg_ratings['Faculty Name'].unique()

# Generate a graph for each faculty
for faculty in faculties:
    # Filter data for the current faculty
    faculty_data = avg_ratings[avg_ratings['Faculty Name'] == faculty]
    
    # Create the plot
    plt.figure(figsize=(15, 8))
    bars = plt.bar(faculty_data['Rating Category'], faculty_data['Rating'], color='skyblue')
    
    # Add labels and title
    plt.title(f'Average Ratings for {faculty}', fontsize=16)
    plt.xlabel('Rating Category', fontsize=12)
    plt.ylabel('Average Rating (1-5)', fontsize=12)
    plt.ylim(0, 5.5)
    
    # Rotate x-axis labels for readability
    plt.xticks(rotation=45, ha='right', fontsize=10)
    
    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, height, 
                 f'{height:.2f}', ha='center', va='bottom', fontsize=10)
    
    # Adjust layout and save the plot
    plt.tight_layout()
    plt.savefig(f'{faculty}_ratings.png', dpi=300)  # Save as image
    plt.show()  # Display the plot
