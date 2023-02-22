from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
# import time

# cred = credentials.Certificate("smart-power-adapter-3a443-firebase-adminsdk-4gp49-a276da6c45.json")
cred = credentials.Certificate(
    "smart-adapter-test1-firebase-adminsdk-9nc3j-f8cd8e9177.json")
firebase_admin.initialize_app(cred)

db = firestore.client()
# devices = db.collection(u'devices').document(u'QEIZrUmZGUuzBqRnw0jZ')
# device_data = devices.get()
# # for device in devices:
# #     print(device)
# #     # device_arr= device.to_dict()
# #     return device.to_list()
# if device_data.exists:
#     print(f'Document data: {device_data.to_dict()}')
# else:
#     print(u'No such document!')

# collections = db.collection('cities').document('SF').collections()
# for collection in collections:
#     for doc in collection.stream():
#         print(f'{doc.id} => {doc.to_dict()}')
# docs = db.collection(u'cars').document(u'reg no').collection(u'readings').stream()
# print(docs)
# for doc in docs:
#     print(f'{doc.id} => {doc.to_dict()}')


# doc_ref = db.collection(u'cars').document(u'reg no')
# doc = doc_ref.get().to_dict()
# #print(doc)
# brand = doc["brand"]
# print(brand)
# #print(doc.to_dict())

# doc_ref = db.collection(u'smart plug').document(u'ID 001').collection(u'readings')
# docs = doc_ref.get()
# #read all documents
# for doc in docs:
#     print(doc.to_dict())
#     print(f'{doc.id} => {doc.to_dict()}')


# -------------------------------------- Get the current week number
# import datetime
# import time
# while True:
#     now = datetime.datetime.now()
#     week_number = now.isocalendar()[1]
#     print(f"Week number: {week_number}")

#     # Sleep for a minute
#     time.sleep(60)


devices_col_ref = db.collection(u'devices')
# read all documents
data = []

now = datetime.now()
three_months_ago = now - timedelta(days=30)

for device_doc_snap in devices_col_ref.stream():
    device_id = device_doc_snap.id
    
    readings_col_ref = device_doc_snap.reference.collection(u'readings')
    for reading_doc_snap in readings_col_ref.where(u"time", u">=", three_months_ago.timestamp()).stream():
        # print(reading_doc_snap.to_dict())
        datum = reading_doc_snap.to_dict()

        #print(datum)

        datum["isOn"] = True if datum["i"] > 0.01 else False
        datum["day_of_week"] = datetime.fromtimestamp(datum["time"]).weekday()
        datum["time_of_day"] = datetime.fromtimestamp(datum["time"]).strftime("%I")
        datum["power"] = datum["i"]*datum["v"]       

        data.append(datum)
        #print(data)
        df = pd.DataFrame.from_dict(data)
        #print(df)
        #df.to_csv(device_id + ".csv")


        hourly_data = df.groupby(['day_of_week', 'time_of_day']).agg({'power': ['mean', 'std']})
        hourly_data.columns = ['_'.join(col).rstrip('_') for col in hourly_data.columns.values]

        hourly_data = hourly_data.reset_index()
        hourly_data = hourly_data[['day_of_week', 'time_of_day', 'power_mean', 'power_std']]

        print(hourly_data)


#avg_data = pd.json_normalize(d1)
#d1['time'] = pd.to_datetime(d1['time'], unit='ms')
#d1= d1.set_index('time')


#hourly_data.to_csv("hourly_data.csv", index=True)

X_train, X_test, y_train, y_test = train_test_split(hourly_data[['day_of_week', 'time_of_day']], hourly_data['power_mean'], test_size=0.2, random_state=42)

model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

#y_pred = model.predict([[0,9]])
#mse = mean_squared_error(y_test, y_pred)
#print(y_pred)

output_data = pd.DataFrame(columns=['day_of_week', 'time_of_day', 'power', 'std'])

obj = {}
for day in range(7):
    if day not in obj:
        obj[day] = []
    for hour in range(24):
        power = model.predict([[day, hour]])
        obj[day].append([hour, power[0]])
        
print(obj)