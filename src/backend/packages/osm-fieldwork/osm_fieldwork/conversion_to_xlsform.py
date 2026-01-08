import io
import logging

from yxf.yaml import read_yaml
from yxf.excel import write_xlsform

log = logging.getLogger(__name__)

def convert_to_xlsform(yaml_file):
    """
    Reads a YAML file and converts in-memory to XLSForm bytes using the yxf library.
    """
    try:
        with open(yaml_file, encoding="utf-8") as file:
            yaml_content = file.read()
        
        form_dictionary = read_yaml(yaml_content)

        output_buffer = io.BytesIO()

        write_xlsform(form_dictionary, output_buffer)
        xlsx_bytes = output_buffer.getvalue()

        log.info(f'Successfully converted YAML file: {yaml_file} to XLSForm bytes.')

        return xlsx_bytes

    except Exception as e: 
        log.exception(f'An error occurred during in-memory conversion for YAML file: {yaml_file}')
        raise
