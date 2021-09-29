import requests
import json
import config
import ast
from os import getcwd
from functions import unzipIt
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc

### Worker classes - NO GUI - can be threaded

class Downloader(qtc.QObject):
    """ An object for downloading HSI files in a separate thread """

    fileUnzipped = qtc.pyqtSignal(str)
    fileDownloaded = qtc.pyqtSignal(str)
    def __init__(self, id, url):
        super().__init__()
        self.id = id
        self.url = url

    def downloadHSI(self):
        print('Downloading to:', getcwd())
        r = requests.get(self.url)
        filename = self.id + '.zip'
        with open(filename, 'wb') as f:
            f.write(r.content)

        print(f'Download of {self.id} finished')
        self.fileDownloaded.emit(f'Download of {self.id} finished')

        try:
            unzipIt(filename)
            self.fileUnzipped.emit(self.id[:22])
        except:
            print('Error unzipping file %s.zip' % self.id)

class LogIner(qtc.QObject):
    """ An object to control logging into USGS server """

    log_signal = qtc.pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.login()

    def login(self):
        """ Login to USGS """
        serviceUrl = config.serviceUrl
        config.apiKey
        
        username = 'jgallino'
        password = 'SrOP84X4SeuW'
        
        # login
        payload = {'username' : username, 'password' : password}
        try:
            config.apiKey = self.toDict(self.sendRequest(serviceUrl + "login", payload))
        except Exception as e:
            print(e)

        if config.apiKey:
            if config.apiKey['data']:
                print("API Key: " + config.apiKey['data'] + "\n")
                self.login_success(config.apiKey['data'])
                self.log_signal.emit('Logged into USGS!')
            else:
                self.login_failed(config.apiKey['errorCode'], config.apiKey['errorMessage'])
                self.log_signal.emit(f"USGS Login failed!\t{config.apiKey['errorMessage']}")
        else:
            self.login_failed('No valid response.', 'USGS server may be down or you are not online.')
            self.log_signal.emit('USGS Server is down or you are not connected to the internet')

    def toDict(self, j):
        try:
            converted = json.loads(j)
            return converted
        except:
            err = '\n### Did not receive valid JSON. USGS site may be down for maintenance\n\n'
            print(err.upper())
            return None


    def sendRequest(self, url, data, apiKey = None):  
        json_data = json.dumps(data)
        headers = {'X-Auth-Token': config.apiKey} 
        if config.apiKey:
            response = requests.post(url, json_data, headers = headers)  
            # print('\nsending with headers to %s: %s %s' % (url.replace(serviceUrl,''), data, headers)) 
        else:
            response = requests.post(url, json_data)
            print('sending:', data) 

        # print('response is', response.text)

        if 'API key has expired' in response.text:
            print('API key expired. Logging in again...')
            self.login()
            self.sendRequest(self, url, data, apiKey=config.apiKey)

        try:
            httpStatusCode = response.status_code 
            if response == None:
                print("No output from service")
                
            output = response.content
            
            if self.toDict(output)['errorCode']:
                print(self.toDict(output)['errorCode'], "- ", self.toDict(output)['errorMessage'])
                
            if  httpStatusCode == 404:
                print("404 Not Found")
                
            elif httpStatusCode == 401: 
                print("401 Unauthorized")
                
            elif httpStatusCode == 400:
                print("Error Code", httpStatusCode)
            
        except Exception as e: 
                response.close()
                print(e)
                
            
        response.close()
        return output


    def findFilesize(self, r_id):
    
        dl_query = { 'entityIds': r_id,
                'datasetName' : 'EO1_HYP_PUB'}
        dl_info = self.sendRequest(config.serviceUrl + "download-options", dl_query, config.apiKey)
        dl_data = self.toDict(dl_info)['data']
        
        dl_data = ast.literal_eval(str(dl_data[0]))
        r_productId = dl_data['id']
        r_filesize = round(int(dl_data['filesize']) / 1048576, 2)

        dl_query = { 'downloads' : [{'entityId': r_id,
                                'productId' : r_productId}],
                    'downloadApplication': 'EE'}
        dl_request = self.sendRequest(config.serviceUrl + "download-request", dl_query, config.apiKey)
        dl_data = self.toDict(dl_request)['data']
        # print(dl_data)
        try:
            r_url = dl_data['availableDownloads'][0]['url']
        except:
            r_url = dl_data['preparingDownloads'][0]['url']
        finally:
            return r_filesize, r_url



    def login_success(self, apiKeyData):
        config.apiKey = apiKeyData
        print('successfully logged in to USGS!')
    
    def login_failed(self, eCode, eText):
        errorText = eCode +'\n'+ eText
        print(errorText)





server = LogIner()
