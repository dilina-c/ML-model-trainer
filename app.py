import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
import joblib
import firebase_admin
from firebase_admin import credentials,firestore,storage
from datetime import datetime, timedelta
import os, time

cred = credentials.Certificate("smart-power-adapter-3a443-firebase-adminsdk-4gp49-a276da6c45.json")
firebase_admin.initialize_app(cred,{'storageBucket' : "smart-power-adapter-3a443.appspot.com"})

def trainPredictionModel():
    try:
        while True:
            
            db = firestore.client()
            devices_col_ref = db.collection(u'devices')
            bucket = storage.bucket()
            now = datetime.now()
            three_months_ago = now - timedelta(days=30)
            data=[]
            print("data retrieving from firebase....")
            for device_doc_snap in devices_col_ref.stream():
                device_id = device_doc_snap.id
                readings_col_ref=device_doc_snap.reference.collection(u'readings')
                print("data retrieving from "+ device_id)
                for reading_doc_snap in readings_col_ref.where(u"time", u">=", three_months_ago.timestamp()).stream():
                    datum=reading_doc_snap.to_dict()
                    datum["isOn"] = True if datum["i"] > 0.01 else False
                    datum["day_of_week"] = datetime.fromtimestamp(datum["time"]/1000).weekday()
                    datum["time_of_day"] = datetime.fromtimestamp(datum["time"]/1000).strftime("%I")
                    datum["power"] = datum["i"]*datum["v"]
                    data.append(datum)
                print("data retrieved")
                df= pd.DataFrame.from_dict(data)

                X1 = df[['time_of_day', 'day_of_week']]
                y1 = df['isOn']

                model1 = RandomForestClassifier()
                model1.fit(X1.values, y1.values)

                fileName1 = device_id +'_anomaly.joblib'
                joblib.dump(model1,f'{fileName1}')
                print("Anamoaly model saved for device "+ device_id)
                blob = bucket.blob(fileName1)
                blob.upload_from_filename(fileName1)
                os.remove(fileName1)
                print("Anomaly detection model uploaded to firebase for device "+ device_id)

                # model for power consumption

                hourly_data = df.groupby(['day_of_week', 'time_of_day']).agg({'power': ['mean', 'std']})
                hourly_data.columns = ['_'.join(col).rstrip('_') for col in hourly_data.columns.values]

                hourly_data = hourly_data.reset_index()
                hourly_data = hourly_data[['day_of_week', 'time_of_day', 'power_mean', 'power_std']]

                X2 = hourly_data[['time_of_day', 'day_of_week']]
                y2 = hourly_data['power_mean']

                model2 = RandomForestRegressor(n_estimators=100, random_state=42)
                model2.fit(X2.values, y2.values)

                fileName2= device_id +'_power_consumption.joblib'
                joblib.dump(model2,f'{fileName2}')
                print("Power consumption detection model saved for device "+ device_id)
                blob = bucket.blob(fileName2)
                blob.upload_from_filename(fileName2)
                os.remove(fileName2)
                print("Power consumption detection model uploaded to firebase for device "+ device_id)

            print("model training completed")
            time.sleep(60*60*6)
    except Exception as e: 
        print(e)
        

if __name__ == "__main__":
    trainPredictionModel()
