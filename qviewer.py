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
        # plt.clf()
        plt.cla()
        print(plt.get_fignums())
        # Raster image
        filename = item.text() + '.L1R'
        filepath = os.path.join(DOWNLOAD_PATH, filename[:-4], filename)

        # Raster header file
        h_filename = item.text() + '.hdr'
        h_filepath = os.path.join(DOWNLOAD_PATH, filename[:-4], h_filename)

        # self.converting.emit()

        img = envi.open(h_filepath, filepath)
        
        # self.convertDone.emit()
       
        self.properties_text.setText(str(img).replace('\t', ''))
        self.view = s.ImageView(img, (50, 27, 17), stretch=((.01, .99), (.01, .99), (.01, .98)), interpolation='none', source=img)
        # self.v_ax.imshow(img, (4, 3, 1),figsize=(10,10), stretch=((.01, .99), (.01, .99), (.01, .98)))
        # self.view = s.imshow(img, (4, 3, 1), fignum=1)
        self.view.spectrum_plot_fig_id = 2
        self.view.show(mode='data', fignum=1)
        
        
        self.v_canvas.draw()
        self.v_canvas2.draw()

    def __init__(self, *args, **kwargs):
        super().__init__()

        self.layout = qtw.QHBoxLayout()
        self.setLayout(self.layout)
        print(dir(ImageView))
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
        self.layout.addWidget(self.v_midframe)

        self.v_fig = plt.figure(figsize=(12,4), tight_layout=True)
        self.s_fig = plt.figure(figsize=(3,4), tight_layout=True)
        # self.s_fig.set(gcf,'Position', get(gcf,'Position') + [0,0,150,0])
        # self.v_fig, self.s_fig = plt.subplots(nrows=1, ncols=2, figsize=(12,4))
        self.v_canvas = FigureCanvasQTAgg(self.v_fig)
        self.v_canvas2 = FigureCanvasQTAgg(self.s_fig)
        # self.v_canvas = MplCanvas(self)
        self.v_canvas.setSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Expanding)
        self.v_canvas_nav = NavigationToolbar2QT(self.v_canvas, self.v_midframe)
        
        self.v_midframe.layout().addWidget(self.v_canvas)
        self.v_midframe.layout().addWidget(self.v_canvas_nav)
        self.v_midframe.layout().addWidget(self.v_canvas2)
        self.v_canvas.draw()
        self.v_canvas2.draw()

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
        
        # self.v_canvas.mouseDoubleClickEvent.connect