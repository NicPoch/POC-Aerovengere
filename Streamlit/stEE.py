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
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsRegressor
from sklearn import tree
import numpy as np
import time
import pickle

AVERAGE_TROPOSPHERE_HEIGHT_M=1000

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
    dbfile = open('infoImagesAndViz', 'rb')     
    data = pickle.load(dbfile)    
    return data

def add_ee_layer(self, ee_image_object, vis_params, name):
    """Adds a method for displaying Earth Engine image tiles to folium map."""
    map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)
    folium.raster_layers.TileLayer(
        tiles=map_id_dict['tile_fetcher'].url_format,
        attr='Map Data &copy; <a href="https://earthengine.google.com/">Google Earth Engine</a>',
        name=name,
        overlay=False,

        control=True
    ).add_to(self)

def createMap(idate,fdate,lat,lon,data):
    folium.Map.add_ee_layer = add_ee_layer
    i_date = f'{idate.year}-{idate.month}-{idate.day}'
    f_date = f'{fdate.year}-{fdate.month}-{fdate.day}'
    my_map = folium.Map(location=[lat, lon], zoom_start=7)
    for name in data.keys():
        try:
            tile=data[name]['image'].select(data[name]['param']).filterDate(i_date, f_date)
            tile=tile.mean()
            tile=tile.divide(AVERAGE_TROPOSPHERE_HEIGHT_M)
            tile=tile.multiply(data[name]['M']*1000)
            my_map.add_ee_layer(tile, data[name]['vis_params'], name)
        except:
            pass

    folium.LayerControl(collapsed = False).add_to(my_map)
    return my_map

def createModels(data,param):
    X_train, y_train=data['time'],data[param]
    models = []
    models.append(('KN', KNeighborsRegressor(n_neighbors=5,weights='uniform')))    
    models.append(('DT',tree.DecisionTreeRegressor(max_depth=8)))    
    modelInformation={}
    for name, model in models:
        X_train=np.array(X_train)
        X_train=X_train.reshape(-1, 1)
        y_train=np.array(y_train)
        trainModel=model.fit(X_train,y_train)
        modelInformation[name]={'trainModel':trainModel}     
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
        info[data[name]['param']]/=AVERAGE_TROPOSPHERE_HEIGHT_M
        info[data[name]['param']]*=data[name]['M']*1000
        models[name]=createModels(info,data[name]['param'])
        for model_name in models[name].keys():
            temp=info[["time","source"]].copy()
            temp["source"]=model_name
            dataTime=np.array(temp['time'])
            dataTime=dataTime.reshape(-1,1)
            pred=models[name][model_name]['trainModel'].predict(dataTime)
            temp[data[name]['param']]=pred
            info=info.append(temp)
        info['time'] = pd.to_datetime(info['time'], unit='ms')
        fig=px.scatter(info,x="time",y=data[name]['param'],title=f'{name} over time',color="source")
        graphs.append(fig)
    return graphs,models

def unix_time_millis():
    return (datetime.datetime.now() - datetime(1970, 1, 1)).total_seconds() * 1000.0

def determineAQI(avg,p):
    if(p=='CO'):
        if(avg<=4500):
            return "Good"
        if(avg<=9500):
            return "Moderate"
        if(avg<=12500):
            return  "Unhealthy for some groups"
        if(avg<=15500):
            return "Unhealthy"
        if(avg<=30500):
            return "Very Unhealthy"
        return "Hazardous"
    if(p=='NO2'):
        if(avg<=0.054):
            return "Good"
        if(avg<=0.101):
            return "Moderate"
        if(avg<=0.361):
            return  "Unhealthy for some groups"
        if(avg<=0.65):
            return "Unhealthy"
        if(avg<=1.25):
            return "Very Unhealthy"
        return "Hazardous"
    if(p=='SO2'):
        if(avg<=36):
            return "Good"
        if(avg<=76):
            return "Moderate"
        if(avg<=186):
            return  "Unhealthy for some groups"
        if(avg<=304):
            return "Unhealthy"
        if(avg<=605):
            return "Very Unhealthy"
        return "Hazardous"
    return ""

def main():
    #Header
    st.header("POC Aerovengers")
    st.subheader("Why Air Quality?")
    with open("whyAQ.txt",encoding = 'utf-8') as f:
        text=f.readline()
        st.markdown(text)
    st.subheader("Air Quality Categories for Pollutant")
    st.dataframe(pd.read_csv('TableAQI.csv'))
    #Sidebar
    start_date=st.sidebar.date_input("Start Date",value=datetime.date.today()-timedelta(days=20),min_value=datetime.date(2018,7,4))
    end_date=st.sidebar.date_input("End Date",value=datetime.date.today()-timedelta(days=7),max_value=datetime.date.today()-timedelta(days=7),min_value=start_date)
    area=st.sidebar.slider("Distance from center (m)",min_value=500,max_value=100000,value=1000)
    #Main
    st.subheader("Visualize Pollutants")
    user_input = st.text_input("Search for a city or country", "Paris")
    lat,lon=getCoordinates(user_input)
    data=loadImagesAndViz()
    my_map=createMap(start_date,end_date,lat,lon,data)
    folium_static(my_map)    
    st.subheader(f'Data for {user_input}')
    st.markdown(f'Latitude of Place: {lat}')
    st.markdown(f'Longitude of Place: {lon}')
    st.markdown(f'Sample Area from place: {area} meters')
    graphs,models=timeGraphs(data,lat,lon,area)
    for g in graphs:
        st.plotly_chart(g)
    st.subheader("Predict Today")
    for pollutant in models.keys():
        st.markdown(f'{pollutant}')
        avg=0
        for model in models[pollutant].keys():
            dataTime=np.array(int(round(time.time() * 1000)))
            dataTime=dataTime.reshape(-1, 1)
            pred=models[pollutant][model]['trainModel'].predict(dataTime)
            avg=0.5*pred[0]
            st.markdown(f'  \t{model}: {round(pred[0],5)} ppb')
        st.markdown(f'AQI: {determineAQI(avg,pollutant)}')
    
if __name__=="__main__":
    main()
