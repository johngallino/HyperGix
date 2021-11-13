from matplotlib.backends.backend_qt5 import NavigationToolbar2QT
import spectral as s
from spectral.graphics.spypylab import ImageView, KeyParser, ImageViewMouseHandler,  set_mpl_interactive, ParentViewPanCallback
from spectral.io import aviris
import spectral.io.envi as envi
import os
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import matplotlib
import shutil
import numpy as np
matplotlib.use('Qt5Agg')
from brokenaxes import brokenaxes
from osgeo import gdal
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg)
from os.path import exists
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc

from config import HYPERION_SCANS_PATH as DOWNLOAD_PATH


gdal.UseExceptions()


class MyImageView(ImageView):
    def __init__(self, data=None, bands=None, classes=None, source=None, brokenaxes=True,
                 **kwargs):
                 ImageView.__init__(self, data, bands, classes, source,
                 **kwargs)
                 self.broken = brokenaxes

    lastPixel = {"row": 0, "col": 0}
    
    def show(self, mode=None, fignum=None):
        super().show(mode, fignum)
        self.cb_mouse = MyMouseHandler(self, self.broken)
        self.cb_mouse.connect()
        # self.cb_mouse.show_events = True

    def updateLastPixel(self, r, c):
        self.lastPixel["row"] = r
        self.lastPixel["col"] = c

    def open_zoom(self, center=None, size=None, fignum=2):
        '''Modified original method to display zoomed view in self NOT a new window '''

        from spectral import settings
        import matplotlib.pyplot as plt
        if size is None:
            size = settings.imshow_zoom_pixel_width
        (nrows, ncols) = self.data.shape[:2]
        fig_kwargs = {}
        if settings.imshow_zoom_figure_width is not None:
            width = settings.imshow_zoom_figure_width
            fig_kwargs['figsize'] = (width, width)
        # fig = plt.figure(**fig_kwargs)
        # fig = self.
        # self.imshow_data_kwargs
        # view = ImageView(source=self.source)
        # view.set_data(self.data, self.bands, **self.rgb_kwargs)
        # view.set_classes(self.classes, self.class_colors)
        # view.imshow_data_kwargs = self.imshow_data_kwargs.copy()
        kwargs = {'extent': (-0.5, ncols - 0.5, nrows - 0.5, -0.5)}
        self.imshow_data_kwargs.update(kwargs)
        # view.imshow_class_kwargs = self.imshow_class_kwargs.copy()
        # view.imshow_class_kwargs.update(kwargs)
        # view.callbacks_common = self.callbacks_common
        # view.spectrum_plot_fig_id = self.spectrum_plot_fig_id
        self.show(fignum=fignum, mode=self.display_mode)
        self.axes.set_xlim(0, size)
        self.axes.set_ylim(size, 0)
        self.interpolation = 'nearest'
        if center is not None:
            print('panning to', center[1], center[0])
            self.pan_to(*center)
            self.axes.add_patch(patches.Rectangle((center[1]-1, center[0]-1), 2, 2, linewidth=1, edgecolor='w', facecolor='none'))
            
            
            # self.axes.add_patch(patches.Rectangle((0, 0), 3, 3, linewidth=1, edgecolor='w', facecolor='none'))

        # return view

