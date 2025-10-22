import os 
import logging

from yxf import yaml_string_to_xlsform_bytes

logger = logging.getLogger(__name__)

def convert_to_xlsform(yaml_file):
    """
    Reads a YAML file and converts in-memory to XLSForm bytes using yxf's yaml_string_to_xlsform_bytes.
    """
    try:
        with open(yaml_file, encoding="utf-8") as file:
            yaml_content = file.read()
        
        xlsx_bytes = yaml_string_to_xlsform_bytes(yaml_content, source_name=os.path.basename(yaml_file))

        logger.info(f'Successfully converted YAML file: {yaml_file} to XLSForm bytes.')

    except Exception as e: 
        logger.exception(f'An error occurred during in-memory conversion for YAML file: {yaml_file}')

    return xlsx_bytes
