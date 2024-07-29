# DICOM Segmentation Writer

This package is implemented to create multiframe DICOM SEG (segmentation) files from NIfTI files or numpy arrays. The primary class in this package is `Writer`, which contains two main functions for creating DICOM SEG files. Additionally, there is a `generate_metadata.py` script for generating a metadata JSON file required by the main module.The seg_writer library leverages pydicom and highdicom for this conversion.

# Class: `Writer`

The `Writer` class provides methods for generating DICOM SEG files from different input formats. It includes the following main methods:

## Method: `from_nifti`

Creates a DICOM SEG file from a NIfTI file.

**Parameters:**
- `nifti_file_path` (str): Path to the NIfTI file with .nii or .nii.gz suffix containing the segmentation data.
- `dicom_series_path` (str): Path to the directory containing the source DICOM series.
- `metadata_file_path` (str): Path to the JSON file containing the segmentation metadata.
- `output_path` (str): Path to the directory where the output DICOM SEG file will be saved.

**Usage Example:**
```
from seg_writer.Writer import Writer

writer = Writer()
writer.from_nifti(
    nifti_file_path="path/to/nifti/file.nii",
    dicom_series_path="path/to/dicom/series/",
    metadata_file_path="path/to/metadata/file.json",
    output_path="path/to/output/directory/"
)
```
## Method: `from_array`

Creates a DICOM SEG file from a numpy array.

**Parameters:**
- `pixel_array` (np.ndarray): Numpy array containing the segmentation data.
- `dicom_series_path` (str): Path to the directory containing the source DICOM series.
- `metadata_file_path` (str): Path to the JSON file containing the segmentation metadata.
- `output_path` (str): Path to the directory where the output DICOM SEG file will be saved.

**Usage Example:**
```
from seg_writer.Writer import Writer

writer = Writer()
writer.from_array(
    pixel_array=numpy_array,
    dicom_series_path="path/to/dicom/series/",
    metadata_file_path="path/to/metadata/file.json",
    output_path="path/to/output/directory/"
)
```
### Additional Functions
**Available at utils.py**

### METHOD: `_load_nifti_file`

Loads a NIfTI file and returns the pixel values as a numpy array.

**Parameters:**

- `nifti_file_path` (str): Path to the NIfTI file.

### Method: `read_metadata`

Reads the segmentation metadata JSON file.

**Parameters:**

- `metadata_file_path` (str): Path to the metadata file.

### Method: `filter_segment_descriptions`

Filters and organizes the segmentation metadata.

**Parameters:**

- `metadata_file_path` (str): Path to the metadata file.

### Method: `_normalize_source_images`

Normalizes the source DICOM images, ensuring they have no 'NumberOfFrames' tag.

**Parameters:**

- `dcms_or_paths` (Union[List[pydicom.Dataset], str]): List of DICOM datasets or path to the DICOM series directory.

### Method: `check_for_overlap`

Checks for overlap in segments and validates the file.

**Parameters:**

- `segmentation` (Union[sitk.Image, np.ndarray, Path]): Segmentation data.

### Method: `match_shape_segmentation_and_dicom`

Checks if the shape of the segmentation matches the shape of the original DICOM series.

**Parameters:**

- `segmentation` (np.ndarray): Numpy array containing the segmentation data.

- `dicom_series_path` (str): Path to the directory containing the source DICOM series.

- `dicom_datasets` (List[pydicom.Dataset]): List of DICOM datasets.

### Method: `get_nifti_labels`

Checks if labels are present in the input segmentation and returns the labels if they exist.

**Parameters:**

- `segmentation` (Union[np.ndarray, Path]): Segmentation data.

### Method: `reading_back`

Reads the generated DICOM SEG file for final confirmation.

**Parameters:**

- `output_file_path` (str): Path to the generated DICOM SEG file.

### Method: `compress_dicom`

Compressing a DICOM file using deflate.

**Parameters:**

- `input_file_path` (str): Path to the input DICOM file + file name.

- `output_file_path` (str): Path to the output compressed DICOM file + file name.


## generate_metadata.py
The generate_metadata.py script generates a metadata JSON file required by the main module. It processes a CSV file and a segmentation file to produce the metadata.

## Function: `create_metadata`
Generates metadata for segmentation based on the provided CSV file and segmentation data.

**Parameters:**

- `segmentation` (str or np.ndarray): Path to the segmentation file or numpy array containing the segmentation data.

- `csv_path` (str): Path to the CSV file containing label information.

- `output_path` (str): Path to the directory where the metadata JSON file will be saved.

**Usage Example:**
```
from seg_writer.tools.create_metadata import create_metadata

create_metadata(
    segmentation="path/to/segmentation.nii",
    csv_path="path/to/labels.csv",
    output_path="path/to/output/metadata.json"
)
```
**CSV File Format**
The CSV file should contain the label IDs and corresponding descriptions in the following format:

label_id,label_name
1,spleen
2,kidney_right
3,kidney_left
...

**note:csv file should pass to function without header like the example below**

1,spleen
2,kidney_right
3,kidney_left
...
