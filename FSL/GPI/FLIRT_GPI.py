# Author: Ashley Anderson
# Date: 2015-08-25 13:21 

import gpi
import numpy as np

from gpi.ebe import IFilePath, OFilePath, Command
from functools import partial
from neurotools.fileIO.neuroIO import writeNifti, readNifti

realtypes = [np.int32, np.int64, np.float32, np.float64]
complextypes = [np.complex64, np.complex128]

class ExternalNode(gpi.NodeAPI):
    """ A node for co-registering two volumes (same resolution and FOV).
        INPUT:
            fixed: reference image or image volume
            moving: input image volume to be co-registered with reference 
            ** input image volumes must be 2 or 3 dimensional
        WIDGETS:
            res: resolution for each dimension of the input data
            interp: final interpolation mode
            cost: cost metric to use for registration
            dof: degrees of freedom (for 3D data, for 2D data dof = 3)
                6 = rigid-body translation and rotation
                7 = 6 + isotropic scale
                9 = 6 + anisotropic scale
                12 = affine transformation
        OUTPUT:
            out: moving image co-registered to align with fixed image
            T: 4x4 transformation matrix
    """

    def initUI(self):
        self.addInPort('fixed', 'NPYarray', dtype=realtypes + complextypes)
        self.addInPort('moving', 'NPYarray', dtype=realtypes + complextypes)
        self.addInPort('init', 'NPYarray', ndim=2, obligation=gpi.OPTIONAL)

        self.addWidget('DoubleSpinBox', 'res[-1]', min=0.1, max=20, val=1)
        self.addWidget('DoubleSpinBox', 'res[-2]', min=0.1, max=20, val=1)
        self.addWidget('DoubleSpinBox', 'res[-3]', min=0.1, max=20, val=1)

        self.addWidget('ComboBox', 'interp',
            items=('trilinear', 'nearestneighbor', 'sinc', 'spline'),
            val='sinc')
        self.addWidget('ComboBox', 'cost',
            items=('mutalinfo', 'corratio', 'normcorr', 'normmi', 'leastsq'),
            val='corratio')

        self.addWidget('ComboBox', 'dof', items=('6', '7', '9', '12'), val='6')
        self.addWidget('SpinBox', 'coarse search angle', min=1, max=90, val=60)
        self.addWidget('SpinBox', 'fine search angle', min=1, max=90, val=18)

        self.addOutPort('out', 'NPYarray')
        self.addOutPort('T', 'NPYarray', ndim=2)
        
    def validate(self):
        fixed = self.getData('fixed')
        moving = self.getData('moving')

        if (fixed.ndim < 2 or fixed.ndim > 3 or
            moving.ndim < 2 or moving.ndim > 3):
            print("COREGISTER ERR: input images must be 2D or 3D")
            return 1
        if fixed.shape != moving.shape:
            print("COREGISTER ERR: input images must have equal shape")
            return 1

        for ii in range(3):
            vis = -(ii-3) <= fixed.ndim
            self.setAttr('res[{}]'.format(ii-3), visible=vis) 

        return 0
        
    def compute(self):
        fixed = self.getData('fixed')
        moving = self.getData('moving')
        T = self.getData('init')

        zres = self.getVal('res[-3]')
        yres = self.getVal('res[-2]')
        xres = self.getVal('res[-1]')
        fixedAffine = movingAffine = np.diag((zres, yres, xres, 1))

        fixedWriter = partial(writeNifti, affine=fixedAffine)
        movingWriter = partial(writeNifti, affine=movingAffine)

        # FLIRT can't handle complex data, so we will use the magnitude if the
        # inputs are complex
        if fixed.dtype in complextypes:
            fixed_ = IFilePath(fixedWriter, np.abs(fixed), suffix=".nii")
        else:
            fixed_ = IFilePath(fixedWriter, fixed, suffix=".nii")

        if moving.dtype in complextypes:
            moving_ = IFilePath(movingWriter, np.abs(moving), suffix=".nii")
        else:
            moving_ = IFilePath(movingWriter, moving, suffix=".nii")

        # this is where the registration is performed, unless an initial
        # transformation matrix (T) is provided
        out_ = None
        if T is None:
            out_ = OFilePath(readNifti, suffix=".nii.gz")
            omat_ = OFilePath(np.loadtxt)

            flirt = 'flirt'
            if fixed.ndim == 2:
                flirt += ' -2D'

            Command(flirt,
                '-dof {}'.format(self.getVal('dof')),
                '-interp {}'.format(self.getVal('interp')),
                '-cost {}'.format(self.getVal('cost')),
                '-searchcost {}'.format(self.getVal('cost')),
                '-coarsesearch {}.'.format(self.getVal('coarse search angle')),
                '-finesearch {}'.format(self.getVal('fine search angle')),
                '-searchrx -20 20', '-searchry -20 20', '-searchrz -20 20',
                '-in', moving_, '-ref', fixed_, '-out', out_, '-omat', omat_)

            T = omat_.data()

            [f.close() for f in (fixed_, moving_, out_, omat_)]

        # magnitude images have been registered
        # if the input is complex, apply the transformation to the real and
        # imaginary channels separately (this requires running FLIRT two more
        # times)
        if moving.dtype in complextypes or out_ is None:
            out = np.zeros(moving.shape, dtype=moving.dtype)
            for ii in (np.real, np.imag):
                if moving.dtype in realtypes and ii == np.imag:
                    continue

                fixed_ = IFilePath(fixedWriter, ii(fixed), suffix=".nii")
                moving_ = IFilePath(movingWriter, ii(moving), suffix=".nii")
                T_ = IFilePath(np.savetxt, T)
                out_ = OFilePath(readNifti, suffix=".nii.gz")

                flirt = 'flirt -applyxfm'
                if moving.ndim == 2:
                    flirt += ' -2D'

                Command(flirt,
                    '-interp {}'.format(self.getVal('interp')),
                    '-init', T_, '-in', moving_, '-ref', fixed_, '-out', out_)

                if ii == np.real:
                    out += out_.data()
                else:
                    out += 1j * out_.data()

                [f.close() for f in (fixed_, moving_, out_, T_)]
        # if the input is real, just use the output image from FLIRT
        else:
            out = out_.data()

        self.setData('out', out)
        self.setData('T', T)

        return 0

