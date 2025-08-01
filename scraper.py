# scraper.py
import csv
import os
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone

# --- Configuration ---
LOG_FILE = "auction_log.csv"
LAST_RUN_FILE = "last_run.txt"
CSV_HEADER = ['Plate Number', 'Price', 'Last Seen']
UAE_TZ = timezone(timedelta(hours=4))
AUCTION_URL = "https://www.emiratesauction.com/plates/fujairah/online"

# --- Schedule Intervals (in minutes) ---
NORMAL_INTERVAL = 8 * 60  # 8 hours
CLOSING_INTERVAL = 10     # 10 minutes
FINAL_INTERVAL = 3        # 3 minutes

def get_minimum_remaining_time():
    """
    Scrapes the auction page to find the countdown timers for all active plates
    and returns the shortest remaining time in SECONDS.
    """
    try:
        response = requests.get(AUCTION_URL)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return 36000 # Default to normal interval on error

    soup = BeautifulSoup(response.content, 'html.parser')
    
    # This selector is now correct for the specified website.
    timer_elements = soup.select('div.plate-actions span.AutionTimer')
    
    if not timer_elements:
        print("No auction timers found. The auction may be over.")
        return None

    min_total_seconds = sys.maxsize

    for timer in timer_elements:
        time_str = timer.get_text(strip=True)
        parts = time_str.split(':')
        try:
            if len(parts) == 3: # HH:MM:SS
                h, m, s = [int(p) for p in parts]
                total_seconds = h * 3600 + m * 60 + s
            elif len(parts) == 2: # MM:SS
                m, s = [int(p) for p in parts]
                total_seconds = m * 60 + s
            else:
                continue
            if total_seconds < min_total_seconds:
                min_total_seconds = total_seconds
        except ValueError:
            continue
            
    if min_total_seconds == sys.maxsize:
        print("Could not parse any timers.")
        return 36000 # Default to normal
    
    print(f"Found {len(timer_elements)} timers. Shortest time: {min_total_seconds} seconds.")
    return min_total_seconds

def perform_full_scrape():
    """
    This function now correctly scrapes the plate numbers and prices from the website.
    It returns a list of lists, e.g., [['F 123', 50000], ['J 456', 75000]]
    """
    print("Performing full data scrape...")
    try:
        response = requests.get(AUCTION_URL)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    
    scraped_data = []
    # This selector finds each auction item container
    auction_items = soup.select('div.plate-box')

    for item in auction_items:
        try:
            # Find the plate number within the item container
            plate_number_tag = item.select_one('div.plate-no span.value')
            if not plate_number_tag:
                continue
            plate_number = plate_number_tag.get_text(strip=True)

            # Find the price within the item container
            price_tag = item.select_one('div.plate-price span.value')
            if not price_tag:
                continue
            # Clean up the price string and convert to an integer
            price_str = price_tag.get_text(strip=True).replace(',', '')
            price = int(price_str)
            
            scraped_data.append([plate_number, price])
        except (ValueError, AttributeError):
            # Skip this item if there's an issue with finding tags or converting data
            continue
            
    return scraped_data

def get_last_run_time():
    """Reads the timestamp from the last_run.txt file."""
    try:
        with open(LAST_RUN_FILE, 'r') as f:
            return datetime.fromisoformat(f.read().strip())
    except FileNotFoundError:
        return None

def record_run_time():
    """Writes the current timestamp to the last_run.txt file."""
    with open(LAST_RUN_FILE, 'w') as f:
        f.write(datetime.now(UAE_TZ).isoformat())

def append_to_csv(scraped_data):
    """Appends new scraped data to the CSV log file."""
    file_exists = os.path.exists(LOG_FILE)
    existing_plates = set()
    if file_exists:
        try:
            with open(LOG_FILE, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                if next(reader, None):
                    for row in reader:
                        if row: existing_plates.add(row[0])
        except (IOError, csv.Error):
             print("Warning: Could not read existing log file. It may be corrupted.")


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
        exit()

    current_interval = NORMAL_INTERVAL
    if min_time_left_sec <= 5 * 60: # 5 minutes
        current_interval = FINAL_INTERVAL
        print(f"STATE: Final Minutes (< 5 mins). Interval: {current_interval} mins.")
    elif min_time_left_sec <= 2 * 60 * 60: # 2 hours
        current_interval = CLOSING_INTERVAL
        print(f"STATE: Closing Hours (< 2 hours). Interval: {current_interval} mins.")
    else:
        print(f"STATE: Normal (> 2 hours). Interval: {current_interval / 60} hours.")
        
    last_run = get_last_run_time()
    should_run = False

    if last_run is None:
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
        data_to_log = perform_full_scrape()
        if data_to_log:
            append_to_csv(data_to_log)
            record_run_time()
            print("Scrape complete and timestamp recorded.")
        else:
            print("Scrape was performed, but no new data was found to log.")
