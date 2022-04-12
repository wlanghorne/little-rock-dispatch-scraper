from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from scraper_functions import format_out_files, gather_latest_dispatches, intialize_temp_file, get_latest_dispatch, create_dir, create_file, create_metadata_file, write_to_kaggle
from time import sleep
from datetime import date
import csv
import os 

# Paths to csv file that will store data 
output_path = './outputs'
driver_path = './chromedriver'
url = 'https://clrweb.littlerock.state.ar.us/pub/public_menu.php'
kaggle_path = './kaggle'
orgin_metadata_path = './dataset-metadata.json'

# CSV headers 
headers = ['Call type', 'Location', 'Dispatch time']

# Create output directory if it doesn't already exist 
create_dir(output_path)

# Create the output directory for the current day if it doesn't already exist
today = str(date.today())
output_path = os.path.join(output_path, today)
create_dir(output_path)

# Create the final output directory for the current day if it doesn't already exist
output_path = os.path.join(output_path, 'final')
create_dir(output_path)

# CSV final output file and temp storage file containing reports for the current day 
out_file = today + '.csv'
temp_file = today + '_temp.csv'
out_file_path = os.path.join(output_path, out_file)
temp_file_path = os.path.join(os.path.split(output_path)[0], temp_file)

# If the csv file doesn't exist, create it w/ headers and generate meta data file for kaggle
# Set boolean value for if new dataset depending on if new file was created 
is_new_dataset = create_file(out_file_path, headers)
create_metadata_file(kaggle_path, orgin_metadata_path, output_path, today)

# Initiate driver
chrome_options = Options()
chrome_options.add_argument("--headless")
s = Service(driver_path)
driver = webdriver.Chrome(service=s, options=chrome_options)
driver.get(url)

# Update status in terminal
print("Opening url ...")

# Delay to allow data to load 
WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[class='paginate_button current']")))

# Select all dispatches
select_entries = Select(driver.find_element(By.NAME,'cadEventTable_length'))
select_entries.select_by_value('-1')

# Delay to allow data to load 
WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[class='paginate_button previous disabled']")))

# Update status in terminal 
print("Getting latest saved dispatch ...")

# Get latest dispatch time 
latest_dispatch = get_latest_dispatch(out_file_path)

# Get table rows 
table_body = driver.find_element(By.CSS_SELECTOR,'tbody')
rows = table_body.find_elements(By.CSS_SELECTOR,'tr')

# Update status in terminal 
print("Gathering latest dispatches ...")

# Create or overwrite temp file 
intialize_temp_file(temp_file_path, headers)

# If there are new dispatches, update kaggle

if gather_latest_dispatches(temp_file_path, rows, latest_dispatch):

	# Update status in terminal 
	print("Formating output files ...")

	format_out_files(latest_dispatch, temp_file_path, out_file_path)

	# Write final data to kaggle 
	write_to_kaggle(is_new_dataset, kaggle_path, output_path)