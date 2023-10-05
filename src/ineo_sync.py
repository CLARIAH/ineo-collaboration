import dotenv
"""
This files loads some environment variables from a .env file
The .env file is NOT included in the repository, but is required to run this script
The .env file will be checked in into the private repo later
"""
dotenv.load_dotenv()
api_token: str = dotenv.get_key('.env', 'API_TOKEN')
print(api_token)

def main():
    # TODO:
    pass