__version__ = "0.1.2"

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
import numpy as np
from pathlib import Path
import os
