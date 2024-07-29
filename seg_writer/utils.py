import SimpleITK as sitk
import numpy as np
from pathlib import Path
import os
import pydicom
import importlib.util

# Check for ovelap segments and validate file 
def check_for_overlap(segmentation):
    """Check for overlap in segments and validate the file."""
    is_overlap = False 
    if isinstance(segmentation, sitk.Image):
        is_overlap = segmentation.GetNumberOfComponentsPerPixel() > 1
    elif isinstance(segmentation, np.ndarray):
        segmentation = sitk.GetImageFromArray(segmentation)
        is_overlap = segmentation.GetNumberOfComponentsPerPixel() > 1
    elif isinstance(segmentation, Path):
        try:
            segmentation = sitk.ReadImage(str(segmentation))
            is_overlap = segmentation.GetNumberOfComponentsPerPixel() > 1
        except Exception as e:
            raise ValueError(f"{segmentation} is not a valid image file.") from e

    if is_overlap:
        raise ValueError(
            "Multi-class segmentations can only be "
            "represented with a single component per voxel."
        )

# Check shape of nifti with original dicom file
def match_shape_segmentation_and_dicom(segmentation,dicom_series_path,dicom_datasets):
    """Check if the shape of the segmentation matches the shape of the original DICOM series."""
    dicom_shape = len([dicom_series_path+ i for i in os.listdir(dicom_series_path) if '.dcm' in i])
    dicom_rows, dicom_columns = dicom_datasets[0].Rows, dicom_datasets[0].Columns

    if segmentation.shape != (dicom_shape,dicom_rows,dicom_columns):
        try:
            # Ensure the NIfTI array has the same number of slices as the DICOM series
            if segmentation.shape[0] != dicom_shape:
                #Find the axis with the matching number of slices
                slice_axis = np.argmax([segmentation.shape[0] == dicom_shape,
                            segmentation.shape[1] == dicom_shape,
                            segmentation.shape[2] == dicom_shape])
            # Reorder the axes to match the DICOM shape (slices, rows, columns)
            segmentation = np.moveaxis(segmentation, slice_axis, 0)
        except Exception as e:
            if segmentation.shape[1] != dicom_rows or segmentation.shape[2] != dicom_columns:
                raise ValueError(f"The shape of nifti file with {segmentation.shape} is incompatible with shape of source dicom series with {(dicom_shape,dicom_datasets[0].Rows,dicom_datasets[0].Columns)}")
    return segmentation
# Check if labels present in input segmentation or not return labels if exists and return error if no labels found
def get_nifti_labels(segmentation):
    """Check if labels are present in the input segmentation and return labels if they exist."""
    if isinstance(segmentation, np.ndarray):
        labels = np.trim_zeros(np.unique(segmentation))
    elif isinstance(segmentation, str):
        sitk_image = sitk.ReadImage(str(segmentation))
        image_data = sitk.GetArrayFromImage(sitk_image)
        labels = np.trim_zeros(np.unique(image_data))
    else:
        raise ValueError("Unsupported segmentation type.")
    
    if len(labels) == 0:
        raise ValueError("No segments found for encoding as DICOM-SEG")
    return labels


# Test reading back
def reading_back(output_file_path):
    """Read the generated DICOM SEG file for final confirmation."""
    try:
        _ = pydicom.dcmread(str(output_file_path),force=True)
    except Exception as ex:
        print("DICOMSeg creation failed. Error:\n{}".format(ex))


# Compress dicom seg file
def compress_dicom(input_file_path: str, output_file_path: str):
    """Compress a DICOM file using deflate."""
    ds = pydicom.dcmread(input_file_path)
    ds.is_explicit_VR = True
    ds.is_little_endian = True
    ds.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1.99" # Deflated TransferSyntaxUID 
    ds.save_as(output_file_path)

    
def find_package_directory(package_name='seg_writer'):
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        return None
    return os.path.dirname(spec.origin)
    