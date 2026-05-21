import textwrap
from pathlib import Path
from string import Template
from typing import Optional, Union

from ichor.core.files.file import File, WriteFile


class ExtractModelsScript(WriteFile, File):
    _filetype = ".py"

    def __init__(
        self,
        path: Union[Path, str],
    ):
        File.__init__(self, path)

        # find path to parent folder (5_TRAINING)
        # make 6_MODELS/system_name if it doesn't exist yet
        # copy data from folder to new folder - should be easy

    # write file from a template
    def _write_file(self, path: Path, *args, **kwargs):

        # set up template for polus script
        extract_models_script_template = Template(textwrap.dedent("""
            import os
            import shutil
            import glob
            
            def main():
                current_dir = os.getcwd()
            
                # 1. Split the current path and locate "5_TRAINING"
                parts = current_dir.split(os.sep)
            
                if "5_TRAINING" not in parts:
                    raise RuntimeError("Could not find '5_TRAINING' in the current path.")
            
                idx = parts.index("5_TRAINING")
            
                # system_name = directory immediately after 5_TRAINING
                try:
                    system_name = parts[idx + 1]
                except IndexError:
                    raise RuntimeError("'5_TRAINING' has no child directory in the path.")
            
                # leaf directory = the deepest directory in the current path
                leaf_dir = parts[-1]
            
                # 2. Parent directory above 5_TRAINING
                parent_dir = os.sep.join(parts[:idx]) or os.sep
            
                # 3. Build destination path: 6_MODELS / system_name / leaf_dir
                models_root = os.path.join(parent_dir, "6_MODELS")
                models_dir = os.path.join(models_root, system_name, leaf_dir)
                os.makedirs(models_dir, exist_ok=True)
            
                # 4. Recursively find all .model files under current directory
                model_files = glob.glob(os.path.join(current_dir, "**", "*.model"), recursive=True)
            
                # 5. Copy .model files into the new models_dir
                for file_path in model_files:
                    shutil.copy(file_path, models_dir)
            
                print(f"system_name = {system_name}")
                print(f"leaf_dir = {leaf_dir}")
                print(f"Copied {len(model_files)} model files into: {models_dir}")
            
            
            if __name__ == "__main__":
                main()
            

        """))

        script_text = extract_models_script_template.substitute()

        return script_text
