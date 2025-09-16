import textwrap
from pathlib import Path
from string import Template 
from typing import Optional, Union

from ichor.core.files.file import File, WriteFile


class DiversityScript(WriteFile, File):
    _filetype = ".py"

    def __init__(
        self,
        path: Union[Path, str],
        seed_geom: Union[Path, str],
        output_dir: Union[Path, str],
        filename: Union[Path, str],
        system_name: Optional[str] = None,
        weights_vector: Optional[str] = None,
        group_average: Optional[str] = None,
        write_ferebus_inputs: Optional[bool] = None,
        chunk_size: Optional[int] = None,
        rotate_traj: Optional[bool] = None,
        rot_method: Optional[str] = None,
        parallel: Optional[bool] = None,
        auto_stop: Optional[bool] = None,
        sample_size: Optional[int] = None,
    ):
        File.__init__(self, path)

        self.seed_geom = Path(seed_geom)
        self.output_dir = Path(output_dir)
        self.filename = Path(filename)
        self.system_name: str = system_name
        self.weights_vector: str = weights_vector
        self.group_average: bool = group_average
        self.write_ferebus_inputs: bool = write_ferebus_inputs
        self.chunk_size: int = chunk_size
        self.rotate_traj: bool= rotate_traj
        self.rot_method: str = rot_method
        self.parallel: bool = parallel
        self.auto_stop: bool = auto_stop
        self.sample_size: int = sample_size


    def set_write_defaults_if_needed(
        self,
    ):  
        self.system_name = self.system_name or self.seed_geom.stem
        self.output_dir = self.output_dir or Path.cwd()
        self.weights_vector = self.weights_vector or "HL1:1"
        self.group_average = self.group_average or False
        self.write_ferebus_inputs = self.write_ferebus_inputs or False
        self.chunk_size = self.chunk_size or 500
        self.rotate_traj = self.rotate_traj or True
        self.rot_method = self.rot_method or "KU"
        self.parallel = self.parallel or True
        self.auto_stop = self.auto_stop or False
        self.sample_size = self.sample_size or 10000

    # write file from a template
    def _write_file(self, path: Path, *args, **kwargs):
        self.set_write_defaults_if_needed()

        # set up template for polus script
        polus_script_template = Template(textwrap.dedent("""
        from polus.trajectories.commons import File
        from polus.trajectories.diversity import DIVSampler
        import numpy as np

        job = DIVSampler(
            systemName="$system_name",
            weightsVector="$weights_vector",   
            groupAverage=$group_average,  
            writeFerebusInputs=$write_ferebus_inputs,
            chunkSize=$chunk_size,
            rotateTraj=$rotate_traj,
            rotMethod="$rot_method",                                 
            parallel=$parallel,
            autoStop=$auto_stop,
            seedGeom="$seed_geom",
            outputDir="$output_dir",                                                                                                                                                                     
            filename="$filename",
            sampleSize= "[$sample_size]",                                
        )

        job.Execute()                                                                   
        """))

        # subsitute template values into script
        script_text = polus_script_template.substitute(
            system_name = self.system_name,
            weights_vector = self.weights_vector,
            group_average = self.group_average,
            write_ferebus_inputs = self.write_ferebus_inputs,
            chunk_size = self.chunk_size,
            rotate_traj = self.rotate_traj,
            rot_method = self.rot_method,
            parallel = self.parallel,
            auto_stop = self.auto_stop,
            seed_geom = self.seed_geom,
            output_dir = self.output_dir,
            filename = self.filename,
            sample_size = self.sample_size,
        )

        return(script_text)