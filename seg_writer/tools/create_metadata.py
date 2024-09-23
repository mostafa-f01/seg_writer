import csv
import numpy as np
import SimpleITK
from palettable.tableau import tableau
import os
import json

# Get color palette
colormap = tableau.get_map("Tableau_20")

# Default CSV delimiter
CSV_DELIMITER = ","

# Parse csv
def parse_csv(csv_path):
    with open(csv_path) as file:
        csv_reader = csv.reader(file, delimiter=CSV_DELIMITER)
        len_label_id = 0
        labels = []
        for row in csv_reader:
            label_id = int(row[0].strip())
            labels.append(label_id)
            len_label_id +=1
    return len_label_id , labels

# Func to Get class ID form segmentation
def get_labels(segmentation,csv_path):
    print("Reading segmentation to identify ROIs...")
    if isinstance(segmentation,str):
        if os.path.exists(segmentation):
            image = SimpleITK.ReadImage(segmentation)
            image_data = SimpleITK.GetArrayFromImage(image)
            labels = np.trim_zeros(np.unique(image_data))
    elif isinstance(segmentation, np.ndarray):
        labels = np.trim_zeros(np.unique(segmentation))

    else:
        raise ValueError(f"The provided {segmentation} is not supported or can not accessible.")
    
    all_lables , whole_label = parse_csv(csv_path)
    if len(labels) != all_lables:
        labels = whole_label

    return labels


# Get class name's from CSV file that user supplied
def parse_labelmap_file(labelmap_path, labels):
    labels_dict = {}
    line_count = 0

    with open(labelmap_path) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=CSV_DELIMITER)
        for row in csv_reader:
            label_id = int(row[0].strip())
            label_name = row[1].strip()
            if label_id in labels:  # only include ids that are actually present in file
                labels_dict[label_id] = label_name
            line_count += 1

        for label in labels:  # check that all labels present in image are included in labels_dict
            if label not in labels_dict:
                raise ValueError(f"Label with pixel value {label} is not present in the CSV file!")
        print(
            f"{len(labels)}/{len(labels)} labels correctly mapped with the provided CSV file, generating metadata file now..."
        )
    return labels_dict

# Generate Metadata from each class
def generate_metadata(roi_dict, series_description="Segmentation"):
    if roi_dict is not None:
        segment_attributes = [get_segments(roi_dict)]
    else:
        segment_attributes = [[get_segment(1, "Probability Map", colormap.colors[0])]]

    basic_info = {
        "ContentCreatorName": "MARCOPACS",
        "ClinicalTrialSeriesID": "Session1",
        "ClinicalTrialTimePointID": "1",
        "SeriesDescription": series_description,
        "SeriesNumber": "",
        "InstanceNumber": "",
        "segmentAttributes": segment_attributes,
        "ContentLabel": "SEGMENTATION",
        "ContentDescription": "Image segmentation",
        "ClinicalTrialCoordinatingCenterName": "dcmqi",
        "BodyPartExamined": "",
    }

    return basic_info

def get_segments(roi_dict):
    segments = []
    i = 0
    for label, description in roi_dict.items():
        segments.append(get_segment(label, description, colormap.colors[i % len(colormap.colors)]))
        i += 1

    return segments

def get_segment(label, description, color):
    return {
        # Make sure we are using a simple int (not a NumPy type)
        "labelID": int(label),
        "SegmentDescription": description,
        "SegmentLabel": description,
        "SegmentAlgorithmType": "AUTOMATIC",
        "SegmentAlgorithmName": "Automatic",
        # Snomed Coding for Tissue
        "SegmentedPropertyCategoryCodeSequence": {
            "CodeValue": "85756007",
            "CodingSchemeDesignator": "SCT",
            "CodeMeaning": "",
        },
        # Snomed Coding for Organ
        "SegmentedPropertyTypeCodeSequence": {
            "CodeValue": "",
            "CodingSchemeDesignator": "SCT",
            "CodeMeaning": "",
        },
        # Color to display
        "RecommendedDisplayCIELabValue": color,
    }

def create_metadata(segmentation,csv_path,output_path):

    lables = get_labels(segmentation,csv_path)
    lable_map = parse_labelmap_file(csv_path,lables)
    meta = generate_metadata(lable_map)

    # Convert and write JSON object to file
    with open(output_path, "w") as outfile:
        json.dump(meta, outfile,indent=4)
    print("metadata generated successfully")