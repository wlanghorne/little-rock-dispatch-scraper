from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from scraper_functions import create_file, get_latest_dispatch, get_dispatches_to_notify, open_dispatch_log, create_message, send_message, create_api_service_object
from time import sleep
from datetime import date
import csv
import os
import sys 

# Paths to csv file that will store data 
output_path = './outputs'
latest_dispatch_path = os.path.join(output_path, 'last_dispatch.csv')
driver_path = './chromedriver'
url = 'https://clrweb.littlerock.state.ar.us/pub/public_menu.php'

# CSV HEADERS 
HEADERS = ['Call type', 'Location', 'Dispatch time']

# Calls that will trigger notifications 
# TODO: Currently contains test call types, update with correct call types
CALLS_TO_NOTIFY_ON = {'DISTURBANCE IN PROGRESS'}

# Process args 
argv = sys.argv
argv_len = len(argv)
if argv_len < 4:
	print('ERROR: Must enter at least four arguments. 1) sender email address, 2) path to file with Google API JSONs, 3-n) recipient email addresses')
	exit()
else: 
	SENDER_ADDRESS = argv[1]
	PATH_TO_API_FILES = argv[2]
	RECIP_ADDRESSES = []
	for i in range (3, argv_len):
		RECIP_ADDRESSES.append(argv[i])

# Create latest dispatch file if needed 
create_file(latest_dispatch_path, HEADERS)

# Initiate driver
chrome_options = Options()
chrome_options.add_argument("--headless")
s = Service(driver_path)
driver = webdriver.Chrome(service=s, options=chrome_options)
driver.get(url)

open_dispatch_log(driver)

# Get latest dispatch time 
latest_dispatch = get_latest_dispatch(latest_dispatch_path)

# Get table rows 
table_body = driver.find_element(By.CSS_SELECTOR,'tbody')
rows = table_body.find_elements(By.CSS_SELECTOR,'tr')

# Check if new reports require notification
dispatches_to_notify = get_dispatches_to_notify(latest_dispatch, rows, latest_dispatch_path, CALLS_TO_NOTIFY_ON, HEADERS)

# Check if there any dispatches worth trigging notifications
if not dispatches_to_notify: 
	print('No calls requiring notification')
else:
	print(dispatches_to_notify)
	# Comp 
	subject = 'LRPD responding to: ' 
	body = ''
	for notif in dispatches_to_notify:
		subject = subject + notif[0] + ', '
		body = body + notif[0] + ', ' + notif[1] + ', ' + notif[2] + ', ' + '\n'

	for recip in RECIP_ADDRESSES:
		message = create_message(SENDER_ADDRESS, recip, subject, body)
		send_message(create_api_service_object (PATH_TO_API_FILES), SENDER_ADDRESS, message)

