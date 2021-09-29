import os
import pickle
import matplotlib
matplotlib.use('Qt5Agg')

from osgeo import gdal
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg)
from config import HYPERION_SCANS_PATH
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc
gdal.UseExceptions()


TARGET_BANDS = [8, 13, 15, 25, 55, 77, 82, 85, 91, 93, 97, 102, 112, 115, 120, 137, 158, 183]

LAN_PATH = os.path.join(os.getcwd(), 'downloads')
PROFILES_PATH = os.path.join(os.getcwd(), 'profiles.bin')
NICKNAMES_PATH = os.path.join(os.getcwd(), 'nicknames.bin')

class Pixel:
    """ A single pixel taken from a hyperspectral image """
    def __init__(self, source, row, col):
        self.source = source
        self.row = row
        self.col = col

class Profile:
    """ A spectral profile """
    def __init__(self, name):
        self.name = name
        self.pixels = []
        self.avgSpectra = []

    def addPixel(self, pixel):
        self.pixels.append(pixel)

    def delPixel(self, i):
        del self.pixels[i]

    def showValues(self):
        print(self.pixels)


class qProfileManager(qtw.QFrame):

    def load_shit(self):
        
        if os.path.exists(PROFILES_PATH) and os.stat(PROFILES_PATH).st_size > 0:
            infile = open(PROFILES_PATH,'rb')
            self.profiles = pickle.load(infile)
            infile.close()
            print('profiles.bin loaded')
        else:
            print('No profiles bin file found')

    def viewProfile(self, item):

            """ Reads contents of the selected spectral profile """
    
            for profile in self.profiles:
                if profile.name == item.text():
                    target = profile
                    pixelCount = len(target.pixels)

            # self.pixelLabel.setText(f'{item.text()}\n{pixelCount} pixels')
            
            self.plot1.cla()

            for i in range(len(target.pixels)):
                self.plot1.plot(target.pixels[i], label= 'pixel %s ' %i)

            self.plot1.legend()
            self.plot1.set_xlabel("Spectral Band")
            self.plot1.set_title(f'{item.text()}\n{pixelCount} pixels')
            # self.plot1.title(item.text())
            self.canvas.draw()
            
    
    def plotAllProfiles(self):
        """ Plots all profiles on one graph"""
        self.plot1.cla()
        for profile in self.profiles: 
            pixels = profile.pixels
            avgSpectra = []
            for j in range(len(self.TARGET_BANDS)):
                total = 0
                for i in range(len(pixels)):
                    total += pixels[i][j]
                    avg = round(total/len(pixels))
                avgSpectra.append(avg)
            print(profile.name + '\n'+ str(avgSpectra) + '\n')
            
            profile.avgSpectra = avgSpectra
            self.plot1.plot(avgSpectra, label=profile.name)
        self.plot1.legend()
        # self.plot1.set_xticks([0, 1, 2, 3])
        self.plot1.set_xlabel('Band')
        self.plot1.set_title('All Saved Spectral Profiles')
        
        self.canvas.draw()
            

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.TARGET_BANDS = [8, 13, 15, 25, 55, 77, 82, 85, 91, 93, 97, 102, 112, 115, 120, 137, 158, 183]
        self.profiles = []
        self.load_shit()

        self.layout = qtw.QGridLayout()

        ### LEFT FRAME
        self.profilesLabel = qtw.QLabel("<b>Saved Profiles</b>")
        self.profilesLabel.setAlignment(qtc.Qt.AlignCenter)
        self.layout.addWidget(self.profilesLabel, 0, 0)

        self.profileList = qtw.QListWidget()
        self.profileList.setFixedWidth(180)
        self.profileList.setSizePolicy(qtw.QSizePolicy.Fixed, qtw.QSizePolicy.Expanding)
        self.layout.addWidget(self.profileList, 1, 0)
        
        self.plotAllButton = qtw.QPushButton("Plot All", clicked=self.plotAllProfiles)
        self.layout.addWidget(self.plotAllButton, 2, 0)

        for profile in self.profiles:
            self.profileList.addItem(profile.name)

        self.profileList.itemDoubleClicked.connect(self.viewProfile)

        
        ### Profile Details
        self.pixelLabel = qtw.QLabel("0<br>pixels")
        self.pixelLabel.setAlignment(qtc.Qt.AlignCenter)
        self.pixelLabel.setFont(qtg.QFont('Arial font', 12))
        # self.layout.addWidget(self.pixelLabel, 0, 1, 1, 3)


        self.pixelWindow = qtw.QFrame(self)
        self.pixelWindow.setSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Expanding)
        self.pixelWindow.setFrameShape(qtw.QFrame.Box)
        self.pixelWindow.setLayout(qtw.QVBoxLayout())
        self.layout.addWidget(self.pixelWindow, 1, 1, 2, 3)

        self.setLayout(self.layout)

    
        self.fig = Figure(figsize=(12,4))
    
        self.plot1 = self.fig.add_subplot(111)
        
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.canvas.setSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Expanding)

        # self.pixelWindow.layout().addWidget(self.pixelLabel)

        self.pixelWindow.layout().addWidget(self.canvas)
        # self.viewProfile(item=self.profileList.itemFromIndex()