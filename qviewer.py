from matplotlib.backends.backend_qt5 import NavigationToolbar2QT
import spectral as s
import spectral.io.envi as envi
import os
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Qt5Agg')

from osgeo import gdal
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg)

from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc

from config import HYPERION_SCANS_PATH as DOWNLOAD_PATH
from functions import tifCruncher


gdal.UseExceptions()

class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = plt.figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

class qViewer(qtw.QWidget):
    """ A class for the Image Viewer GUI panel """

    converting = qtc.pyqtSignal()
    convertDone = qtc.pyqtSignal()

    def openTiffFromList(self, item):
        """ Processes and opens a GeoTiff image in the viewer """
        plt.clf()
        filename = item.text() + '.L1R'
        filepath = os.path.join(DOWNLOAD_PATH, filename[:-4], filename)

        h_filename = item.text() + '.hdr'
        h_filepath = os.path.join(DOWNLOAD_PATH, filename[:-4], h_filename)

        h_envi = item.text() + '.envi.hdr'
        h_envi_filepath = os.path.join(DOWNLOAD_PATH, filename[:-4], h_envi)

        # img = gdal.Open(filepath)
        # cols = img.RasterXSize
        # rows = img.RasterYSize
        # bands = img.RasterCount

        # envi.create_image(h_filepath, interleave='bil', dtype='int16', ext='.L1R', shape=(rows, cols, bands), offset=453, force=True)
        # print('filepath is:', filepath)
        # filepath = gdal.Open(filepath)
        
        self.converting.emit()
        # tiffed = tifCruncher(filepath, filename)
        # gdal.Translate(lan_file, tiffed, format='LAN', outputType=gdal.GDT_Int16) #took out options=['-scale']
        img = envi.open(h_filepath, filepath)
        
        self.convertDone.emit()
       
        self.properties_text.setText(str(img).replace('\t', ''))
        # self.view = s.ImageView(img, (4, 3, 1), stretch=((.01, .99), (.01, .99), (.01, .98)), resample=True, interpolation='none')
        self.view = s.ImageView(img, (50, 27, 17), stretch=((.01, .99), (.01, .99), (.01, .98)), interpolation='none')
        # self.v_ax.imshow(img, (4, 3, 1),figsize=(10,10), stretch=((.01, .99), (.01, .99), (.01, .98)))
        # self.view = s.imshow(img, (4, 3, 1), fignum=1)
        self.view.show(mode='data', fignum=1)
        
        self.v_canvas.draw()

    def __init__(self, *args, **kwargs):
        super().__init__()

        self.layout = qtw.QHBoxLayout()
        self.setLayout(self.layout)

        # Internal variables
        self.downloads = []
        self.readable_files = {}

        #Left Frame
        self.leftFrame = qtw.QVBoxLayout()
        self.dl_label = qtw.QLabel("<b>Downloads</b>")
        self.dl_label.setAlignment(qtc.Qt.AlignCenter)
        self.dl_label.setFont(qtg.QFont('Arial', 12))

        self.downloadList = qtw.QListWidget()
        self.downloadList.setFixedWidth(230)
        self.downloadList.setSizePolicy(qtw.QSizePolicy.Fixed, qtw.QSizePolicy.Expanding)
        self.downloadList.itemDoubleClicked.connect(self.openTiffFromList)
        self.open_btn = qtw.QPushButton("Import GeoTiff")
        self.open_btn.setSizePolicy(qtw.QSizePolicy.Minimum, qtw.QSizePolicy.Preferred)

        self.leftFrame.addWidget(self.dl_label)
        self.leftFrame.addWidget(self.downloadList)
        self.leftFrame.addWidget(self.open_btn)

        self.layout.addLayout(self.leftFrame)

        if os.path.join(os.getcwd(), 'downloads'):
            print('downloads folder found')
        else:
            print(os.path.join(os.getcwd(), 'downloads'))
            print(DOWNLOAD_PATH)
            os.mkdir(DOWNLOAD_PATH)

        for root, dirs, files in os.walk(DOWNLOAD_PATH, topdown=False):
            for name in files:
                if name[-3:] == 'L1R':
                    # print('inserting', name[:-4], 'in list')
                    # print(os.path.join(root, name))
                    self.downloadList.addItem(name[:-4])
                    self.readable_files[name[:-4]] = os.path.join(root, name)

        # Mid frame
        self.v_midframe = qtw.QWidget()
        self.v_midframe.setLayout(qtw.QVBoxLayout())
        self.layout.addWidget(self.v_midframe)

        # self.v_fig = plt.figure(figsize=(12,4))
        # self.v_canvas = FigureCanvasQTAgg(self.v_fig)
        self.v_canvas = MplCanvas(self)
        self.v_canvas.setSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Expanding)
        self.v_canvas_nav = NavigationToolbar2QT(self.v_canvas, self.v_midframe)
        
        self.v_midframe.layout().addWidget(self.v_canvas)
        self.v_midframe.layout().addWidget(self.v_canvas_nav)
        self.v_canvas.draw()

        # def do_zoom(event):
        #     factor = 1.001 ** event.delta
        #     self.v_canvas_widget.scale(tk.ALL, event.x, event.y, factor, factor/2)

        # Right frame
        self.rightFrame = qtw.QVBoxLayout()
        self.layout.addLayout(self.rightFrame)

        self.properties_label = qtw.QLabel("File Properties")
        self.properties_text = qtw.QTextBrowser()
        self.properties_text.setFixedWidth(230)
        self.properties_text.setFixedHeight(150)
        

        self.rightFrame.addStretch()
        self.rightFrame.addWidget(self.properties_label)
        self.rightFrame.addWidget(self.properties_text)
        self.rightFrame.addStretch()
        # self.openTiffFromList(event=None)