class MyMouseHandler(ImageViewMouseHandler):
    def __init__(self, view, broken, *args, **kwargs):
        super(MyMouseHandler, self).__init__(view)
        self.filteredBandList = []
        self.brokenaxes = broken
        print('Broken Axes is:', self.brokenaxes)
        if self.view.source.bands.centers:
            bandcount = len(self.view.source.bands.centers)
        elif self.view.source.nbands:
            bandcount = self.view.source.nbands
        else:
            bandcount = self.view.source.shape[2]
            
        for i in range(bandcount):
            if i not in range(57, 78):
                self.filteredBandList.append(i)
        
    def handle_event(self, event):
        '''Callback for click event in the image display.'''
        if self.show_events:
            print(event, ', key = %s' % event.key)
        if event.inaxes is not self.view.axes:
            return
        (r, c) = (int(event.ydata + 0.5), int(event.xdata + 0.5))
        (nrows, ncols) = self.view._image_shape
        if r < 0 or r >= nrows or c < 0 or c >= ncols:
            return
        kp = KeyParser(event.key)
        
        if event.button == 1:
            if event.dblclick and kp.key is None :
                print(kp.key)
                if self.view.source is not None:
                    from spectral import settings
                    import matplotlib.pyplot as plt
                    if self.view.spectrum_plot_fig_id is None:
                        print('self.view.spectrum_plot_fig_id is none')
                        f = plt.figure()
                        self.view.spectrum_plot_fig_id = f.number
                    try:
                        f = plt.figure(self.view.spectrum_plot_fig_id)
                    except:
                        f = plt.figure()
                        self.view.spectrum_plot_fig_id = f.number
                    f.clf()
                    if self.brokenaxes:
                        s = brokenaxes(xlims=((400, 915), (932, 2500)), hspace=.01, wspace=.04)
                        x = np.linspace(400, 2500, len(self.filteredBandList))
                        subimage = self.view.source.read_subimage([r], [c], self.filteredBandList)[0][0]
                        s.plot(x, subimage)
                        s.set_xlabel('Wavelength')
                    else:
                        s = f.gca()
                        settings.plotter.plot(self.view.source[r, c],
                                            self.view.source)
                        s.xaxis.axes.relim()
                        s.xaxis.axes.autoscale(True)
                        s.set_xlabel('Band')
                        subimage = self.view.source.read_pixel(r, c)
                    
                    
                    # s.set_ylabel('Reflectance')
                    try:
                        s.set_title(f'Pixel({r},{c}) Spectra')
                    except:
                        pass

                    
                    f.canvas.draw()
                    
                    #subclass code additions below
                    self.view.updateLastPixel(r, c)
                    self.lastpixel = {"row": r, "col": c}
                    print(self.lastpixel, '\n\n', subimage)
                    
class NavigationToolbar(NavigationToolbar2QT):
    # only display the buttons we need
    toolitems = [t for t in NavigationToolbar2QT.toolitems if
                 t[0] in ('Home', 'Back', 'Forward', 'Pan', 'Zoom', 'Save')]

class MaterialDialog(qtw.QWidget):
    def __init__(self, materials, parent = None):
        super(MaterialDialog, self).__init__(parent)
        self.materials = materials
        layout = qtw.QFormLayout()
        
        self.setLayout(layout)
        self.setWindowTitle("Assign to Material Profile")
        self.le = qtw.QLineEdit()
        self.btn = qtw.QPushButton("Choose from list")
        self.btn.clicked.connect(self.getItem)
        layout.addRow(self.btn, self.le)
        self.show()

    def getItem(self):
        items = tuple(self.materials)
		
        item, ok = qtw.QInputDialog.getItem(self, "Assign this pixel to a material profile", "Stored Profiles", items, 0, False)
        if ok and item:
          self.le.setText(item)
                


