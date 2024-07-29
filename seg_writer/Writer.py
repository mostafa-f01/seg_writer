import pydicom
import SimpleITK as sitk
import highdicom as hd
from typing import List, Union
from os import PathLike
import json
from highdicom import AlgorithmIdentificationSequence
from pydicom.sr.codedict import codes
import os
from seg_writer.utils import *
from concurrent.futures import ThreadPoolExecutor
import gc

class Writer:

    AnyStr = Union[bytes, str]
    FSPath = Union[AnyStr, PathLike]

    def __init__(self):
        pass
    
    # Load nifti file and returns pixel values as numpy array
    def _load_nifti_file(self,nifti_file_path):
        sitk_image = sitk.ReadImage(nifti_file_path)
        return sitk.GetArrayFromImage(sitk_image)

    # Load segmentaion metadata json file
    def read_metadata(self,metadata_file_path):
        with open(metadata_file_path, 'r') as file:
            return json.load(file)

    # Filter segmentation filter and orginize it
    def filter_segment_descriptions(self, metadata_file_path):
        metadata = self.read_metadata(metadata_file_path)
        segment_attributes = [item for sublist in metadata['segmentAttributes'] for item in sublist]
        filtered_descriptions = []
        for desc in segment_attributes:
            #if desc['labelID'] in labels:
            # Correctly create CodedConcept objects
            category = hd.sr.CodedConcept(
                value=desc['SegmentedPropertyCategoryCodeSequence']['CodeValue'],
                scheme_designator=desc['SegmentedPropertyCategoryCodeSequence']['CodingSchemeDesignator'],
                meaning=desc['SegmentedPropertyCategoryCodeSequence']['CodeMeaning']
            )
            type_code = hd.sr.CodedConcept(
                value=desc['SegmentedPropertyTypeCodeSequence']['CodeValue'],
                scheme_designator=desc['SegmentedPropertyTypeCodeSequence']['CodingSchemeDesignator'],
                meaning=desc['SegmentedPropertyTypeCodeSequence']['CodeMeaning']
            )
            # Create the SegmentDescription object
            segment_description = hd.seg.SegmentDescription(
                segment_number=desc['labelID'],
                segment_label=desc['SegmentLabel'],
                segmented_property_category=category,
                segmented_property_type=type_code,
                algorithm_type=hd.seg.SegmentAlgorithmTypeValues.AUTOMATIC.value,
                algorithm_identification=AlgorithmIdentificationSequence(
                    name='AI',  
                    version='',  
                    family=codes.cid7162.ArtificialIntelligence 
                )
            )
            filtered_descriptions.append(segment_description)
        return filtered_descriptions

    def _normalize_source_images(self, dcms_or_paths: Union[List[pydicom.Dataset], FSPath]) -> List[pydicom.Dataset]:
        """Normalize source DICOM images, ensuring they have no 'NumberOfFrames' tag."""

        def process_dicom_file(elem):
            if isinstance(elem, pydicom.Dataset):
                # Check if 'NumberOfFrames' tag exists and delete it
                if 'NumberOfFrames' in elem:
                    del elem.NumberOfFrames
                return elem
            else:
                dcm = pydicom.dcmread(elem, stop_before_pixels=True,force=True)
                # Check if 'NumberOfFrames' tag exists and delete it
                if 'NumberOfFrames' in dcm:
                    del dcm.NumberOfFrames
                return dcm

        result: List[pydicom.Dataset] = []
        dicom_series_files = [os.path.join(dcms_or_paths, i) for i in os.listdir(dcms_or_paths) if '.dcm' in i]

        with ThreadPoolExecutor() as executor:
            result = list(executor.map(process_dicom_file, dicom_series_files))

        return result


    def from_nifti(self,nifti_file_path, dicom_series_path, metadata_file_path, output_path):

        # Check overlap
        check_for_overlap(segmentation=nifti_file_path)
        
        # Load the NIfTI file to get the pixel data
        pixel_array = self._load_nifti_file(nifti_file_path)

        # Iterate on segmentation to check is lables present and if no lables presents return error and if found one return list of uniqe lables
        get_nifti_labels(nifti_file_path)

        # Normalize the source DICOM images
        dicom_datasets = self._normalize_source_images(dicom_series_path)
        
        # Match the shape of segmentation and source dicom files
        pixel_array = match_shape_segmentation_and_dicom(pixel_array,dicom_series_path,dicom_datasets)

        # Read the metadata and filter the segment descriptions
        #metadata = self.read_metadata(metadata_file_path)
        segment_descriptions = self.filter_segment_descriptions(metadata_file_path)
        
        # Normalize the source DICOM images
        dicom_datasets = self._normalize_source_images(dicom_series_path)

        # Create the DICOM SEG file
        seg_instance_uid = hd.UID()
        seg = hd.seg.Segmentation(
            source_images=dicom_datasets,
            pixel_array=pixel_array,
            segmentation_type=hd.seg.SegmentationTypeValues.BINARY,
            segment_descriptions=segment_descriptions,
            series_instance_uid=hd.UID(),
            series_number=dicom_datasets[0].SeriesNumber,
            sop_instance_uid=seg_instance_uid,
            instance_number=1,
            manufacturer="",
            manufacturer_model_name="",
            software_versions="",
            device_serial_number="",
            omit_empty_frames=True,
        )

        # Save the DICOM SEG file
        os.makedirs(output_path, exist_ok=True)
        output_file_path = os.path.join(output_path, f"SR{dicom_datasets[0].SeriesNumber}"+"_segmentation_temp.dcm")
        seg.save_as(str(output_file_path))

        # Call deflated method for compression
        compressed_file = os.path.join(output_path, f"SR{dicom_datasets[0].SeriesNumber}"+"_segmentation.dcm")
        compress_dicom(output_file_path,compressed_file)
        os.remove(output_file_path)

        # Read the generated file for final confirmation
        reading_back(compressed_file)

        # Explicitly manage memory
        del pixel_array
        del dicom_datasets
        del segment_descriptions
        gc.collect()

        return compressed_file

    def from_array(self, pixel_array, dicom_series_path, metadata_file_path, output_path):
        
        # Check overlap
        check_for_overlap(segmentation=pixel_array)

        # Iterate on segmentation to check is lables present and if no lables presents return error and if found one return list of uniqe lables
        get_nifti_labels(pixel_array)

        # Normalize the source DICOM images
        dicom_datasets = self._normalize_source_images(dicom_series_path)

        # Match the shape of segmentation and source dicom files
        match_shape_segmentation_and_dicom(pixel_array,dicom_series_path,dicom_datasets)

        # Make segmentation descriptions
        segment_descriptions = self.filter_segment_descriptions(metadata_file_path)

        # Create the DICOM SEG file
        seg_instance_uid = hd.UID()
        seg = hd.seg.Segmentation(
            source_images=dicom_datasets,
            pixel_array=pixel_array,
            segmentation_type=hd.seg.SegmentationTypeValues.BINARY,
            segment_descriptions=segment_descriptions,
            series_instance_uid=hd.UID(),
            series_number=dicom_datasets[0].SeriesNumber,
            sop_instance_uid=seg_instance_uid,
            instance_number=1,
            manufacturer="",
            manufacturer_model_name="",
            software_versions="",
            device_serial_number="",
            omit_empty_frames=True,
        )

        # Save the DICOM SEG file
        os.makedirs(output_path, exist_ok=True)
        output_file_path = os.path.join(output_path, f"SR{dicom_datasets[0].SeriesNumber}"+"_segmentation_temp.dcm")
        seg.save_as(str(output_file_path))

        # Call deflated method for compression
        compressed_file = os.path.join(output_path, f"SR{dicom_datasets[0].SeriesNumber}"+"_segmentation.dcm")
        compress_dicom(output_file_path,compressed_file)
        os.remove(output_file_path)

        # Read the generated file for final confirmation
        reading_back(compressed_file)

        # Explicitly manage memory
        del pixel_array
        del dicom_datasets
        del segment_descriptions
        gc.collect()
        return compressed_file