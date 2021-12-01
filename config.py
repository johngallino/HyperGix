import os

apiKey = ""
serviceUrl = "https://m2m.cr.usgs.gov/api/api/json/stable/"
headers = {}
TARGET_BANDS = [13, 18, 33, 43, 50, 82, 91, 98, 102, 112, 115, 129, 137, 158, 183]

TARGET_WAVELENGTHS = [477.69, 528.57, 681.2, 782.95, 854.18, 962.91, 1053.69, 1124.28, 1164.68, 1265.56, 1295.86, 1437.04, 1517.83, 1729.7, 1981.86]

HYP_WAVELENGTHS = [355.59,  365.76,  375.94,  386.11,  396.29,  406.46,  416.64,  426.82,
436.99,  447.17,  457.34,  467.52,  477.69,  487.87,  498.04,  508.22,
518.39,  528.57,  538.74,  548.92,  559.09,  569.27,  579.45,  589.62,
599.80,  609.97,  620.15,  630.32,  640.50,  650.67,  660.85,  671.02,
681.20,  691.37,  701.55,  711.72,  721.90,  732.07,  742.25,  752.43,
762.60,  772.78,  782.95,  793.13,  803.30,  813.48,  823.65,  833.83,
844.00,  854.18,  864.35,  874.53,  884.70,  894.88,  905.05,  915.23,
925.41, #SENSOR GAP
932.64,  942.73,
952.82,  962.91,  972.99,  983.08,  993.17, 1003.30, 1013.30, 1023.40,
1033.49, 1043.59, 1053.69, 1063.79, 1073.89, 1083.99, 1094.09, 1104.19,
1114.19, 1124.28, 1134.38, 1144.48, 1154.58, 1164.68, 1174.77, 1184.87,
1194.97, 1205.07, 1215.17, 1225.17, 1235.27, 1245.36, 1255.46, 1265.56,
1275.66, 1285.76, 1295.86, 1305.96, 1316.05, 1326.05, 1336.15, 1346.25,
1356.35, 1366.45, 1376.55, 1386.65, 1396.74, 1406.84, 1416.94, 1426.94,
1437.04, 1447.14, 1457.23, 1467.33, 1477.43, 1487.53, 1497.63, 1507.73,
1517.83, 1527.92, 1537.92, 1548.02, 1558.12, 1568.22, 1578.32, 1588.42,
1598.51, 1608.61, 1618.71, 1628.81, 1638.81, 1648.90, 1659.00, 1669.10,
1679.20, 1689.30, 1699.40, 1709.50, 1719.60, 1729.70, 1739.70, 1749.79,
1759.89, 1769.99, 1780.09, 1790.19, 1800.29, 1810.38, 1820.48, 1830.58,
1840.58, 1850.68, 1860.78, 1870.87, 1880.98, 1891.07, 1901.17, 1911.27,
1921.37, 1931.47, 1941.57, 1951.57, 1961.66, 1971.76, 1981.86, 1991.96,
2002.06, 2012.15, 2022.25, 2032.35, 2042.45, 2052.45, 2062.55, 2072.65,
2082.75, 2092.84, 2102.94, 2113.04, 2123.14, 2133.24, 2143.34, 2153.34,
2163.43, 2173.53, 2183.63, 2193.73, 2203.83, 2213.93, 2224.03, 2234.12,
2244.22, 2254.22, 2264.32, 2274.42, 2284.52, 2294.61, 2304.71, 2314.81,
2324.91, 2335.01, 2345.11, 2355.21, 2365.20, 2375.30, 2385.40, 2395.50,
2405.60, 2415.70, 2425.80, 2435.89, 2445.99, 2456.09, 2466.09, 2476.19,
2486.29, 2496.39, 2506.48, 2516.59, 2526.68, 2536.78, 2546.88, 2556.98,
2566.98, 2577.08]

# Target Band wavelengths
# 8 - 426.82
# 13 - 477.69
# 15 - 498.04
# 25 - 599.8
# 55 - 905.05
# 77 - 912.45
# 82 - 962.91
# 85 - 993.17
# 91 - 1053.69
# 93 - 1073.89
# 97 - 1114.19
# 102 - 1164.68
# 112 - 1265.56
# 115 - 1295.86
# 120 - 1346.25
# 137 - 1517.83
# 158 - 1729.7
# 183 - 1981.86


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