from setuptools import setup, find_packages

setup(
    name='seg_writer',
    version='0.1.4',
    description="Package to create multiframe DICOM SEG files from NIfTI files or numpy arrays",
    packages=find_packages(include=['seg_writer', 'seg_writer.*']),
    install_requires=[
        'highdicom',
        'numpy',
        'pillow',
        'pillow-jpls',
        'pydicom',
        'SimpleITK',
        'pylibjpeg',
        'palettable',
        'pylibjpeg-libjpeg',
        'pylibjpeg-openjpeg',
        'imagecodecs',

    ],
    package_data={
        '': ['./examples/*/*.json']
    }
)