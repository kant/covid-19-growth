import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import pandas as pd
from c19us_combined import df_us

# Be aware of Firestore pricing: https://firebase.google.com/docs/firestore/pricing
# TODO:
#   Async
#   Incremental daily uploads

# Create the database client
cred = credentials.Certificate('.google_service_account_key.json')
firebase_admin.initialize_app(cred, {
    'projectId': 'covidlocal',
})
db = firestore.client()

# Turn date and fips into columns
df_us = df_us.reset_index()

# Break up df_us into json strings for each date
df_us['date_string'] = df_us.date.apply(lambda date: date.strftime('%Y-%m-%d'))
date_list = df_us.date_string.unique().tolist()
json_by_date = {}
for date in date_list:
    df = df_us[df_us['date_string'] == date]
    date_json = df.to_json(orient='index')
    json_by_date[date] = date_json

print(json_by_date.__class__)

# Upload json string for each date as a document
for date_string, json_string in json_by_date.items():
  db.collection(u'us-data').document(date_string).set({'json': json_string})

# Delete a collection. This does not work if there are sub-collections present
# https://firebase.google.com/docs/firestore/solutions/delete-collections
def delete_collection(coll_ref, batch_size=100):
    docs = coll_ref.limit(batch_size).stream()
    deleted = 0
    for doc in docs:
        print(u'Deleting doc {}'.format(doc.id))
        doc.reference.delete()
        deleted = deleted + 1
    if deleted >= batch_size:
        return delete_collection(coll_ref, batch_size)