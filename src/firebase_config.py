import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    if firebase_admin._apps:
        return firestore.client()

    try:
        creds_json = os.getenv("FIREBASE_CREDENTIALS")

        if creds_json:
            creds_dict = json.loads(creds_json)
            cred = credentials.Certificate(creds_dict)
        else:
            cred = credentials.Certificate("firebase-credentials.json")

        firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized successfully")
        return firestore.client()

    except Exception as e:
        raise RuntimeError(f"Firebase initialization failed: {e}")

db = initialize_firebase()