class qViewer(qtw.QWidget):
    """ A class for the Image Viewer GUI panel """

    readyForData = qtc.pyqtSignal()
    lastPixel_sig = qtc.pyqtSignal(str, int, int, str)
    nicknameChosen = qtc.pyqtSignal(str, str)
    requestFilepath = qtc.pyqtSignal(str)
    switchToLAN = qtc.pyqtSignal(str)

    def populateScans(self, scans):
        print('scans received:', scans)
        for scan in scans:
            self.downloadList.addItem(scan)

    def populateMaterials(self, materials):
        print('materials received:', materials)
        self.materials = materials

    def openExternalScan(self, filepath):
        """ Receives a filepath from the db and loads it in the viewer window.
        
            First it will try opening with spectral python.
            If that doesn't work, it will try opening explicitly as an aviris file.
            If that doesn't work, it will look for a similarly-named LAN file to open
            If that doesn't work, it will try to convert the GeoTiff into a LAN file to open
            If that doesn't work, it gives up and delivers an error 

        """
        
        try:
            img = s.open_image(filepath)
        except Exception as e:
            try:
                img = aviris.open(filepath)
            except:
                try:
                    dst_filename = filepath[:-3] + 'lan'

                    if os.path.exists(dst_filename):
                        img = s.open_image(dst_filename)
                    else:
                        img = gdal.Open(filepath)
                        print('Converting GeoTiff file to LAN for use with Spectral Python')
                        gdal.UseExceptions()
                        print('Please wait, this may take a few moments...')
                        gdal.Translate(dst_filename, img, format='LAN', outputType=gdal.GDT_Int16, options=['-scale'])

                        try:
                            img = s.open_image(dst_filename)
                            self.switchToLAN.emit(filepath) # <---- not wired up yet
                        except:
                            qtw.QMessageBox.critical(None, 'File Open Error', f'Could not load file: {filepath}\n{e}')
                            return
                
                except:
                    qtw.QMessageBox.critical(None, 'File Open Error', f'Could not load file: {filepath}\n{e}')
                    return

        desc = gdal.Info(filepath)
        desc = desc.split('Band 1 Block')[0]

        self.properties_text.setText(str(img).replace('\t', ''))
        self.properties_text.append(desc)

        self.view = MyImageView(img, (50, 27, 17), stretch=((.01, .99), (.01, .99), (.01, .98)), interpolation='none', source=img, brokenaxes=False)
        self.view.spectrum_plot_fig_id = 4
        
        self.view.show(mode='data', fignum=3)
        plt.tight_layout()
        print(self.view.lastPixel)
        
        self.v_imageCanvas.draw()
        self.v_spectraCanvas.draw()


    def openHyperionFromList(self, item):
        """ Processes and opens a Hyperion image in the viewer """
        self.v_fig.clf()
        
        # Raster image
        item = item.text().split(' ')[0]
        filename = item + '.L1R'
        filepath = os.path.join(DOWNLOAD_PATH, filename[:-4], filename)
        self.sourcename = filename

        if os.path.exists(filepath):
            # file is a normal hyperion file with .hdr header file
            h_filename = item + '.hdr'
            h_filepath = os.path.join(DOWNLOAD_PATH, filename[:-4], h_filename)

            img = envi.open(h_filepath, filepath)
            
        else:
            # file was imported and path has to be queried from db
            self.requestFilepath.emit(item)
            return
        
        desc = gdal.Info(filepath)
        desc = desc.split('Band 1 Block')[0]

        self.properties_text.setText(str(img).replace('\t', ''))
        self.properties_text.append(desc)
        self.view = MyImageView(img, (50, 27, 17), stretch=((.01, .99), (.01, .99), (.01, .98)), interpolation='none', source=img)
        self.view.spectrum_plot_fig_id = 4
        
        self.view.show(mode='data', fignum=3)
        plt.tight_layout()
        print(self.view.lastPixel)
        
        self.v_imageCanvas.draw()
        self.v_spectraCanvas.draw()

    def announcePixel(self):
        r = self.view.lastPixel["row"]
        c = self.view.lastPixel["col"]
        source = self.sourcename
        
        # pop up here
        # self.matPop = MaterialDialog(self.materials)
        items = tuple(self.materials)
		
        item, ok = qtw.QInputDialog.getItem(self, "Assign material", "Stored Profiles", items, 0, False)
        if ok:
            mat = item
            self.lastPixel_sig.emit(source, r, c, mat)

    def importFile(self):
        dlg = qtw.QFileDialog()
        dlg.setWindowTitle('Import a Hyperspectral Image')
        dlg.setFileMode(qtw.QFileDialog.ExistingFile)
        dlg.setNameFilter("Hyperspectral files (*.hdr *.L1R *.lan *.tif *.hd5);;All files (*.*)")
        filename = None
        
        if dlg.exec_() == qtw.QDialog.Accepted:
            filename = dlg.selectedFiles()

        if filename:

            filename = str(filename[0])
            print(filename)
            fileFormat = filename[-3:]
            parts = filename.split('/')
            i = len(parts) -1
            fileID = parts[i].replace(f'.{fileFormat}', '')
            print('\n')

            try:
                if fileFormat == 'lan':
                    
                    img = s.open_image(filename)
                    bandLimit = img.nbands
                    print('\n',img) 
       
                elif fileFormat == 'hdr':
                    print('Processing ENVI hdr file...')
                    print('Please wait...')
                    img = envi.open(filename)
                    print('\n', img)
                         
                elif fileFormat == 'img': 
                    print('Processing img file...')
                    print('Please wait...')
                    img = envi.open(filename.replace('.img', '.hdr'), filename)
                    bandLimit = img.nbands
                    print('\n',img) 
                        
                elif fileFormat == 'tif':
                    print('Processing TIF file...')
                    print('Please wait...')

                    try:
                        img = s.open_image(filename)
                        print('\n',img) 
                    except Exception as e:
                        print(f'Error with file: {filename}\n{e}\n')
                        img = gdal.Open(filename) 
                        bandLimit = img.RasterCount
                        
                        print('Rows:    ', img.RasterXSize)
                        print('Samples: ', img.RasterYSize)
                        print('Bands:   ', img.RasterCount)
                    
                    # if os.path.exists(filename[:-3] + 'lan'):
                    #     print('\nThis GeoTiff has already been converted to a LAN file. Skipping conversion...')
                    #     dst_filename = filename[:-3] + 'lan'
                    #     img = s.open_image(dst_filename)
                    # else:
                    #     print('Converting GeoTiff file to LAN for use with Spectral Python')
                    #     dst_filename = filename[:-3] + 'lan'
                    #     gdal.UseExceptions()
                    #     print('Please wait, this may take a few mins...')
                    #     gdal.Translate(dst_filename, img, format='LAN', outputType=gdal.GDT_Int16, options=['-scale'])
                    #     img = s.open_image(dst_filename)
                    
 
                else: #if not acceptable file type go here
                    print(fileFormat, 'is not an accepted filetype yet')
                    qtw.QMessageBox.critical(None, 'File Open Error', f'Could not load file: {fileFormat} is not an accepted filetype yet')
                    # img = envi.open(h_filepath, filepath)
                    # with open(filename, 'r') as fh:
                    #     print(fh.read())

            except Exception as e:
                print('ERROR:', e)
                qtw.QMessageBox.critical(None, 'File Open Error', f'Could not load file: {e}')

            else:
                nickname, ok = qtw.QInputDialog.getText(self, 'Enter a Nickname', 'Would you like to enter a nickname for this file for easier reference?:')
                if ok:
                    self.nicknameChosen.emit(filename, nickname)
                    self.downloadList.addItem(f'{fileID} ({nickname})')
                else:
                    self.nicknameChosen.emit(filename, 'None')
                    self.downloadList.addItem(f'{fileID}')


    def __init__(self, *args, **kwargs):
        super().__init__()
        # s.settings.imshow_figure_size = (2, 20)
        self.layout = qtw.QHBoxLayout()
        self.setLayout(self.layout)
        
        # Internal variables
        self.downloads = []
        self.readable_files = {}
        self.scansToAdd = []

        #Left Frame
        self.leftFrame = qtw.QVBoxLayout()
        self.dl_label = qtw.QLabel("<b>Downloads</b>")
        self.dl_label.setAlignment(qtc.Qt.AlignCenter)
        self.dl_label.setFont(qtg.QFont('Arial', 12))

        self.downloadList = qtw.QListWidget()
        self.downloadList.setFixedWidth(230)
        self.downloadList.setSizePolicy(qtw.QSizePolicy.Fixed, qtw.QSizePolicy.Expanding)
        self.downloadList.itemDoubleClicked.connect(self.openHyperionFromList)
        self.open_btn = qtw.QPushButton("Import GeoTiff", clicked=self.importFile)
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
                    # self.downloadList.addItem(name[:-4])
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
        # self.v_imageFrame.setStyleSheet("background-color:#ccc;")
        self.v_imageFrame.setLayout(qtw.QVBoxLayout())

        self.splitter = qtw.QSplitter()

        self.subLayout = qtw.QWidget()
        # self.subLayout.setStyleSheet("background-color:red;")
        self.subLayout.setLayout(qtw.QVBoxLayout())

        self.subLayout2 = qtw.QWidget()
        # self.subLayout2.setStyleSheet("background-color:blue;")
        self.subLayout2.setLayout(qtw.QVBoxLayout())
       
        self.v_fig = plt.figure(figsize=(1,5), dpi=80)
        self.s_fig = plt.figure(figsize=(6,5))

        print('v_fig number:', self.v_fig.number)
        print('s_fig number:', self.s_fig.number)

        self.v_imageCanvas = FigureCanvasQTAgg(self.v_fig)
        self.v_spectraCanvas = FigureCanvasQTAgg(self.s_fig)
        self.v_canvas_nav = NavigationToolbar(self.v_imageCanvas, self.v_midframe)

        self.ax1 = plt.Axes(self.v_fig, [0., 0., 1., 1.])
        self.v_fig.add_axes(self.ax1)
        self.ax1.set_axis_off()
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
        
        # self.clearPlot_btn = qtw.QPushButton("Clear Plot")
        # self.clearPlot_btn.clicked.connect(plt.cla)
        self.addPixel_btn = qtw.QPushButton("Add Pixel to Profile", clicked=self.announcePixel)
        self.addPixel_btn.setMaximumWidth(200)
        

        # self.pixelButtons.layout().addWidget(self.clearPlot_btn)
        self.pixelButtons.layout().addWidget(self.addPixel_btn)

        self.v_imageCanvas.draw()
        self.v_spectraCanvas.draw()

        

        
