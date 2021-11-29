import config
import workers as w
import os
from workers import Databaser, LogIner
from qmanager import qProfileManager
from qhypbrowser import QHypbrowser
from qviewer import qViewer

from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc

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


class MyWindow(qtw.QMainWindow):
    """ Class for main application window """
    receiveLogInSignal = qtc.pyqtSignal
    reportLoginCredentials = qtc.pyqtSignal(str, str)
    
    def __init__(self):
        super(MyWindow, self).__init__()
        self.setGeometry(100, 100, 1300, 900) #top, left, width, height
        self.version = '1.0'
        self.setWindowTitle('HyperGix Hyperspectral Software ' + self.version)

        self.databoy = Databaser()
        self.server = LogIner()
        self.HGsettings = qtc.QSettings('John Gallino', 'HyperGix')
        self.login2USGS()

        #USGS Login Credentials
        # self.HGsettings.setValue('username', 'jgallino')
        # self.HGsettings.setValue('password', 'SrOP84X4SeuW')
        # self.HGsettings.sync()

        self.initUI()

        #checking that all files in download folder are in DB
        for dir in os.listdir(config.HYPERION_SCANS_PATH):
            self.databoy.add_scan(dir)

        self.mainNotebook.tab1.nicknameChosenB.connect(self.databoy.add_scan)

        
        if config.apiKey:
            self.loggedIn = True
        else:
            self.loggedIn = False

    def login2USGS(self):
        self.server.username = self.HGsettings.value('username', 'jgallino', type=str)
        self.server.password = self.HGsettings.value('password', 'SrOP84X4SeuW', type=str)
        self.server.login()

    def setCredentials(self, u, p):
        self.HGsettings.setValue('username', u)
        self.HGsettings.setValue('password', p)

        
    def initUI(self):
        self.mainNotebook = MyNotebook(self, self.server)
        self.setCentralWidget(self.mainNotebook)

        #Menu Bar
        # self.menubar = self.menuBar()
        # self.file_menu = self.menubar.addMenu('File')

        self.status_bar = qtw.QStatusBar()

        # Download progress bar
        self.dl_pbar = ProgressBar(self, minimum=0, maximum=100, textVisible=False, objectName="RedProgressBar")
        self.dl_pbar.setMaximumWidth(165)
        self.status_bar.addPermanentWidget(self.dl_pbar)

        # Logging in to USGS
        self.server.requestCredentials.connect(self.setCredentials)
        self.mainNotebook.tab1.newCredentials.connect(self.setCredentials)

        # STATUS BAR MESSAGES
        
        self.setStatusBar(self.status_bar)
        # self.receiveLogInSignal.connect(server.send_log_signal)
        # self.receiveLogInSignal.emit()
        # self.server.log_signal.connect(self.status_bar.showMessage)
        self.server.log_signal_true.connect(lambda: self.status_bar.showMessage('Logged into USGS!'))
        self.server.log_signal_false.connect(lambda: self.status_bar.showMessage('Not logged into USGS'))
        self.mainNotebook.tab1.newCredentials.connect(lambda: self.status_bar.showMessage('USGS Login credentials updated!', 3000))
        self.mainNotebook.tab1.performingSearch.connect(lambda: self.status_bar.showMessage('Performing search...'))
        self.mainNotebook.tab1.loadingResults.connect(lambda: self.status_bar.showMessage('Loading results...'))
        self.mainNotebook.tab1.downloadStartedB.connect(self.status_bar.showMessage)
        self.mainNotebook.tab1.downloadStartedB.connect(self.dl_pbar.startDownload)
        self.mainNotebook.tab1.downloadFinishedB.connect(self.status_bar.showMessage)
        self.mainNotebook.tab1.downloadFinishedB.connect(self.dl_pbar.finishDownload)
        self.mainNotebook.tab1.resultsLoaded.connect(self.status_bar.showMessage)
        self.mainNotebook.tab3.switchToLAN.connect(lambda: self.status_bar.showMessage('Please wait while the file is converted...'), 5000)
        self.mainNotebook.tab1.downloadUnzippedB.connect(self.mainNotebook.tab3.downloadList.addItem)
        self.databoy.delPixelSuccess.connect(lambda: self.status_bar.showMessage(f'Pixel {str} has been deleted', 5000))
        self.databoy.raggedArrayAlert.connect(lambda: self.status_bar.showMessage(f'Warning: It is not recommended to assign pixels from different sensors to the same material class', 10000))

        # Populating scan list
        self.mainNotebook.tab3.readyForData.connect(self.databoy.report_scans)
        self.mainNotebook.tab3.nicknameChosen.connect(self.databoy.add_scan)
        self.mainNotebook.tab3.switchToLAN.connect(self.databoy.change_scan_filepath_to_lan)
        self.databoy.scansInDB.connect(self.mainNotebook.tab3.populateScans)
        self.databoy.addScanSuccess.connect(self.mainNotebook.tab3.downloadList.addItem)

        # Deleting a scan
        self.mainNotebook.tab3.signal_delete.connect(self.databoy.delete_Scan)
        self.databoy.delScanSuccess.connect(self.mainNotebook.tab3.remove_scan_from_list)

        # Opening external files
        self.mainNotebook.tab3.requestFilepath.connect(self.databoy.report_data_for_fileID)
        self.databoy.reportFilepath.connect(self.mainNotebook.tab3.openExternalScan)

        # Storing row and col of last pixel clicked
        self.mainNotebook.tab3.lastPixel_sig.connect(self.databoy.add_pixel)

        # Working with materials
        self.mainNotebook.tab2.addMaterial.connect(self.databoy.add_material)
        self.databoy.matsInDB.connect(self.mainNotebook.tab2.populateMaterials)
        self.databoy.matsInDB.connect(self.mainNotebook.tab3.populateMaterials)
        self.mainNotebook.tab3.readyForData.connect(self.databoy.report_mats)
        self.mainNotebook.tab2.pixelsPlease.connect(self.databoy.report_pixels_for_material)
        self.databoy.reportPixels.connect(self.mainNotebook.tab2.plotProfile)

        # Deleting a material profile
        self.mainNotebook.tab2.deleteThisPid.connect(self.databoy.delete_Profile)
        self.databoy.delProfileSuccess.connect(self.mainNotebook.tab2.remove_profile_from_list)

        #Spectral angles calculation
        self.databoy.reportMeans.connect(self.mainNotebook.tab3.setMeans)

        # Working with pixel data
        self.mainNotebook.tab2.pixelViewer.pixelListView.itemClicked.connect(self.databoy.report_info_for_pid)
        self.databoy.reportPixelSource.connect(self.mainNotebook.tab2.pixelViewer.findPixel)
        self.mainNotebook.tab2.reportAverage.connect(self.databoy.update_average_for_material)
        self.mainNotebook.tab2.pixelViewer.requestPixelDeleted.connect(self.databoy.deletePixel)
        self.databoy.delPixelSuccess.connect(self.mainNotebook.tab2.pixelViewer.removePixelFromList)
        
        #Go signal
        self.mainNotebook.tab3.readyForData.emit()

        

    def updateCredentials(self, username, password):
        self.HGsettings.setValue('username', username)
        self.HGsettings.setValue('password', password)
        print('new credentials saved')

        

class MyNotebook(qtw.QWidget):

    def __init__(self, parent, server):
        super(qtw.QWidget, self).__init__(parent)
        self.layout = qtw.QVBoxLayout(self)
        self.server = server
        # Initialize tabs
        self.tabs = qtw.QTabWidget()
        self.tab1 = QHypbrowser(self)
        self.tab2 = qProfileManager()
        self.tab3 = qViewer()
        # self.tab4 = qClassifier()
        self.tabs.resize(300,200)


        # Add tabs
        self.tabs.addTab(self.tab3, "Image Viewer")
        self.tabs.addTab(self.tab2, "Spectra Manager")
        self.tabs.addTab(self.tab1, "USGS Search")
        # self.tabs.addTab(self.tab4, "Classifier")


        # Add tabs to widget
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

   

def window():
    app = qtw.QApplication(sys.argv)
    win = MyWindow()
    win.show()
    sys.exit(app.exec_())

win = window()
