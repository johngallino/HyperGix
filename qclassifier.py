from matplotlib.backends.backend_qt5 import NavigationToolbar2QT
import spectral as s
from spectral.graphics.spypylab import ImageView, KeyParser, ImageViewMouseHandler,  set_mpl_interactive, ParentViewPanCallback
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

class qClassifier(qtw.QWidget):
    ''' A class for the widget holding pixel classifer tools '''
    print('nothing here yet')
    