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
latest_dispatch_path = './outputs'
driver_path = './chromedriver'
url = 'https://clrweb.littlerock.state.ar.us/pub/public_menu.php'
kaggle_path = './kaggle'