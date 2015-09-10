# Author: Ashley Anderson
# Date: 2015-08-28 07:54

import gpi
import numpy as np

from gpi.ebe import IFilePath, OFilePath, Command
from functools import partial
from neurotools.fileIO.neuroIO import writeNifti, readNifti

realtypes = [np.int32, np.int64, np.float32, np.float64]
complextypes = [np.complex64, np.complex128]

class ExternalNode(gpi.NodeAPI):
    """ A node for segmenting the brain.
        INPUT:
            in: a 3D neuro image 
        WIDGETS:
            res: resolution for each dimension of the input data
        OUTPUT:
            brain: a brain-only image, extracted using the FSL brain extraction
                tool (BET)
            seg: the segmented image labels
    """

    def initUI(self):
        self.addInPort('in', 'NPYarray', ndim=3)

        self.addWidget('DoubleSpinBox', 'res[-1]', min=0.1, max=20, val=1)
        self.addWidget('DoubleSpinBox', 'res[-2]', min=0.1, max=20, val=1)
        self.addWidget('DoubleSpinBox', 'res[-3]', min=0.1, max=20, val=1)
        self.addWidget('ExclusivePushButtons', 'contrast',
                        buttons=['T1', 'T2', 'PD'], val=0)

        self.addOutPort('brain', 'NPYarray')
        self.addOutPort('seg', 'NPYarray')
        
    def compute(self):
        in_image = self.getData('in')

        zres = self.getVal('res[-3]')
        yres = self.getVal('res[-2]')
        xres = self.getVal('res[-1]')
        inAffine = np.diag((zres, yres, xres, 1))

        inWriter = partial(writeNifti, affine=inAffine)

        # Nifti1 can't handle complex data, so we will use the magnitude if the
        # inputs are complex
        if in_image.dtype in complextypes:
            in_image_ = IFilePath(inWriter, np.abs(in_image), suffix=".nii")
        else:
            in_image_ = IFilePath(inWriter, in_image, suffix=".nii")

        brain_= OFilePath(readNifti)
        seg_= OFilePath(readNifti)

        bet = 'bet2'
        Command(bet, in_image_, brain_)

        fast = 'fast'
        Command(fast, '-t {}'.format(self.getVal('contrast')+1),
                '-o', seg_, brain_)

        self.setData('brain', brain_.data(".nii.gz"))
        self.setData('seg', seg_.data("_seg.nii.gz"))

        [f.close() for f in (in_image_, brain_, seg_)]

        return 0

