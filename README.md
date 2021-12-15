# HyperGix
A hyperspectral imagery organization and analysis tool built in Python and PyQt

HyperGix is an open-source, user-friendly desktop application to experiment with and learn about hyperspectral imagery. It is written in Python 3 and uses the PyQt5 GUI framework for its interface. The backend of HyperGix is a SQLite database included with the application that stores data about the user’s hyperspectral files, as well as spectral information to be discussed in detail later in this report. The software is still in alpha and has not yet gone through thorough bug testing.

	HyperGix aims to be intuitive and easy to use, with little instruction necessary. Presently it consists of three modules: Image Viewer, Spectra Manager, and USGS Search.  Using HyperGix, the user can organize and view hyperspectral files downloaded to their system, in either RGB (red, green, blue), single-band or Normalized Difference Vegetation Index (NDVI) views. The user may also perform Principal Component Analysis (PCA) on an image, define custom material classes and assign individual pixels from hyperspectral images to those classes to create a training set for classification tasks.
	
	If the user does not have access to hyperspectral files, or is inexperienced in where to find them, the USGS Search interface allows them to simply search for a geolocation and browse available hyperspectral scans to download from the United States Geological Society’s database of Hyperion satellite scans captured from the years 2000 to 2017. However, the USGS interface is cumbersome and difficult to navigate. By using HyperGix, and its user-friendly Google Maps-based interface, the data access is significantly improved.

Requires GDAL to be installed - gdal.org
