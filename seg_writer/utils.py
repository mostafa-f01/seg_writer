import SimpleITK as sitk
import numpy as np
from pathlib import Path
import os
import pydicom
import importlib.util
from pydicom.tag import Tag
import nibabel as nib

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

    # Ensure the file is uncompressed before applying compression
    if ds.file_meta.TransferSyntaxUID.is_compressed:
        ds.decompress()

    ds.is_implicit_VR = False
    ds.is_little_endian = True
    ds.file_meta.TransferSyntaxUID = pydicom.uid.DeflatedExplicitVRLittleEndian

    # Save the compressed file
    ds.save_as(output_file_path, write_like_original=False)

    
def find_package_directory(package_name='seg_writer'):
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        return None
    return os.path.dirname(spec.origin)

def add_color(metadata,dicom_dataset):
    for i in metadata:
        for sequence in dicom_dataset.SegmentSequence:
            RecommendedDisplayCIELabValue = Tag(0x0062,0x000D)
            label = i["SegmentLabel"]
            try:
                color = (i["RecommendedDisplayCIELabValue"])
            except KeyError:
                color = (i["recommendedDisplayRGBValue"])

            if label in sequence.SegmentLabel:
                sequence.add_new(RecommendedDisplayCIELabValue,'US',value=color)
                
    return dicom_dataset


def reorient_pixel_array(nifti_file_path, refrenced_ds_path):
    # Read the DICOM series
    dicom_reader = sitk.ImageSeriesReader()
    dicom_file_names = dicom_reader.GetGDCMSeriesFileNames(refrenced_ds_path)
    dicom_reader.SetFileNames(dicom_file_names)
    dicom_sitk_image = dicom_reader.Execute()
    dicom_array = sitk.GetArrayFromImage(dicom_sitk_image)

    # Load NIfTI file
    nifti_img = nib.load(nifti_file_path)
    nifti_data = nifti_img.get_fdata()
    affine_matrix = nifti_img.affine

    # Get the shapes
    nifti_shape = nifti_data.shape
    dicom_shape = dicom_sitk_image.GetDepth()

    # Get slice positions from the DICOM metadata
    dicom_positions = np.array([dicom_sitk_image.TransformIndexToPhysicalPoint((0, 0, i)) for i in range(dicom_shape)])

    # Derive slice positions from the NIfTI affine matrix
    nifti_positions = np.array([affine_matrix @ np.array([0, 0, i, 1]) for i in range(nifti_shape[2])])[:, :3]

    # Create an array to hold the segmented data and reorient based on the slice axis
    slice_axis = np.argmax([nifti_shape[0] == dicom_shape,
                            nifti_shape[1] == dicom_shape,
                            nifti_shape[2] == dicom_shape])
    
    segment_array = np.zeros(dicom_array.shape,dtype=np.uint8)

    if slice_axis == 1:
        for i in range(nifti_data.shape[1]):
            for x in range(nifti_data.shape[0]):
                for y in range(nifti_data.shape[2]):
                    segment_array[i, x, y] = nifti_data[x, i, y]

    elif slice_axis == 2:
        for i in range(nifti_data.shape[2]):
            for x in range(nifti_data.shape[0]):
                for y in range(nifti_data.shape[1]):
                    segment_array[i, x, y] = nifti_data[x, y, i]

    else:
        segment_array = nifti_data
    
    # Compare first and last slice positions
    if np.linalg.norm(nifti_positions[0] - dicom_positions[0]) > np.linalg.norm(nifti_positions[-1] - dicom_positions[0]):
        segment_array = segment_array[::-1]

    # Rotate the segment array as needed
    segment_array = np.rot90(segment_array, k=1, axes=(1, 2))

    return segment_array