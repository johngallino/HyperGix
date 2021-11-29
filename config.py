import os

apiKey = ""
serviceUrl = "https://m2m.cr.usgs.gov/api/api/json/stable/"
headers = {}
TARGET_BANDS = [8, 13, 15, 25, 55, 77, 82, 85, 91, 93, 97, 102, 112, 115, 120, 137, 158, 183]


# if 'App' not in os.getcwd():
#     if os.path.isfile(os.path.join(os.getcwd(), 'App')):
#         os.chdir(os.path.join(os.getcwd(), 'App'))
# else:
HYPERION_SCANS_PATH = os.path.join(os.getcwd(), 'downloads')

import numpy as np

def spectral_angles(data, members):     # Copied from spectral python library
    '''Calculates spectral angles with respect to given set of spectra.

    Arguments:

        `data` (:class:`numpy.ndarray` or :class:`spectral.Image`):

            An `MxNxB` image for which spectral angles will be calculated.

        `members` (:class:`numpy.ndarray`):

            `CxB` array of spectral endmembers.

    Returns:

        `MxNxC` array of spectral angles.


    Calculates the spectral angles between each vector in data and each of the
    endmembers.  The output of this function (angles) can be used to classify
    the data by minimum spectral angle by calling argmin(angles).
    '''
    print (members.shape)
    print(data.shape)
    assert members.shape[1] == data.shape[2], \
        'Matrix dimensions are not aligned.'

    m = np.array(members, np.float64)
    m /= np.sqrt(np.einsum('ij,ij->i', m, m))[:, np.newaxis]
    
    norms = np.sqrt(np.einsum('ijk,ijk->ij', data, data))
    dots = np.einsum('ijk,mk->ijm', data, m)
    dots = np.clip(dots / norms[:, :, np.newaxis], -1, 1)
    return np.arccos(dots)