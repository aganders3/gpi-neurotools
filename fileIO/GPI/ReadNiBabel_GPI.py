# Author: Ashley Anderson III <aganders3@gmail.com>
# Date: 2015-09-09 13:48 

import gpi
import os
import numpy as np
import nibabel as nib

class ExternalNode(gpi.NodeAPI):
    """Read data and affine matrix from files supported by NiBabel
    Supported formats (see http://nipy.org/nibabel for more info):
        * ANALYZE (plain, SPM99, SPM2 and later)
        * GIFTI
        * NIfTI1, NIfTI2
        * MINC1, MINC2
        * MGH
        * ECAT
        * Philips PAR/REC
    OUTPUT:
        image: image data as N-D NumPy array
        affine: affine matrix as 2-D NumPy array
    WIDGETS:
        input-file: path of the image file you would like to read
        reverse-dims: transpose the image data upon reading it in
    """

    def initUI(self):
       # Widgets
        self.addWidget('OpenFileBrowser', 'input-file',
                button_title='Browse', caption='Open File')
        self.addWidget('PushButton', 'reverse-dims',
                       toggle=True, val=False, collapsed=True) 

        # IO Ports
        self.addOutPort(title='image', type='NPYarray')
        self.addOutPort(title='affine', type='NPYarray')

    def compute(self):
        # start file browser
        fname = gpi.TranslateFileURI(self.getVal('input-file'))


        # check that the path actually exists
        if not os.path.exists(fname):
            self.log.node("Path does not exist: "+str(fname))
            return 0

        nibabel_image = nib.load(fname)

        out_data = np.ascontiguousarray(nibabel_image.get_data())
        if self.getVal('reverse-dims'):
            out_data = np.ascontiguousarray(out_data.T)

        self.setData('image', out_data)
        self.setData('affine', nibabel_image.affine)

        return(0)
