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

    # write file from a template
    def _write_file(self, path: Path, *args, **kwargs):

        # set up template for polus script
        diversity_script_template = Template(
            textwrap.dedent(
                """
            import os
            import shutil
            import glob
            import sys

            def main():
                current_dir = os.getcwd()
                workdir = os.path.abspath(os.path.join(current_dir, "../../"))

                # models directory (create if it doesn't exist)
                models_dir = os.path.join(workdir, "models")
                os.makedirs(models_dir, exist_ok=True)

                # recursively find all .model files under current directory
                model_files = glob.glob(os.path.join(workdir, "**", "*.model"), recursive=True)

                # copy all .model files into models_dir
                for file_path in model_files:
                    shutil.copy(file_path, models_dir)


            if __name__ == "__main__":
                main()

        """
            )
        )

        return script_text
