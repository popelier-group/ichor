import textwrap
from pathlib import Path
from string import Template
from typing import Union

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
        extract_models_script_template = Template(
            textwrap.dedent(
                """
            import os
            import shutil
            import glob
            from pathlib import Path

            # progress bars, with a no-op fallback if tqdm is unavailable
            try:
                from tqdm import tqdm
            except ImportError:
                def tqdm(iterable, **kwargs):
                    return iterable

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
                #    (walked with a progress bar so it does not look frozen)
                model_files = []
                for dirpath, _dirnames, filenames in tqdm(os.walk(current_dir), desc="Finding model files"):
                    for fname in filenames:
                        if fname.endswith(".model"):
                            model_files.append(os.path.join(dirpath, fname))

                # 6. Copy .model files into the new models_dir
                for file_path in tqdm(model_files, desc="Copying models"):
                    shutil.copy(file_path, models_dir)

                # 7. Also co-locate the held-out CSVs with the models so the set can
                #    be evaluated later without needing 5_TRAINING. External validation
                #    goes to test_set/, internal validation to valid_set/. The
                #    per-property subfolder is preserved because the CSV file names are
                #    identical across properties (the property is only in the folder
                #    name and the CSV column header).
                for set_suffix, dest_name in (
                    ("EXT_VALIDATION_SET", "test_set"),
                    ("INT_VALIDATION_SET", "valid_set"),
                ):
                    csv_pattern = os.path.join(str(current_dir), "**", "*_" + set_suffix + ".csv")
                    csv_files = glob.glob(csv_pattern, recursive=True)
                    for csv_path in tqdm(csv_files, desc="Copying " + set_suffix):
                        prop_name = os.path.basename(os.path.dirname(csv_path))
                        csv_dest_dir = os.path.join(models_dir, dest_name, prop_name)
                        os.makedirs(csv_dest_dir, exist_ok=True)
                        shutil.copy(csv_path, csv_dest_dir)
                    print("Copied " + str(len(csv_files)) + " " + set_suffix + " CSVs into " + dest_name)

                print(f"system_name = {system_name}")
                print(f"leaf_dir = {leaf_dir}")
                print(f"Copied {len(model_files)} model files into: {models_dir}")

            if __name__ == "__main__":
                main()
        """
            )
        )

        script_text = extract_models_script_template.substitute()

        return script_text
