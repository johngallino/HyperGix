import config
import json
import os
import geocoder 
import workers as w
from workers import server
from ast import literal_eval 
from urllib.request import urlopen 
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc



class ResultBox(qtw.QFrame):
    """ A class to show a single search result """
    
    downloadStartedA = qtc.pyqtSignal(str)
    downloadFinishedA = qtc.pyqtSignal(str)
    downloadUnzippedA = qtc.pyqtSignal(str)

    def beginDownload(self, id, url):

        def confirm(i):
            if i.text() == '&Yes':
                self.downloader = w.Downloader(id, url)
                self.downloadThread = qtc.QThread()
                self.downloader.moveToThread(self.downloadThread)
                self.downloader.fileDownloaded.connect(self.downloadThread.quit)
                self.downloadStartedA.connect(self.downloader.downloadHSI)
                self.downloadStartedA.emit(f'Currently downloading {self.id.text()}...')
                self.downloader.fileDownloaded.connect(self.downloadFinishedA)
                self.downloader.fileUnzipped.connect(self.downloadUnzippedA)
                self.downloadThread.start()
                
    
        self.confirmPop = qtw.QMessageBox()
        self.confirmPop.setText("Are you sure you want to download this file?")
        self.confirmPop.setWindowTitle('Confirm download')
        self.confirmPop.setStandardButtons(qtw.QMessageBox.Yes | qtw.QMessageBox.Cancel)
        self.confirmPop.buttonClicked.connect(confirm)
        self.confirmPop.show()

    def __init__(self, imageLabel, id, caption, count):
        super().__init__()
        self.layout = qtw.QVBoxLayout()
        self.setLayout(self.layout)
        r_filesize, r_url = server.findFilesize(id) # Should be threaded
        self.thumbnail = imageLabel
        self.thumbnail.setAlignment(qtc.Qt.AlignCenter)
        self.id = qtw.QLabel(id)
        self.id.setAlignment(qtc.Qt.AlignCenter)
        self.id.setMargin(10)
        self.counterLabel = qtw.QLabel(f'Result {count+1}')
        self.caption = qtw.QLabel(caption)
        self.download_button = qtw.QPushButton(f'Download {r_filesize} MBs HSI File', clicked=(lambda: self.beginDownload(id, r_url)))

        self.layout.addWidget(self.counterLabel)
        self.layout.addWidget(self.thumbnail)
        self.layout.addWidget(self.id)
        self.layout.addWidget(self.caption)
        self.layout.addWidget(self.download_button)
        



