import os
import matplotlib
import spectral.io.envi as envi
from spectral.graphics.spypylab import ImageView
from qviewer import qViewer, NavigationToolbar, MyImageView
matplotlib.use('Qt5Agg')
from osgeo import gdal
from brokenaxes import brokenaxes
import matplotlib.patches as patches
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from config import HYPERION_SCANS_PATH, HYP_WAVELENGTHS
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc
gdal.UseExceptions()


TARGET_BANDS = [8, 13, 15, 25, 55, 77, 82, 85, 91, 93, 97, 102, 112, 115, 120, 137, 158, 183]

LAN_PATH = os.path.join(os.getcwd(), 'downloads')
PROFILES_PATH = os.path.join(os.getcwd(), 'profiles.bin')
NICKNAMES_PATH = os.path.join(os.getcwd(), 'nicknames.bin')

class PixelViewer(qtw.QFrame):
    ''' A class for the small PixelViewer submodule within Spectra Manager module '''
    import spectral as s

    requestPixelDeleted = qtc.pyqtSignal(str)

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
        self.delPixel_btn = qtw.QPushButton("Delete Pixel", clicked=self.delete_pixel)
        self.delPixel_btn.setMaximumWidth(150)
        
        self.leftFrame.addWidget(self.pixelListLabel)
        self.leftFrame.addWidget(self.pixelListView)
        self.leftFrame.addWidget(self.delPixel_btn, )

        self.layout.addLayout(self.leftFrame)
        self.view = None
        

        # Right Side

        self.v_midframe = qtw.QWidget()
        self.v_midframe.setFixedWidth(180)
        self.v_midframe.setLayout(qtw.QVBoxLayout())
        self.v_midframe.setStyleSheet("background-color:#ccc; padding:0,0")
        self.v_fig = plt.figure(figsize=(10, 1))
        self.v_imageCanvas = FigureCanvasQTAgg(self.v_fig)
        self.ax1 = plt.Axes(self.v_fig, [0., 0., 1., 1.])
        self.v_fig.add_axes(self.ax1)
        self.ax1.set_axis_off()
        self.v_midframe.layout().addWidget(self.v_imageCanvas)
        self.v_imageCanvas.draw()

        self.layout.addWidget(self.v_midframe)
        self.pixelDetailLabel = qtw.QLabel()
        self.layout.addWidget(self.pixelDetailLabel)

    def populate_pixel_list(self):
        self.pixelListView.clear()
        for pixel in self.pixelsToList:
            self.pixelListView.addItem(pixel)

    def delete_pixel(self):
        target = self.pixelListView.currentItem().text()
        self.requestPixelDeleted.emit(target)

    def remove_pixel_from_list(self, pid):
        items_list = self.pixelListView.findItems(pid, qtc.Qt.MatchExactly)
        for item in items_list:
            r = self.pixelListView.row(item)
            self.pixelListView.takeItem(r)

    def find_pixel(self, source, r, c):
        # print(f'finding pixel {r},{c} from {source}')
        self.v_fig.clear()
        self.ax1 = plt.Axes(self.v_fig, [0., 0., 1., 1.])
        self.v_fig.add_axes(self.ax1)
        self.ax1.set_axis_off()
        source2 = source.replace('\\', '/')
        parts = source2.split('/')
        name = parts[(len(parts)-1)][:-4]
        self.pixelDetailLabel.setText(f'{name}\nRow: {r}\nCol: {c}')
        try:
            img = envi.open(source.replace('.L1R', '.hdr'), source)
            self.view = MyImageView(img, (32, 21, 13), stretch=((.01, .99), (.01, .99), (.01, .98)), interpolation='none', source=img)        
            self.view.open_zoom(center=(r,c), size=65, fignum=2)
        except:
            try:
                import spectral as s
                img = s.open_image(source)
                self.view = MyImageView(img, (32, 21, 13), stretch=((.01, .99), (.01, .99), (.01, .98)), interpolation='none', source=img)        
                self.view.open_zoom(center=(r,c), size=65, fignum=2)
            except Exception as e:
                print(e)
                fig = self.v_fig
                ax = fig.add_subplot()
                fig.subplots_adjust(top=0.85)
                ax.axis([0, 10, 0, 10])
                ax.text(2, 5, r'Missing Scan', fontsize=7)

                ax.set_axis_off()
        self.v_imageCanvas.draw()
        

