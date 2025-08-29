import streamlit as st
import pandas as pd
import os
import math

class StudentDataAnalyser:
    def __init__(self):
        self.students_df = None
        self.branches = {}
        
        # Create output directories
        self.create_directories()
    
    def create_directories(self):
        """Create output directories if they don't exist"""
        directories = ['branch_files', 'branchwise_groups', 'uniform_groups']
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def load_data(self, uploaded_file):
        """Load student data from uploaded file"""
        try:
            if uploaded_file.name.endswith('.csv'):
                self.students_df = pd.read_csv(uploaded_file)
            else:
                self.students_df = pd.read_excel(uploaded_file)
            
            # Validate required columns
            required_cols = ['Roll', 'Name', 'Email']
            if not all(col in self.students_df.columns for col in required_cols):
                st.error(f"Missing required columns: {required_cols}")
                return False
            
            # Extract branches and create branch groups
            self.students_df['Branch'] = self.students_df['Roll'].str[4:6]
            
            # Group students by branch
            for branch in self.students_df['Branch'].unique():
                branch_students = self.students_df[self.students_df['Branch'] == branch].copy()
                self.branches[branch] = branch_students.sort_values('Name')
                
            return True
            
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            return False
    
    def save_branch_files(self):
        """Save individual branch CSV files"""
        saved_files = []
        
        for branch, students in self.branches.items():
            filename = f"branch_files/{branch}.csv"
            students[['Name', 'Roll', 'Email']].to_csv(filename, index=False)
            saved_files.append(filename)
            
        return saved_files
    
    def create_and_save_branchwise_groups(self, num_groups):
        """Create and save branch-wise mixed groups"""
        groups = [[] for _ in range(num_groups)]
        branch_names = sorted(self.branches.keys())
        
        # Round-robin assignment by branch
        current_group = 0
        for branch in branch_names:
            for _, student in self.branches[branch].iterrows():
                groups[current_group].append(student.to_dict())
                current_group = (current_group + 1) % num_groups
        
        # Save group files
        saved_files = []
        for i, group in enumerate(groups):
            if group:
                filename = f"branchwise_groups/G{i+1}.csv"
                group_df = pd.DataFrame(group)
                group_df[['Name', 'Roll', 'Email']].to_csv(filename, index=False)
                saved_files.append(filename)
        
        # Save statistics
        stats_file = self.save_statistics(groups, "branchwise_groups/stats_branchwise.csv")
        saved_files.append(stats_file)
        
        return saved_files, groups
    
    def create_and_save_uniform_groups(self, num_groups):
        """Create and save uniform mixed groups"""
        groups = [[] for _ in range(num_groups)]
        
        # Sort branches by size (largest first)
        sorted_branches = sorted(self.branches.items(), key=lambda x: len(x[1]), reverse=True)
        
        # Calculate target group size
        total_students = sum(len(students) for students in self.branches.values())
        target_size = math.ceil(total_students / num_groups)
        
        current_group = 0
        for branch_name, students in sorted_branches:
            for _, student in students.iterrows():
                # Move to next group if current is full (except last group)
                if len(groups[current_group]) >= target_size and current_group < num_groups - 1:
                    current_group += 1
                groups[current_group].append(student.to_dict())
        
        # Save group files
        saved_files = []
        for i, group in enumerate(groups):
            if group:
                filename = f"uniform_groups/G{i+1}.csv"
                group_df = pd.DataFrame(group)
                group_df[['Name', 'Roll', 'Email']].to_csv(filename, index=False)
                saved_files.append(filename)
        
        # Save statistics
        stats_file = self.save_statistics(groups, "uniform_groups/stats_uniform.csv")
        saved_files.append(stats_file)
        
        return saved_files, groups
    
    def save_statistics(self, groups, filename):
        """Save statistics file"""
        stats_data = []
        branch_names = sorted(self.branches.keys())
        
        # Create header
        header = ['Group'] + branch_names + ['Total']
        
        # Calculate stats for each group
        for i, group in enumerate(groups):
            if group:
                row = [f"G{i+1}"]
                group_df = pd.DataFrame(group)
                
                total = 0
                for branch in branch_names:
                    count = len(group_df[group_df['Branch'] == branch])
                    row.append(count)
                    total += count
                
                row.append(total)
                stats_data.append(row)
        
        # Save statistics
        stats_df = pd.DataFrame(stats_data, columns=header)
        stats_df.to_csv(filename, index=False)
        
        return filename