class QHypbrowser(qtw.QWidget):
    """ Class for the USGS Hyperion Search module of the program """

    performingSearch = qtc.pyqtSignal()
    loadingResults = qtc.pyqtSignal()
    resultsLoaded = qtc.pyqtSignal(str)
    downloadStartedB = qtc.pyqtSignal(str)
    downloadFinishedB = qtc.pyqtSignal(str)
    downloadUnzippedB = qtc.pyqtSignal(str)

    def __init__(self, parent):
        super(qtw.QWidget, self).__init__(parent)
        self.layout = qtw.QVBoxLayout()

        # Search bar area
        self.searchLabel = qtw.QLabel("Search by place name or lat/lng coordinates", self)
        self.searchLabel.setSizePolicy(qtw.QSizePolicy.Minimum, qtw.QSizePolicy.Fixed)
        self.layout.addWidget(self.searchLabel)
        self.searchBoxLayout = qtw.QHBoxLayout()
        self.layout.addLayout(self.searchBoxLayout)

        self.searchBox = qtw.QLineEdit(self)
        self.searchBox.setText('Manhattan')
        self.searchBox.returnPressed.connect(self.onSearch)
        self.searchBox.setFixedWidth(300)
        self.searchButton = qtw.QPushButton("Search", clicked=self.onSearch)
        self.searchButton.setSizePolicy(qtw.QSizePolicy.Fixed, qtw.QSizePolicy.Fixed)
        self.searchBoxLayout.addWidget(self.searchBox)
        self.searchBoxLayout.addWidget(self.searchButton)

        self.spacer = qtw.QWidget(self)
        self.spacer.setFixedWidth(50)
        self.searchBoxLayout.addWidget(self.spacer)

        self.resultsLabel = qtw.QLabel("Results per page", self)
        self.resultsLabel.setSizePolicy(qtw.QSizePolicy.Fixed, qtw.QSizePolicy.Fixed)
        self.resultsBox = qtw.QSpinBox(self)
        self.resultsBox.setValue(3)
        self.resultsBox.setMinimum(1)
        self.resultsBox.valueChanged.connect(self.updatePageSize)
        
        self.searchBoxLayout.addWidget(self.resultsLabel)
        self.searchBoxLayout.addWidget(self.resultsBox)

        self.cloudLabel = qtw.QLabel("Cloud threshold", self)
        self.cloudLabel.setSizePolicy(qtw.QSizePolicy.Fixed, qtw.QSizePolicy.Fixed)
        self.cloudLabel.setContentsMargins(25, 0, 0, 0)
        self.cloudBox = qtw.QSpinBox(self)
        self.cloudBox.setValue(60)
        self.cloudBox.setSingleStep(10)
        self.cloudBox.valueChanged.connect(self.updateCloudThresh)
        self.searchBoxLayout.addWidget(self.cloudLabel)
        self.searchBoxLayout.addWidget(self.cloudBox)
        self.searchBoxLayout.addStretch()

        # self.testbtn = qtw.QPushButton("all pixmaps", clicked=self.printPixmaps)
        # self.searchBoxLayout.addWidget(self.testbtn)

        self.prev_btn = qtw.QPushButton("<<", clicked=lambda:self.showResults('back'))
        self.prev_btn.hide()
        
        self.next_btn = qtw.QPushButton(">>", clicked=lambda:self.showResults('next'))
        self.next_btn.hide()
        
        
        self.GridLayout = qtw.QGridLayout()

        self.splitter = qtw.QSplitter()
        
        self.layout.addWidget(self.splitter)
        # Code for the terminal
        self.terminalBox = qtw.QTextEdit(self)

        # Terminal styling
        self.terminalFont = qtg.QFont('Courier New', 10)
        self.terminalFont.setStyleHint(qtg.QFont.Monospace)
        self.terminalFont.setStyleStrategy(
            qtg.QFont.PreferAntialias |
            qtg.QFont.PreferQuality
        )
        self.terminalBox.setFont(self.terminalFont)
        self.terminalBox.setStyleSheet("background-color: #dbf0ff; color: #2d6993;")

        self.terminalBox.setSizePolicy(qtw.QSizePolicy.Minimum, qtw.QSizePolicy.MinimumExpanding)
        self.terminalBox.setAcceptRichText(0)
        self.terminalBox.setPlaceholderText('server response will appear here...')
        self.terminalBox.setReadOnly(1)
        self.terminalBox.setFocus(0) #DOESNT WORK

        # self.GridLayout.addWidget(self.terminalBox, 0, 0)
        self.splitter.addWidget(self.terminalBox)

        # Main results area
        self.resultsWindow = qtw.QFrame(self)
        self.resultsWindow.setFrameShape(qtw.QFrame.Box)
        # self.GridLayout.addWidget(self.resultsWindow, 0, 1, 1, 3)
        self.splitter.addWidget(self.resultsWindow)
        self.splitter.setSizes([250,650])


        # Result page navigation
        self.nav_layout = qtw.QHBoxLayout()
        self.next_btn.setMaximumWidth(85)
        self.prev_btn.setMaximumWidth(85)
        # self.nav_layout.addStretch()
        self.nav_layout.addWidget(self.prev_btn, qtc.Qt.AlignCenter)
        self.nav_layout.addWidget(self.next_btn, qtc.Qt.AlignCenter)

        self.resultsBoxHolder = qtw.QHBoxLayout()

        # Results area contents
        self.resultsVert = qtw.QVBoxLayout()
        self.resultsWindow.setLayout(self.resultsVert)
        self.resultsVert.addLayout(self.resultsBoxHolder)
        self.resultsVert.addLayout(self.nav_layout)

        # Master layout
        self.setLayout(self.layout)

        # Internal Variables - important!
        self.pageSize = self.resultsBox.value()
        self.cloudThreshold = self.cloudBox.value()
        self.counter = 0
        self.r_labels = []
        self.r_captions = []
        self.r_boxes = []
        self.r_thumbs = []
        self.qframes = []

    def updatePageSize(self, int):
        self.pageSize = int
        

    def updateCloudThresh(self, int):
        self.cloudThreshold = int
        

    def onSearch(self):
        self.counter = 0
        self.performingSearch.emit()
        self.clearResults()
        self.terminalBox.clear()
        # Use geocoder to determine place name (very fast)
        g = geocoder.google(self.searchBox.text(), maxRows=5, key="AIzaSyBeL-NSIgeEPx1E1jMMjjKet5FBGWxMnPs")
        self.terminalBox.append(str(g))
        latlon = str(g.latlng[0]) + ', ' + str(g.latlng[1])

        for result in g:
            self.terminalBox.append(str(result.address) + " " + str(result.latlng))
        # Actual USGS search performed next
        self.searchLatLon(latlon, result.address)
     
        

    def searchLatLon(self, latlonfull, *argv):
        serviceUrl = "https://m2m.cr.usgs.gov/api/api/json/stable/"
        searchTimer = qtc.QElapsedTimer()
        searchTimer.start() # Will be measuring elapsed time for search

        latlon = latlonfull.split(',')
        lat = float(latlon[0])
        lon = float(latlon[1])
        print('Searching for %f, %f' % (lat, lon))
        self.terminalBox.append('\nSearching for %f, %f' % (lat, lon))
        
        # self.statusLabel.setText('Searching...')
        datasetName = "EO1_HYP_PUB"
        
        spatialFilter =  {'filterType' : "mbr",
                            'lowerLeft' : {'latitude' : lat, 'longitude' : lon},
                            'upperRight' : { 'latitude' : lat, 'longitude' : lon}}
                            
        acquisitionFilter = {'start' : '2000-12-10', 'end' : '2017-12-10'}
        cloudCoverFilter = {'min' : '0', 'max' : self.cloudBox.value(), 'includeUnknown' : 'True'}

        sceneFilter = { 'spatialFilter': spatialFilter,
                        'acquisitionFilter' : acquisitionFilter,
                        'cloudCoverFilter' : cloudCoverFilter}

        payload = {'datasetName' : datasetName,
                'sceneFilter' : sceneFilter}
                
        datasets = 0
        datasets = server.sendRequest(serviceUrl + "scene-search", payload, config.apiKey)
        
        obj = json.loads(datasets)
        pretty = json.dumps(obj, indent=3)
        # Print results to terminal
        self.terminalBox.append(pretty)
        
        self.results = server.toDict(datasets)['data']['results']

        self.loadingResults.emit()
        self.resultCount = (len(server.toDict(datasets)['data']['results']))
        if not self.resultCount:
            print('No results for that search')

        if len(argv)>1: #Pulls the place name from the search query for results label
            place = argv[1]
        else:
            place = latlonfull
          
        self.resultsLoaded.emit(f"{self.resultCount} results found for '{self.searchBox.text()}'")
        self.showResults(self.results) 
        self.terminalBox.append(f'Found results in {searchTimer.elapsed() /1000} seconds')
        searchTimer.restart()

    def downloadThumbnails(self, results):
        for result in self.results: # SHOULD BE THREADED
            # Processing json and making images for all results
            browse = result['browse']
            browseDetails = literal_eval(str(browse[0]))
            r_imageURL = urlopen(browseDetails['browsePath'])
            r_image_bytes = r_imageURL.read()
            r_image = qtg.QImage.fromData(r_image_bytes)
            self.r_thumbs.append(r_image)


    def printPixmaps(self):
        d = qtw.QDialog(self)
        d.setLayout(qtw.QHBoxLayout())
        if len(self.r_thumbs) > 0:
            for i in range(len(self.r_thumbs)):
                label = qtw.QLabel(self)
                r_pixmap = qtg.QPixmap.fromImage(self.r_thumbs[i])
                label.setPixmap(r_pixmap.scaledToHeight(600))
                d.layout().addWidget(label)
            d.show()


    def clearResults(self):
        # print("clearing the results window")
        for i in reversed(range(self.resultsBoxHolder.count())): 
            try:
                self.resultsBoxHolder.itemAt(i).widget().hide()
            except:
                continue

        
        


    def showResults(self, direction='next'):
        """ Erase results and display next [pageSize] results """
        self.clearResults()
        self.qframes = []
        self.r_thumbs = []
        self.downloadThumbnails(self.results)

        if direction == 'back':
            self.counter = self.counter - self.pageSize*2

        for j in range(min(self.pageSize, self.resultCount)):
            if self.counter < self.resultCount:

                r_date = self.results[self.counter]['temporalCoverage']['endDate'].split()[0]
                
                r_coords =  str(self.results[self.counter]['spatialCoverage']['coordinates'][0][0])
                r_id = self.results[self.counter]['entityId']
                r_pixmap = qtg.QPixmap.fromImage(self.r_thumbs[self.counter])
                r_label = qtw.QLabel(self)
                r_label.setPixmap(r_pixmap.scaledToHeight(600))
                
                r_clouds = str(self.results[self.counter]['cloudCover'])
                captionString =  'Captured ' + r_date + '\n' + r_coords + '\nCloud Cover: ' + r_clouds
                singleResult = ResultBox(r_label, r_id, captionString, self.counter)

                singleResult.downloadStartedA.connect(self.downloadStartedB) #sending signals up the hierarchy
                singleResult.downloadFinishedA.connect(self.downloadFinishedB)
                singleResult.downloadUnzippedA.connect(self.downloadUnzippedB)
                self.qframes.append(singleResult)
                self.resultsBoxHolder.addWidget(self.qframes[j])
                
                self.counter += 1
                # print('displaying result', self.counter, 'of', self.resultCount)
        # print('COUNTER IS NOW %s' % self.counter)
    

        if self.resultCount > self.pageSize:
            self.next_btn.show()
            
        if self.counter > self.pageSize:
            self.prev_btn.show()

        else:
            try:
                self.prev_btn.hide()
            except: pass

        if self.counter >= self.resultCount:
            try:
                self.next_btn.hide()
            except: pass
