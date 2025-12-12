from app import create_app
from dotenv import load_dotenv
import os

# Create the path to the .env file
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')

# Load the .env file if it exists
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)