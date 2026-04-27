import schedule
import time
import threading
import sys
import os

# Add project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from data_pipeline.scraper import HeroScraper

class DataScheduler:
    def __init__(self, interval_hours=24):
        self.interval_hours = interval_hours
        self.job = None
        self.running = False
        self.thread = None
    
    def _run_scrape(self):
        """Internal method to run the scraper"""
        print(f"Running scheduled scrape at {time.ctime()}")
        scraper = HeroScraper()
        scraper.run_full_scrape()
    
    def start(self):
        """Start the scheduler"""
        if self.running:
            print("Scheduler is already running")
            return
        
        # Schedule the job
        self.job = schedule.every(self.interval_hours).hours.do(self._run_scrape)
        self.running = True
        
        # Run in a separate thread
        def run_scheduler():
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        self.thread = threading.Thread(target=run_scheduler, daemon=True)
        self.thread.start()
        print(f"Scheduler started. Will run every {self.interval_hours} hours.")
    
    def stop(self):
        """Stop the scheduler"""
        if not self.running:
            print("Scheduler is not running")
            return
        
        self.running = False
        if self.job:
            schedule.cancel_job(self.job)
        if self.thread:
            self.thread.join(timeout=5)
        print("Scheduler stopped.")
    
    def run_once(self):
        """Run the scrape immediately"""
        print("Running scrape immediately...")
        self._run_scrape()

# Example usage (for testing)
if __name__ == "__main__":
    scheduler = DataScheduler(interval_hours=1)  # Run every hour for testing
    scheduler.start()
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.stop()