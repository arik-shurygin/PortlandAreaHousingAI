import re
import time

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
import sklearn

zips=[]
#elementerySchools = []
#middleSchools = []
#highSchools = []
def scrapewebpage(address, driver, dict):
    driver.get(address)
    time.sleep(2)
    content = driver.page_source
    soup = BeautifulSoup(content, features="html.parser")
    for div in soup.findAll('div', attrs={'class':'si-listing'}):
        driver.start_client()
        street=div.find('div', attrs={'class':'si-listing__title-main'})
        zip=div.find('div', attrs={'class':'si-listing__title-description'})
        price=div.find('div', attrs={'class':'si-listing__photo-price'})
        i = 0
        bed = "Error"
        bath = "Error"
        squarefeet = "Error"
        for a in div.findAll('div', attrs={'class': 'si-listing__info-value'}):
            if i ==0:
                bed = a
            elif i ==1:
                bath = a
            else:
                squarefeet = a
            i += 1

        if(bed != "Error" and bath != "Error" and squarefeet != "Error"):
            #Cleaning up the text to remove a variety of characters and strings
            street = street.text.split("#")[0].split("Unit")[0]
            zips.append(zip.text)
            price = price.text.split()[0].replace(',', '').strip('\"')
            bed = bed.text.strip('\n').strip('\t').strip('\"').strip(' ')
            bath = bath.text.strip('\n').strip('\t').strip('\"').strip(' ')
            squarefeet = squarefeet.text.strip('\n').strip('\t').strip(' ').strip('\"').replace(',', '')
            dict.__setitem__(street, [price, squarefeet, bed, bath])
"""
takes an address and looks up information about that addresses public school district and crime statistics
will remove homes from a provided dictionary that do not match to a home on record
Parameters:
           address: address being looked up in the system
           driver: chrome driver opperating the scraper
           returndict: dictionary being updated when/if a home can not be found
Required: driver != None, returndict != None, www.portlandmaps.com is up and running
returns: None
Modifies: returndict: removes homes not found on portlandmaps.com from this dictionary
"""
def gatherCrimeData(address, driver, returndict):
    validAddress = False
    validYearBuilt = False
    driver.get("https://www.portlandmaps.com/")
    time.sleep(3)
    driver.find_element_by_id("search_input").send_keys(address + "\n")
    time.sleep(3)
    content = driver.page_source
    soup = BeautifulSoup(content, features="html.parser")
    infopage = soup.find('dl', attrs = {"class": "dl-horizontal"})
    yearbuilt = "error"
    if infopage != None:
        test = infopage.find('dt').text
        if test == "Year Built":
            yearbuiltrough = infopage.find('dd').text
            if any(char.isdigit() for char in yearbuiltrough):
                validYearBuilt = True
                yearbuilt = re.sub("[^0-9]", "", yearbuiltrough)
    totalTax = "error"
    for div in soup.find_all('div', attrs={'class':"panel panel-default"}):
        i = 0
        if div.find("div", {"id": "schools"}) != None:
            elementrySchool = "error"
            middleSchool = "error"
            highSchool = "error"
            for school in div.find('dl', attrs={'class': "dl-horizontal"}).find_all("dd"):
                if i == 1:
                    elementrySchool = school.text
                elif i ==2:
                    middleSchool = school.text
                elif i ==3:
                    highSchool = school.text
                i += 1
            if elementrySchool != "error" and middleSchool != "error" and highSchool != "error" and totalTax != "error":
                home = returndict.get(address)
                home.append(elementrySchool)
                home.append(middleSchool)
                home.append(highSchool)
                home.append(yearbuilt)
                validAddress = True
        if div.find("div", {"id": "assessor"}) != None:
            j = 0
            for home in div.findAll("blockquote"):
                if i ==2:
                    for tax in home.findAll("dd"):
                        if j ==1:
                            totalTax = tax.text
                        j += 1
                    #break
                i +=1
            if totalTax != "error":
                returndict.get(address).append(totalTax.strip("\"").strip(",").split(".")[0])
    #remove element if not found in the database
    if not validAddress or not validYearBuilt:
        del returndict[address]
"""
Scrapes a collection of housing data using a mix of realtor sites and portland area provided school districts and
predicted tax / crime data by region. Writes data out to a CSV file and returns a dictionary of the same data.
Parameters: fileName: name of the CSV file you would like to overwrite/create(if not existing) containing housing data
Assumptions: That the following sites are up and functional:
         - https://www.findhousesinoregon.com/property-search/results/?searchid=125152&sortby=m.DateListed%20DESC&has
           photo=1&regtype=in&awid=houses%20for%20sale%20in%20portland%20or&gclid=Cj0KCQiArdLvBRCrARIsAGhB_sydmIybye1a
           UAqfA8bIcg5fmPyc6AEWTNv6nTPCDae37QpeEJqt4jgaArWHEALw_wcB
         - https://www.portlandmaps.com/
         - fileName ends with the .csv extension
Returns:
         A dictionary of type <Home address, Array of information about the home> in which the array follows the format
         of [price, square footage, beds, baths, Total taxes on the property, Elementary school, Middle school, 
         High school, predicted property tax, and year built

         Updates a CSV file named "homes.CSV" to include the same data as the dictionary in CSV format.
"""
def startScrape(fileName):
    driverOriginal = webdriver.Chrome("C:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe")
    returnDict = dict()
    for i in range(146):
        if i >= 1:
            scrapewebpage("https://www.findhousesinoregon.com/property-search/results/?searchid=125152&sortby=m.DateListed%20DESC&hasphoto=1&regtype=in&awid=houses%20for%20sale%20in%20portland%20or&gclid=Cj0KCQiArdLvBRCrARIsAGhB_sydmIybye1aUAqfA8bIcg5fmPyc6AEWTNv6nTPCDae37QpeEJqt4jgaArWHEALw_wcB/#pagenum_"+ str(i) + "/",
                          driverOriginal, returnDict)

    dictcopy = dict(returnDict)
    for address in returnDict.keys():
        gatherCrimeData(str(address), driverOriginal, dictcopy)

    returnDict = dictcopy
    #converting dictionary into arrays to use panda and transfer to csv
    streets2, beds2, baths2, squarefootages2, prices2, elementerySchools, middleSchools, highSchools, taxes, yearsbuilt\
        = [], [], [], [], [], [], [], [], [], []
    for home in returnDict.keys():
        homeinfo = returnDict.get(home)
        if len(homeinfo) == 9:
            streets2.append(home)
            prices2.append(homeinfo[0])
            squarefootages2.append(homeinfo[1])
            beds2.append(homeinfo[2])
            baths2.append(homeinfo[3])
            taxes.append(homeinfo[4])
            elementerySchools.append(homeinfo[5])
            middleSchools.append(homeinfo[6])
            highSchools.append(homeinfo[7])
            yearsbuilt.append(homeinfo[8])
    df = pd.DataFrame({'Street': streets2, 'Price': prices2, "Beds": beds2, "Baths": baths2,
                       "Square Footage": squarefootages2, 'Total Taxes': taxes, 'Elementary School': elementerySchools,
                       'Middle School': middleSchools, 'High School': highSchools, 'Year built': yearsbuilt})
    df.to_csv(fileName, index=False, encoding='utf-8')
    return returnDict


startScrape("homesUpdated2.csv")