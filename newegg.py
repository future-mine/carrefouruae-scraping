'''

This short program utilizes the tools of requests and beautiful soup in order to web scrape information from the
products page of Newegg and parses it into a useful CSV data file for analysis.

'''
import re
import secrets
import pymysql
import json
from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
from os.path  import basename
import PySimpleGUI as sg
import csv

db = ''
def get_html(url):
    '''
        Accepts a single URL argument and makes an HTTP GET request to that URL. If nothing goes wrong and
        the content-type of the response is some kind of HTMl/XML, return the raw HTML content for the
        requested page. However, if there were problems with the request, return None.
    '''
    try:
        with closing(get(url, stream=True)) as resp:
            if quality_response(resp):
                return resp.content
            else:
                return None
    except RequestException as re:
        print(f"There was an error during requests to {url} : {str(re)}")
        return None

def dbconnect():
    try:
        db = pymysql.connect(
            host='localhost',
            user='root',
            passwd='',
            db='market_food1'
        )
    except Exception as e:
        sys.exit("Can't connect to database")
    return db

def insertDb(brandname, itemname, price, packsize, origin, ingredients, allergy, imagenames, category):
    # try:
    #     with db.cursor() as cursor:
    #         cursor = db.cursor()
    #         print(brandname, itemname, price, packsize, origin, ingredients, allergy, imagenames)
    #         add_item  = ("INSERT INTO foods "
    #                     "(brandname, itemname, price, packsize, origin, allergy) "
    #                     "VALUES (%s, %s, %s, %s, %s, %s,%s,%s)")
    #         data_item = (brandname, itemname, price, packsize, origin, allergy)
    #         print(cursor.execute(add_item,data_item))
    #         db.commit()
    #         cursor.close()
    # except Exception as e:
    #     print (e)
    try:
        with db.cursor() as cursor:
            cursor = db.cursor()
            sql = "INSERT INTO `foods` (`brandname`, `itemname`,`price`,`packsize`,`origin`,`ingredients`,`allergy`,`imagenames`, `category`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            cursor.execute(sql, (brandname, itemname, price, packsize, origin, ingredients, allergy, imagenames, category))
            db.commit()
            cursor.close()
    except Exception as e:
        print (e)


def quality_response(resp):
    '''
        Returns true if response seems to be HTML, false otherwise.
    '''
    content_type = resp.headers["Content-Type"].lower()
    return (resp.status_code == 200 and content_type is not None and content_type.find("html") > - 1)

def get_products_url_one(url):
    ''' 
        Downloads the webpage, iterates over <div> elements and picks out the brand, product name, product
        price and shipping costs into a list.
    '''

    base_url = "https://www.carrefouruae.com"
    # print(url)
    # url = "https://www.carrefouruae.com/mafuae/en/bio-organic-food/c/F1200000?&qsort=relevance&pg=1"
    response = get_html(url)
    # print(response)

    items_desc = []
    if response is not None:
        soup = BeautifulSoup(response, "html.parser")
        products = soup.find_all("div", {"class": "plp-list__item"})
        for product in products:

            product_url = product.find("a", {"class": "js-gtmProdData"}).get('href')
            items_desc.append(product_url)

            # print(product_url)

        return items_desc
    # else:
    #     return 
    raise Exception(f"There was an error retrieving contents at {url}")

def generate_unique_key(size=15):
    return secrets.token_urlsafe(size)[:size]

