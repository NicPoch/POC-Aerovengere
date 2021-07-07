from datetime import time
from time import sleep
import ee
import pickle
from datetime import datetime

ee.Initialize()

def loadImagesAndViz():
    data={}
    #Carbon monoxide
    image=ee.ImageCollection("COPERNICUS/S5P/NRTI/L3_CO")
    vis_params = {
        "min": 0,
        "max": 50500,
        "palette": ['green', 'yellow', 'orange', 'red', 'purple', 'brown']
    }
    data['CO']={'image':image,'vis_params':vis_params,'param':'CO_column_number_density','M':28.01}
    #Nitrogen Dioxide
    image=ee.ImageCollection("COPERNICUS/S5P/NRTI/L3_NO2")
    vis_params = {
        "min": 0,
        "max": 2.049,
        "palette": ['green', 'yellow', 'orange', 'red', 'purple', 'brown']
    }
    data['NO2']={'image':image,'vis_params':vis_params,'param':'NO2_column_number_density','M':46.0055}
    #Ozone
    """image=ee.ImageCollection("COPERNICUS/S5P/NRTI/L3_O3")
    vis_params = {
        "min": 0,
        "max": 0.375,
        "palette": ['green', 'yellow', 'orange', 'red', 'purple', 'yellow', 'brown']
    }
    data['o3']={'image':image,'vis_params':vis_params,'param':'O3_column_number_density','M':48/3}"""
    #Sulfur dioxide
    image=ee.ImageCollection("COPERNICUS/S5P/NRTI/L3_SO2")
    vis_params = {
        "min": 0.0,
        "max": 1004,
        "palette": ['green', 'yellow', 'orange', 'red', 'purple', 'brown']
    }
    data['SO2']={'image':image,'vis_params':vis_params,'param':'SO2_column_number_density','M':64.066}
    
    return data
def Job():
    while True:
        data=loadImagesAndViz()
        dbfile = open('infoImagesAndViz', 'wb')
        pickle.dump(data, dbfile)                     
        dbfile.close()
        today = datetime.now()
        print("Last Update: ",today.strftime("%d/%m/%Y %H:%M:%S"))
        sleep(86400)
if __name__=="__main__":
    Job()
