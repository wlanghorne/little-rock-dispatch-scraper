from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from scraper_functions import create_dir, create_file
from time import sleep
from datetime import date
import csv
import os 

# Paths to csv file that will store data 
output_path = './outputs'
driver_path = './chromedriver'
url = 'https://clrweb.littlerock.state.ar.us/pub/public_menu.php'

# CSV headers 
headers = ['Call type', 'Location', 'Dispatch time']

# Create output directory if it doesn't already exist 
create_dir(output_path)

# CSV final output file and temp storage file containing reports for the current day 
out_file = str(date.today()) + '.csv'
temp_file = str(date.today()) + '_temp.csv'
out_file_path = os.path.join(output_path, out_file)
temp_file_path = os.path.join(output_path, temp_file)


# If the csv file doesn't exist, create it and add headers
create_file(out_file_path, headers)

# Initiate driver
s = Service(driver_path)
driver = webdriver.Chrome(service=s)
driver.get(url)

# Delay to allow data to load 
sleep(10)

# Select all dispatches
select_entries = Select(driver.find_element(By.NAME,'cadEventTable_length'))
select_entries.select_by_value('-1')


# Get latest dispatch time 
latest_dispatch = ''
with open(out_file_path, 'r') as f:
    latest_dispatch_holder = False
    reader = csv.reader(f)
    # skip header 
    next(reader)
    # try to open second row and extract the last dispatch time
    try: 
        second_row = next(reader)
        latest_dispatch = second_row[2]
    except StopIteration as exception:
        print(exception)
        latest_dispatch = False

with open(temp_file_path, 'w') as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    f.close()

# Get table rows 
table_body = driver.find_element(By.CSS_SELECTOR,'tbody')
rows = table_body.find_elements(By.CSS_SELECTOR,'tr')

# Gather new dispatch calls 
for row in rows:
    # Get cell data 
    cells = row.find_elements(By.CSS_SELECTOR, 'td')
    cell_data = []
    for cell in cells:
        cell_data.append(cell.get_attribute('innerHTML'))
        # Check if the latest data in the dispatch log matches the latest data in the sheet 
    if cell_data[2] == latest_dispatch:
        break 
    else: 
        # Write to file  
        with open(temp_file_path, 'a') as f:
            writer = csv.writer(f)
            writer.writerow(cell_data)
            f.close()

# Write old dispatch calls beneath new calls in temp file 
if latest_dispatch: 
    with open(temp_file_path, 'a') as temp_f:
        writer = csv.writer(temp_f)
        with open(file_path, 'r') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                writer.writerow(row)
            f.close()
        temp_f.close()

# Write temp file into file  
with open(out_file_path, 'w') as f:
    writer = csv.writer(f)
    with open(temp_file_path, 'r') as temp_f:
        reader = csv.reader(temp_f)
        for row in reader:
            writer.writerow(row)
        temp_f.close()
    f.close()


