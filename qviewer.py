import os
from os.path import exists
import shutil

from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg)
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Qt5Agg')
import numpy as np
from osgeo import gdal
import spectral as s
from spectral.algorithms.algorithms import spectral_angles
from spectral.graphics.spypylab import ImageView, KeyParser, ImageViewMouseHandler
from spectral.io import aviris
from spectral.io import envi
from brokenaxes import brokenaxes
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc
from PyQt5.QtCore import QPoint, Qt

from config import HYPERION_SCANS_PATH as DOWNLOAD_PATH
from config import TARGET_BANDS, TARGET_WAVELENGTHS, HYP_WAVELENGTHS

import warnings
warnings.filterwarnings("ignore")

gdal.UseExceptions()

# if os.name == "nt":
#     matplotlib.rcParams.update({'font.size': 10})
if os.name =='posix':
    font = {'family' : 'Arial',
        'size'   : 8}

matplotlib.rc('font', **font)


class MyImageView(ImageView):
    ''' Subclass of SPy's ImageView customized for HyperGix'''
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
        
        kwargs = {'extent': (-0.5, ncols - 0.5, nrows - 0.5, -0.5)}
        self.imshow_data_kwargs.update(kwargs)
        self.show(fignum=fignum, mode=self.display_mode)
        self.axes.set_xlim(0, size)
        self.axes.set_ylim(size, 0)
        self.interpolation = 'nearest'
        if center is not None:
            self.pan_to(*center)
            self.axes.add_patch(patches.Rectangle((center[1]-1, center[0]-1), 2, 2, linewidth=1, edgecolor='w', facecolor='none'))
            
class MyMouseHandler(ImageViewMouseHandler):
    def __init__(self, view, broken, *args, **kwargs):
        super(MyMouseHandler, self).__init__(view)
        self.filteredBandList = []
        self.brokenaxes = broken
        if self.view.source.bands.centers:
            self.bandcount = len(self.view.source.bands.centers)
        elif self.view.source.nbands:
            self.bandcount = self.view.source.nbands
        else:
            self.bandcount = self.view.source.shape[2]
            
        for i in range(self.bandcount):
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
                        s = brokenaxes(xlims=((400, 915), (922, 2500)), hspace=.01, wspace=.04)
                        x = HYP_WAVELENGTHS
                        subimage = self.view.source.read_subimage([r], [c], self.filteredBandList)[0][0]
                        targetbands = self.view.source.read_subimage([r], [c], TARGET_BANDS)[0][0]
                        s.plot(x, subimage)
                        s.set_xlabel('Wavelength')
                        s.set_ylabel('Reflectance')

                        # RGB Legend Overlay

                        s.plot([620, 720],[-300, -300], '-r', linewidth=4, markersize=12)
                        s.plot([495, 570],[-300, -300], '-g', linewidth=4, markersize=12)
                        s.plot([450, 495],[-300, -300], '-b', linewidth=4, markersize=12)
                        s.plot([760, 1400],[-300, -300], '-k', alpha=.3, linewidth=4, markersize=12)

                        # Target Band overlay
                        s.plot(TARGET_WAVELENGTHS, targetbands, '.m', markersize = 8)
                        
                        
                    else:
                        s = f.gca()
                        settings.plotter.plot(self.view.source[r, c],
                                            self.view.source)
                        s.xaxis.axes.relim()
                        s.xaxis.axes.autoscale(True)
                        s.set_xlabel('Band')
                        s.set_ylabel('Reflectance')
                        subimage = self.view.source.read_pixel(r, c)
                    
                    
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