class QSpectraManager(qtw.QFrame):
    ''' A class for the Spectra Manager module of HyperGix '''
    addMaterial = qtc.pyqtSignal(str)
    readyForMaterials = qtc.pyqtSignal()
    pixelsPlease = qtc.pyqtSignal(str)
    deleteThisPid = qtc.pyqtSignal(str)
    reportAverage = qtc.pyqtSignal(str, list)

    def populate_materials(self, materials):
        # print('materials received:', materials)
        self.materials = materials
        for profile in self.materials:
            self.profileList.addItem(profile)
 
    def request_pixels(self, item):
        material = item.text()
        self.pixelsPlease.emit(material)

    def plot_profile(self, pixelList, bandcount):
        """ Receives a list of pixel data and plots it in the viewer tab """
        import numpy as np

        self.currentPixels = []
        material = self.profileList.currentItem()
        material = material.text()
        badbands = range(57,78)

        if pixelList:
            pixelCount = len(pixelList)
            self.pixelLabel.setText(f'{material}\n{pixelCount} pixels')

            self.plot1.cla()
            self.x = np.linspace(400, 2500, bandcount)
            self.plotList = []
            for pixel in pixelList:
                pid = list(pixel.keys())
                self.currentPixels.append(pid[0])
                self.pixelViewer.pixelsToList = self.currentPixels
                self.pixelViewer.pixelListView.clear()
                self.pixelViewer.populate_pixel_list()
                

                for i in pixel:
                    stringList = pixel[i].split()
                    intList = list(map(int, stringList))
                    count = len(intList)
                    while count > 0:
                        if count in badbands:
                            intList.pop(count)
                        count -= 1
                    while len(intList) < bandcount:
                        intList.append(0)

                    
                    self.plot1.plot(self.x, intList, label=f'Pixel {i}', linewidth='1', alpha=0.3)
                    self.plotList.append(intList)

                     # RGB Legend Overlay

                    self.plot1.plot([620, 720],[-300, -300], '-r', linewidth=4, markersize=12)
                    self.plot1.plot([495, 570],[-300, -300], '-g', linewidth=4, markersize=12)
                    self.plot1.plot([450, 495],[-300, -300], '-b', linewidth=4, markersize=12)
                    self.plot1.plot([760, 1400],[-300, -300], '-k', alpha=.3, linewidth=4, markersize=12)


            np.set_printoptions(precision = 2, suppress = True)
            avg = [np.mean(x) for x in zip(*self.plotList)]
            
            

            self.plot1.plot(self.x, avg, label='Average', linestyle='-', linewidth='2', color='midnightblue')
            self.plot1.legend()
            self.plot1.set_xlabel("Wavelength")
            self.canvas.draw()
            
            self.reportAverage.emit(material, avg)
            # self.deletePixelButton.show()

        else:
            self.pixelLabel.setText(f'No pixels stored for {material}')
            self.plot1.cla()
            self.deletePixelButton.hide()
        
        self.canvas.draw()

    def delete_pixel(self):
        """ Pops up a modal window asking which pixel to remove from db """
        items = tuple(self.currentPixels)
		
        item, ok = qtw.QInputDialog.getItem(self, "Select Pixel", "Which pixel to delete?", items, 0, False)
        if ok:
            badPixel = item
            self.deleteThisPid.emit(badPixel)

    def delete_profile(self):
        item = self.profileList.currentItem()
        item = item.text()
        self.deleteThisPid.emit(item)

    def new_profile_popup(self):
        """ Pops up a modal window for creating a new profile """
        self.new_profile_popup = qtw.QDialog()
        self.new_profile_popup.move(500,500)
        self.new_profile_popup.setWindowTitle('Create A New Profile')
        self.new_profile_popup.setLayout(qtw.QFormLayout())
        
        p_name = qtw.QLineEdit()

        self.new_profile_popup.layout().addRow(qtw.QLabel("New Material Profile"))
        self.new_profile_popup.layout().addRow('Profile Name:', p_name)
        
        self.new_profile_popup.layout().addRow(qtw.QPushButton("Create Profile", clicked=lambda: self.create_profile(p_name.text())))
        self.new_profile_popup.show()

    def create_profile(self, name):
        self.addMaterial.emit(name)
        self.new_profile_popup.hide()
        self.profileList.addItem(name)
        print(f'{name} profile added to db')

    def remove_profile_from_list(self, name):
        items_list = self.profileList.findItems(name, qtc.Qt.MatchExactly)
        for item in items_list:
            r = self.profileList.row(item)
            self.profileList.takeItem(r)
        
    
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

        self.addProfileButton = qtw.QPushButton("Create New Profile", clicked=self.new_profile_popup)
        self.layout.addWidget(self.addProfileButton, 2, 0)

        self.delProfileButton = qtw.QPushButton('Delete Profile', clicked=self.delete_profile)
        self.layout.addWidget(self.delProfileButton, 3, 0)
        
        # self.layout.addWidget(self.plotAllButton, 3, 0)
               

        self.profileList.itemDoubleClicked.connect(self.request_pixels)
        
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
        # print('qmanager spectral plot figure is:', self.fig.number)
    
        self.plot1 = self.fig.add_subplot(111)

        self.canvas = FigureCanvasQTAgg(self.fig)
        self.canvas.setSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Expanding)

        self.pixelWindow.layout().addWidget(self.pixelLabel)
        self.pixelWindow.layout().addWidget(self.canvas)
        
        # Delete pixel button
        self.deletePixelButton = qtw.QPushButton("Delete A Pixel", clicked=self.delete_pixel)
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
        # self.requestPixels(self.profileList.setCurrentItem())
        