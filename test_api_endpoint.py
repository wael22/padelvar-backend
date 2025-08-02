import requests
import json

# Test the actual API endpoint
url = 'http://localhost:5000/api/admin/clubs/3/courts'

# First, let's login as admin to get the session
login_url = 'http://localhost:5000/api/auth/login'
login_data = {
    'email': 'admin@padelvar.com',
    'password': 'admin123'
}

session = requests.Session()

print("🔐 Logging in as admin...")
login_response = session.post(login_url, json=login_data)
print(f"Login status: {login_response.status_code}")

if login_response.status_code == 200:
    print("✅ Login successful!")
    
    # Now test the courts endpoint
    print(f"\n🏟️ Testing courts endpoint: {url}")
    courts_response = session.get(url)
    print(f"Courts status: {courts_response.status_code}")
    
    if courts_response.status_code == 200:
        courts_data = courts_response.json()
        print("✅ Courts data received:")
        print(json.dumps(courts_data, indent=2))
        
        # Check each court for valid ID
        courts = courts_data.get('courts', [])
        print(f"\n🔍 Analyzing {len(courts)} courts:")
        for i, court in enumerate(courts):
            print(f"  Court {i+1}:")
            print(f"    - Type: {type(court)}")
            print(f"    - Has 'id': {'id' in court if isinstance(court, dict) else 'N/A'}")
            print(f"    - ID value: {court.get('id', 'MISSING') if isinstance(court, dict) else 'N/A'}")
            print(f"    - Full data: {court}")
            
    else:
        print(f"❌ Courts request failed: {courts_response.text}")
else:
    print(f"❌ Login failed: {login_response.text}")
