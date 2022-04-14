from datetime import datetime 
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import json
import os
import shutil
import base64

def create_dir(path):
	if not os.path.isdir(path):
		os.mkdir(path)

def create_file(path, headers):
	if not os.path.exists(path):
	    with open(path, 'w') as f:
	        writer = csv.writer(f)
	        writer.writerow(headers)
	        f.close()
	        # indicate that new file was created 
	        return True 
	# ensure headers are in file if file exists
	else: 
		try:
			same_headers = True
			with open(path, 'r') as f:
				reader = csv.reader(f)
				if not headers == next(reader):
					same_headers = False
				f.close()
			if not same_headers: 
				with open(path, 'w') as f:
					writer = csv.writer(f)
					writer.writerow(headers)
					f.close()
		except:
			with open(path, 'w') as f:
				writer = csv.writer(f)
				writer.writerow(headers)
				f.close()
		return False

def has_no_csv(path):
  file_names = os.listdir(path)
  for file_name in file_names:
  	if file_name.endswith('.csv'):
  		return False
  return True

def get_latest_dispatch(out_file_path):
	with open(out_file_path, 'r') as f:
		reader = csv.reader(f)
		# skip header 
		next(reader)
		# try to open second row and extract the last dispatch time
		try: 
			second_row = next(reader)
			latest_dispatch = second_row[2]
			return latest_dispatch
		except StopIteration as exception:
			print(exception)
			latest_dispatch = False

def intialize_temp_file (temp_file_path, headers):
	with open(temp_file_path, 'w') as f:
		writer = csv.writer(f)
		writer.writerow(headers)
		f.close()

def open_dispatch_log(driver): 
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

def gather_latest_dispatches(temp_file_path, rows, latest_dispatch, today):
	is_first_row = True
	for row in rows: 
		cells = row.find_elements(By.CSS_SELECTOR, 'td')
		# Check if the latest data in the dispatch log matches the latest data in the sheet and ensure that only dispatches for the given day are included 
		dispatch_time = cells[2].get_attribute('innerHTML')   
		if dispatch_time == latest_dispatch or today not in dispatch_time:
			if is_first_row:
				# if the lastest recorded dispatch is the latest one on the site, the record is up to date  
				return False 
			else:
				return True 
		# If there is new data, write to the temp_file
		else:
			cell_data = []
			for cell in cells:
				cell_data.append(cell.get_attribute('innerHTML'))
			# Write to file 
			with open(temp_file_path, 'a') as f:
				writer = csv.writer(f)
				writer.writerow(cell_data)
				f.close()
		is_first_row = False 
	return True 

def get_dispatches_to_notify(latest_dispatch, rows, latest_dispatch_path, calls_to_notify_on, headers):
	is_first_row = True
	calls_to_notify = []
	for row in rows: 
		cells = row.find_elements(By.CSS_SELECTOR, 'td')
		# Check if the latest data in the dispatch log matches the latest data in the sheet and ensure that only dispatches for the given day are included 
		dispatch_time = cells[2].get_attribute('innerHTML') 
		if dispatch_time == latest_dispatch:
			if is_first_row: 
				# if the lastest recorded dispatch is the latest one on the site, the notifier is up to date  
				return False  
			else: 
				return calls_to_notify
		else: 
			cell_data = []
			for cell in cells:
				cell_data.append(cell.get_attribute('innerHTML'))
				# Update the latest dispatch file with the first dispatch listed on the log site 
			if is_first_row:
				with open(latest_dispatch_path, 'w') as f:
					writer = csv.writer(f)
					writer.writerow(headers)
					writer.writerow(cell_data)
					f.close()
				is_first_row = False
			if cell_data[0] in calls_to_notify_on:
				calls_to_notify.append(cell_data)
	return calls_to_notify

def format_out_files(latest_dispatch, temp_file_path, final_file_path):
	# Write old dispatch calls beneath new calls in temp file 
	if latest_dispatch: 
	    with open(temp_file_path, 'a') as temp_f:
	        writer = csv.writer(temp_f)
	        with open(final_file_path, 'r') as f:
	            reader = csv.reader(f)
	            next(reader)
	            for row in reader:
	                writer.writerow(row)
	            f.close()
	        temp_f.close()
	# Write temp file into file  
	with open(final_file_path, 'w') as f:
	    writer = csv.writer(f)
	    with open(temp_file_path, 'r') as temp_f:
	        reader = csv.reader(temp_f)
	        for row in reader:
	            writer.writerow(row)
	        temp_f.close()
	    f.close()

def update_metadata_file(metadata_path, new_metadata_dict, final_file_path):
	# read existing metadata for dataset into dict 
	meta_dict = {}
	with open(metadata_path) as json_file:
		meta_dict = json.load(json_file)
		json_file.close()

	new_metadata_dict['path'] = str(os.path.split(final_file_path)[1])

	# get the number of csv files already included in the dataset  
	path_num = len(meta_dict['resources'])
	meta_dict['resources'].insert(0, new_metadata_dict)

	# write new meta data back into json file 
	with open(metadata_path, 'w') as json_file:
		json.dump(meta_dict, json_file)

def write_to_kaggle(is_new_dataset, kaggle_path, dataset_path):
	# if the dataset is new, create a new dataset using cmd line 
	if is_new_dataset:
		# create new dataset on kaggle
		create_dataset_cmd = kaggle_path + ' datasets create -u -p ' + dataset_path
		os.system(create_dataset_cmd)
	else: 
		# tag update message with current time 
		update_time = str(datetime.now())
		update_msg = ' -m "Loaded new reports at' + update_time +'"'
		# update data set 
		update_dataset_cmd = kaggle_path + ' datasets version -p ' + dataset_path + update_msg
		os.system(update_dataset_cmd)

# Credit: https://developers.google.com/gmail/api/guides/sending#recommendations-link
def create_message(sender, to, subject, message_text):
	message = MIMEText(message_text)
	message['to'] = to
	message['from'] = sender
	message['subject'] = subject
	b64_bytes = base64.urlsafe_b64encode(message.as_bytes())
	b64_string = b64_bytes.decode()
	return {'raw': b64_string}

# Credit: https://developers.google.com/gmail/api/guides/sending#recommendations-link
def send_message(service, user_id, message):
	try:
		message = (service.users().messages().send(userId=user_id, body=message)
	               .execute())
		print('Message Id: %s' % message['id'])
		return message
	except HttpError as error:
		print('An error occurred: %s' % error)

# Build API service 
# Credit: https://developers.google.com/gmail/api/quickstart/python
def create_api_service_object (path_to_api_files):
	path_to_token = os.path.join(path_to_api_files, 'token.json')
	path_to_creds = os.path.join(path_to_api_files, 'credentials.json')
	# If modifying these scopes, delete the file token.json.	
	scopes = ['https://www.googleapis.com/auth/gmail.send']
	creds = None
	if os.path.exists(path_to_token):
		creds = Credentials.from_authorized_user_file(path_to_token, scopes)
	# If there are no (valid) credentials available, let the user log in.
	if not creds or not creds.valid:
		if creds and creds.expired and creds.refresh_token:
			creds.refresh(Request())
		else:
			flow = InstalledAppFlow.from_client_secrets_file(
                path_to_creds, scopes)
			creds = flow.run_local_server(port=0)
		# Save the credentials for the next run
		with open(path_to_token, 'w') as token:
			token.write(creds.to_json())
	try:
		# Call the Gmail API
		service = build('gmail', 'v1', credentials=creds)
		return service
	except HttpError as error:
		# TODO(developer) - Handle errors from gmail API.
		print(f'An error occurred: {error}')
