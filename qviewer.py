from matplotlib.backends.backend_qt5 import NavigationToolbar2QT
import spectral as s
from spectral.graphics.spypylab import ImageView
import spectral.io.envi as envi
import os
import matplotlib.pyplot as plt
import matplotlib
import shutil
matplotlib.use('Qt5Agg')

from osgeo import gdal
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg)
from os.path import exists

from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc

from config import HYPERION_SCANS_PATH as DOWNLOAD_PATH
from functions import tifCruncher


gdal.UseExceptions()

class NavigationToolbar(NavigationToolbar2QT):
    # only display the buttons we need
    toolitems = [t for t in NavigationToolbar2QT.toolitems if
                 t[0] in ('Home', 'Back', 'Forward', 'Pan', 'Zoom', 'Save')]


class qViewer(qtw.QWidget):
    """ A class for the Image Viewer GUI panel """


    def openTiffFromList(self, item):
        """ Processes and opens a GeoTiff image in the viewer """
        # plt.clf()
        # self.s_fig.cla()
        self.v_fig.clf()
        
        # Raster image
        filename = item.text() + '.L1R'
        filepath = os.path.join(DOWNLOAD_PATH, filename[:-4], filename)

        # Raster header file
        h_filename = item.text() + '.hdr'
        h_filepath = os.path.join(DOWNLOAD_PATH, filename[:-4], h_filename)

        img = envi.open(h_filepath, filepath)
        desc = gdal.Info(filepath)
        # desc = desc.split('Corner Coordinates')[0]
        # print('\n'+desc)
        
        
        self.properties_text.setText(str(img).replace('\t', ''))
        self.properties_text.append(desc)
        self.view = s.ImageView(img, (50, 27, 17), stretch=((.01, .99), (.01, .99), (.01, .98)), interpolation='none', source=img)
        self.view.spectrum_plot_fig_id = 2
        self.view.show(mode='data', fignum=1)
        
        
        self.v_imageCanvas.draw()
        self.v_spectraCanvas.draw()

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

        self.properties_label = qtw.QLabel("File Properties")
        self.properties_text = qtw.QTextBrowser()
        self.properties_text.setFixedWidth(230)
        self.properties_text.setFixedHeight(150)
        
        self.leftFrame.addWidget(self.dl_label)
        self.leftFrame.addWidget(self.downloadList)
        self.leftFrame.addWidget(self.open_btn, )
        self.leftFrame.addWidget(self.properties_label)
        self.leftFrame.addWidget(self.properties_text)

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
                    filename = name[:-4]

                    old_header = os.path.join(DOWNLOAD_PATH, filename, f'{filename}.bak')
                    header = os.path.join(DOWNLOAD_PATH, filename, f'{filename}.hdr')

                    if not exists(old_header):
                        # Making a new copy of header with corrected offset of 2502
                        print(f'Corrected header not found for {name}. Creating it now...')
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

        # Mid frame
        self.v_midframe = qtw.QWidget()
        self.v_midframe.setLayout(qtw.QVBoxLayout())

        self.v_imageFrame = qtw.QWidget()
        self.v_imageFrame.setLayout(qtw.QVBoxLayout())

        self.splitter = qtw.QSplitter()

        self.subLayout = qtw.QWidget()
        self.subLayout.setLayout(qtw.QVBoxLayout())

        self.subLayout2 = qtw.QWidget()
        self.subLayout2.setLayout(qtw.QVBoxLayout())
       
        self.v_fig = plt.figure(figsize=(1,5))
        self.s_fig = plt.figure(figsize=(6,5))

        self.v_imageCanvas = FigureCanvasQTAgg(self.v_fig)
        self.v_spectraCanvas = FigureCanvasQTAgg(self.s_fig)
        self.v_canvas_nav = NavigationToolbar(self.v_imageCanvas, self.v_midframe)

        self.ax1 = plt.Axes(self.v_fig, [0., 0., 1., 1.])
        self.ax1.set_axis_off()
        self.v_fig.add_axes(self.ax1)
        self.s_fig.suptitle('Pixel Spectra', fontsize=10)

        self.pixelButtons = qtw.QWidget()
        self.pixelButtons.setLayout(qtw.QHBoxLayout())

        self.v_midframe.layout().addWidget(self.v_imageFrame)
        self.v_imageFrame.layout().addWidget(self.splitter)
        self.layout.addWidget(self.v_midframe)
        self.subLayout.layout().addWidget(self.v_canvas_nav)
        self.subLayout.layout().addWidget(self.v_imageCanvas)
        self.subLayout2.layout().addWidget(self.v_spectraCanvas)
        self.subLayout2.layout().addWidget(self.pixelButtons)
        self.splitter.addWidget(self.subLayout)
        self.splitter.addWidget(self.subLayout2)
        
        self.clearPlot_btn = qtw.QPushButton("Clear Plot")
        self.clearPlot_btn.clicked.connect(plt.cla)
        self.addPixel_btn = qtw.QPushButton("Add Pixel to Profile")
        

        self.pixelButtons.layout().addWidget(self.clearPlot_btn)
        self.pixelButtons.layout().addWidget(self.addPixel_btn)

        self.v_imageCanvas.draw()
        self.v_spectraCanvas.draw()

        
