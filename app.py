import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

import joblib
import firebase_admin
from firebase_admin import credentials,firestore
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials ,storage
import os
import time


def trainPredictionModel():
    try:
        while True:
            cred = credentials.Certificate("smart-power-adapter-3a443-firebase-adminsdk-4gp49-a276da6c45.json")
            firebase_admin.initialize_app(cred,{'storageBucket' : "smart-power-adapter-3a443.appspot.com"})
            db = firestore.client()
            devices_col_ref = db.collection(u'devices')
            bucket = storage.bucket()
            now = datetime.now()
            three_months_ago = now - timedelta(days=2)
            data=[]
            print("data retrieving from firebase....")
            for device_doc_snap in devices_col_ref.stream():
                device_id = device_doc_snap.id
                readings_col_ref=device_doc_snap.reference.collection(u'readings')
                print("data retrieving from "+ device_id)
                for reading_doc_snap in readings_col_ref.where(u"time", u">=", three_months_ago.timestamp()).stream():
                    datum=reading_doc_snap.to_dict()
                    datum["isOn"] = True if datum["i"] > 0.4 else False
                    datum["day_of_week"] = datetime.fromtimestamp(datum["time"]/1000).weekday()
                    datum["time_of_day"] = datetime.fromtimestamp(datum["time"]/1000).strftime("%I")
                    data.append(datum)
                print("data retrieved")
                df= pd.DataFrame.from_dict(data)

                X = df[['time_of_day', 'day_of_week']]
                y = df['isOn']

                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

                model = RandomForestClassifier()
                model.fit(X_train.values, y_train.values)

                score = model.score(X_test.values, y_test.values)
                
                fileName = device_id +'.joblib'
                joblib.dump(model,f'{fileName}')
                print("model saved for device "+ device_id)
                blob = bucket.blob(fileName)
                blob.upload_from_filename(fileName)
                #os.remove(fileName)
                print("model uploaded to firebase for device "+ device_id)
            print("model training completed")
            time.sleep(60*60*6)
    except Exception as e: 
        print(e)
        

if __name__ == "__main__":
    trainPredictionModel()
