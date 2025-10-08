import os 
import asyncio
import tempfile
import shutil
import subprocess
import importlib
from pathlib import Path
from importlib.resources.abc import Traversable

async def convert_yaml_to_xlsform(yaml_resource_path : Traversable):
    """ Converting a YAMLForm to XLSForm bytes using the 'yxf' command-line tool.
    """
    with importlib.resources.as_file(yaml_resource_path) as yaml_filepath:
         file_name = yaml_resource_path.name

         with tempfile.TemporaryDirectory() as temporary_directory: 
            temporary_yaml_filepath = Path(temporary_directory) / file_name
            shutil.copy(yaml_filepath, temporary_yaml_filepath)
            temporary_output_file = Path(temporary_directory) / "output.xlsx"

            try: 
                conversion = await asyncio.create_subprocess_exec(
                    "python", "-m", "yxf", str(temporary_yaml_filepath), "-o", temporary_output_file,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE)
                stdout_data, stderr_data = await conversion.communicate()
            except FileNotFoundError as e: 
                raise RuntimeError(f"'yxf' module not found.")
            
            if conversion.returncode != 0:
                raise RuntimeError(f"Conversion from YAMLForm to XLSForm failed: '{stderr_data.decode()}'")
            
            form_bytes = temporary_output_file.read_bytes() 

            return form_bytes