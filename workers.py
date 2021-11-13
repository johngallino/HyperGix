import requests
import json
import config
import ast
import shutil
import os
import sys
import spectral.io.envi as envi
from PyQt5 import QtSql as qts
from osgeo import gdal
from os import getcwd
from functions import unzipIt
from config import HYPERION_SCANS_PATH as DOWNLOAD_PATH
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc

### Worker classes - NO GUI - can be threaded

class Databaser(qtw.QWidget):
    """" Class for interacting with the database """

    scansInDB = qtc.pyqtSignal(list)
    matsInDB = qtc.pyqtSignal(list)
    reportPixels = qtc.pyqtSignal(list, int)
    reportPixelSource = qtc.pyqtSignal(str, int, int)
    reportFilepath = qtc.pyqtSignal(str)

    def report_scans(self):
        scans = self.pull_scans()
        self.scansInDB.emit(scans)
    
    def report_mats(self):
        mats = self.pull_materials()
        self.matsInDB.emit(mats)

    def pull_scans(self):
        ''' returns a list of scans in the database'''
        query = self.db.exec('SELECT id, nickname FROM scans')
        scans = []
        while query.next():
            if query.value(1) != 'None':
                scans.append(f'{query.value(0)} ({query.value(1)})')
            else:
                scans.append(query.value(0))
            # print(query.value(0), query.value(1))
        return scans

    def pull_materials(self):
        ''' returns a list of all materials in the database '''
        query1 = qts.QSqlQuery(self.db)
        query1.exec('SELECT * FROM materials')
        materials = []
        while query1.next():
            materials.append(query1.value(1))
        # print(materials)
        return materials
    
    def get_mid(self, material):
        matQuery = qts.QSqlQuery(self.db)
        matQuery.prepare('SELECT mid FROM materials WHERE name=:material')
        matQuery.bindValue(':material', material)
        matQuery.exec_()
        target_mat = 'ERROR'
        if matQuery.next():
            target_mat = matQuery.value(0)
            return target_mat
        else:
            print('no material in db matches', material)
            return None
    
    def add_scan(self, id, nickname='None'):
        ''' adds a hyperspectral image to the database '''
        # assume you receive an id like 'EO1H0140312014030110KF'

        if ':' in id or '/' in id:
            parts = id.split('/')
            i = len(parts) -1
            filepath = id
            fileFormat = id[-3:]
            id = parts[i].replace(f'.{fileFormat}', '')
        else:
            fileFormat = 'L1R'
            

        presenceCheck = qts.QSqlQuery(self.db)
        presenceCheck.prepare('SELECT * FROM scans WHERE id=:id')
        presenceCheck.bindValue(':id', id)
        presenceCheck.exec_()
        if not presenceCheck.next():
            present = False
            print(f'{id} is not in the database currently')
        else:
            present = True
            print(f'{id} already in database')

        
        def infoSearch(file, term, datalength):
            ''' use this method to pull data from gdal.info '''
            if file.find(term) != -1:
                i = file.find(term) + len(term)
                data = file[i:i+datalength]
                return data.rstrip()
            else:
                print(f"!!! Did not find '{term}'")
                return None

        def pull_numbers_from_line(file, i, term):
            ''' use this method to pull data from .MET file '''
            line = file[i]
            num = ''
            start = line.find(term) + len(term)

            if start != -1:
                num = line[start:].rstrip()
                return num
            else:
                print(f"!!! Did not find '{term}'")
                return None

        def pull_date_from_multispec_tiff(file):
            ''' use this method to pull data from a tiff file generated by Multispec '''
            import re

            # First lets find the exact line needed and store the linenumber as i
            i = 0
            lookup = 'Generated by MultiSpecUniversal'
            target = ''

            for line in file.splitlines():
                if lookup in line:
                    target = line
                    break
            
        
            print(f'using regex on line: {target}')

            datepattern = '([0-9]+(-[0-9]+)+)'
            timepattern = '[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,3})?'

            date = re.search(datepattern, target)
            time = re.search(timepattern, target)

            if date and time:
                return date.group(), time.group()
            elif date:
                return date.group()
            else:
                print(f"!!! Did not find date or time values'")
                return None

        if not present:

            if os.path.isdir(f'{config.HYPERION_SCANS_PATH}\{id})'):
                filepath = os.path.join(config.HYPERION_SCANS_PATH, id, f'{id}.{fileFormat}')
                info = gdal.Info(filepath).split('Corner ')[0]
                print(info)

            else:
                info = gdal.Info(filepath).split('Corner ')[0]
                print(f'\nGDAL INFO for {id}.{fileFormat}')
                print('=======================================================')
                print(info)
                print('================== END GDAL INFO ======================\n')

            metapath = os.path.join(config.HYPERION_SCANS_PATH, id, f'{id}.MET')

            if os.path.exists(metapath):
                with open(metapath) as f:
                    lines = f.read()
                    f.seek(0,0)
                    linelist = f.readlines()
                    # print(lines)
                    f.close()

            elif os.path.exists(filepath.replace(filepath[:-3], 'MET')):
                metapath = filepath.replace(filepath[:-3], 'MET')
                with open(metapath) as f:
                    lines = f.read()
                    f.seek(0,0)
                    linelist = f.readlines()
                    # print(lines)
                    f.close()
            else:
                print(f'No metadata file found for {id}\n')
                linelist = None

            driver = infoSearch(info, 'Driver: ', 19)
            print('DRIVER IS', driver)

            if 'LAN' in driver:
                import spectral as s
                from datetime import date as d
                try:
                    img = s.open_image(filepath)
                    rows = img.shape[0]
                    samples = img.shape[1]
                    bands = img.shape[2]

                    if img.interleave == 1:
                        interleave = 'BIL'
                    elif img.interleave == 2:
                        interleave = 'BIP'
                    elif img.interleave == 3:
                        interleave = 'BSQ'
                    else:
                        interleave = 'BIL'
                    
                    sensor = None
                    date = d.today().strftime("%b %d %Y")
                    time = None

                except Exception as e:
                    print(e)

            elif 'GTiff' in driver:
                img = gdal.Open(filepath)
                rows = img.RasterXSize
                samples = img.RasterYSize
                bands = img.RasterCount
                interleave = 'BIL'
                sensor = None
                if 'Generated by MultiSpecUniversalIntel' in gdal.Info(filepath):
                    date, time = pull_date_from_multispec_tiff(gdal.Info(filepath))
                    interleave = 'BSQ'
                else:
                    date = None
                    time = None
                    interleave = 'BSQ'
      

            else:
                rows = infoSearch(info, 'Number of Along Track Pixels=', 4)
                samples = infoSearch(info, 'Number of Cross Track Pixels=', 4)
                bands = infoSearch(info, 'Number of Bands=', 3)
                interleave = infoSearch(info, 'Interleave Format=', 3)
                sensor = infoSearch(info, 'L1 File Generated By=', 15)
                datetime = infoSearch(info, 'Time of L1 File Generation=', 20)
                
                try:
                    dt = datetime.split(' ')
                    date = dt[0] +' '+ dt[1] + ' ' + dt[3]
                    time = dt[2]
                except:
                    date = datetime if datetime else None
                    time = None

            if linelist:
                c_lat = pull_numbers_from_line(linelist, 1, 'Site Latitude                ')
                c_lon = pull_numbers_from_line(linelist, 2, 'Site Latitude                ')
                ul_lat = pull_numbers_from_line(linelist, 22, ' = ')
                ul_lon = pull_numbers_from_line(linelist, 23, ' = ')
                ur_lon = pull_numbers_from_line(linelist, 24, ' = ')
                ur_lat = pull_numbers_from_line(linelist, 25, ' = ')
                ll_lon = pull_numbers_from_line(linelist, 26, ' = ')
                ll_lat = pull_numbers_from_line(linelist, 27, ' = ')
                lr_lon = pull_numbers_from_line(linelist, 28, ' = ')
                lr_lat = pull_numbers_from_line(linelist, 29, ' = ')
            else:
                c_lat = None 
                c_lon = None
                ul_lat = None
                ul_lon = None 
                ur_lat = None
                ur_lon = None
                ll_lon = None
                ll_lat = None
                lr_lon = None
                lr_lat = None
            

            print('\nAdding the following to database...')
            print('id:', id)
            print('nickname:', nickname)
            print('rows:', rows)
            print('samples:', samples)
            print('bands:', bands)
            print('interleave:', interleave)
            print('sensor:', sensor)
            print('date:', date)
            print('time:', time)
            print('c_lat:', c_lat)
            print('c_lon:', c_lon)
            print('ul_lat:', ul_lat)
            print('ul_lon:', ul_lon)
            print('ur_lat:', ur_lat)
            print('ur_lon:', ur_lon)
            print('ll_lat:', ll_lat)
            print('ll_lon:', ll_lon)
            print('lr_lat:', lr_lat)
            print('lr_lon:', lr_lon)
            print('\n')

            insertQuery = qts.QSqlQuery(self.db)
            insertQuery.prepare(
                'INSERT INTO scans(id, nickname, filepath,'
                'rows, samples, bands, sensor, interleave, date, time,'
                'ul_lat, ul_lon, ur_lat, ur_lon, ll_lat, ll_lon, lr_lat,'
                'lr_lon, c_lat, c_lon) VALUES (:id, :nickname, :filepath,'
                ':rows, :samples, :bands, :sensor, :interleave, :date, :time,'
                ':ul_lat, :ul_lon, :ur_lat, :ur_lon, :ll_lat, :ll_lon, :lr_lat,'
                ':lr_lon, :c_lat, :c_lon)'
            )
            insertQuery.bindValue(':id', id)
            insertQuery.bindValue(':nickname', nickname)
            insertQuery.bindValue(':filepath', filepath)
            insertQuery.bindValue(':rows', rows)
            insertQuery.bindValue(':samples', samples)
            insertQuery.bindValue(':bands',bands)
            insertQuery.bindValue(':interleave', interleave)
            insertQuery.bindValue(':sensor', sensor)
            insertQuery.bindValue(':date', date)
            insertQuery.bindValue(':time', time)
            insertQuery.bindValue(':c_lat', c_lat)
            insertQuery.bindValue(':c_lon', c_lon)
            insertQuery.bindValue(':ul_lat', ul_lat)
            insertQuery.bindValue(':ul_lon', ul_lon)
            insertQuery.bindValue(':ur_lat', ur_lat)
            insertQuery.bindValue(':ur_lon', ur_lon)
            insertQuery.bindValue(':ll_lat', ll_lat)
            insertQuery.bindValue(':ll_lon', ll_lon)
            insertQuery.bindValue(':lr_lat', lr_lat)
            insertQuery.bindValue(':lr_lon', lr_lon)
            good = insertQuery.exec_()
            
            if good:
                print(f'scan {id} added successfully to db')
                #send signal to add to the list
            else:
                print('SCAN NOT ADDED TO DATABASE!\n', insertQuery.lastError().text())
      
    def add_pixel(self, id, r, c, material ):
        ''' adds a pixel to the database '''
        presenceCheck = qts.QSqlQuery(self.db)
        presenceCheck.prepare('SELECT * FROM pixels WHERE source=:source AND row=:row AND col=:col')
        presenceCheck.bindValue(':source', id)
        presenceCheck.bindValue(':row', r)
        presenceCheck.bindValue(':col', c)
        presenceCheck.exec_()
        if not presenceCheck.next():
            print('id is:', id)
            header = id.replace('L1R', 'hdr')
            header = os.path.join(DOWNLOAD_PATH, id[:-4], header)
            filepath = os.path.join(DOWNLOAD_PATH, id[:-4], id)
            

            img = envi.open(header, filepath)
            spectra = ''
            for val in img[r,c]:
                spectra += str(val) + ' '

            print('spectra is:', spectra)

            print(f'That pixel is not in the database currently')
            # print('gonna add', id, r, c, material)

            target_mat = self.get_mid(material)

            insertQuery = qts.QSqlQuery(self.db)
            insertQuery.prepare('INSERT INTO pixels(source, row, col, material, spectra)'
                'VALUES (:source, :row, :col, :material, :spectra)'
                )
            insertQuery.bindValue(':source', id.replace('.L1R', ''))
            insertQuery.bindValue(':row', r)
            insertQuery.bindValue(':col', c)
            insertQuery.bindValue(':material', target_mat)
            insertQuery.bindValue(':spectra', spectra)
            good = insertQuery.exec_()

            if good:
                print(f'pixel {id} added successfully to db')
            else:
                print(insertQuery.lastError().text())

        else:
            present = True
            print(f'That pixel is already in database with material {presenceCheck.value(4)}')

    def add_material(self, name):
        ''' adds a new material to the database '''
        presenceCheck = qts.QSqlQuery(self.db)
        presenceCheck.prepare('SELECT * FROM materials WHERE name=:name')
        presenceCheck.bindValue(':name', name)

        presenceCheck.exec_()
        if not presenceCheck.next():
            present = False
            print(f'That material is not in the database currently. Adding it now...')

            insertQuery = qts.QSqlQuery(self.db)
            insertQuery.prepare('INSERT INTO materials (name) values (:name)')
            insertQuery.bindValue(':name', name)
            good = insertQuery.exec_()

            if good:
                print(f'{name} added successfully to db')
            else:
                print(insertQuery.lastError().text())
        else:
            present = True
            print(f'That material is already in the database')

    def report_pixels_for_material(self, name):

        ''' queries the database for all pixels belonging to a material '''
        mid = self.get_mid(name)
        query1 = qts.QSqlQuery(self.db)
        query1.prepare('SELECT pid, spectra, bands FROM pixels LEFT JOIN scans on scans.id = pixels.source WHERE material = :material')
        query1.bindValue(':material', mid)
        query1.exec_()
        results=[]
        bandcounts = []

        while query1.next():
            results.append({str(query1.value(0)): query1.value(1)})
            bandcounts.append(int(query1.value(2)))

        if results:
            print(str(len(results)) + f' Pixels for {name}')
            print('Max num of bands is', max(bandcounts))
            # print(results)
            print('\n')
            self.reportPixels.emit(results, max(bandcounts))

        else:
            print(f'No pixels for {name}')
            print('\n')
            self.reportPixels.emit(results, 242)

        
    def update_average_for_material(self, material, values):
        values = str(values)
        query1 = qts.QSqlQuery(self.db)
        print('values:', values)
        print('material:', material)
        query1.prepare('UPDATE materials SET spectra = :vals WHERE name = :material')
        query1.bindValue(':vals', values)
        query1.bindValue(':material', material)
        good = query1.exec_()

        if good:
            print(f'average spectra for {material} updated')
        else:
            print('query error:', query1.lastError().text())

    def report_info_for_pid(self, pid):
        ''' given a pixel ID (pid), returns row, column and source image from db '''
        pid = pid.text()
        print(pid)
        query = qts.QSqlQuery(self.db)
        query.prepare('SELECT filepath, row, col from pixels LEFT JOIN scans on scans.id = pixels.source where pid = :pid')
        query.bindValue(':pid', pid)
        query.exec_()
        
        if query.next():
            print('returning', query.value(0), query.value(1), query.value(2))
            self.reportPixelSource.emit(query.value(0), query.value(1), query.value(2))

    def report_data_for_fileID(self, id):
        ''' given a scan id, returns filepath from db '''

        query = qts.QSqlQuery(self.db)
        query.prepare('SELECT filepath from scans where id = :id')
        query.bindValue(':id', id)
        query.exec_()
        
        if query.next():
            self.reportFilepath.emit(query.value(0))
        else:
            self.reportFilepath.emit(f'ERR: no path for {id}')


    def deletePixel(self, pid):
        ''' deletes a pixel from db by given PID '''
        query1 = qts.QSqlQuery(self.db)
        query1.prepare('DELETE from pixels WHERE pid = :pid')
        query1.bindValue(':pid', pid)
        good = query1.exec_()

        if good:
            print(f'Pixel {pid} deleted from db')
        else:
            print(query1.lastError().text())


    def __init__(self):
        super().__init__()
        self.db = qts.QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName('data.db')
    
        if not self.db.open():
            error = self.db.lastError().text()
            qtw.QMessageBox.critical(
                None, 'DB Connection Error',
                'Could not open database file: ',
                f'{error}')
            sys.exit(1)
        else:
            print('connected to data.db')

        required_tables = {'materials', 'pixels', 'scans', 'sqlite_sequence'}
        tables = self.db.tables()
        missing_tables = required_tables - set(tables)
        if missing_tables:
            qtw.QMessageBox.critical(
                None, 'DB Integrity Error',
                'Missing tables, please repair DB: '
                f'{missing_tables}')
            sys.exit(1)
        else:
            print('DB integrity check - OK!')


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
        self.filename = self.id + '.zip'
        with open(self.filename, 'wb') as f:
            f.write(r.content)

        print(f'Download of {self.id} finished')
        self.fileDownloaded.emit(f'Download of {self.id} finished')

        try:
            unzipIt(self.filename)
            self.fileUnzipped.emit(self.id[:22])
        except:
            print('Error unzipping file %s.zip' % self.id)

        try:
            self.headerFix()
        except:
            print('Error making fix to header file')

    def headerFix(self):
        old_header = os.path.join(DOWNLOAD_PATH, self.filename[:-11], f'{self.filename[:-11]}.bak')
        header = os.path.join(DOWNLOAD_PATH, self.filename[:-11], f'{self.filename[:-11]}.hdr')

        # Making a new copy of header with adjusted offset of 2502
        os.rename(header, old_header)
        shutil.copyfile(old_header, header)

        file = open(header, 'r')
        replacement = ""
        for line in file:
            line = line.strip()
            changes = line.replace("header offset = 0", "header offset = 2502")
            replacement = replacement + changes + "\n"
        file.close()

        fout = open(header, 'w')
        fout.write(replacement)
        fout.close()

    # def deleteExtraFiles(self):
    #     ''' A function to keep only the .L1R and header files and delete everything else'''
    #     for root, dirs, files in os.walk(DOWNLOAD_PATH, topdown=False):
    #         for name in files:
    #             if name[-3:] != 'L1R' and name[-3:] != 'hdr':
    #                 try:
    #                     os.remove(name)
    #                 except:
    #                     print(f"Error trying to delete {name}")

        


class LogIner(qtc.QObject):
    """ An object to control logging into USGS server """

    log_signal = qtc.pyqtSignal(str)

    def send_log_signal(self,text):
        self.log_signal.emit(text)

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
                self.send_log_signal('Logged into USGS!')
            else:
                self.login_failed(config.apiKey['errorCode'], config.apiKey['errorMessage'])
                self.send_log_signal(f"USGS Login failed!\t{config.apiKey['errorMessage']}")
        else:
            self.login_failed('No valid response.', 'USGS server may be down or you are not online.')
            self.send_log_signal('USGS Server is down or you are not connected to the internet')

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
