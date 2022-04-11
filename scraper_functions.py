import csv
import os

def create_dir(path):
	if not os.path.isdir(path):
		os.mkdir(path)

def create_file(path, headers):
	if not os.path.exists(path):
	    with open(path, 'w') as f:
	        writer = csv.writer(f)
	        writer.writerow(headers)
	        f.close()
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

