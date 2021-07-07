import ee
from sklearn.neighbors import KNeighborsRegressor
from sklearn import tree
import numpy as np
import flask
from flask import request,jsonify
import pickle
import pandas as pd
import time

#Average tropospheric height
AVERAGE_TROPOSPHERE_HEIGHT_M=1000
#Initializes connection to Google Earth Engine
ee.Initialize()
#Prediction model
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

app = flask.Flask(__name__)
app.config["DEBUG"] = True

@app.route('/', methods=['GET'])
def home():
    return "<h1>Aerovengers REST API</h1>"

@app.route('/api/prediction',methods=['POST'])
def predictAQIPollutants():
    req=request.json
    point=ee.Geometry.Point(req["lat"],req["lon"])
    resp={}
    dbfile = open('infoImagesAndViz', 'rb')    
    data = pickle.load(dbfile)
    for name in data.keys():
        info=data[name]['image'].select(data[name]['param']).getRegion(point,req["area"]).getInfo()      
        info=pd.DataFrame(info)
        info=info.dropna()
        info.columns=info.iloc[0]
        info=info.iloc[1:]  
        info["source"]="Real"
        info=info[["time",data[name]['param'],"source"]]
        info[data[name]['param']]/=AVERAGE_TROPOSPHERE_HEIGHT_M
        info[data[name]['param']]*=data[name]['M']*1000
        model=createModels(info,data[name]['param'])
        dataTime=np.array(int(round(time.time() * 1000)))
        dataTime=dataTime.reshape(-1, 1)
        kn_pred=model["KN"]["trainModel"].predict(dataTime)[0]
        tree_pred=model["DT"]["trainModel"].predict(dataTime)[0]
        avg=(kn_pred+tree_pred)/2
        pred=determineAQI(avg,name)
        resp[name]={"KN":kn_pred,"DT":tree_pred,"avg":avg,"status":pred}
    return jsonify(resp)
@app.route('/api/historic/CO', methods=['POST'])
def historicCO():
    req=request.json
    point=ee.Geometry.Point(req["lat"],req["lon"])
    dbfile = open('infoImagesAndViz', 'rb')    
    data = pickle.load(dbfile)
    info=data["CO"]['image'].select(data["CO"]['param']).getRegion(point,req["area"]).getInfo()      
    info=pd.DataFrame(info)
    info=info.dropna()
    info.columns=info.iloc[0]
    info=info.iloc[1:]  
    info=info[["time",data["CO"]['param']]]
    info[data["CO"]['param']]/=AVERAGE_TROPOSPHERE_HEIGHT_M
    info[data["CO"]['param']]*=data["CO"]['M']*1000
    info=info.rename(columns={data["CO"]['param']: 'CO'})
    return jsonify(info.to_dict())
@app.route('/api/historic/NO2', methods=['POST'])
def historicNO2():
    req=request.json
    point=ee.Geometry.Point(req["lat"],req["lon"])
    dbfile = open('infoImagesAndViz', 'rb')    
    data = pickle.load(dbfile)
    info=data["NO2"]['image'].select(data["NO2"]['param']).getRegion(point,req["area"]).getInfo()      
    info=pd.DataFrame(info)
    info=info.dropna()
    info.columns=info.iloc[0]
    info=info.iloc[1:]  
    info=info[["time",data["NO2"]['param']]]
    info[data["NO2"]['param']]/=AVERAGE_TROPOSPHERE_HEIGHT_M
    info[data["NO2"]['param']]*=data["NO2"]['M']*1000
    info=info.rename(columns={data["NO2"]['param']: 'NO2'})
    return jsonify(info.to_dict())
@app.route('/api/historic/SO2', methods=['POST'])
def historicSO2():
    req=request.json
    point=ee.Geometry.Point(req["lat"],req["lon"])
    dbfile = open('infoImagesAndViz', 'rb')    
    data = pickle.load(dbfile)
    info=data["SO2"]['image'].select(data["SO2"]['param']).getRegion(point,req["area"]).getInfo()      
    info=pd.DataFrame(info)
    info=info.dropna()
    info.columns=info.iloc[0]
    info=info.iloc[1:]  
    info=info[["time",data["SO2"]['param']]]
    info[data["SO2"]['param']]/=AVERAGE_TROPOSPHERE_HEIGHT_M
    info[data["SO2"]['param']]*=data["SO2"]['M']*1000
    info=info.rename(columns={data["SO2"]['param']: 'SO2'})
    return jsonify(info.to_dict())


app.run()