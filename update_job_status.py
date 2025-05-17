import pandas as pd
import os
import glob
from datetime import datetime

def get_latest_job_file():
    """Get the most recent job tracking CSV file"""
    files = glob.glob("job_tracker/data/*.csv")
    if not files:
        print("No job tracking files found.")
        return None
    
    # Sort files by modification time (newest first)
    latest_file = max(files, key=os.path.getmtime)
    return latest_file

def update_job_status(job_id, status, date_applied=None, resume_link=None, notes=None):
    """Update the status and other information for a specific job"""
    file_path = get_latest_job_file()
    if not file_path:
        return False
    
    try:
        # Load the CSV file
        df = pd.read_csv(file_path)
        
        # Find the job by ID
        if job_id not in df['job_id'].values:
            print(f"Job ID {job_id} not found in the file.")
            return False
        
        # Update the job information
        df.loc[df['job_id'] == job_id, 'status'] = status
        
        if date_applied:
            df.loc[df['job_id'] == job_id, 'date_applied'] = date_applied
        else:
            # If status is 'Applied' and no date is provided, use today's date
            if status == 'Applied':
                df.loc[df['job_id'] == job_id, 'date_applied'] = datetime.now().strftime("%Y-%m-%d")
        
        if resume_link:
            df.loc[df['job_id'] == job_id, 'resume_link'] = resume_link
        
        # Add notes column if it doesn't exist
        if notes and 'notes' not in df.columns:
            df['notes'] = None
        
        if notes:
            df.loc[df['job_id'] == job_id, 'notes'] = notes
        
        # Save the updated file
        df.to_csv(file_path, index=False)
        print(f"Updated job {job_id} status to '{status}'")
        return True
    
    except Exception as e:
        print(f"Error updating job status: {e}")
        return False

def list_jobs(status=None):
    """List jobs, optionally filtered by status"""
    file_path = get_latest_job_file()
    if not file_path:
        return
    
    try:
        # Load the CSV file
        df = pd.read_csv(file_path)
        
        # Filter by status if provided
        if status:
            filtered_df = df[df['status'] == status]
        else:
            filtered_df = df
        
        if filtered_df.empty:
            print(f"No jobs found{' with status ' + status if status else ''}.")
            return
        
        # Display jobs
        display_columns = ['job_id', 'company', 'job_title', 'status', 'date_applied', 'type', 'email']
        display_columns = [col for col in display_columns if col in filtered_df.columns]
        
        print(f"\nJobs{' with status ' + status if status else ''}:")
        print(filtered_df[display_columns])
        print(f"\nTotal: {len(filtered_df)} jobs")
    
    except Exception as e:
        print(f"Error listing jobs: {e}")

if __name__ == "__main__":
    # Example usage
    print("Job Application Status Updater")
    print("1. List all jobs")
    print("2. List jobs by status")
    print("3. Update job status")
    
    choice = input("Enter your choice (1-3): ")
    
    if choice == '1':
        list_jobs()
    
    elif choice == '2':
        status = input("Enter status to filter by (e.g., Applied, Not Applied): ")
        list_jobs(status)
    
    elif choice == '3':
        job_id = input("Enter job ID to update: ")
        print("\nSelect new status:")
        print("1. Applied")
        print("2. Interview Scheduled")
        print("3. Rejected")
        print("4. Offer Received")
        print("5. Custom status")
        
        status_choice = input("Enter your choice (1-5): ")
        
        status_map = {
            '1': 'Applied',
            '2': 'Interview Scheduled',
            '3': 'Rejected',
            '4': 'Offer Received'
        }
        
        if status_choice in status_map:
            status = status_map[status_choice]
        else:
            status = input("Enter custom status: ")
        
        date_applied = input("Enter date applied (YYYY-MM-DD) or leave blank for today: ")
        resume_link = input("Enter resume link (optional): ")
        notes = input("Enter any notes (optional): ")
        
        update_job_status(job_id, status, date_applied, resume_link, notes)
    
    else:
        print("Invalid choice.")