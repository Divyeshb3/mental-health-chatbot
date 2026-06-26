import firebase_admin
from firebase_admin import credentials, firestore
import os

# Path to your Firebase service account key
KEY_PATH = "firebase_key.json"

# Initialize Firebase only once
if not firebase_admin._apps:
    cred = credentials.Certificate(KEY_PATH)
    firebase_admin.initialize_app(cred)

# Firestore client
db = firestore.client()