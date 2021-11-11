import os
import pickle
import matplotlib
import spectral.io.envi as envi
from spectral.graphics.spypylab import ImageView
from qviewer import qViewer, NavigationToolbar, MyImageView
matplotlib.use('Qt5Agg')
import spectral as s
import numpy as np
from osgeo import gdal
from brokenaxes import brokenaxes
import matplotlib.patches as patches
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from config import HYPERION_SCANS_PATH
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc
gdal.UseExceptions()


TARGET_BANDS = [8, 13, 15, 25, 55, 77, 82, 85, 91, 93, 97, 102, 112, 115, 120, 137, 158, 183]

LAN_PATH = os.path.join(os.getcwd(), 'downloads')
PROFILES_PATH = os.path.join(os.getcwd(), 'profiles.bin')
NICKNAMES_PATH = os.path.join(os.getcwd(), 'nicknames.bin')

class PixelViewer(qtw.QFrame):

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.setFrameShape(qtw.QFrame.Box)
        self.pixelsToList = []
        # Left Side
        self.setMaximumWidth(500)
        self.layout = qtw.QHBoxLayout()
        self.setLayout(self.layout)
        self.leftFrame = qtw.QVBoxLayout()
        self.pixelListLabel = qtw.QLabel("<b>Pixel Viewer</b>")
        self.pixelListLabel.setAlignment(qtc.Qt.AlignCenter)
        self.pixelListLabel.setFont(qtg.QFont('Arial', 12))

        self.pixelListView = qtw.QListWidget()
        self.pixelListView.setMaximumWidth(150)
        self.pixelListView.setSizePolicy(qtw.QSizePolicy.Minimum, qtw.QSizePolicy.Expanding)
        # self.downloadList.itemDoubleClicked.connect(self.openTiffFromList)
        self.delPixel_btn = qtw.QPushButton("Delete Pixel")
        self.delPixel_btn.setMaximumWidth(150)
        
        self.leftFrame.addWidget(self.pixelListLabel)
        self.leftFrame.addWidget(self.pixelListView)
        self.leftFrame.addWidget(self.delPixel_btn, )

        self.layout.addLayout(self.leftFrame)
        

        # Right Side

        self.v_midframe = qtw.QWidget()
        self.v_midframe.setMaximumWidth(180)
        self.v_midframe.setLayout(qtw.QVBoxLayout())
        self.v_midframe.setStyleSheet("background-color:#ccc; padding:0,0")
        
       
        self.v_fig = plt.figure(figsize=(10, 1))
        print('pixel viewer v_fig is', self.v_fig.number) ### It's 2

        self.v_imageCanvas = FigureCanvasQTAgg(self.v_fig)
        # self.v_canvas_nav = NavigationToolbar2QT(self.v_imageCanvas, self.v_midframe)

        self.ax1 = plt.Axes(self.v_fig, [0., 0., 1., 1.])
        self.v_fig.add_axes(self.ax1)
        self.ax1.set_axis_off()

  
        # self.v_midframe.layout().addWidget(self.v_canvas_nav)
        self.v_midframe.layout().addWidget(self.v_imageCanvas)
        # self.v_midframe.layout().addWidget(self.subLayout)

        self.v_imageCanvas.draw()

        self.layout.addWidget(self.v_midframe)
        self.pixelDetailLabel = qtw.QLabel()
        self.layout.addWidget(self.pixelDetailLabel)
        # self.layout.addWidget(self.v_canvas_nav)


    def populatePixelList(self):
        
        self.pixelListView.clear()

        for pixel in self.pixelsToList:
            self.pixelListView.addItem(pixel)

    def findPixel(self, source, r, c):
        print('SOURCE IS', source)
        self.v_fig.clear()
        self.ax1 = plt.Axes(self.v_fig, [0., 0., 1., 1.])
        self.v_fig.add_axes(self.ax1)
        self.ax1.set_axis_off()
        name = source.replace('.L1R', '')[-22:]
        self.pixelDetailLabel.setText(f'{name}\nRow: {r}\nCol: {c}')
        img = envi.open(source.replace('.L1R', '.hdr'), source)
        self.view = MyImageView(img, (50, 27, 17), stretch=((.01, .99), (.01, .99), (.01, .98)), interpolation='none', source=img)        
        # self.view.show(fignum=1)
        # self.view.pan_to(r,c)
        self.view.open_zoom(center=(r,c), size=65, fignum=2)
        # self.view.axes.add_patch(patches.Rectangle((r,c), 2, 2, linewidth=1, facecolor='none'))

        self.v_imageCanvas.draw()
        

        
        



