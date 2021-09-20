import os
import requests
import glob
import csv
import re
import time
from datetime import date
from bs4 import BeautifulSoup
from heapq import nsmallest
from haversine import haversine,Unit

'''
Following code are used to get 500 regions's name in Victoria and download html of the Domain page.
'''

# suburbs.csv download from github (https://github.com/michalsn/australian-suburbs).
# It used to get regions' name in Victoria and calculate distance between regions and melbourne city.
# Following function get the regions' name of Victoria and calculate the distance. 
# In this project, we only considered 500 regions closest to the city(Melbourne VIC 3000).
def get_suburb_list():
    suburb_dict = {}
    location_mel = (144.97142,-37.82744)
    location_syd = (151.20998,-33.86794)
    with open('suburbs.csv') as suburb_file:
        reader = csv.reader(suburb_file,delimiter=",")
        flag = 0
        for row in reader:
            if flag != 0 and row[4] == 'VIC':
                suburb_name = row[1].lower().replace(" ","-") + "-" + row[4].lower().replace(" ","-") + "-" + row[3].lower().replace(" ","-")
                location = (float(row[14]),float(row[13]))
                distance = haversine(location_mel,location)
                suburb_dict[suburb_name] = distance
            flag = 1
        suburb_list = nsmallest(500, suburb_dict, key = suburb_dict.get)
    return suburb_list,suburb_dict

suburb_list,suburb_dict = get_suburb_list()
print(len(suburb_list))

def write_file(file_path:str, content:str):
    with open(file_path,'w',encoding='utf8') as f:
        f.write(content)

def get_check(html):
    soup = BeautifulSoup(html,features="html.parser")
    no_match_check = soup.select("h3[class='css-1c8ubmt']")
    if no_match_check:
        no_match_text = no_match_check[0].get_text()
        print(no_match_text)
        return False
    else:
        return True

# create folder and download all necessary pages 
download_dir = 'domain_vic_400.com.au'
for r in suburb_list:
    join_dir = f'{download_dir}/{r}'
    os.makedirs(join_dir,exist_ok=True)
    print("download region ==================================================", r)
    for page in range(1,51):
        file_path = f'{join_dir}/{str(page).zfill(3)}.html'
        url = f'https://www.domain.com.au/sold-listings/{r}/?excludepricewithheld=1&page={page}'
        if os.path.isfile(file_path):
            print(f'read from cached: {file_path}')
        else:
            html = requests.get(url).text
            time.sleep(0.2)
            if get_check(html):
                print(page)
                write_file(file_path,html)
                print(f'successfully download: {url}')
            else:
                break