class qViewer(qtw.QWidget):
    """ A class for the Image Viewer GUI panel """

    readyForData = qtc.pyqtSignal()
    lastPixel_sig = qtc.pyqtSignal(str, int, int, str)
    nicknameChosen = qtc.pyqtSignal(str, str)
    requestFilepath = qtc.pyqtSignal(str, str)
    switchToLAN = qtc.pyqtSignal(str)
    switchFinished = qtc.pyqtSignal()
    signal_delete = qtc.pyqtSignal(str)
    statusMessage = qtc.pyqtSignal(str, int)
    request_coords = qtc.pyqtSignal(str)
    means = np.zeros((6,66))

    def deleteScan(self):
        item = self.downloadList.currentItem()
        item = item.text().split(' ')[0]
        # print('current item is', item)
        self.signal_delete.emit(item)

    def remove_scan_from_list(self, name):
        items_list = self.downloadList.findItems(name, qtc.Qt.MatchStartsWith)
        for item in items_list:
            r = self.downloadList.row(item)
            self.downloadList.takeItem(r)

    def populateScans(self, scans):
        # print('scans received:', scans)
        for scan in scans:
            self.downloadList.addItem(scan)
        self.openFromDownloadList(None)

    def populateMaterials(self, materials):
        # print('materials received:', materials)
        self.materials = materials

    def openExternalScan(self, filepath, mode='RGB'):
        """ Receives a filepath from the db and loads it in the viewer window.
        
            First it will try opening with spectral python.
            If that doesn't work, it will try opening explicitly as an aviris file.
            If that doesn't work, it will look for a similarly-named LAN file to open
            If that doesn't work, it will try to convert the GeoTiff into a LAN file to open
            If that doesn't work, it gives up and delivers an error 

        """
        
        try:
            self.img = s.open_image(filepath)
        except Exception as e:
            try:
                self.img = aviris.open(filepath)
            except:
                try:
                    dst_filename = filepath[:-3] + 'lan'

                    if os.path.exists(dst_filename):
                        self.img = s.open_image(dst_filename)
                    else:
                        self.img = gdal.Open(filepath)
                        print('Converting GeoTiff file to LAN for use with Spectral Python')
                        gdal.UseExceptions()
                        print('Please wait, this may take a few moments...')
                        gdal.Translate(dst_filename, self.img, format='LAN', outputType=gdal.GDT_Int16, options=['-scale'])

                        try:
                            self.switchToLAN.emit(filepath)
                            self.img = s.open_image(dst_filename)
                            self.switchFinished.emit()
                        except:
                            qtw.QMessageBox.critical(None, 'File Open Error', f'{e}')
                            return
                
                except:
                    qtw.QMessageBox.critical(None, 'File Open Error', f'{e}')
                    return

        desc = gdal.Info(filepath)
        desc = desc.split('Band 1 Block')[0]

        self.properties_text.setText(str(self.img).replace('\t', ''))
        self.properties_text.append(desc)
        self.properties_text.scrollToAnchor('Data Source')
        # would be nice to figure out how to scroll to the top automatically here

        self.coords_label.hide()

        self.view.spectrum_plot_fig_id = 4
        
        if mode == 'RGB':
            
            self.view = MyImageView(self.img, (32, 21, 13), stretch=((.01, .99), (.01, .99), (.01, .98)), source=self.img, brokenaxes=False)
            self.view.spectrum_plot_fig_id = 4
            self.view.show(mode='data', fignum=3)
            self.r_entry.setText('32')
            self.g_entry.setText('21')
            self.b_entry.setText('13')

        elif mode == 'single':
            self.view = MyImageView(self.img, (50, 50, 50), stretch=((.01, .99), (.01, .99), (.01, .98)), source=self.img, brokenaxes=False)
            self.view.spectrum_plot_fig_id = 4
            self.view.show(mode='data', fignum=3)
            if self.bandSlider.maximum() < self.view.cb_mouse.bandcount:
                self.bandSlider.setMaximum(self.view.cb_mouse.bandcount)
                self.bandValidator.setTop(self.view.cb_mouse.bandcount)
                self.bandSlider.setTickInterval(10)

        elif mode == 'NDVI':
            vi = s.ndvi(self.img, 30, 85)
            colors = ["black", "grey", "red", "yellow", "lawngreen"]
            cmap1 = matplotlib.colors.LinearSegmentedColormap.from_list("mycmap", colors)      
            self.view = MyImageView(vi, stretch=((.03, .98)), source=self.img, cmap=cmap1)      
            self.view.spectrum_plot_fig_id = 4
            self.view.show(mode='data', fignum=3)


        plt.tight_layout()
                
        self.v_imageCanvas.draw()
        self.v_spectraCanvas.draw()

    def openFromDownloadList(self, item):
        
        if item is None:
            try:
                item = self.downloadList.item(0)
                self.openHyperionFromList(item, mode='RGB')
            except:
                return

        if self.b1.isChecked():
            mode = 'RGB'
            self.viewRGBlayout.show()
            self.viewSingleBandlayout.hide()
            self.viewNDVIlayout.hide()
            self.openHyperionFromList(item, mode)

        elif self.b2.isChecked():
            mode = 'single'
            self.viewRGBlayout.hide()
            self.viewNDVIlayout.hide()
            self.viewSingleBandlayout.show()
            
            self.openHyperionFromList(item, mode)
            self.bandValidator.setTop(self.view.cb_mouse.bandcount)
            self.bandSlider.setMaximum(self.view.cb_mouse.bandcount)
            
        
        elif self.b3.isChecked():
            mode = 'NDVI'
            self.viewRGBlayout.hide()
            self.viewSingleBandlayout.hide()
            self.viewNDVIlayout.show()
            self.openHyperionFromList(item, mode)

    def openHyperionFromList(self, item, mode='RGB'):
        """ Processes and opens a Hyperion image in the viewer """
        self.v_fig.clf()
        r = int(self.r_entry.text())
        g = int(self.g_entry.text())
        b = int(self.b_entry.text())
        sb = self.bandSlider.value()
        # Raster image
        self.item = item.text().split(' ')[0]
        filename = self.item + '.L1R'
        filepath = os.path.join(DOWNLOAD_PATH, filename[:-4], filename)
        self.sourcename = filename

        if os.path.exists(filepath):
            # file is a normal hyperion file with .hdr header file
            h_filename = self.item + '.hdr'
            h_filepath = os.path.join(DOWNLOAD_PATH, filename[:-4], h_filename)

            self.img = envi.open(h_filepath, filepath)
            
        else:
            # file was imported and path has to be queried from db
            self.requestFilepath.emit(self.item, mode)
            return
        
        desc = gdal.Info(filepath)
        desc = desc.split('Band 1 Block')[0]

        self.properties_text.setText(str(self.img).replace('\t', ''))
        self.properties_text.append(desc)
        bar = self.properties_text.verticalScrollBar()
        bar.setValue(0)

        self.request_coords.emit(filename[:-4])

        if mode == 'RGB':
            
            self.view = MyImageView(self.img, (r, g, b), stretch=((.01, .99), (.01, .99), (.01, .98)), source=self.img)
            self.view.spectrum_plot_fig_id = 4
            self.view.show(mode='data', fignum=3)
            self.r_entry.setText(str(r))
            self.g_entry.setText(str(g))
            self.b_entry.setText(str(b))

        elif mode == 'single':
            sb = self.bandSlider.value()
            self.view = MyImageView(self.img, bands=tuple([sb]), stretch=((.01, .98)), source=self.img)
            self.view.spectrum_plot_fig_id = 4
            self.view.show(mode='data', fignum=3)
            if self.bandSlider.maximum() < self.view.cb_mouse.bandcount:
                self.bandSlider.setMaximum(self.view.cb_mouse.bandcount)
                self.bandValidator.setTop(self.view.cb_mouse.bandcount)
                self.bandSlider.setTickInterval(10)

        elif mode == 'NDVI':
            vi = s.ndvi(self.img, 30, 85)
            colors = ["black", "grey", "red", "yellowgreen", "lawngreen"]
            cmap1 = matplotlib.colors.LinearSegmentedColormap.from_list("mycmap", colors)      
            self.view = MyImageView(vi, stretch=((.05, .95)), source=self.img, cmap=cmap1)      
            self.view.spectrum_plot_fig_id = 4
            self.view.show(mode='data', fignum=3)


        plt.tight_layout()
        # print(self.view.lastPixel)
        
        self.v_imageCanvas.draw()
        self.v_spectraCanvas.draw()


    def setMeans(self, means):
        means = np.array(means)
        self.means = means
        # print('Means updated')

    def changeSingleBand(self, sb): # receiving sb as int
        value = str(sb)
        self.bandLabel.setText(value)
        # print('mode is', self.mode)
        if self.view:
            try:
                if self.mode == 'Normal':
                    self.view = s.imshow(self.img, bands=tuple([sb-1]), stretch=((.01, .98)), fignum=3)
                if self.mode == 'PCA':
                    self.view = s.imshow(self.img_pc, bands=tuple([sb-1]), stretch=((.01, .98)), fignum=3)
            except Exception as e:
                print('changeBand error', e)
        

    def changeRGBBand(self, r, g, b): #receiving r g b as strings
        print('r:', r, 'g:', g, 'b', b)
        rgb_int = [int(r), int(g), int(b)]
        self.r_entry.setText(r)
        self.g_entry.setText(g)
        self.b_entry.setText(b)
        if self.view:
            try:
                self.view.set_data(self.img, bands=(rgb_int[0], rgb_int[1], rgb_int[2]), stretch=((.01, .99), (.01, .99), (.01, .98)), source=self.img)
            except Exception as e:
                print(e)

    def announcePixel(self):
        r = self.view.lastPixel["row"]
        c = self.view.lastPixel["col"]
        source = self.sourcename
        
        # pop up here
        items = tuple(self.materials)
		
        item, ok = qtw.QInputDialog.getItem(self, "Assign material", "Stored Profiles", items, 0, False)
        if ok:
            mat = item
            self.lastPixel_sig.emit(source, r, c, mat)

    def importFile(self):
        dlg = qtw.QFileDialog()
        dlg.setWindowTitle('Import a Hyperspectral Image')
        dlg.setFileMode(qtw.QFileDialog.ExistingFile)
        dlg.setNameFilter("Hyperspectral files (*.hdr *.L1R *.lan *.tif *.hd5 *.he5);;All files (*.*)")
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
                    
                    if os.path.exists(filename[:-3] + 'lan'):
                        print('\nThis GeoTiff has already been converted to a LAN file. Skipping conversion...')
                        dst_filename = filename[:-3] + 'lan'
                        img = s.open_image(dst_filename)
                    else:
                        print('Converting GeoTiff file to LAN for use with Spectral Python')
                        dst_filename = filename[:-3] + 'lan'
                        gdal.UseExceptions()
                        print('Please wait, this may take a few mins...')
                        gdal.Translate(dst_filename, img, format='LAN', outputType=gdal.GDT_Int16, options=['-scale'])
                        img = s.open_image(dst_filename)
                    
 
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

    def calculate_pca(self):
        import time
        tick = time.perf_counter()
        self.statusMessage.emit('Calculating PCA. Please wait...', 60000)
        self.mode = 'PCA'
        print('\n\nCALCULATING PCA\n=====================\n ', self.img.filename)
        tic = time.perf_counter()
        self.pc = s.principal_components(self.img)
        toc = time.perf_counter()
        self.s_fig.clear()
        matrix = s.imshow(self.pc.cov, fignum=4)
        print(f'Calculating the principal components took {toc-tic:04f} seconds')
        self.s_fig.suptitle('Covariance Matrix', fontsize=10) # doesnt work?

        # print('Calculating number of eigenvalues to retain 99% of image variance...\n')
        tic = time.perf_counter()
        self.pc_99 = self.pc.reduce(fraction=0.99)
        eigens = self.pc_99.eigenvalues.size
        toc = time.perf_counter()
        print(f'Calculating the # of eigenvalues to reach 99% ({eigens}) took {toc-tic:04f} seconds')

        self.img_orig = self.img
        tic = time.perf_counter()
        self.img_pc = self.pc_99.transform(self.img)
        toc = time.perf_counter()
        print(f'Transforming image took {toc-tic:04f} seconds')
        # print('shape of img_pc is', self.img_pc.shape)

        self.b2.setChecked(True)
        tic = time.perf_counter()
        self.bandSlider.setMaximum(eigens)
        self.bandSlider.setValue(1)
        self.bandSlider.setTickInterval(1)
        self.bandSlider.setSingleStep(1)
        self.bandValidator.setTop(eigens)
        toc = time.perf_counter()
        print(f'Updating UI took {toc-tic:04f} seconds')
        

        tic = time.perf_counter()
        self.view.set_data(self.img_pc[:, :, :eigens], bands=(0, 0, 0), stretch=((.01, .98), (.01, .98), (.01, .98)))
        toc = time.perf_counter()
        print(f'Rendering PCA view took {toc-tic:04f} seconds')
        
        print(f'\nWhole PCA process took {toc - tick:04f} seconds')
        self.statusMessage.emit(f'PCA calculated - took {toc - tick:04f} seconds', 10000)
        
        # UNCOMMENT BELOW TO SAVE PCA OUTPUT AUTOMATICALLY (WILL LOCK UP THE PROGRAM WHILE SAVING)
        # try:
        #     tic = time.perf_counter()
        #     for i in range(0, eigens):
        #         s.save_rgb(f'{self.img_orig.filename[:-4]}-PCA_{i+1}.jpg', self.img_pc, bands=tuple([i]), stretch=((.01, .98)))
        #     tic = time.perf_counter()
        #     print(f'Saving PCA finished - {toc-tic:04f} seconds')
        #     print(f'Whole PCA process took {toc - tick:04f} seconds')
        #     self.statusMessage.emit('PCA calculated and saved to scan folder.', 5000)
        # except Exception as e:
        #     print('saving error - ', e)

        

    def calculate_spectral_angles(self):
        from config import TARGET_BANDS as tg
        import time
        tick = time.perf_counter()
        self.statusMessage.emit('Calculating Spectral Angles. Please wait...', None)
        np.set_printoptions(threshold=np.inf)
        imgCube = self.img.read_bands(tg)
        imgCube = imgCube.astype('float64')
        angles = spectral_angles(imgCube, self.means)
        clmap = np.argmin(angles, 2)
        
        # with open(f"{self.img.filename[:-4]} - Spectral Classes.txt", "w") as external_file:
        #     print(imgCube, file=external_file)
        #     external_file.close()

        self.s_fig.clear()
        v = s.imshow(classes=(clmap + 1), interpolation='nearest', source=self.img, colors=s.spy_colors, fignum=3)
        tock = time.perf_counter()
        v.spectrum_plot_fig_id = 4
        s.save_rgb(f'{self.img.filename[:-4]}-gt.jpg', clmap+1, colors=s.spy_colors)
        self.statusMessage.emit(f'Spectral angle classification and pixel classification complete! - took {tock-tick:04f} seconds', 5000)
        
    def back_to_normal(self):
        self.mode = 'Normal'

    def update_coords(self, coords):
        self.coords_label.setText(coords)
        self.coords_label.show()
            
    def __init__(self, *args, **kwargs):
        super().__init__()
        # s.settings.imshow_figure_size = (2, 20)
        self.layout = qtw.QHBoxLayout()
        self.setLayout(self.layout)
        
        # Internal variables
        self.downloads = []
        self.readable_files = {}
        self.scansToAdd = []
        self.mode = 'Normal'

        #Left Frame
        self.leftFrame = qtw.QVBoxLayout()
        self.dl_label = qtw.QLabel("<b>Scan Library</b>")
        self.dl_label.setAlignment(qtc.Qt.AlignCenter)
        self.dl_label.setFont(qtg.QFont('Arial', 12))

        self.downloadList = qtw.QListWidget()
        self.downloadList.setFixedWidth(230)
        self.downloadList.setSizePolicy(qtw.QSizePolicy.Fixed, qtw.QSizePolicy.Expanding)
        self.downloadList.itemDoubleClicked.connect(self.openFromDownloadList)
        self.downloadList.itemDoubleClicked.connect(self.back_to_normal)

        self.open_btn = qtw.QPushButton("Import Spectral Scan", clicked=self.importFile)
        self.del_btn = qtw.QPushButton('Remove From Library', clicked=self.deleteScan)
        
        self.properties_label = qtw.QLabel("File Properties")
        self.properties_text = qtw.QTextEdit()
        self.properties_text.setReadOnly(True)
        self.properties_text.setTextInteractionFlags(qtc.Qt.TextSelectableByMouse)
        self.properties_text.setFixedWidth(230)
        self.properties_text.setFixedHeight(150)
        
        self.leftFrame.addWidget(self.dl_label)
        self.leftFrame.addWidget(self.downloadList)
        self.leftFrame.addWidget(self.open_btn)
        self.leftFrame.addWidget(self.del_btn)
        self.leftFrame.addWidget(self.properties_label)
        self.leftFrame.addWidget(self.properties_text)

        self.layout.addLayout(self.leftFrame)

        if os.path.join(os.getcwd(), 'downloads'):
            # print('downloads folder found')
            pass
        else:
            print(os.path.join(os.getcwd(), 'downloads'))
            print(DOWNLOAD_PATH)
            os.mkdir(DOWNLOAD_PATH)

        # Populating scans list and correcting Hyperion header offset error
        for root, dirs, files in os.walk(DOWNLOAD_PATH, topdown=False):
            for name in files:
                if name[-3:] == 'L1R':

                    self.readable_files[name[:-4]] = os.path.join(root, name)
                    filename = name[:-4]

                    old_header = os.path.join(DOWNLOAD_PATH, filename, f'{filename}.bak')
                    header = os.path.join(DOWNLOAD_PATH, filename, f'{filename}.hdr')

                    if not exists(old_header):
                        # Making a new copy of header with corrected offset of 2502
                        print(f'Corrected header not found for {name}. Creating it now...')
                        try:
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
                        except:
                            print('Could not create corrected header file. Maybe .hdr file is missing?')
                            pass

        # Mid frame
        self.v_midframe = qtw.QWidget()
        self.v_midframe.setLayout(qtw.QVBoxLayout())

        self.v_imageFrame = qtw.QWidget()
        # self.v_imageFrame.setStyleSheet("background-color:#ccc;")
        self.v_imageFrame.setLayout(qtw.QVBoxLayout())

        self.splitter = qtw.QSplitter()

        self.subLayout = qtw.QWidget()
        # self.subLayout.setStyleSheet("background-color:#ccc;")
        self.subLayout.setLayout(qtw.QVBoxLayout())
        self.subLayout.setMinimumWidth(350)
        self.subLayout.setSizePolicy(qtw.QSizePolicy.Preferred, qtw.QSizePolicy.Expanding)
        self.subLayout.layout().setContentsMargins(0,0,0,0)
        
        self.imageHolder = qtw.QWidget()

        self.subLayout2 = qtw.QWidget()
        # self.subLayout2.setStyleSheet("background-color:blue;")
        self.subLayout2.setLayout(qtw.QVBoxLayout())

        #Coords label
        self.coords_label = qtw.QLabel('')
        self.coords_label.setAlignment(qtc.Qt.AlignCenter)
        self.coords_label.setTextInteractionFlags(qtc.Qt.TextSelectableByMouse)

        # View Mode
        self.VMBox = qtw.QWidget()
        VMlayout = qtw.QHBoxLayout()
        self.VMBox.setLayout(VMlayout)
        self.b1 = qtw.QRadioButton('RGB')
        self.b1.setChecked(True)
        self.b1.toggled.connect(lambda:self.openFromDownloadList(self.downloadList.currentItem()))
        VMlayout.addWidget(self.b1)

        self.b2 = qtw.QRadioButton('Single Band')
        self.b2.toggled.connect(lambda:self.openFromDownloadList(self.downloadList.currentItem()))
        VMlayout.addWidget(self.b2)

        self.b3 = qtw.QRadioButton('NDVI')
        self.b3.toggled.connect(lambda:self.openFromDownloadList(self.downloadList.currentItem()))
        VMlayout.addWidget(self.b3)
        VMlayout.addStretch()

        # RGB Controls
        self.viewRGBlayout = qtw.QWidget()
        self.viewRGBlayout.setLayout(qtw.QHBoxLayout())
        self.viewRGBlayout.layout().addWidget(qtw.QLabel('R:'))
        self.r_entry = qtw.QLineEdit()
        self.r_entry.setText('32')
        self.r_entry.setFixedWidth(30)
        self.viewRGBlayout.layout().addWidget(self.r_entry)
        self.viewRGBlayout.layout().addWidget(qtw.QLabel('G:'))
        self.g_entry = qtw.QLineEdit()
        self.g_entry.setText('21')
        self.g_entry.setFixedWidth(30)
        self.viewRGBlayout.layout().addWidget(self.g_entry)
        self.viewRGBlayout.layout().addWidget(qtw.QLabel('B:'))
        self.b_entry = qtw.QLineEdit()
        self.b_entry.setText('13')
        self.b_entry.setFixedWidth(30)
        self.viewRGBlayout.layout().addWidget(self.b_entry)
        self.viewRGBlayout.layout().addStretch()
        self.r_entry.editingFinished.connect(lambda: self.changeRGBBand(self.r_entry.text(), self.g_entry.text(), self.b_entry.text()))
        self.g_entry.editingFinished.connect(lambda: self.changeRGBBand(self.r_entry.text(), self.g_entry.text(), self.b_entry.text()))
        self.b_entry.editingFinished.connect(lambda: self.changeRGBBand(self.r_entry.text(), self.g_entry.text(), self.b_entry.text()))

        # Single Band Controls
        self.viewSingleBandlayout = qtw.QWidget()
        self.viewSingleBandlayout.setLayout(qtw.QHBoxLayout())
        self.bandSlider = qtw.QSlider(qtc.Qt.Horizontal)
        self.bandSlider.setMinimum(1)
        self.bandSlider.setMaximum(225)
        self.bandSlider.setSingleStep(1)
        self.bandSlider.setValue(50)
        self.bandSlider.setTickInterval(10)
        self.bandSlider.setTickPosition(qtw.QSlider.TicksBelow)
        self.bandSlider.setMinimumWidth(200)
        self.bandLabel = qtw.QLineEdit(str(self.bandSlider.value()))
        self.bandLabel.setFixedWidth(30)
        self.bandLabel.setMaxLength(3)
        self.bandValidator = qtg.QIntValidator(1, 225)
        self.bandLabel.setValidator(self.bandValidator)
        self.viewSingleBandlayout.layout().addWidget(self.bandLabel)
        self.viewSingleBandlayout.layout().addWidget(self.bandSlider)
        self.viewSingleBandlayout.layout().addStretch()

        def labelChange(v):
            v = str(v)
            self.bandLabel.setText(v)

        self.bandSlider.setTracking(False)
        self.bandSlider.valueChanged.connect(labelChange)
        self.bandSlider.valueChanged.connect(lambda: self.changeSingleBand(self.bandSlider.value()))
        # self.bandSlider.sliderReleased.connect(lambda: self.changeSingleBand(self.bandSlider.value()))
        self.bandLabel.editingFinished.connect(lambda: self.bandSlider.setValue(int(self.bandLabel.text())))

        # NDVI Color Scale
        self.viewNDVIlayout = qtw.QWidget()
        self.viewNDVIlayout.setLayout(qtw.QVBoxLayout())
        self.viewNDVIlayout.layout().setContentsMargins(0,0,0,0)

        n_fig, ax = plt.subplots(figsize=(2, .5), num=10)
        # self.viewNDVIlayout.setStyleSheet("background-color:red;")
        n_fig.subplots_adjust(bottom=.8)
        # print('n_fig number:', n_fig.number)

        cmap = (matplotlib.colors.ListedColormap(["black", "grey", "red", "yellow", "lawngreen"]))
        bounds = [-1, 0, .25, .5, 1]
        norm = matplotlib.colors.BoundaryNorm(bounds, cmap.N)
        n_fig.colorbar(
            matplotlib.cm.ScalarMappable(cmap=cmap, norm=norm),
            cax=ax,
            boundaries=bounds, 
            ticks=bounds,
            spacing='uniform',
            orientation='horizontal',
            label='NDVI Scale',
        )
        
        self.NDVICanvas = FigureCanvasQTAgg(n_fig) #Creation of the display canvas
        self.NDVICanvas.draw()
        self.viewNDVIlayout.layout().addWidget(self.NDVICanvas)
       
        self.v_fig = plt.figure(figsize=(1,5), dpi=80, num=3)
        self.s_fig = plt.figure(figsize=(6,5), num=4)

        # print('v_fig number:', self.v_fig.number)
        # print('s_fig number:', self.s_fig.number)

        self.v_imageCanvas = FigureCanvasQTAgg(self.v_fig)
        self.imageHolder.setLayout(qtw.QVBoxLayout())
        self.imageHolder.layout().addWidget(self.v_imageCanvas)
        self.imageHolder.setSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Expanding)
        self.v_spectraCanvas = FigureCanvasQTAgg(self.s_fig)
        self.v_canvas_nav = NavigationToolbar(self.v_imageCanvas, self.v_midframe)

        self.ax1 = plt.Axes(self.v_fig, [0., 0., 1., 1.])
        self.v_fig.add_axes(self.ax1)
        self.ax1.set_axis_off()
        self.s_fig.suptitle('Pixel Spectra')
        # self.ax2 = plt.Axes(self.s_fig, [400, 2500, 0, 5000])
        # self.s_fig.add_axes(self.ax2)
        sax = self.s_fig.gca()
        sax.text(.2, .5, 'Double click on the image for pixel spectra')

        self.pixelButtons = qtw.QWidget()
        self.pixelButtons.setLayout(qtw.QHBoxLayout())

        self.v_midframe.layout().addWidget(self.v_imageFrame)
        self.v_imageFrame.layout().addWidget(self.splitter)

        self.layout.addWidget(self.v_midframe)
        self.subLayout.layout().addWidget(self.v_canvas_nav)
        self.subLayout.layout().addWidget(self.imageHolder)
        self.subLayout.layout().addWidget(self.coords_label)
        self.subLayout.layout().addWidget(self.VMBox)
        self.subLayout.layout().addWidget(self.viewNDVIlayout)
        self.subLayout.layout().addWidget(self.viewRGBlayout)
        self.subLayout.layout().addWidget(self.viewSingleBandlayout)
        self.viewSingleBandlayout.hide()
        self.viewNDVIlayout.hide()
        self.subLayout2.layout().addWidget(self.v_spectraCanvas)
        self.subLayout2.layout().addWidget(self.pixelButtons)
        self.splitter.addWidget(self.subLayout)
        self.splitter.addWidget(self.subLayout2)
        
        # self.clearPlot_btn = qtw.QPushButton("Clear Plot")
        # self.clearPlot_btn.clicked.connect(plt.cla)
        self.addPixel_btn = qtw.QPushButton("Add Pixel to Profile", clicked=self.announcePixel)
        self.addPixel_btn.setMaximumWidth(200)

        self.PCA_btn = qtw.QPushButton("Calculate PCA", clicked = self.calculate_pca)
        self.PCA_btn.setMaximumWidth(200)

        self.specAngle_btn = qtw.QPushButton("Calculate Classes", clicked = self.calculate_spectral_angles)
        self.specAngle_btn.setMaximumWidth(200)
        
        # self.pixelButtons.layout().addWidget(self.clearPlot_btn)
        self.pixelButtons.layout().addWidget(self.addPixel_btn)
        self.pixelButtons.layout().addWidget(self.PCA_btn)
        self.pixelButtons.layout().addWidget(self.specAngle_btn)

        self.v_imageCanvas.draw()
        self.v_spectraCanvas.draw()

        

        

        
