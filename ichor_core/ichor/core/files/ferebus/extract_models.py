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
            from pathlib import Path
        
            def find_seq_folder(start: Path) -> Path:
                \"\"\"Find the folder that sits between TRAIN-* and iqa, regardless of depth.\"\"\"
                p = start
        
                # Step 1: walk upward until we hit TRAIN-*
                while p != p.parent:
                    if p.name.startswith("TRAIN-"):
                        break
                    p = p.parent
        
                # Step 2: search for the directory whose parent is TRAIN-X
                # IMPORTANT: include the starting directory itself
                for parent in (start,) + tuple(start.parents):
                    if parent.parent == p:
                        return parent
        
                raise RuntimeError("Could not determine SEQ folder")
        
            def main():
                current_dir = Path(os.getcwd())
        
                # 1. Split the current path and locate "5_TRAINING"
                parts = current_dir.parts
        
                if "5_TRAINING" not in parts:
                    raise RuntimeError("Could not find '5_TRAINING' in the current path.")
        
                idx = parts.index("5_TRAINING")
        
                # system_name = directory immediately after 5_TRAINING
                try:
                    system_name = parts[idx + 1]
                except IndexError:
                    raise RuntimeError("'5_TRAINING' has no child directory in the path.")
        
                # 2. Robust SEQ folder detection
                seq_dir = find_seq_folder(current_dir)
                leaf_dir = seq_dir.name
        
                # 3. Parent directory above 5_TRAINING
                parent_dir = os.sep.join(parts[:idx]) or os.sep
        
                # 4. Build destination path: 6_MODELS / system_name / leaf_dir
                models_root = os.path.join(parent_dir, "6_MODELS")
                models_dir = os.path.join(models_root, system_name, leaf_dir)
                os.makedirs(models_dir, exist_ok=True)
        
                # 5. Recursively find all .model files under current directory
                model_files = glob.glob(os.path.join(str(current_dir), "**", "*.model"), recursive=True)
        
                # 6. Copy .model files into the new models_dir
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
