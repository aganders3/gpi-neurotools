import numpy as np
import nibabel as nib

def writeNifti(filename, data, affine=np.eye(4)):
    nifti1_image = nib.Nifti1Image(data, affine)
    nifti1_image.to_filename(filename)

def readNifti(filename):
    loaded_image = nib.nifti1.load(filename)
    return loaded_image.get_data()