def main():
    st.set_page_config(
        page_title="Student Data Analyser",
        layout="wide"
    )
    
    st.title("🎓 Student Data Analyser")
    st.markdown("Upload student data and automatically save groups to local folders")
    
    # Initialize grouping system
    if 'grouping' not in st.session_state:
        st.session_state.grouping = StudentDataAnalyser()
    
    # File upload section
    st.subheader(" Upload Student Data")
    uploaded_file = st.file_uploader(
        "Choose Excel or CSV file",
        type=['xlsx', 'xls', 'csv']
    )
    
    if uploaded_file:
        if st.session_state.grouping.load_data(uploaded_file):
            st.success(" Data loaded successfully!")
            
            # Show data summary
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Summary")
                st.metric("Total Students", len(st.session_state.grouping.students_df))
                st.metric("Total Branches", len(st.session_state.grouping.branches))
            
            with col2:
                st.subheader("🏫 Branches")
                for branch in sorted(st.session_state.grouping.branches.keys()):
                    count = len(st.session_state.grouping.branches[branch])
                    st.write(f"**{branch}**: {count} students")
            
            # Group settings
            st.subheader("⚙️ Group Settings")
            num_groups = st.number_input("Number of Groups", min_value=2, max_value=20, value=5)
            
            # Processing buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("💾 Save Branch Files", type="primary"):
                    with st.spinner("Saving branch files..."):
                        saved_files = st.session_state.grouping.save_branch_files()
                        st.success(f"✅ Saved {len(saved_files)} branch files to `branch_files/` folder")
                        for file in saved_files:
                            st.write(f"📄 {file}")
            
            with col2:
                if st.button("🔄 Create Branch-wise Groups", type="primary"):
                    with st.spinner("Creating branch-wise groups..."):
                        saved_files, groups = st.session_state.grouping.create_and_save_branchwise_groups(num_groups)
                        st.success(f"✅ Saved {len(saved_files)} files to `branchwise_groups/` folder")
                        
                        # Show group summary
                        st.write("**Group Summary:**")
                        for i, group in enumerate(groups):
                            if group:
                                group_df = pd.DataFrame(group)
                                branch_dist = group_df['Branch'].value_counts()
                                st.write(f"G{i+1}: {len(group)} students - {dict(branch_dist)}")
            
            with col3:
                if st.button("📊 Create Uniform Groups", type="primary"):
                    with st.spinner("Creating uniform groups..."):
                        saved_files, groups = st.session_state.grouping.create_and_save_uniform_groups(num_groups)
                        st.success(f"✅ Saved {len(saved_files)} files to `uniform_groups/` folder")
                        
                        # Show group summary
                        st.write("**Group Summary:**")
                        for i, group in enumerate(groups):
                            if group:
                                group_df = pd.DataFrame(group)
                                branch_dist = group_df['Branch'].value_counts()
                                st.write(f"G{i+1}: {len(group)} students - {dict(branch_dist)}")
    
    # Information section
    st.subheader("📂 Output Folder Structure")
    st.code("""
project_folder/
├── student_grouping_app.py
├── requirements.txt
├── branch_files/          # Individual branch CSV files
│   ├── AI.csv
│   ├── CB.csv
│   └── ...
├── branchwise_groups/     # Branch-wise mixed groups
│   ├── G1.csv
│   ├── G2.csv
│   ├── ...
│   └── stats_branchwise.csv
└── uniform_groups/        # Uniform mixed groups
    ├── G1.csv
    ├── G2.csv
    ├── ...
    └── stats_uniform.csv
    """)

    # Instructions
    with st.expander("📋 How to Use"):
        st.markdown("""
        ### Steps:
        1. **Upload** your Excel/CSV file with student data
        2. **Set** the number of groups you want
        3. **Click** the processing buttons:
           - Save Branch Files: Creates individual files per branch
           - Create Branch-wise Groups: Round-robin mixing by branch
           - Create Uniform Groups: Sequential filling by branch size
        
        ### File Locations:
        - All files are automatically saved to respective folders in your project directory
        - No manual downloads needed - files appear directly on your local system
        - Each processing creates files in separate folders for organization
        
        ### Input Requirements:
        - File must contain: **Roll**, **Name**, **Email** columns
        - Roll number format: Characters 5-6 = branch code (e.g., "1401AI01")
        """)

if __name__ == "__main__":
    main()