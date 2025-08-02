#!/usr/bin/env python3
"""
Test script pour déboguer l'API d'enregistrement
"""

import requests
import json

def test_recording_start():
    """Test de démarrage d'enregistrement"""
    
    # URL de l'API
    url = "http://localhost:5000/api/recording/start"
    
    # Données du test
    data = {
        "court_id": 1,  # Premier terrain
        "duration": 90,
        "title": "Test Recording",
        "description": "Test description"
    }
    
    # Headers
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print("Testing recording start API...")
        print(f"URL: {url}")
        print(f"Data: {json.dumps(data, indent=2)}")
        
        # Faire la requête
        response = requests.post(url, json=data, headers=headers)
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"Response JSON: {json.dumps(response_data, indent=2)}")
        except:
            print(f"Response Text: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_recording_start()
