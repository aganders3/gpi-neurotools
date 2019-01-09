# Author: Ashley Anderson III <aganders3@gmail.com> 
# Date: 2015-09-09 16:49 

import gpi
import numpy as np
import nibabel as nib

# key = image type as string
# val = (nibabel class, file extension)
file_types =  {'analyze' : (nib.AnalyzeImage, '.img'),
               'nifti1' : (nib.Nifti1Image, '.nii')}

class ExternalNode(gpi.NodeAPI):
    """Write data and affine matrix to files supported by NiBabel
    Supported formats (see http://nipy.org/nibabel for more info):
        * ANALYZE (plain, SPM99, SPM2 and later)
        * NIfTI1
    INPUT:
        image: image data as N-D NumPy array
        affine: affine matrix as 2-D NumPy array
    WIDGETS:
        output-file: path of the image file you would like to write
        file-type: format of the file to write (see supported formats above)
        reverse-dims: transpose the image data before writing it out (often the
            dimension order is different in GPI from what you would like stored
            in the file)
    """

    def initUI(self):
        # Widgets
        self.addWidget('SaveFileBrowser', 'output-file', button_title='Browse',
                       caption='Save File')
        self.addWidget('ComboBox', 'file-type',
                       items=list(file_types.keys()), val='nifti1')
        self.addWidget('PushButton', 'reverse-dims',
                       toggle=True, val=False, collapsed=True) 

        # IO Ports
        self.addInPort('in', 'NPYarray')
        self.addInPort('affine', 'NPYarray', obligation=gpi.OPTIONAL, ndim=2)

    def compute(self):
        fullpath = gpi.TranslateFileURI(self.getVal('output-file'))
        filetype, ext = file_types[self.getVal('file-type')]
        fullpath += ext

        data = self.getData('in')
        affine = self.getData('affine')

        if self.getVal('reverse-dims'):
            data = data.T

        if affine is None:
            affine = np.eye(4)

        nibabel_image = filetype(data, affine) # add header?
        nibabel_image.to_filename(fullpath)

        return 0