def get_item(url):
    response = get_html(url)
    items = []
    if response is not None:
        soup = BeautifulSoup(response, "html.parser")
        item = soup.find("div", {"class": "productinfo__header"})
        if(item is None):
            return
        print(type(item))

        if(item.find("a", {"class": "fc--blue fw--semibold"})):
            brand_name = item.find("a", {"class": "fc--blue fw--semibold"}).text
        else:
            brand_name = ''
        print(brand_name)
        # .p.a.text 
        
        item_name = item.find("h1", {"class": "productinfo__name"}).text

        print(item_name)
        price_init = item.find("h2", {"class": "productinfo__price"}).text 
        price = " ".join(price_init.split())       

        print(price)

        item1 = soup.find("div", {"class": "hidden-sm g-xs-nopad productinfo__header"})
        if(item1.find(text = re.compile('Pack size\d*'))):
            pack_size = item1.find(text = re.compile('Pack size\d*')).split(':')[1]
        else:
            pack_size = ''
        print(pack_size) 

        if(len(item1.find_all('span', {"class": "c--flex--wide"})) > 1):
            origin = item1.find_all('span', {"class": "c--flex--wide"})[1].find('strong').text
        else:
            origin = ''
        # origin = item1.find_all('span')
        # , text = re.compile('Origin:\d*')
        print(origin)
        if(soup.find('h3', text = 'Ingredients')):
            ingredients = soup.find('h3', text = 'Ingredients').parent.p.text.split(', ')
        else:
            ingredients = []
        ingredients_json = json.dumps(ingredients)
        print(ingredients_json)
        if(soup.find('h3', text = 'Allergy Information')):
            allergy = soup.find('h3', text = 'Allergy Information').parent.p.text
        else:
            allergy = ''

        print(allergy)

        imagenames = []
        imageitem = soup.find('div', {'class':'productinfo-slider slick'}).find_all('div', recursive = False)
        # imageitem = soup.find_all('img')
        # imageitem = soup.find_all("div", {"class": "slick-track"})
        for img in imageitem:
            imagelink = img.find('img')['data-lazy']
            imagelink_split = imagelink.split('.')
            print(imagelink, imagelink_split)
            image_name = generate_unique_key(100)
            image_name_jpg = image_name + '.jpg'
            print(image_name)
            img_data = get(imagelink).content
            while True:
                print("imagekkkkk")
                if (img_data):
                    break
                img_data = get(imagelink).content
            with open('images/' + image_name_jpg, 'wb') as handler:
                handler.write(img_data)
            imagenames.append(image_name_jpg)
        imagenames_json = json.dumps(imagenames)
        category_name = []
        if(soup.find('ul', {'class':'comp-breadcrumb hidden-xs'})):
            categorys = soup.find('ul', {'class':'comp-breadcrumb hidden-xs'}).find_all('li', recursive = False)
            print(len(categorys))
            for i in range(1,(len(categorys)-1)):
                category_name.append(categorys[i].a.text)
        else:
            categerys = []
        category_name_json = json.dumps(category_name)
        print(category_name)


        insertDb(brand_name, item_name, price, pack_size, origin, ingredients_json, allergy, imagenames_json, category_name_json)
        return True
    else:
        return False
    #     return 
    # raise Exception(f"There was an error retrieving contents at {url}")






        

def read_products():
    ''' 
        Accepts a single item list as an argument, proceses through the list and writes all the products into
        a single CSV data file.
    '''
    headers = "itemurls\n"
    filename = "itemurls1.csv"
    itemlll = []
    try: 
        f = open(filename, "r")
        items = f.read()
        itemlll = items.split('\n')
        f.close()

        return itemlll
    except:
        print("There was an error writing to the CSV data file.")
    
if __name__ == "__main__":

    db = dbconnect()
    print("Getting list of products and descriptions...")
    base_url = "https://www.carrefouruae.com"

    # Event Loop to process "events" and get the "values" of the inputs
    item_desc = []
    item_desc = read_products()
    print(len(item_desc))
    idd = 0
    # for item_url in item_desc:
    #     if(len(item_url) > 1):
    #         # if (idd > 9):
    #         #     break
    #         while True:
    #             flag = get_item(base_url + item_url)
    #             if (flag):
    #                 break
    #         idd = idd + 1
    # print(idd)
    # urlggg = '/mafuae/en/baby-products/milk-food-juices/baby-toddler-meals/flours-cereals-rice/blevit-d-instant-tea-for-colic-200g/p/1420521'
    # get_item(base_url + urlggg)
    for i in  range(3518 , len(item_desc)):
        item_url = item_desc[i]

        # if(i >= len(item_desc)):
        #     break
        if(len(item_url) > 1):
            # if (idd > 9):
            #     break
            flag = get_item(base_url + item_url)

            idd = idd + 1
            print(i)
    print(idd)


    print("...done\n")

    print("Writing product information to a CSV file...")
    # write_products(item_desc)
    print("...done\n")