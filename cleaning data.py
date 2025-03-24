
import pandas as pd
import numpy as np

# Load the data
# Note: You'll need to save your data as a CSV or Excel file first
file_path = 'feedback-raw data.csv'  # Change this to your file path
df = pd.read_csv(file_path)

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

# Helper function to identify which columns belong to which course/faculty
def identify_course_columns(columns):
    course_blocks = []
    current_block = []
    current_course = None

    for i, col in enumerate(columns):
        if col.startswith('Feedback on '):
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

# Get the course blocks
course_blocks = identify_course_columns(df.columns)

# Process each row
for index, row in df.iterrows():
    student_name = row['Name of the Student']
    srn = row['SRN']
    section = row['Section']

    if pd.isna(student_name) or pd.isna(srn):
        continue

    # Process each course block
    for course_name, column_indices in course_blocks:
        # Find faculty name column
        faculty_col = [i for i in column_indices if 'Name of the Faculty' in df.columns[i]]
        if not faculty_col:
            continue

        faculty_name = row[df.columns[faculty_col[0]]]

        # Find question columns
        question_cols = [i for i in column_indices if 'Please give a rating' in df.columns[i]]

        # Process each question
        for q_col in question_cols:
            question = df.columns[q_col]
            rating = row[df.columns[q_col]]

            if not pd.isna(rating):
                student_names.append(student_name)
                srns.append(srn)
                sections.append(section)
                faculty_names.append(faculty_name)
                courses.append(course_name)
                rating_types.append(question)
                ratings.append(rating)

        # Get comments if available
        comment_col = [i for i in column_indices if df.columns[i] == 'Comments']
        if comment_col:
            comment = row[df.columns[comment_col[0]]]
            comments.append({
                'Student': student_name,
                'SRN': srn,
                'Faculty': faculty_name,
                'Course': course_name,
                'Comment': comment
            })

        # Get course feedback questions
        course_feedback_cols = [i for i in column_indices if 'The course' in df.columns[i]]
        for cf_col in course_feedback_cols:
            question = df.columns[cf_col]
            rating = row[df.columns[cf_col]]

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

# Save the transformed data
faculty_ratings_df.to_excel('faculty_ratings.xlsx', index=False)
comments_df.to_excel('student_comments.xlsx', index=False)
course_feedback_df.to_excel('course_feedback_ratings.xlsx', index=False)

print("Transformation complete!")
print(f"- Faculty ratings: {len(faculty_ratings_df)} records")
print(f"- Student comments: {len(comments_df)} records")
print(f"- Course feedback ratings: {len(course_feedback_df)} records")
