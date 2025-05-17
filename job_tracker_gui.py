import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import os
import sys
from datetime import datetime
import webbrowser
from linkedin_job_tracker import LinkedInJobTracker

class JobTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LinkedIn Job Application Tracker")
        self.root.geometry("1200x700")
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.search_tab = ttk.Frame(self.notebook)
        self.track_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.search_tab, text="Search Jobs")
        self.notebook.add(self.track_tab, text="Track Applications")
        
        # Setup search tab
        self.setup_search_tab()
        
        # Setup track tab
        self.setup_track_tab()
        
        # Load existing data if available
        self.current_file = None
        self.load_latest_file()
    
    def setup_search_tab(self):
        # Create frame for search options
        search_frame = ttk.LabelFrame(self.search_tab, text="Search LinkedIn Jobs", padding="10")
        search_frame.pack(fill=tk.X, padx=10, pady=10)
    
        # Job title
        ttk.Label(search_frame, text="Job Title:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.job_title_var = tk.StringVar(value="Python Developer")
        ttk.Entry(search_frame, textvariable=self.job_title_var, width=30).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
    
        # Location
        ttk.Label(search_frame, text="Location:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.location_var = tk.StringVar(value="Toronto")
        ttk.Entry(search_frame, textvariable=self.location_var, width=30).grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
    
        # Job type
        ttk.Label(search_frame, text="Job Type:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.job_type_var = tk.StringVar()
        job_type_combo = ttk.Combobox(search_frame, textvariable=self.job_type_var, width=28)
        job_type_combo['values'] = ('Any', 'Full-time', 'Part-time', 'Contract', 'Internship')
        job_type_combo.current(0)
        job_type_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
    
        # Number of pages
        ttk.Label(search_frame, text="Pages to Scrape:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.pages_var = tk.IntVar(value=2)
        ttk.Spinbox(search_frame, from_=1, to=10, textvariable=self.pages_var, width=5).grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)

        # Add job age filter
        ttk.Label(search_frame, text="Job Age Filter:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.age_filter_var = tk.StringVar()
        age_filter_combo = ttk.Combobox(search_frame, textvariable=self.age_filter_var, width=28)
        age_filter_combo['values'] = ('Any Time', 'Past 24 Hours', 'Past Week', 'Past Month')
        age_filter_combo.current(0)
        age_filter_combo.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
    
        # Search button - FIX: Move to a more visible position and make it more prominent
        search_button = ttk.Button(search_frame, text="Search Jobs", command=self.search_jobs)
        search_button.grid(row=2, column=2, columnspan=2, sticky=tk.W, padx=5, pady=5)
    
        # Progress bar and status
        self.progress_var = tk.DoubleVar()
        ttk.Progressbar(search_frame, variable=self.progress_var, maximum=100).grid(row=4, column=0, columnspan=4, sticky=tk.EW, padx=5, pady=5)
    
        self.status_var = tk.StringVar(value="Ready to search")
        ttk.Label(search_frame, textvariable=self.status_var).grid(row=5, column=0, columnspan=4, sticky=tk.W, padx=5, pady=5)
    
    def setup_track_tab(self):
        # Create frame for job list
        list_frame = ttk.LabelFrame(self.track_tab, text="Job Applications", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
        # Create toolbar
        toolbar = ttk.Frame(list_frame)
        toolbar.pack(fill=tk.X, pady=5)
    
        # Filter by status
        ttk.Label(toolbar, text="Filter by Status:").pack(side=tk.LEFT, padx=5)
        self.filter_var = tk.StringVar()
        filter_combo = ttk.Combobox(toolbar, textvariable=self.filter_var, width=15)
        filter_combo['values'] = ('All', 'Applied', 'Not Applied', 'Interview Scheduled', 'Rejected', 'Offer Received')
        filter_combo.current(0)
        filter_combo.pack(side=tk.LEFT, padx=5)
        filter_combo.bind('<<ComboboxSelected>>', self.filter_jobs)
    
        # Refresh button
        ttk.Button(toolbar, text="Refresh", command=self.refresh_job_list).pack(side=tk.LEFT, padx=5)
    
        # Load file button
        ttk.Button(toolbar, text="Load File", command=self.load_file).pack(side=tk.LEFT, padx=5)

        ttk.Button(toolbar, text="Remove Old Jobs", 
          command=lambda: self.filter_by_age(30)).pack(side=tk.LEFT, padx=5)
    
        # Create treeview for job list
        columns = ('job_id', 'company', 'job_title', 'status', 'date_applied', 'deadline', 'type', 'contact_person', 'email', 'application_link')
        self.job_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
    
        # Define headings
        self.job_tree.heading('job_id', text='ID')
        self.job_tree.heading('company', text='Company')
        self.job_tree.heading('job_title', text='Job Title')
        self.job_tree.heading('status', text='Status')
        self.job_tree.heading('date_applied', text='Date Applied')
        self.job_tree.heading('deadline', text='Deadline')
        self.job_tree.heading('type', text='Job Type')
        self.job_tree.heading('contact_person', text='Contact Person')
        self.job_tree.heading('email', text='Email')
        self.job_tree.heading('application_link', text='Application Link')
    
        # Define columns width
        self.job_tree.column('job_id', width=80)
        self.job_tree.column('company', width=150)
        self.job_tree.column('job_title', width=200)
        self.job_tree.column('status', width=100)
        self.job_tree.column('date_applied', width=100)
        self.job_tree.column('deadline', width=100)
        self.job_tree.column('type', width=100)
        self.job_tree.column('contact_person', width=150)
        self.job_tree.column('email', width=200)
        self.job_tree.column('application_link', width=200)
    
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.job_tree.yview)
        self.job_tree.configure(yscroll=scrollbar.set)
    
        # Add horizontal scrollbar for wide content
        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.job_tree.xview)
        self.job_tree.configure(xscroll=h_scrollbar.set)
    
        # Pack treeview and scrollbars
        self.job_tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
        # Bind double-click event
        self.job_tree.bind('<Double-1>', self.open_job_details)
    
        # Create right-click menu
        self.context_menu = tk.Menu(self.job_tree, tearoff=0)
        self.context_menu.add_command(label="Update Status", command=self.update_job_status)
        self.context_menu.add_command(label="Open Application Link", command=self.open_application_link)
        self.context_menu.add_command(label="Copy Email", command=self.copy_email)
        self.job_tree.bind('<Button-3>', self.show_context_menu)
    
    def search_jobs(self):
        """Search for jobs on LinkedIn"""
        job_title = self.job_title_var.get()
        location = self.location_var.get()
        job_type = self.job_type_var.get()
        pages = self.pages_var.get()
        age_filter = self.age_filter_var.get()

        # Convert age filter to days
        max_age_days = None
        if age_filter == 'Past 24 Hours':
            max_age_days = 1
        elif age_filter == 'Past Week':
            max_age_days = 7
        elif age_filter == 'Past Month':
            max_age_days = 30
        
        if not job_title or not location:
            messagebox.showerror("Error", "Job title and location are required")
            return
        
        # Update status
        self.status_var.set(f"Searching for {job_title} jobs in {location}...")
        self.progress_var.set(10)
        self.root.update()
        
        try:
            # Create job tracker
            job_type_map = {
                'Full-time': 'F',
                'Part-time': 'P',
                'Contract': 'C',
                'Internship': 'I'
            }
            
            job_type_param = job_type_map.get(job_type) if job_type != 'Any' else None
            
            tracker = LinkedInJobTracker(
                job_title=job_title,
                location=location,
                job_type=job_type_param
            )
            
            # Update status
            self.status_var.set("Collecting job IDs...")
            self.progress_var.set(30)
            self.root.update()
            
            # Search for jobs
            job_ids = tracker.search_jobs(num_pages=pages, max_age_days=max_age_days)
            
            # Update status
            self.status_var.set(f"Found {len(job_ids)} jobs. Extracting details...")
            self.progress_var.set(60)
            self.root.update()
            
            # Extract job details
            tracker.extract_job_details(job_ids)
            
            # Save to CSV
            self.status_var.set("Saving job data...")
            self.progress_var.set(90)
            self.root.update()
            
            csv_file = tracker.save_to_csv()
            
            # Update status
            self.status_var.set(f"Completed! Saved {len(tracker.job_list)} jobs to {csv_file}")
            self.progress_var.set(100)
            
            # Load the new file
            self.current_file = csv_file
            self.load_job_data()
            
            # Switch to track tab
            self.notebook.select(1)
            
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def load_latest_file(self):
        """Load the most recent job tracking CSV file"""
        try:
            files = os.listdir("job_tracker/data")
            csv_files = [f for f in files if f.endswith('.csv')]
            
            if not csv_files:
                self.status_var.set("No job tracking files found")
                return
            
            # Sort files by modification time (newest first)
            csv_files.sort(key=lambda x: os.path.getmtime(os.path.join("job_tracker/data", x)), reverse=True)
            
            self.current_file = os.path.join("job_tracker/data", csv_files[0])
            self.load_job_data()
            
        except Exception as e:
            self.status_var.set(f"Error loading file: {str(e)}")
    
    def load_file(self):
        """Open file dialog to load a CSV file"""
        file_path = filedialog.askopenfilename(
            initialdir="job_tracker/data",
            title="Select Job Tracking File",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*"))
        )
        
        if file_path:
            self.current_file = file_path
            self.load_job_data()
    
    def load_job_data(self):
        """Load job data from the current file"""
        if not self.current_file or not os.path.exists(self.current_file):
            return
        
        try:
            # Clear existing data
            for item in self.job_tree.get_children():
                self.job_tree.delete(item)
            
            # Load the CSV file
            df = pd.read_csv(self.current_file)
            
            # Update status
            self.status_var.set(f"Loaded {len(df)} jobs from {os.path.basename(self.current_file)}")
            
            # Insert data into treeview
            for _, row in df.iterrows():
                values = []
                for col in self.job_tree['columns']:
                    if col in row:
                        values.append(row[col])
                    else:
                        values.append("")
                
                self.job_tree.insert('', tk.END, values=values)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error loading job data: {str(e)}")
    
    def filter_jobs(self, event=None):
        """Filter jobs by status"""
        if not self.current_file:
            return
        
        try:
            # Clear existing data
            for item in self.job_tree.get_children():
                self.job_tree.delete(item)
            
            # Load the CSV file
            df = pd.read_csv(self.current_file)
            
            # Filter by status
            status = self.filter_var.get()
            if status != 'All':
                df = df[df['status'] == status]
            
            # Insert data into treeview
            for _, row in df.iterrows():
                values = []
                for col in self.job_tree['columns']:
                    if col in row:
                        values.append(row[col])
                    else:
                        values.append("")
                
                self.job_tree.insert('', tk.END, values=values)
            
            # Update status
            self.status_var.set(f"Showing {len(df)} jobs with status '{status}'")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error filtering jobs: {str(e)}")
    
    def refresh_job_list(self):
        """Refresh the job list"""
        self.load_job_data()

    def filter_by_age(self, max_days=30):
        """Filter out jobs older than max_days"""
        if not self.current_file:
            messagebox.showinfo("Info", "No job data loaded")
            return
        
        try:
            # Load the CSV file
            df = pd.read_csv(self.current_file)
            
            if 'posting_date' not in df.columns and 'time_posted' in df.columns:
                # Try to parse posting dates from time_posted
                df['posting_date'] = None
                for idx, row in df.iterrows():
                    if pd.notna(row['time_posted']):
                        # Create a temporary tracker to use the parsing method
                        temp_tracker = LinkedInJobTracker("", "")
                        date = temp_tracker._parse_posting_date(row['time_posted'])
                        if date:
                            df.at[idx, 'posting_date'] = date
            
            if 'posting_date' not in df.columns:
                messagebox.showinfo("Info", "Cannot filter by age: posting dates not available")
                return
            
            # Convert posting_date to datetime
            df['posting_date'] = pd.to_datetime(df['posting_date'])
            
            # Calculate job age in days
            today = pd.Timestamp(datetime.now().date())
            df['age_days'] = (today - df['posting_date']).dt.days
            
            # Filter jobs
            old_count = len(df[df['age_days'] > max_days])
            df_filtered = df[df['age_days'] <= max_days]
            
            if len(df_filtered) == len(df):
                messagebox.showinfo("Info", f"No jobs older than {max_days} days found")
                return
            
            # Ask for confirmation
            if messagebox.askyesno("Confirm", f"Remove {old_count} jobs older than {max_days} days?"):
                # Save the filtered data
                df_filtered.to_csv(self.current_file, index=False)
                messagebox.showinfo("Success", f"Removed {old_count} old job listings")
                
                # Refresh the job list
                self.load_job_data()

        except Exception as e:
            messagebox.showerror("Error", f"Error filtering jobs: {str(e)}")
    
    def open_job_details(self, event):
        """Open job details dialog when double-clicking a job"""
        item = self.job_tree.selection()[0]
        job_values = self.job_tree.item(item, 'values')
        
        if not job_values:
            return
        
        # Create details window
        details_window = tk.Toplevel(self.root)
        details_window.title(f"Job Details: {job_values[2]} at {job_values[1]}")
        details_window.geometry("600x500")
        
        # Load full job data
        try:
            df = pd.read_csv(self.current_file)
            job_id = job_values[0]
            job_data = df[df['job_id'] == job_id].iloc[0]
            
            # Create scrollable frame
            main_frame = ttk.Frame(details_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            canvas = tk.Canvas(main_frame)
            scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
            
            scrollable_frame = ttk.Frame(canvas)
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Add job details
            row = 0
            for col in df.columns:
                if col != 'description':  # Display description separately
                    ttk.Label(scrollable_frame, text=f"{col.replace('_', ' ').title()}:", font=('', 10, 'bold')).grid(
                        row=row, column=0, sticky=tk.W, padx=5, pady=2)
                    
                    value = str(job_data[col]) if pd.notna(job_data[col]) else ""
                    ttk.Label(scrollable_frame, text=value, wraplength=400).grid(
                        row=row, column=1, sticky=tk.W, padx=5, pady=2)
                    
                    row += 1
            
            # Add description if available
            if 'description' in df.columns and pd.notna(job_data['description']):
                ttk.Label(scrollable_frame, text="Description:", font=('', 10, 'bold')).grid(
                    row=row, column=0, sticky=tk.NW, padx=5, pady=2)
                
                description_text = tk.Text(scrollable_frame, wrap=tk.WORD, width=50, height=15)
                description_text.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
                description_text.insert(tk.END, job_data['description'])
                description_text.config(state=tk.DISABLED)
            
            # Add buttons
            button_frame = ttk.Frame(details_window)
            button_frame.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Button(button_frame, text="Update Status", 
                      command=lambda: self.update_job_status(job_id=job_id)).pack(side=tk.LEFT, padx=5)
            
            if pd.notna(job_data['application_link']):
                ttk.Button(button_frame, text="Open Application Link", 
                          command=lambda: webbrowser.open(job_data['application_link'])).pack(side=tk.LEFT, padx=5)
            
            if pd.notna(job_data['email']):
                ttk.Button(button_frame, text="Copy Email", 
                          command=lambda: self.copy_to_clipboard(job_data['email'])).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(button_frame, text="Close", 
                      command=details_window.destroy).pack(side=tk.RIGHT, padx=5)
            
        except Exception as e:
            ttk.Label(details_window, text=f"Error loading job details: {str(e)}").pack(padx=10, pady=10)
    
    def update_job_status(self, event=None, job_id=None):
        """Update job status"""
        if not job_id:
            # Get selected job
            selection = self.job_tree.selection()
            if not selection:
                messagebox.showinfo("Info", "Please select a job to update")
                return
        
            item = selection[0]
            job_values = self.job_tree.item(item, 'values')
            job_id = job_values[0]
    
        # Create update window
        update_window = tk.Toplevel(self.root)
        update_window.title("Update Job Status")
        update_window.geometry("500x400")
    
        # Status
        ttk.Label(update_window, text="Status:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        status_var = tk.StringVar()
        status_combo = ttk.Combobox(update_window, textvariable=status_var, width=20)
        status_combo['values'] = ('Applied', 'Not Applied', 'Interview Scheduled', 'Rejected', 'Offer Received')
        status_combo.current(0)
        status_combo.grid(row=0, column=1, sticky=tk.W, padx=10, pady=10)
    
        # Date applied
        ttk.Label(update_window, text="Date Applied:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)
        date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(update_window, textvariable=date_var, width=20).grid(row=1, column=1, sticky=tk.W, padx=10, pady=10)
    
        # Application deadline
        ttk.Label(update_window, text="Application Deadline:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=10)
        deadline_var = tk.StringVar()
        ttk.Entry(update_window, textvariable=deadline_var, width=20).grid(row=2, column=1, sticky=tk.W, padx=10, pady=10)
    
        # Application link
        ttk.Label(update_window, text="Application Link:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=10)
        link_var = tk.StringVar()
        ttk.Entry(update_window, textvariable=link_var, width=40).grid(row=3, column=1, sticky=tk.W, padx=10, pady=10)
    
        # Resume link
        ttk.Label(update_window, text="Resume Link:").grid(row=4, column=0, sticky=tk.W, padx=10, pady=10)
        resume_var = tk.StringVar()
        ttk.Entry(update_window, textvariable=resume_var, width=40).grid(row=4, column=1, sticky=tk.W, padx=10, pady=10)
    
        # Notes
        ttk.Label(update_window, text="Notes:").grid(row=5, column=0, sticky=tk.NW, padx=10, pady=10)
        notes_text = tk.Text(update_window, width=40, height=5)
        notes_text.grid(row=5, column=1, sticky=tk.W, padx=10, pady=10)
    
        # Save button
        def save_status():
            try:
                # Load the CSV file
                df = pd.read_csv(self.current_file)
            
                # Update the job information
                df.loc[df['job_id'] == job_id, 'status'] = status_var.get()
                df.loc[df['job_id'] == job_id, 'date_applied'] = date_var.get()
                df.loc[df['job_id'] == job_id, 'deadline'] = deadline_var.get()
                df.loc[df['job_id'] == job_id, 'application_link'] = link_var.get()
                df.loc[df['job_id'] == job_id, 'resume_link'] = resume_var.get()
            
                # Add notes column if it doesn't exist
                if 'notes' not in df.columns:
                    df['notes'] = None
            
                df.loc[df['job_id'] == job_id, 'notes'] = notes_text.get("1.0", tk.END).strip()
            
                # Save the updated file
                df.to_csv(self.current_file, index=False)
            
                messagebox.showinfo("Success", f"Updated job {job_id} status to '{status_var.get()}'")
                update_window.destroy()
            
                # Refresh job list
                self.refresh_job_list()
            
            except Exception as e:
                messagebox.showerror("Error", f"Error updating job status: {str(e)}")
    
        ttk.Button(update_window, text="Save", command=save_status).grid(row=6, column=0, columnspan=2, pady=20)
    
        # Try to load existing values
        try:
            df = pd.read_csv(self.current_file)
            job_data = df[df['job_id'] == job_id].iloc[0]
        
            status_combo.set(job_data['status'] if pd.notna(job_data['status']) else 'Not Applied')
            date_var.set(job_data['date_applied'] if pd.notna(job_data['date_applied']) else '')
        
            if 'deadline' in job_data and pd.notna(job_data['deadline']):
                deadline_var.set(job_data['deadline'])
            
            if 'application_link' in job_data and pd.notna(job_data['application_link']):
                link_var.set(job_data['application_link'])
            
            if 'resume_link' in job_data and pd.notna(job_data['resume_link']):
                resume_var.set(job_data['resume_link'])
            
            if 'notes' in job_data and pd.notna(job_data['notes']):
                notes_text.insert(tk.END, job_data['notes'])
        except:
            pass
        
     
    
    def open_application_link(self, event=None):
        """Open job application link in browser"""
        selection = self.job_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        job_values = self.job_tree.item(item, 'values')
        job_id = job_values[0]
        
        try:
            df = pd.read_csv(self.current_file)
            job_data = df[df['job_id'] == job_id].iloc[0]
            
            if pd.notna(job_data['application_link']):
                webbrowser.open(job_data['application_link'])
            else:
                messagebox.showinfo("Info", "No application link available for this job")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error opening application link: {str(e)}")
    
    def copy_email(self, event=None):
        """Copy email to clipboard"""
        selection = self.job_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        job_values = self.job_tree.item(item, 'values')
        
        if len(job_values) >= 8 and job_values[7]:  # Email is at index 7
            self.copy_to_clipboard(job_values[7])
            messagebox.showinfo("Success", "Email copied to clipboard")
        else:
            messagebox.showinfo("Info", "No email available for this job")
    
    def copy_to_clipboard(self, text):
        """Copy text to clipboard"""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
    
    def show_context_menu(self, event):
        """Show context menu on right-click"""
        if self.job_tree.selection():
            self.context_menu.post(event.x_root, event.y_root)

if __name__ == "__main__":
    # Create directories if they don't exist
    os.makedirs("job_tracker/data", exist_ok=True)
    
    # Create and run the app
    root = tk.Tk()
    app = JobTrackerApp(root)
    root.mainloop()