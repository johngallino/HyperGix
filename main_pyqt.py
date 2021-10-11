from typing_extensions import final
import config
import workers as w
import os
from osgeo import gdal
from workers import server
from qmanager import qProfileManager, Profile
from qhypbrowser import QHypbrowser
from qviewer import qViewer
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc
from PyQt5 import QtSql as qts

import sys


class ProgressBar(qtw.QProgressBar):

    def __init__(self, *args, **kwargs):
        super(ProgressBar, self).__init__(*args, **kwargs)
        self.setValue(0)
        self.hide()
        # if self.minimum() != self.maximum():
        #     self.timer = qtc.QTimer(self, timeout=self.onTimeout)
        #     self.timer.start(randint(1, 3) * 1000)
        
    def startDownload(self):
        self.show()
        self.setMaximum(0)
    
    def finishDownload(self):
        self.setMaximum(100)
        self.hide()

class Databaser():
    """" Class for interacting with the database """

    def pull_materials(self):
        ''' returns a list of all materials in the database '''
        query1 = qts.QSqlQuery(self.db)
        # query1.prepare('SELECT * FROM materials')
        # query1.bindValue(':id', material_id)
        query1.exec('SELECT * FROM materials')
        materials = []
        while query1.next():
            materials.append(query1.value(1))
        print(materials)
        return materials
    

    def add_scan(self, id, nickname='None'):
        ''' adds a hyperspectral image to the database '''
        # assume you receive an id like 'EO1H0140312014030110KF'
        if os.path.dirname(f'{config.HYPERION_SCANS_PATH}\{id})'):
            filepath = os.path.join(config.HYPERION_SCANS_PATH, id, f'{id}.L1R')
            info = gdal.Info(filepath)

        def infoSearch(file, term, datalength):
            if file.find(term) is not -1:
                i = file.find(term) + len(term)
                data = file[i:i+datalength]
                return data
            else:
                print(f"!!! Did not find '{term}'")

        rows = infoSearch(info, 'Number of Along Track Pixels=', 4)
        samples = infoSearch(info, 'Number of Cross Track Pixels=', 3)
        bands = infoSearch(info, 'Number of Bands=', 3)
        interleave = infoSearch(info, 'Interleave Format=', 3)
        datetime = infoSearch(info, 'Time of L1 File Generation=', 20)
        dt = datetime.split(' ')
        date = dt[0] +' '+ dt[2] + ' ' + dt[4]
        time = dt[3]

        metapath = os.path.join(config.HYPERION_SCANS_PATH, id, f'{id}.MET')

        with open(metapath) as f:
            lines = f.read()
            print(lines)
            f.close()

        c_lat = infoSearch(lines, 'Site Latitude                ', 7).rstrip()
        c_lon = infoSearch(lines, 'Site Longitude               ', 7).rstrip()
        
        print('\n')
        print('id:', id)
        print('rows:', rows)
        print('samples:', samples)
        print('bands:',bands)
        print('interleave:', interleave)
        print('date:', date)
        print('time:', time)
        print('c_lat:', c_lat)
        print('c_lon:', c_lon)
        print('\n')

        

        





    def __init__(self):
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



class MyWindow(qtw.QMainWindow):
    """ Class for main application window """

    
    def __init__(self):
        super(MyWindow, self).__init__()
        self.setGeometry(100, 100, 1300, 900) #top, left, width, height
        self.version = '0.1'
        self.setWindowTitle('HyperGix Hyperspectral Software ' + self.version)
        self.databoy = Databaser()
        self.databoy.add_scan('EO1H0140312014030110KF')
            
        self.initUI()

        if config.apiKey:
            self.loggedIn = True
        else:
            self.loggedIn = False

        

    def initUI(self):
        self.mainNotebook = MyNotebook(self)
        self.setCentralWidget(self.mainNotebook)

        #Menu Bar
        # self.menubar = self.menuBar()
        # self.file_menu = self.menubar.addMenu('File')


        self.status_bar = qtw.QStatusBar()

        # Download progress bar
        self.dl_pbar = ProgressBar(self, minimum=0, maximum=100, textVisible=False, objectName="RedProgressBar")
        self.dl_pbar.setMaximumWidth(165)
        self.status_bar.addPermanentWidget(self.dl_pbar)


        # STATUS BAR MESSAGES
        
        self.setStatusBar(self.status_bar)
        self.mainNotebook.tab1.performingSearch.connect(lambda: self.status_bar.showMessage('Performing search...'))
        self.mainNotebook.tab1.loadingResults.connect(lambda: self.status_bar.showMessage('Loading results...'))
        self.mainNotebook.tab1.downloadStartedB.connect(self.status_bar.showMessage)
        self.mainNotebook.tab1.downloadStartedB.connect(self.dl_pbar.startDownload)
        self.mainNotebook.tab1.downloadFinishedB.connect(self.status_bar.showMessage)
        self.mainNotebook.tab1.downloadFinishedB.connect(self.dl_pbar.finishDownload)
        self.mainNotebook.tab1.resultsLoaded.connect(self.status_bar.showMessage)
        self.mainNotebook.tab1.downloadUnzippedB.connect(self.mainNotebook.tab3.downloadList.addItem)
    

        

class MyNotebook(qtw.QWidget):

    def __init__(self, parent):
        super(qtw.QWidget, self).__init__(parent)
        self.layout = qtw.QVBoxLayout(self)

        # Initialize tabs
        self.tabs = qtw.QTabWidget()
        self.tab1 = QHypbrowser(self)
        self.tab2 = qProfileManager()
        self.tab3 = qViewer()
        self.tabs.resize(300,200)


        # Add tabs
        self.tabs.addTab(self.tab1, "USGS Search")
        self.tabs.addTab(self.tab2, "Profile Manager")
        self.tabs.addTab(self.tab3, "Image Viewer")


        # Add tabs to widget
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

   

def window():
    app = qtw.QApplication(sys.argv)
    win = MyWindow()
    
    win.show()
    sys.exit(app.exec_())

win = window()
