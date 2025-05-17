import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time
import random
from datetime import datetime
import re
from urllib.parse import urlencode

class LinkedInJobTracker:
    def __init__(self, job_title, location, job_type=None):
        """Initialize the LinkedIn job tracker with search parameters"""
        self.job_title = job_title
        self.location = location
        self.job_type = job_type
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.job_list = []
        
        # Create directory structure
        os.makedirs('job_tracker', exist_ok=True)
        os.makedirs('job_tracker/data', exist_ok=True)
        
    def search_jobs(self, num_pages=3, max_age_days=None):
        """Search for jobs on LinkedIn and collect job IDs"""
        print(f"Searching for {self.job_title} jobs in {self.location}...")
        job_ids = []
    
        # Add LinkedIn's date filter if max_age_days is specified
        if max_age_days:
            if max_age_days <= 1:
                date_filter = 'r86400'  # Past 24 hours
            elif max_age_days <= 7:
                date_filter = 'r604800'  # Past week
            elif max_age_days <= 30:
                date_filter = 'r2592000'  # Past month
            else:
                date_filter = None
        else:
            date_filter = None
    
        for page in range(num_pages):
            start = page * 25  # LinkedIn uses 25 jobs per page
        
            # Construct the URL for LinkedIn job search
            params = {
                'keywords': self.job_title,
                'location': self.location,
                'start': start
            }
            if self.job_type:
                params['f_JT'] = self.job_type  # f_JT=F for Full-time, f_JT=C for Contract, etc.
        
            # Add date filter if specified
            if date_filter:
                params['f_TPR'] = date_filter
            
            list_url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?{urlencode(params)}"
            
            try:
                # Send a GET request to the URL and store the response
                response = requests.get(list_url, headers=self.headers)
                
                if response.status_code == 200:
                    # Parse the response and find all list items (job postings)
                    list_soup = BeautifulSoup(response.text, "html.parser")
                    page_jobs = list_soup.find_all("li")
                    
                    # Extract job IDs
                    for job in page_jobs:
                        try:
                            base_card_div = job.find("div", {"class": "base-card"})
                            if base_card_div and base_card_div.get("data-entity-urn"):
                                job_id = base_card_div.get("data-entity-urn").split(":")[-1]
                                job_ids.append(job_id)
                        except Exception as e:
                            print(f"Error extracting job ID: {e}")
                    
                    print(f"Found {len(page_jobs)} jobs on page {page+1}")
                    
                    # Add a random delay to avoid being blocked
                    time.sleep(random.uniform(2, 5))
                else:
                    print(f"Failed to fetch page {page+1}: Status code {response.status_code}")
            except Exception as e:
                print(f"Error fetching page {page+1}: {e}")
        
        print(f"Total job IDs collected: {len(job_ids)}")
        return job_ids
    
    def extract_job_details(self, job_ids):
        """Extract detailed information for each job ID"""
        print("Extracting job details...")
        
        for job_id in job_ids:
            # Construct the URL for each job using the job ID
            job_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
            apply_url = f"https://www.linkedin.com/jobs/view/{job_id}"
            
            try:
                # Send a GET request to the job URL and parse the response
                job_response = requests.get(job_url, headers=self.headers)
                
                if job_response.status_code == 200:
                    job_soup = BeautifulSoup(job_response.text, "html.parser")
                    
                    # Create a dictionary to store job details
                    job_post = {
                        'job_id': job_id,
                        'status': 'Not Applied',
                        'date_applied': None,
                        'deadline': None,
                        'type': self._extract_job_type(job_soup),
                        'contact_person': None,
                        'email': self._extract_email(job_soup),
                        'application_link': apply_url,
                        'resume_link': None
                    }
                    
                    # Extract job title
                    try:
                        job_post["job_title"] = job_soup.find("h2", {"class": lambda c: c and "topcard__title" in c}).text.strip()
                    except:
                        job_post["job_title"] = None
                    
                    # Extract company name
                    try:
                        job_post["company"] = job_soup.find("a", {"class": lambda c: c and "topcard__org-name-link" in c}).text.strip()
                    except:
                        try:
                            job_post["company"] = job_soup.find("span", {"class": lambda c: c and "topcard__org-name" in c}).text.strip()
                        except:
                            job_post["company"] = None
                    
                    # Extract location
                    try:
                        job_post["location"] = job_soup.find("span", {"class": lambda c: c and "topcard__flavor--bullet" in c}).text.strip()
                    except:
                        job_post["location"] = None
                    
                    # Extract posting date
                    try:
                        job_post["time_posted"] = job_soup.find("span", {"class": lambda c: c and "posted-time-ago__text" in c}).text.strip()
                        job_post["posting_date"] = self._parse_posting_date(job_post["time_posted"])
                    except:
                        job_post["time_posted"] = None
                    
                    # Extract number of applicants
                    try:
                        job_post["num_applicants"] = job_soup.find("span", {"class": lambda c: c and "num-applicants__caption" in c}).text.strip()
                    except:
                        job_post["num_applicants"] = None
                    
                    # Extract job description for further analysis
                    try:
                        job_description = job_soup.find("div", {"class": "show-more-less-html__markup"})
                        if job_description:
                            job_post["description"] = job_description.text.strip()
                            
                            # Extract application deadline
                            deadline = self._extract_deadline(None, job_post["description"])
                            if deadline:
                                job_post['deadline'] = deadline

                            # Try to extract contact information from description
                            contact_info = self._extract_contact_info(job_post["description"])
                            if contact_info.get('contact_person') and not job_post['contact_person']:
                                job_post['contact_person'] = contact_info.get('contact_person')
                            if contact_info.get('email') and not job_post['email']:
                                job_post['email'] = contact_info.get('email')
                    except:
                        job_post["time_posted"] = None
                        job_post["posting_date"] = None
                        job_post["description"] = None
                    
                    # Append the job details to the job_list
                    self.job_list.append(job_post)
                    
                    # Add a random delay to avoid being blocked
                    time.sleep(random.uniform(1, 3))
                else:
                    print(f"Failed to fetch job {job_id}: Status code {job_response.status_code}")
            except Exception as e:
                print(f"Error fetching job {job_id}: {e}")
        
        print(f"Extracted details for {len(self.job_list)} jobs")
    
    def _extract_job_type(self, soup):
        """Extract job type (Full-time, Contract, Co-op, etc.)"""
        try:
            job_criteria_list = soup.find_all("li", {"class": "description__job-criteria-item"})
            for criteria in job_criteria_list:
                header = criteria.find("h3", {"class": "description__job-criteria-subheader"})
                if header and "Employment type" in header.text:
                    return criteria.find("span", {"class": "description__job-criteria-text"}).text.strip()
            
            # If not found in criteria, try to extract from description
            description = soup.find("div", {"class": "show-more-less-html__markup"})
            if description:
                text = description.text.lower()
                if "full-time" in text or "full time" in text:
                    return "Full-time"
                elif "part-time" in text or "part time" in text:
                    return "Part-time"
                elif "contract" in text:
                    return "Contract"
                elif "co-op" in text or "coop" in text or "internship" in text:
                    return "Co-op/Internship"
        except:
            pass
        return "Not specified"
    
    def _extract_email(self, soup):
        """Extract email from job posting"""
        try:
            # Try to find email in the job description
            description = soup.find("div", {"class": "show-more-less-html__markup"})
            if description:
                text = description.text
                # Look for email patterns
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, text)
                if emails:
                    return emails[0]
        except:
            pass
        return None
    
    def _extract_deadline(self, soup, description_text=None):
        """Extract application deadline from job posting"""
        deadline = None
    
        try:
            # Try to find deadline in the job description
            if not description_text and soup:
                description = soup.find("div", {"class": "show-more-less-html__markup"})
                if description:
                    description_text = description.text
        
            if description_text:
                # Common deadline patterns
                deadline_patterns = [
                    r'application deadline[:\s]*([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?[\s,]+\d{4})',
                    r'apply by[:\s]*([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?[\s,]+\d{4})',
                    r'closing date[:\s]*([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?[\s,]+\d{4})',
                    r'applications close[:\s]*([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?[\s,]+\d{4})',
                    r'deadline[:\s]*([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?[\s,]+\d{4})',
                    r'applications due[:\s]*([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?[\s,]+\d{4})'
                ]
            
                for pattern in deadline_patterns:
                    match = re.search(pattern, description_text, re.IGNORECASE)
                    if match:
                        deadline = match.group(1)
                        break
        except:
            pass
    
        return deadline
    
    def _parse_posting_date(self, time_posted_text):
        """Convert LinkedIn's relative time (e.g., '2 days ago') to an actual date"""
        if not time_posted_text:
            return None
        
        today = datetime.now().date()
    
        # Handle common LinkedIn time formats
        if 'hour' in time_posted_text or 'minute' in time_posted_text:
            return today
        elif 'day' in time_posted_text:
            days = int(re.search(r'(\d+)', time_posted_text).group(1))
            return today - pd.Timedelta(days=days)
        elif 'week' in time_posted_text:
            weeks = int(re.search(r'(\d+)', time_posted_text).group(1))
            return today - pd.Timedelta(weeks=weeks)
        elif 'month' in time_posted_text:
            months = int(re.search(r'(\d+)', time_posted_text).group(1))
            # Approximate a month as 30 days
            return today - pd.Timedelta(days=30*months)
        elif 'year' in time_posted_text:
            years = int(re.search(r'(\d+)', time_posted_text).group(1))
            # Approximate a year as 365 days
            return today - pd.Timedelta(days=365*years)
        else:
            return None
    
    def _extract_contact_info(self, text):
        """Extract contact information from text"""
        result = {'contact_person': None, 'email': None}
        
        if not text:
            return result
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            result['email'] = emails[0]
        
        # Try to extract contact person
        contact_patterns = [
            r'contact\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})',
            r'reach out to\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})',
            r'email\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})',
            r'send.*resume.*to\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})'
        ]
        
        for pattern in contact_patterns:
            matches = re.search(pattern, text, re.IGNORECASE)
            if matches:
                result['contact_person'] = matches.group(1)
                break
        
        return result
    
    def save_to_csv(self):
        """Save job data to CSV file"""
        if not self.job_list:
            print("No job data to save")
            return
        
        # Create a pandas DataFrame
        df = pd.DataFrame(self.job_list)
        
        # Reorder columns to match requested format
        columns = [
            'company', 'job_title', 'status', 'date_applied', 'deadline', 
            'type', 'contact_person', 'email', 'application_link', 'resume_link',
            'location', 'time_posted', 'num_applicants', 'job_id'
        ]
        
        # Only include columns that exist in the DataFrame
        columns = [col for col in columns if col in df.columns]
        
        # Add any remaining columns
        for col in df.columns:
            if col not in columns and col != 'description':
                columns.append(col)
        
        df = df[columns]
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"job_tracker/data/{self.job_title.replace(' ', '_')}_{self.location.replace(' ', '_')}_{timestamp}.csv"
        
        # Save to CSV
        df.to_csv(filename, index=False)
        print(f"Job data saved to {filename}")
        
        return filename
    
    def run(self, num_pages=3, max_age_days=None):
        """Run the complete job tracking process"""
        job_ids = self.search_jobs(num_pages, max_age_days)
        self.extract_job_details(job_ids)
        return self.save_to_csv()

if __name__ == "__main__":
    # Create a job tracker instance
    tracker = LinkedInJobTracker(
        job_title="Python Developer",
        location="Toronto",
        job_type=None  # Optional: specify job type filter
    )
    
    # Run the tracker with age filter (e.g., only jobs from the past 30 days)
    csv_file = tracker.run(num_pages=2, max_age_days=30)
    
    # Load the saved data to display sample results
    if csv_file:
        df = pd.read_csv(csv_file)
        print("\nSample of tracked jobs:")
        print(df[['company', 'job_title', 'status', 'type', 'email', 'application_link']].head())
        print(f"\nTotal jobs tracked: {len(df)}")