from datetime import time
from time import sleep
import ee
from ee import data, image
import pickle
from datetime import datetime

ee.Initialize()

def loadImagesAndViz():
    data={}
    #Carbon monoxide
    image=ee.ImageCollection("COPERNICUS/S5P/NRTI/L3_CO")
    vis_params = {
        "min": 0,
        "max": 0.05,
        "palette": ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red']
    }
    data['CO']={'image':image,'vis_params':vis_params,'param':'CO_column_number_density'}
    #Nitrogen Dioxide
    image=ee.ImageCollection("COPERNICUS/S5P/NRTI/L3_NO2")
    vis_params = {
        "min": 0,
        "max": 0.0002,
        "palette": ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red']
    }
    data['NO2']={'image':image,'vis_params':vis_params,'param':'NO2_column_number_density'}
    #Ozone
    image=ee.ImageCollection("COPERNICUS/S5P/NRTI/L3_O3")
    vis_params = {
        "min": 0.12,
        "max": 0.15,
        "palette": ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red']
    }
    data['o3']={'image':image,'vis_params':vis_params,'param':'O3_column_number_density'}
    #Sulfur dioxide
    image=ee.ImageCollection("COPERNICUS/S5P/NRTI/L3_SO2")
    vis_params = {
        "min": 0.0,
        "max": 0.0005,
        "palette": ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red']
    }
    data['SO2']={'image':image,'vis_params':vis_params,'param':'SO2_column_number_density'}
    
    return data
def Job():
    while True:
        data=loadImagesAndViz()
        dbfile = open('infoImagesAndViz', 'ab')
        pickle.dump(data, dbfile)                     
        dbfile.close()
        today = datetime.now()
        print("Last Update: ",today.strftime("%d/%m/%Y %H:%M:%S"))
        sleep(86400)
if __name__=="__main__":
    Job()