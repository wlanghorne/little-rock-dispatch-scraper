from datetime import datetime
import csv
import json
import os
import shutil 
from selenium.webdriver.common.by import By

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

def gather_latest_dispatches(temp_file_path, rows, latest_dispatch):
	is_first_row = True
	for row in rows: 
		cells = row.find_elements(By.CSS_SELECTOR, 'td')
		# Check if the latest data in the dispatch log matches the latest data in the sheet 
		if cells[2].get_attribute('innerHTML') == latest_dispatch:
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
				print("writing")
				writer = csv.writer(f)
				writer.writerow(cell_data)
				f.close()
		is_first_row = False 

def format_out_files(latest_dispatch, temp_file_path, out_file_path):
	# Write old dispatch calls beneath new calls in temp file 
	if latest_dispatch: 
	    with open(temp_file_path, 'a') as temp_f:
	        writer = csv.writer(temp_f)
	        with open(out_file_path, 'r') as f:
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

def create_metadata_file(kaggle_path, orgin_path, new_path, str_date):
	meta_file_path = os.path.join(new_path, 'dataset-metadata.json')
	if not os.path.exists(meta_file_path):
		create_metadata_cmd = kaggle_path + ' datasets init -p ' + new_path
		print(create_metadata_cmd)
		os.system(create_metadata_cmd)

		# read meta data file into dict 
		meta_dict = {}
		with open(orgin_path) as json_file:
			meta_dict = json.load(json_file)
			json_file.close()

		# change meta data using dates 
		meta_dict['title'] = meta_dict['title'] + str_date
		meta_dict['id'] = meta_dict['id'] + str_date
		meta_dict['resources'][0]['path'] = str_date + '.csv'

		# write new meta data back into json file 
		with open(meta_file_path, 'w') as json_file:
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


