# Statement for enabling the development environment
DEBUG = True

# Define the application directoryipconfig

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Define the database - we are working with
DATABASE_CONNECT_OPTIONS = {"database": 'escuela_futbol',
                            "host": '186.64.122.205',
                            "port": '5432',
                            "user": 'gremio',
                            "password": '1020'
                            }

THREADS_PER_PAGE = 2
# HOST = '25.78.23.166'
# HOST = '25.78.23.166'
HOST = '0.0.0.0'
PORT = 5000
# Enable protection agains *Cross-site Request Forgery (CSRF)*
CSRF_ENABLED = True

# Use a secure, unique and absolutely secret key for
# signing the data.
CSRF_SESSION_KEY = "asdwerwe"

# Secret key for signing cookies
SECRET_KEY = "123sdwr"


api_key_flow = "7F77DD8F-DDDA-4496-BB12-6D9F9BL8729C"
secret_key_flow = "726ae63459d59cf567d026f78c40c2d716c67283"

