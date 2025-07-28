# scraper.py
import csv
import os
from datetime import datetime, timedelta, timezone

# --- Configuration ---
LOG_FILE = "auction_log.csv"
LAST_RUN_FILE = "last_run.txt" # New file to track the last successful scrape
CSV_HEADER = ['Plate Number', 'Price', 'Last Seen']
UAE_TZ = timezone(timedelta(hours=4))

# --- Schedule Intervals (in minutes) ---
# NOTE: The 3-minute interval will run on the 5-minute master clock
# So it may run at 3, 6, 9 mins -> effectively 5, 10, 15 min intervals
NORMAL_INTERVAL = 8 * 60  # 8 hours
CLOSING_INTERVAL = 10     # 10 minutes
FINAL_INTERVAL = 3        # 3 minutes

def get_minimum_remaining_time():
    """
    ### ACTION REQUIRED ###
    You must implement this function. It should scrape the auction page
    to find the countdown timers for all active plates and return the
    shortest remaining time in SECONDS.
    
    - If the auction is over (no plates), return None.
    - If the shortest time is 1 hour 15 mins, return 4500.
    - If the shortest time is 4 mins 30 secs, return 270.
    """
    # Placeholder logic - REPLACE THIS
    print("Checking auction timers... (placeholder logic)")
    # To test the 10-minute interval, return a value less than 7200 (2 hours)
    # For example, 1 hour remaining = 3600 seconds.
    # return 3600 

    # To test the 3-minute interval, return a value less than 300 (5 minutes)
    # For example, 4 minutes remaining = 240 seconds.
    # return 240
    
    # To test the 8-hour interval, return a large value
    # For example, 10 hours remaining = 36000 seconds.
    return 36000
    
    # When the auction is over, your scraping should find no items, so return None.
    # return None

def get_last_run_time():
    """Reads the timestamp from the last_run.txt file."""
    try:
        with open(LAST_RUN_FILE, 'r') as f:
            return datetime.fromisoformat(f.read().strip())
    except FileNotFoundError:
        # If the file doesn't exist, it's the first run
        return None

def record_run_time():
    """Writes the current timestamp to the last_run.txt file."""
    with open(LAST_RUN_FILE, 'w') as f:
        f.write(datetime.now(UAE_TZ).isoformat())

def perform_full_scrape():
    """
    This is your original scraping logic to get plate data and prices.
    It should return a list of lists, e.g., [['F 123', 50000]].
    """
    print("Performing full data scrape...")
    # Your logic to get plate number and price goes here.
    # This is placeholder data for the example.
    scraped_data = [
        ['F 123', 55000],
        ['J 456', 82000],
        ['L 789', 265000]
    ]
    return scraped_data

def append_to_csv(scraped_data):
    """Appends new scraped data to the CSV log file."""
    file_exists = os.path.exists(LOG_FILE)
    existing_plates = set()
    if file_exists:
        with open(LOG_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader) # skip header
            for row in reader:
                if row: existing_plates.add(row[0])

    with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(CSV_HEADER)
        
        for entry in scraped_data:
            plate_number, price = entry[0], entry[1]
            if plate_number not in existing_plates:
                formatted_price = f"{price:,}"
                timestamp = datetime.now(UAE_TZ).strftime('%d-%m-%y %H:%M')
                writer.writerow([plate_number, formatted_price, timestamp])
    print(f"CSV log updated.")

# --- Main Execution Logic ---
if __name__ == "__main__":
    min_time_left_sec = get_minimum_remaining_time()

    if min_time_left_sec is None:
        print("Auction appears to be finished. Halting.")
        # Optional: You could add logic here to disable the workflow via API
        exit()

    # Determine the required scraping interval based on remaining time
    current_interval = NORMAL_INTERVAL
    if min_time_left_sec <= 5 * 60: # 5 minutes
        current_interval = FINAL_INTERVAL
        print(f"STATE: Final Minutes (< 5 mins left). Required interval: {current_interval} mins.")
    elif min_time_left_sec <= 2 * 60 * 60: # 2 hours
        current_interval = CLOSING_INTERVAL
        print(f"STATE: Closing Hours (< 2 hours left). Required interval: {current_interval} mins.")
    else:
        print(f"STATE: Normal (> 2 hours left). Required interval: {current_interval / 60} hours.")
        
    last_run = get_last_run_time()
    should_run = False

    if last_run is None:
        # First ever run, so we should definitely scrape
        should_run = True
        print("First run detected. Performing scrape.")
    else:
        time_since_last_run = (datetime.now(UAE_TZ) - last_run).total_seconds() / 60
        print(f"Time since last scrape: {time_since_last_run:.2f} minutes.")
        if time_since_last_run >= current_interval:
            should_run = True
            print("Time interval has elapsed. Performing scrape.")
        else:
            print("Time interval has not elapsed. Skipping full scrape.")

    if should_run:
        scraped_data = perform_full_scrape()
        append_to_csv(scraped_data)
        record_run_time()
        print("Scrape complete and timestamp recorded.")
