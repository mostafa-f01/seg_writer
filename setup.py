from setuptools import setup, find_packages

setup(
    name='seg_writer',
    version='1.0.0',
    description="Package to create multiframe DICOM SEG files from NIfTI files or numpy arrays",
    packages=find_packages(include=['seg_writer', 'seg_writer.*']),
    package_data={
        '': ['./examples/*/*.json']
    }
)