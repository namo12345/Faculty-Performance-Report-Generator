import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Streamlit App Title
st.title("📊 Faculty Ratings Dashboard")

# Upload File
uploaded_file = st.file_uploader("Upload Faculty Ratings File (CSV or Excel)", type=["xlsx", "csv"])

if uploaded_file is not None:
    try:
        # Read file with first row as headers
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file, encoding="utf-8")  # Ensure first row is used as header
        else:
            df = pd.read_excel(uploaded_file, sheet_name=None, engine="openpyxl")  # Load all sheets
            df = df[list(df.keys())[0]]  # Take first sheet

            # Ensure first row is used as headers
            df.columns = df.iloc[0]  # Set first row as column headers
            df = df[1:].reset_index(drop=True)  # Remove the first row from the data

        st.success("✅ File uploaded successfully!")

        # Identify Faculty Name Column Dynamically
        faculty_col = [col for col in df.columns if "faculty" in col.lower()]
        if not faculty_col:
            st.error("❌ No Faculty Name column found! Check your file.")
            st.stop()
        else:
            faculty_col = faculty_col[0]  # Use the first matching column

        # Clean Faculty Names
        df["Faculty Name"] = df[faculty_col].astype(str).str.replace(r"Section[ -]?[A-Z]?[ -]?", "", regex=True).str.strip()

        # Extract Rating Columns Dynamically
        rating_cols = [col for col in df.columns if "course" in col.lower() or "faculty" in col.lower()]
        if not rating_cols:
            st.error("❌ No Rating columns found! Check your file.")
            st.stop()

        # Melt Data for Analysis
        melted_df = df.melt(id_vars=["Faculty Name"], value_vars=rating_cols, var_name="Rating Category", value_name="Rating")

        # Clean Rating Category Names
        melted_df["Rating Category"] = melted_df["Rating Category"].str.split("(").str[0].str.strip()
        melted_df = melted_df.dropna(subset=["Rating"])  # Remove empty ratings

        # Convert Rating to Numeric
        melted_df["Rating"] = pd.to_numeric(melted_df["Rating"], errors="coerce")

        # Compute **Average** Ratings per Faculty & Category
        avg_ratings = melted_df.groupby(["Faculty Name", "Rating Category"])["Rating"].mean().reset_index()

        # Select Faculty
        faculties = avg_ratings["Faculty Name"].unique()
        selected_faculty = st.selectbox("🎓 Select a Faculty", faculties)

        # Filter Data for Selected Faculty
        faculty_data = avg_ratings[avg_ratings["Faculty Name"] == selected_faculty]

        # Plot Ratings
        fig, ax = plt.subplots(figsize=(12, 6))
        bars = ax.bar(faculty_data["Rating Category"], faculty_data["Rating"], color="skyblue")

        ax.set_title(f"📈 Average Ratings for {selected_faculty}", fontsize=14)
        ax.set_xlabel("Rating Category", fontsize=12)
        ax.set_ylabel("Average Rating (1-5)", fontsize=12)
        ax.set_ylim(0, 5.5)
        plt.xticks(rotation=45, ha="right", fontsize=10)

        # Add labels on bars (showing only **average** rating, not duplicate responses)
        for bar, category in zip(bars, faculty_data["Rating Category"]):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height, f"{height:.2f}", ha="center", va="bottom", fontsize=10)

        st.pyplot(fig)

    except Exception as e:
        st.error(f"⚠️ Error processing the file: {e}")
