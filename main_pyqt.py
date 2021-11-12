from typing_extensions import final
import config
import workers as w
import os
from workers import server, Databaser
from qmanager import qProfileManager
from qhypbrowser import QHypbrowser
from qviewer import qViewer
from qclassifier import qClassifier
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
    
    def __init__(self):
        super(MyWindow, self).__init__()
        self.setGeometry(100, 100, 1300, 900) #top, left, width, height
        self.version = '1.0'
        self.setWindowTitle('HyperGix Hyperspectral Software ' + self.version)

        self.databoy = Databaser()
        self.initUI()

        #checking that all files in download folder are in DB
        for dir in os.listdir(config.HYPERION_SCANS_PATH):
            self.databoy.add_scan(dir)

        self.mainNotebook.tab1.nicknameChosenB.connect(self.databoy.add_scan)

        
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
        # self.receiveLogInSignal.connect(server.send_log_signal)
        # self.receiveLogInSignal.emit()
        server.log_signal.connect(self.status_bar.showMessage)
        self.mainNotebook.tab1.performingSearch.connect(lambda: self.status_bar.showMessage('Performing search...'))
        self.mainNotebook.tab1.loadingResults.connect(lambda: self.status_bar.showMessage('Loading results...'))
        self.mainNotebook.tab1.downloadStartedB.connect(self.status_bar.showMessage)
        self.mainNotebook.tab1.downloadStartedB.connect(self.dl_pbar.startDownload)
        self.mainNotebook.tab1.downloadFinishedB.connect(self.status_bar.showMessage)
        self.mainNotebook.tab1.downloadFinishedB.connect(self.dl_pbar.finishDownload)
        self.mainNotebook.tab1.resultsLoaded.connect(self.status_bar.showMessage)
        self.mainNotebook.tab1.downloadUnzippedB.connect(self.mainNotebook.tab3.downloadList.addItem)
        
        # Populating scan list
        self.mainNotebook.tab3.readyForData.connect(self.databoy.report_scans)
        self.mainNotebook.tab3.nicknameChosen.connect(self.databoy.add_scan)
        # self.mainNotebook.tab3.readyForData.connect(self.databoy.report_mats)
        self.databoy.scansInDB.connect(self.mainNotebook.tab3.populateScans)

        # Storing row and col of last pixel clicked
        self.mainNotebook.tab3.lastPixel_sig.connect(self.databoy.add_pixel)

        # Working with materials
        self.mainNotebook.tab2.addMaterial.connect(self.databoy.add_material)
        self.databoy.matsInDB.connect(self.mainNotebook.tab2.populateMaterials)
        self.databoy.matsInDB.connect(self.mainNotebook.tab3.populateMaterials)
        self.mainNotebook.tab3.readyForData.connect(self.databoy.report_mats)
        self.mainNotebook.tab2.pixelsPlease.connect(self.databoy.report_pixels_for_material)
        self.databoy.reportPixels.connect(self.mainNotebook.tab2.plotProfile)

        # Working with pixel data
        self.mainNotebook.tab2.pixelViewer.pixelListView.itemClicked.connect(self.databoy.report_info_for_pid)
        self.databoy.reportPixelSource.connect(self.mainNotebook.tab2.pixelViewer.findPixel)
        self.mainNotebook.tab2.reportAverage.connect(self.databoy.update_average_for_material)
        
        #Go signal
        self.mainNotebook.tab3.readyForData.emit()

        

class MyNotebook(qtw.QWidget):

    def __init__(self, parent):
        super(qtw.QWidget, self).__init__(parent)
        self.layout = qtw.QVBoxLayout(self)

        # Initialize tabs
        self.tabs = qtw.QTabWidget()
        self.tab1 = QHypbrowser(self)
        self.tab2 = qProfileManager()
        self.tab3 = qViewer()
        self.tab4 = qClassifier()
        self.tabs.resize(300,200)


        # Add tabs
        self.tabs.addTab(self.tab1, "USGS Search")
        self.tabs.addTab(self.tab2, "Spectra Manager")
        self.tabs.addTab(self.tab3, "Image Viewer")
        self.tabs.addTab(self.tab4, "Classifier")


        # Add tabs to widget
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

   

def window():
    app = qtw.QApplication(sys.argv)
    win = MyWindow()
    win.show()
    sys.exit(app.exec_())

win = window()
