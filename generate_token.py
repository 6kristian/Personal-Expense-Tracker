from google_auth_oauthlib.flow import InstalledAppFlow
import os

# Define the scope for Google Drive API (adjust as needed)
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def generate_token():
    """
    Generate a token.json file for Google Drive API access using credentials.json.
    """
    # Path to your credentials file (replace with actual path if different)
    creds_path = "credentials.json"
    
    # Check if credentials.json exists
    if not os.path.exists(creds_path):
        raise FileNotFoundError(
            "Error: credentials.json not found. Please download it from Google Cloud Console."
        )
    
    # Initiate the OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
    creds = flow.run_local_server(port=0)
    
    # Save the credentials to token.json
    with open("token.json", "w") as token_file:
        token_file.write(creds.to_json())
    print("? token.json created successfully!")

if __name__ == "__main__":
    generate_token()
