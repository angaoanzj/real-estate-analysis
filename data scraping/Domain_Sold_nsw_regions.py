import glob
import csv
import re
import os
import requests
from datetime import date
from bs4 import BeautifulSoup
from heapq import nsmallest
from haversine import haversine,Unit

'''
read the html file in folder - domain_vic_400.com.au and extract information of each properties. 
'''

download_dir = 'domain_vic_400_2.com.au'

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
# get download file 
def read_file(file_path:str):
    with open(file_path,'r',encoding='utf8') as f:
        return f.read()

def get_text(element,selector:str):
    tags = element.select(selector)
    return tags[0].getText() if tags else None

# This function helps to extract the infomration of the number beds,baths,parking and landsize of each property
def get_features(element,feature_name:str):
    for feature_item in element.select('span[data-testid=property-features-feature]'):
        if feature_name in str(feature_item):
            item = feature_item.select('span[data-testid=property-features-text-container]')
            if item[0].find(text=True) == '−':
                return '0'
            else:
                return item[0].find(text=True)
        if feature_name == 'Land' and 'm²' in str(feature_item):
            item = feature_item.select('span[data-testid=property-features-text-container]')
            if item[0].find(text=True) == '−':
                return '0'
            else:
                return item[0].find(text=True)
    return None

def get_id(links:str):
    id1 = links.split('/')[-1]
    id2 = id1.split('-')[-1]
    return id2

# This function helps to extract sold date of the property by using regular expression
def parse_time_date(pro_date:str):
    d = re.findall( r'([0-9]{1,2}).([A-Za-z]{3,4}).([0-9]{4})',pro_date)
    (day,month,year) = d[0]
    month = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,'Jul':7,
        'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}[month]
    return date(int(year),int(month),int(day))

# This function helps to extract price by using regular expression
def parse_to_price(price_str:str):
    result = re.findall(r'[0-9,]+',price_str)
    result_price = None
    if result[0]:
        result_price = result[0].replace(',','')
    return result_price

# This function helps to extract information of each properties 
def get_property_info(region,pro_info,region_file,suburb_dict):
    # get the sold channel and sold date 

    card_tag = get_text(pro_info,'span[class=css-1nj9ymt]')
    if "auction" in card_tag:
        sold_location = card_tag.split('auction')[0] + 'auction'
        sold_date = card_tag.split('auction')[1]
    elif "treaty" in card_tag:
        sold_location = card_tag.split('treaty')[0] + 'treaty'
        sold_date = card_tag.split('treaty')[1] 
    else:
        sold_location = None
        sold_date = None
    pro_sold_date = None
    if sold_date:
        pro_sold_date = parse_time_date(sold_date)


    price = get_text(pro_info,'p[class=css-mgq8yx]')
    pro_price = parse_to_price(price)
    address1 = get_text(pro_info,'span[data-testid=address-line1]')
    
    address2 = get_text(pro_info,'span[data-testid=address-line2]')
    if address1:
        temp = address1.split(',')[0]
        address = temp+address2 
    else: 
        address = address2
    
    beds = get_features(pro_info,'Bed')
    Baths = get_features(pro_info,'Bath')
    parking = get_features(pro_info,'Parking')
    land = get_features(pro_info,'Land')

    if land != None:
        l = re.findall(r'([0-9]+)',land)
        land = int(l[0])

    link = pro_info.select('div[class=css-qrqvvg] a')
    link1 = link[0].attrs['href']
    pro_id = get_id(link1)

    building_type = get_text(pro_info,'span.css-693528')
    suburb = region.split('\\')[-1]

    # to avoid repeat properties in the file
    if pro_id not in all_id:
        all_id.append(pro_id)
        distance = suburb_dict[suburb]
        thewriter.writerow([pro_id,str(address),suburb,building_type,sold_location,pro_sold_date,pro_price,beds,
        Baths,parking,land,round(distance,4),link1])

# This function helps to extract html that contains all information of properties in that page.
def parse_listing_page(region:str,region_file:str,suburb_dict:dict):
    html = read_file(region_file)
    soup = BeautifulSoup(html,features="html.parser")
    properties = soup.select('div[data-testid^="listing-card-wrapper"]')
    for pro_info in properties:
        get_property_info(region,pro_info,region_file,suburb_dict)

# This function goes through html file(pages in suburbs) in suburbs folder 
def parse_region_dir(region_dir:str,suburb_dict:dict):
    region = region_dir.split('/')[-1]
    get_region_file = glob.glob(f'{region_dir}/*')
    for region_file in get_region_file:
        parse_listing_page(region,region_file,suburb_dict)

# This function goes through each folder(the suburbs folder) in folder - domain_vic_400.com.au
all_id = []
with open('sold_VIC_2.csv','w',newline='',encoding='utf8') as f:
    thewriter = csv.writer(f)
    thewriter.writerow(['id','address','suburb','type','sold By','sold Date','price','beds',
    'baths','parking','size in m2','distance','url'])
    for region in glob.glob(f'{download_dir}/*'):
        print(region) 
        parse_region_dir(region,suburb_dict)
        
        



