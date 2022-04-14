from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from scraper_functions import has_no_csv, format_out_files, gather_latest_dispatches, intialize_temp_file, get_latest_dispatch, create_dir, create_file, update_metadata_file, write_to_kaggle
from time import sleep
from datetime import date
import csv
import os 

# Paths to csv file that will store data 
output_path = './outputs'
driver_path = './chromedriver'
url = 'https://clrweb.littlerock.state.ar.us/pub/public_menu.php'
kaggle_path = './kaggle'
metadata_path = './outputs/finals/dataset-metadata.json'

# Store basic metadata for new kaggle csv file
new_metadata_dict = {"path": "",
					 "description": "Contains call types, addresses and report times for each Little Rock PD dispatch for the given day",
			         "schema":
			         	{
			                "fields":
			                [
			                    {
			                        "name": "Call type",
			                        "description": "Type of report",
			                        "type": "string"
			                    },
			                    {
			                        "name": ",Location",
			                        "description": "Address of report",
			                        "type": "string"
			                    },
			                    {
			                        "name": "Dispatch time",
			                        "description": "Time of dispatch report",
			                        "type": "datetime"
			                    }
			                ]
			            }
			        }

# CSV headers 
headers = ['Call type', 'Location', 'Dispatch time']

# Create output directory if it doesn't already exist 
create_dir(output_path)

# Create the final output and temporary output directorys
finals_path = os.path.join(output_path, 'finals')
temps_path = os.path.join(output_path, 'temps')
create_dir(temps_path)

# Create a new dataset if there are no csv files in final path 
is_new_dataset = has_no_csv(finals_path)

# CSV final output file and temp storage file containing reports for the current day
today = str(date.today())
final_file = today + '.csv'
temp_file = today + '_temp.csv'
final_file_path = os.path.join(finals_path, final_file)
temp_file_path = os.path.join(temps_path, temp_file)

# If final_file is a new file, update the kaggle metadata
if not os.path.exists(final_file_path):
	update_metadata_file(metadata_path, new_metadata_dict, final_file_path)

# Create final final path if needed 
create_file(final_file_path, headers)

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
latest_dispatch = get_latest_dispatch(final_file_path)

# Get table rows 
table_body = driver.find_element(By.CSS_SELECTOR,'tbody')
rows = table_body.find_elements(By.CSS_SELECTOR,'tr')

# Update status in terminal 
print("Gathering latest dispatches ...")

# Create or overwrite temp file 
intialize_temp_file(temp_file_path, headers)

# If there are new dispatches, update kaggle
if gather_latest_dispatches(temp_file_path, rows, latest_dispatch, today):

	# Update status in terminal 
	print("Formating output files ...")

	format_out_files(latest_dispatch, temp_file_path, final_file_path)

	# Write final data to kaggle 
	write_to_kaggle(is_new_dataset, kaggle_path, finals_path)