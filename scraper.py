# scraper.py
import csv
import os
from datetime import datetime, timezone, timedelta

# --- Configuration ---
LOG_FILE = "auction_log.csv"
CSV_HEADER = ['Plate Number', 'Price', 'Last Seen']
# Set the time zone for UAE (UTC+4)
UAE_TZ = timezone(timedelta(hours=4))

def get_existing_plate_numbers(filename):
    """Reads a CSV file and returns a set of all plate numbers."""
    plate_numbers = set()
    try:
        with open(filename, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip the header row
            for row in reader:
                if row: plate_numbers.add(row[0])
    except FileNotFoundError:
        pass
    return plate_numbers

def scrape_site():
    """
    ### IMPORTANT ###
    This is placeholder data. You must replace the logic in this
    function with your own scraping code using requests and BeautifulSoup.
    It must return a list of lists, like: [['F 123', 50000], ['J 456', 75000]]
    """
    print("Simulating scraping to generate example data...")
    # This is fake data. Your real scraping logic goes here.
    scraped_data = [
        ['F 123', 50000],
        ['J 456', 75000],
        ['L 789', 250000]
    ]
    print(f"Found {len(scraped_data)} item(s) to process.")
    return scraped_data

# --- Main script execution ---
if __name__ == "__main__":
    print("Starting CSV scraper...")
    file_exists = os.path.exists(LOG_FILE)
    existing_plates = get_existing_plate_numbers(LOG_FILE)
    print(f"Found {len(existing_plates)} existing plates in {LOG_FILE}.")

    new_entries = scrape_site()

    with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(CSV_HEADER)

        new_data_count = 0
        for entry in new_entries:
            plate_number, price = entry[0], entry[1]
            if plate_number not in existing_plates:
                formatted_price = f"{price:,}"
                timestamp = datetime.now(UAE_TZ).strftime('%d-%m-%y %H:%M')
                writer.writerow([plate_number, formatted_price, timestamp])
                new_data_count += 1

        if new_data_count > 0:
            print(f"Appended {new_data_count} new entries to {LOG_FILE}.")
        else:
            print("No new data to append.")

    print("Scraper finished.")