class qProfileManager(qtw.QFrame):

    addMaterial = qtc.pyqtSignal(str)
    readyForMaterials = qtc.pyqtSignal()
    pixelsPlease = qtc.pyqtSignal(str)
    deleteThisPid = qtc.pyqtSignal(str)
    calcAvgPls = qtc.pyqtSignal(str)

    def populateMaterials(self, materials):
        print('materials received:', materials)
        self.materials = materials
        for profile in self.materials:
            self.profileList.addItem(profile)
 
    def requestPixels(self, item):
        material = item.text()
        self.pixelsPlease.emit(material)

    def requestAverage(self, item):
        item = item.text()
        self.calcAvgPls.emit(item)

    def plotProfile(self, pixelList, bandcount):
        """ Receives a list of pixel data and plots it in the viewer tab """
        self.currentPixels = []
        material = self.profileList.currentItem()
        material = material.text()
        badbands = range(57,78)

        if pixelList:
            pixelCount = len(pixelList)
            self.pixelLabel.setText(f'{material}\n{pixelCount} pixels')

            self.plot1.cla()
            self.x = np.linspace(400, 2500, 221)
            self.plotList = []
            for pixel in pixelList:
                pid = list(pixel.keys())
                self.currentPixels.append(pid[0])
                self.pixelViewer.pixelsToList = self.currentPixels
                self.pixelViewer.pixelListView.clear()
                self.pixelViewer.populatePixelList()
                

                for i in pixel:
                    stringList = pixel[i].split()
                    intList = list(map(int, stringList))
                    count = len(intList)
                    while count > 0:
                        if count in badbands:
                            intList.pop(count)
                        count -= 1
                    
                    self.plot1.plot(self.x, intList, label=f'Pixel {i}', linewidth='1', alpha=0.3)
                    self.plotList.append(intList)

            print(self.plotList)
            print('length of plotlist is', len(self.plotList))
            avg = [sum(x) / len(x) for x in zip(*self.plotList)]
            

            self.plot1.plot(self.x, avg, label='Average', linestyle='-', linewidth='2', color='midnightblue')
            self.plot1.legend()
            self.plot1.set_xlabel("Wavelength")
            self.canvas.draw()
            
            # self.deletePixelButton.show()

        else:
            self.pixelLabel.setText(f'No pixels stored for {material}')
            self.plot1.cla()
            self.deletePixelButton.hide()
        
    def plotAllProfiles(self):
        """ Plots all profiles on one graph"""
        self.plot1.cla()
        # for profile in self.profiles: 
        #     pixels = profile.pixels
        #     avgSpectra = []
        #     for j in range(len(self.TARGET_BANDS)):
        #         total = 0
        #         for i in range(len(pixels)):
        #             total += pixels[i][j]
        #             avg = round(total/len(pixels))
        #         avgSpectra.append(avg)
        #     print(profile.name + '\n'+ str(avgSpectra) + '\n')
            
        #     profile.avgSpectra = avgSpectra
        #     self.plot1.plot(avgSpectra, label=profile.name)
        # self.plot1.legend()
        # # self.plot1.set_xticks([0, 1, 2, 3])
        # self.plot1.set_xlabel('Band')
        # self.plot1.set_title('All Saved Spectral Profiles')
        
        self.canvas.draw()

    def deletePixel(self):
        """ Pops up a modal window asking which pixel to remove from db """
        items = tuple(self.currentPixels)
		
        item, ok = qtw.QInputDialog.getItem(self, "Select Pixel", "Which pixel to delete?", items, 0, False)
        if ok:
            badPixel = item
            self.deleteThisPid.emit(badPixel)

    def profilePop(self):
        """ Pops up a modal window for creating a new profile """
        self.profilePop = qtw.QDialog()
        self.profilePop.move(500,500)
        self.profilePop.setWindowTitle('Create A New Profile')
        self.profilePop.setLayout(qtw.QFormLayout())
        
        p_name = qtw.QLineEdit()

        self.profilePop.layout().addRow(qtw.QLabel("New Material Profile"))
        self.profilePop.layout().addRow('Profile Name:', p_name)
        
        self.profilePop.layout().addRow(qtw.QPushButton("Create Profile", clicked=lambda: self.createProfile(p_name.text())))
        self.profilePop.show()

    def createProfile(self, name):
        self.addMaterial.emit(name)
        self.profilePop.hide()
        self.profileList.addItem(name)
        print(f'{name} profile added to db')

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.TARGET_BANDS = [8, 13, 15, 25, 55, 77, 82, 85, 91, 93, 97, 102, 112, 115, 120, 137, 158, 183]
        self.profiles = []
        self.materials = []
        self.currentPixels = []
        

        self.layout = qtw.QGridLayout()

        ### LEFT FRAME
        self.profilesLabel = qtw.QLabel("<b>Saved Profiles</b>")
        self.profilesLabel.setAlignment(qtc.Qt.AlignCenter)
        self.layout.addWidget(self.profilesLabel, 0, 0)

        self.profileList = qtw.QListWidget()
        self.profileList.setFixedWidth(180)
        self.profileList.setSizePolicy(qtw.QSizePolicy.Fixed, qtw.QSizePolicy.Expanding)
        self.layout.addWidget(self.profileList, 1, 0)

        self.addProfileButton = qtw.QPushButton("Create New Profile", clicked=self.profilePop)
        self.layout.addWidget(self.addProfileButton, 2, 0)

        self.delProfileButton = qtw.QPushButton('Delete Profile')
        self.layout.addWidget(self.delProfileButton, 3, 0)
        
        self.plotAllButton = qtw.QPushButton("Plot All", clicked=self.plotAllProfiles)
        # self.layout.addWidget(self.plotAllButton, 3, 0)
               

        self.profileList.itemDoubleClicked.connect(self.requestPixels)
        self.profileList.itemDoubleClicked.connect(self.requestAverage)

        
        ### Profile Details
        self.pixelLabel = qtw.QLabel("0<br>pixels")
        self.pixelLabel.setAlignment(qtc.Qt.AlignCenter)
        self.pixelLabel.setFont(qtg.QFont('Arial font', 12))
        # self.layout.addWidget(self.pixelLabel, 0, 1, 1, 3)


        self.pixelWindow = qtw.QFrame(self)
        self.pixelWindow.setSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Expanding)
        self.pixelWindow.setFrameShape(qtw.QFrame.Box)
        self.pixelWindow.setLayout(qtw.QVBoxLayout())
        self.layout.addWidget(self.pixelWindow, 1, 1, 3, 3)

        self.setLayout(self.layout)
        self.fig =  plt.figure(figsize=(12,4))
    
        self.plot1 = self.fig.add_subplot(111)

        self.canvas = FigureCanvasQTAgg(self.fig)
        self.canvas.setSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Expanding)

        self.pixelWindow.layout().addWidget(self.pixelLabel)
        self.pixelWindow.layout().addWidget(self.canvas)
        
        # Delete pixel button
        self.deletePixelButton = qtw.QPushButton("Delete A Pixel", clicked=self.deletePixel)
        self.deletePixelButton.setMaximumWidth(100)
        self.sublayout = qtw.QHBoxLayout()
        self.pixelWindow.layout().addLayout(self.sublayout)
        # self.sublayout.addStretch()
        

        # Pixel viewer
        self.pixelViewer = PixelViewer()
        self.pixelViewer.setMaximumHeight(200)
        self.sublayout.addWidget(self.pixelViewer)
        self.sublayout.addWidget(self.deletePixelButton)
        self.deletePixelButton.hide()

        self.readyForMaterials.emit()
        