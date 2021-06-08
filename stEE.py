from random import shuffle
from ee import data, image
import streamlit as st
import pandas as pd
import datetime
from datetime import date, timedelta
from geopy.geocoders import Nominatim
from streamlit_folium import folium_static
import folium
import ee
import plotly.express as px
from sklearn.model_selection import TimeSeriesSplit
from sklearn.neighbors import KNeighborsRegressor
from sklearn import tree
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import train_test_split
import numpy as np
import time


ee.Initialize()

@st.cache
def getCoordinates(user_input):
    if(len(user_input.strip())==0):
        user_input="Colombia"
    locator = Nominatim(user_agent="myGeocoder")
    location = locator.geocode(user_input)
    return location.latitude,location.longitude

@st.cache
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

def add_ee_layer(self, ee_image_object, vis_params, name):
    """Adds a method for displaying Earth Engine image tiles to folium map."""
    map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)
    folium.raster_layers.TileLayer(
        tiles=map_id_dict['tile_fetcher'].url_format,
        attr='Map Data &copy; <a href="https://earthengine.google.com/">Google Earth Engine</a>',
        name=name,
        overlay=True,
        control=True
    ).add_to(self)

def createMap(idate,fdate,lat,lon,data):
    folium.Map.add_ee_layer = add_ee_layer
    i_date = f'{idate.year}-{idate.month}-{idate.day}'
    f_date = f'{fdate.year}-{fdate.month}-{fdate.day}'
    my_map = folium.Map(location=[lat, lon], zoom_start=7)
    for name in data.keys():
        tile=data[name]['image'].select(data[name]['param']).filterDate(i_date, f_date)
        tile=tile.mean()
        my_map.add_ee_layer(tile, data[name]['vis_params'], name)

    folium.LayerControl(collapsed = False).add_to(my_map)
    return my_map

def createModels(data,param):
    X_train, X_test, y_train, y_test = train_test_split(data['time'],data[param], test_size=0.33,shuffle=False)
    models = []
    models.append(('KN', KNeighborsRegressor()))
    models.append(('DT',tree.DecisionTreeRegressor()))    
    modelInformation={}
    tscv = TimeSeriesSplit(n_splits=10)
    for name, model in models:
        X_train=np.array(X_train)
        X_train=X_train.reshape(-1, 1)
        y_train=np.array(y_train)
        trainModel=model.fit(X_train,y_train)
        cv_results = cross_val_score(model, X_train, y_train, cv=tscv, scoring='r2')
        modelInformation[name]={'trainModel':trainModel,'cv_results':cv_results}     
    return modelInformation

def timeGraphs(data,lat,lon,area):
    point=ee.Geometry.Point(lat,lon)
    graphs=[]
    models={}
    for name in data.keys():
        info=data[name]['image'].select(data[name]['param']).getRegion(point,area).getInfo()      
        info=pd.DataFrame(info)
        info=info.dropna()
        info.columns=info.iloc[0]
        info=info.iloc[1:]  
        info["source"]="Real"
        info=info[["time",data[name]['param'],"source"]]
        info[data[name]['param']]=[(d/10000)*224 for d in info[data[name]['param']]]
        models[name]=createModels(info,data[name]['param'])
        for model_name in models[name].keys():
            temp=info[["time","source"]].copy()
            temp["source"]=model_name
            dataTime=np.array(temp['time'])
            dataTime=dataTime.reshape(-1,1)
            temp[data[name]['param']]=list(models[name][model_name]['trainModel'].predict(dataTime))
            info=info.append(temp)
        info['time'] = pd.to_datetime(info['time'], unit='ms')
        fig=px.scatter(info,x="time",y=data[name]['param'],title=f'{name} over time',color="source")
        graphs.append(fig)
    return graphs,models

def unix_time_millis():
    return (datetime.datetime.now() - datetime(1970, 1, 1)).total_seconds() * 1000.0

def main():
    st.header("POC")
    start_date=st.sidebar.date_input("Start Date",value=datetime.date.today()-timedelta(days=20))
    end_date=st.sidebar.date_input("End Date",value=datetime.date.today()-timedelta(days=7))
    area=st.sidebar.slider("Distance from center (m)",min_value=100,max_value=100000,value=500)
    user_input = st.text_input("Search for city or country", "Paris")
    lat,lon=getCoordinates(user_input)
    data=loadImagesAndViz()
    my_map=createMap(start_date,end_date,lat,lon,data)
    st.subheader("Pollutants Map")
    folium_static(my_map)    
    st.subheader("Air Quality Categories for Pollutant")
    st.dataframe(pd.read_excel('TableAQI.xlsx'))
    st.subheader("Data")
    st.text(f'Latitude of Place: {lat}')
    st.text(f'Longitude of Place: {lon}')
    st.text(f'Sample Area from place: {area}')
    graphs,models=timeGraphs(data,lat,lon,area)
    for g in graphs:
        st.plotly_chart(g)
    st.subheader("Predict Today")
    for pollutant in models.keys():
        st.text(f'{pollutant}')
        for model in models[pollutant].keys():
            dataTime=np.array(int(round(time.time() * 1000)))
            dataTime=dataTime.reshape(-1, 1)
            pred=models[pollutant][model]['trainModel'].predict(dataTime)
            st.text(f'\t{model}: {pred} ppb')
    


if __name__=="__main__":
    main()