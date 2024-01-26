from pathlib import Path

from ichor.core.files.file import WriteFile


class DlPolyControl(WriteFile):
    """Write out a DLPoly CONTROL file. The name of the file needs to be CONTROL,  so DL POLY knows to use it.
    The default Control file is made to be used for geometry optimizations at very low temperatures. Settings must be
    changed to write out a file for water box simulations for example.
    """

    # https://www.ehu.eus/sgi/ARCHIVOS/dlpoly_man.pdf , section 5.1.1

    def __init__(
        self,
        path: Path,
        system_name: str = None,
        ensemble: str = "nvt",
        thermostat: str = "hoover",
        thermostat_settings: list = [0.04],
        temperature: int = 1,
        timestep=0.001,
        steps=500,
        scale=100,
        cutoff=8.0,
        rvwd=8.0,
        dump=1000,
        trajectory_i=0,
        trajectory_j=1,
        trajectory_k=0,
        print_every=1,
        stats_every=1,
        job_time=10000000,
        close_time=20000,
    ):

        super().__init__(path)

        self.system_name = system_name
        self.ensemble = ensemble
        self.thermostat = thermostat
        self.thermostat_settings = thermostat_settings
        self.temperature = temperature
        self.timestep = (timestep,)
        self.steps = steps
        self.scale = scale
        self.cutoff = cutoff
        self.rvdw = rvwd
        self.dump = dump
        self.trajectory_i = trajectory_i
        self.trajectory_j = trajectory_j
        self.trajectory_k = trajectory_k
        self.print_every = print_every
        self.stats_every = stats_every
        self.job_time = job_time
        self.close_time = close_time

    # TODO: implement reading for dlpoly control file
    # def _read_file(self):
    #     ...

    def _write_file(self):

        write_str = ""

        write_str += f"Title: {self.system_name}\n"
        write_str += "\n"
        # ensemble nvt hoover f select NVT ensemble, type Nose-Hoover with thermostat
        # relaxation constant f in ps
        str_thermostat_settings = " ".join([i for i in self.thermostat_settings])
        write_str += (
            f"ensemble {self.ensemble} {self.thermostat} {str_thermostat_settings}\n"
        )
        write_str += "\n"
        write_str += f"temperature {self.temperature}\n"
        write_str += "\n"
        write_str += "\n"
        # timestep in ps
        write_str += f"timestep {self.timestep}\n"
        # number of timesteps
        write_str += f"steps {self.steps}\n"
        # rescale system temperature every n steps during equilibration
        write_str += f"scale {self.scale}\n"
        write_str += "\n"
        write_str += f"cutoff  {self.cutoff}\n"
        write_str += f"rvdw    {self.rvdw}\n"
        write_str += "vdw direct\n"
        write_str += "vdw shift\n"
        write_str += "fflux cluster L1\n"
        write_str += "\n"
        write_str += f"dump  {self.dump}\n"
        write_str += (
            f"traj {self.trajectory_i} {self.trajectory_j} {self.trajectory_k}\n"
        )
        write_str += f"print every {self.print_every}\n"
        write_str += f"stats every {self.stats_every}\n"
        write_str += "fflux print 0 1\n"
        write_str += f"job time {self.job_time}\n"
        write_str += f"close time {self.close_time}\n"
        write_str += "finish\n"

        return write_str
