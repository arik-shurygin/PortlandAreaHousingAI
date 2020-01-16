import math

import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
import sklearn
from sklearn import datasets, linear_model, neural_network
from sklearn.metrics import mean_squared_error, r2_score
import statsmodels.api as sm
from scipy import stats
from scipy.stats import kurtosis, skew
import time
import pandas as pd
import re
from bs4 import BeautifulSoup
from selenium import webdriver

'''
A method which, when given a name of a high school in oregon, returns the ranking of that school in oregon

:param name - name of the school / schools in question, may accept 2 schools seperated by a "or" or "/"
:param driver - webdriver used in search, run with selenium package
:param schooldict - dictionary of all schools and their rankings, allows for fast lookups on repeated schools
:returns - ranking of a specific highschool in oregon
:modifies - schooldict is modified with an additional k,v pair key = name, value = ranking. 
            IF the school has not been seen before
:throws - N/A
:requires - No params = null, driver = selenium driver, "name" ends in high school or high schools if two seperated by 
            "or" or "/" ex: beaverton or southridge high schools. ex2: beaverton high school/southridge high school 
'''
def SchoolSearch(name, driver, schooldict):
    if schooldict.__contains__(name):
        print("dict used")
        return schooldict.get(name)
    driver.get("https://www.usnews.com/education/best-high-schools/oregon/rankings")
    time.sleep(3)
    #handles situation in which a home lands inbetween districts, Website data was scraped from usually formats this
    #situation as "HS1 or HS2" or "HS1/HS2", these if elif statement handle both cases, spliting the name and recursevly
    # running this method with each school, choosing the higher ranked school to represent both
    if(name.__contains__("or")):
        school1 = name.split("or")[0].strip() + " High School"
        school2 = name.split("or")[1][:-1].strip()
        ranking1= SchoolSearch(school1, driver, schooldict)
        ranking2= SchoolSearch(school2, driver, schooldict)
        ranking = str(min(int(ranking1), int(ranking2)))
    elif(name.__contains__("/")):
        school1=name.split("/")[0].strip()
        school2=name.split("/")[1].strip()
        ranking1= SchoolSearch(school1, driver, schooldict)
        ranking2= SchoolSearch(school2, driver, schooldict)
        ranking = str(min(int(ranking1), int(ranking2)))
    else:
        driver.find_element_by_id("search-facet-name").send_keys(name + "\n")
        time.sleep(3)
        source = driver.page_source
        soup = BeautifulSoup(source, features="html.parser")
        ranking = soup.find('p', attrs = {"class": "block-tight"}).find('span', attrs = {'class': "text-normal text-strong"}).text.split("-")[0]
        ranking = re.sub("[^0-9]", "", ranking)
    schooldict.__setitem__(name, ranking)
    print(name + " : "+ ranking)
    return ranking
def LoadAndCleanCsv(path):
    dataframe = pd.read_csv(path)
    driverOriginal = webdriver.Chrome("C:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe")
    schooldict = {}
    for i,j in dataframe.iterrows():
        highSchool = j["High School"]
        ranking = SchoolSearch(highSchool, driverOriginal, schooldict)
        priceStripped = j["Price"].split("$")[1]
        taxesStripped = j["Total Taxes"].split("$")[1].replace(',', '')
        bathsStripped = j['Baths'].split('F')[0]
        dataframe.set_value(i, "Price", priceStripped)
        dataframe.set_value(i, "Total Taxes", taxesStripped)
        dataframe.set_value(i, "Baths", bathsStripped)
        dataframe.set_value(i, "High School", ranking)

    dataframe["Price"] = pd.to_numeric(dataframe['Price'])
    dataframe["Total Taxes"] = pd.to_numeric(dataframe['Total Taxes'])
    dataframe["Baths"] = pd.to_numeric(dataframe['Baths'])
    #dataframe["High School"] = pd.to_numeric(dataframe['High School'])
    #displays first 5 elements on the CSV
    #print(dataframe.head())
    #displays the types of all values in CSV
    print(dataframe.dtypes)
    dataframe.to_csv("homesUpdated3.csv")
    #checks for missing values in the CSV
    print(dataframe.isna().any())
    #Describes int values in CSV.
    print(dataframe.describe())
def trainHousingModel(path):
    dataframe = pd.read_csv(path)
    print(dataframe.describe())
    #priceArray = np.asarray(list(map(lambda x: math.log(x, 2), dataframe["Price"])))
    priceArray = dataframe["Price"].__array__()
    inputArray = []
    for i, j in dataframe.iterrows():
        singleHome = []
        singleHome.append(j["Beds"])
        singleHome.append(j["Baths"])
        singleHome.append(j["Square Footage"])
        singleHome.append(j["Total Taxes"])
        singleHome.append(j["High School"])
        singleHome.append(j["Year built"])
        singleHome = np.array(singleHome)
        inputArray.append(singleHome)
    inputArray = np.asarray(inputArray, dtype=np.float)

    housingmodel = sklearn.neural_network.MLPRegressor()
    housingmodel.batch_size = 4
    housingmodel.fit(X=inputArray, y=priceArray)
    perdictions = []
    #perdictions = housingmodel.predict([[2,2,1500,24386,9,2006], [3,2,2102,5789,68,1987]])
    map(lambda x: perdictions.append(housingmodel.predict(x)), inputArray.tolist())
    i = 0;
    for perdiction in perdictions:
        print(math.pow(perdiction.get(0) - priceArray[i], 2))
        i += 1

    #700,000 and 405,000

    print(perdictions)
    print("Model best loss: ")
    print(housingmodel.best_loss_)
def buildHousingModel():
    #try:
    #LoadAndCleanCsv("../homesUpdated2.csv")
    #except:
     #   print("An error has occured when loading and cleaning the CSV")
    trainHousingModel("../homesCleaned.csv")

buildHousingModel()