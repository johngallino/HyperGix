import os

apiKey = ""
serviceUrl = "https://m2m.cr.usgs.gov/api/api/json/stable/"
headers = {}
TARGET_BANDS = [8, 13, 15, 25, 55, 77, 82, 85, 91, 93, 97, 102, 112, 115, 120, 137, 158, 183]

# if 'App' not in os.getcwd():
#     if os.path.isfile(os.path.join(os.getcwd(), 'App')):
#         os.chdir(os.path.join(os.getcwd(), 'App'))
# else:
HYPERION_SCANS_PATH = os.path.join(os.getcwd(), 'downloads')