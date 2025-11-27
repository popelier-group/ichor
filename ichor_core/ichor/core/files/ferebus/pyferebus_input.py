import textwrap
from pathlib import Path
from string import Template
from typing import Optional, Union

from ichor.core.files.file import File, WriteFile


class PyFerebusScript(WriteFile, File):
    _filetype = ".py"

    def __init__(
        self,
        path: Union[Path, str],
        jd_file: Optional[str] = None,
        submit_to_compute_node: bool = False,
        working_directory: Optional[str] = None,
        move_dataset_files: bool = False,
        platform: Optional[str] = None,
        overwrite_wd: bool = True,
        ncores: Optional[int] = None,
        ntasks: Optional[str] = None,
        rerun: bool = False,
        wall_time: Optional[int] = None,
        training: Optional[int] = None,
        validation: Optional[int] = None,
        nil_test: Optional[int] = None,
        kernel: Optional[str] = None,
        prefactor: Optional[float] = None,
        kpm: Optional[int] = None,
        population_props: bool = False,
        max_iter: Optional[int] = None,
        nagents: Optional[int] = None,
        nluckyagents: Optional[int] = None,
        update_freq: Optional[int] = None,
        max_damping: Optional[float] = None,
        min_damping: Optional[float] = None,
        min_theta: Optional[float] = None,
        max_theta: Optional[float] = None,
        min_wn: Optional[str] = None,
        max_wn: Optional[str] = None,
        a_decay_factor: Optional[float] = None,
        loss: Optional[str] = None,
        huber_delta: Optional[float] = None,
        mean_type: Optional[int] = None,
        is_constant_noise: bool = True,
        stagnation_check_point: Optional[float] = None,
        cmean_range_factor: Optional[float] = None,
        overwrite_stout: bool = True,
        max_reg_weight: Optional[float] = None,
        reg_noise: Optional[float] = None,
        batch_size: Optional[int] = None,
        weights_lambda: Optional[float] = None,
        gwo_cycles: Optional[int] = None,
        elitism: Optional[int] = None,
        transfer_learning: bool = True,
        split_method: Optional[str] = None,
        split_ratio: Optional[float] = None,
        relax_weight: Optional[float] = None,
        multi_source: bool = False,
        nsources: Optional[int] = None,
        full_seeding: bool = True,
        seed_rng: bool = False,
        path_to_executeable: Optional[Path] = None,
    ):
        File.__init__(self, path)

        self.jd_file: str = jd_file
        self.submit_to_compute_node: bool = submit_to_compute_node
        self.working_directory: str = working_directory
        self.move_dataset_files: bool = move_dataset_files
        self.platform: str = platform
        self.overwrite_wd: bool = overwrite_wd
        self.ncores: int = ncores
        self.ntasks: str = ntasks
        self.rerun: bool = rerun
        self.wall_time: int = wall_time
        self.training: int = training
        self.validation: int = validation
        self.nil_test: int = nil_test
        self.kernel: str = kernel
        self.prefactor: float = prefactor
        self.kpm: int = kpm
        self.population_props: bool = population_props
        self.max_iter: int = max_iter
        self.nagents: int = nagents
        self.nluckyagents: int = nluckyagents
        self.update_freq: int = update_freq
        self.max_damping: float = max_damping
        self.min_damping: float = min_damping
        self.min_theta: float = min_theta
        self.max_theta: float = max_theta
        self.min_wn: str = min_wn
        self.max_wn: str = max_wn
        self.a_decay_factor: float = a_decay_factor
        self.loss: str = loss
        self.huber_delta: float = huber_delta
        self.mean_type: int = mean_type
        self.is_constant_noise: bool = is_constant_noise
        self.stagnation_check_point: float = stagnation_check_point
        self.cmean_range_factor: float = cmean_range_factor
        self.overwrite_stout: bool = overwrite_stout
        self.max_reg_weight: float = max_reg_weight
        self.reg_noise: float = reg_noise
        self.batch_size: int = batch_size
        self.weights_lambda: float = weights_lambda
        self.gwo_cycles: int = gwo_cycles
        self.elitism: int = elitism
        self.transfer_learning: bool = transfer_learning
        self.split_method: str = split_method
        self.split_ratio: float = split_ratio
        self.relax_weight: float = relax_weight
        self.multi_source: bool = multi_source
        self.nsources: int = nsources
        self.full_seeding: bool = full_seeding
        self.seed_rng: bool = seed_rng
        self.path_to_executeable: Path = path_to_executeable

    # def machine(self) -> str:
    # """Returns the machine as set in config .yaml file"""

    # return get_param_from_config(
    #     ichor.hpc.global_variables.ICHOR_CONFIG,
    #     ichor.hpc.global_variables.MACHINE,
    # )

    def set_write_defaults_if_needed(
        self,
    ):

        self.jd_file = self.jd_file or "job-details"
        self.submit_to_compute_node = self.submit_to_compute_node or True
        self.working_directory = self.working_directory or None
        self.move_dataset_files = self.move_dataset_files or False
        self.platform = self.platform or "CSF4"
        self.overwrite_wd = self.overwrite_wd or True
        self.ncores = self.ncores or 20
        self.ntasks = self.ntasks or None
        self.rerun = self.rerun or False
        self.wall_time = self.wall_time or 1
        self.training = self.training or 1
        self.validation = self.validation or 1
        self.nil_test = self.nil_test or 0
        self.kernel = self.kernel or "rbfc_per"
        self.prefactor = self.prefactor or 1.0
        self.kpm = self.kpm or 2
        self.population_props = self.population_props or False
        self.max_iter = self.max_iter or 100
        self.nagents = self.nagents or 50
        self.nluckyagents = self.nluckyagents or 5
        self.update_freq = self.update_freq or 10
        self.max_damping = self.max_damping or 2.0
        self.min_damping = self.min_damping or 0.0
        self.min_theta = self.min_theta or 0.0
        self.max_theta = self.max_theta or 0.1
        self.min_wn = self.min_wn or "1.0E-10"
        self.max_wn = self.max_wn or "1.0E-4"
        self.a_decay_factor = self.a_decay_factor or 5.0
        self.loss = self.loss or "mse"
        self.huber_delta = self.huber_delta or 0.05
        self.mean_type = self.mean_type or 21
        self.is_constant_noise = self.is_constant_noise or True
        self.stagnation_check_point = self.stagnation_check_point or 1.2
        self.cmean_range_factor = self.cmean_range_factor or 5.0
        self.overwrite_stout = self.overwrite_stout or True
        self.max_reg_weight = self.max_reg_weight or 40000.0
        self.reg_noise = self.reg_noise or 1.0e-4
        self.batch_size = self.batch_size or 250
        self.weights_lambda = self.weights_lambda or 1.0e-10
        self.gwo_cycles = self.gwo_cycles or 1
        self.elitism = self.elitism or 1
        self.transfer_learning = self.transfer_learning or True
        self.split_method = self.split_method or "random"
        self.split_ratio = self.split_ratio or 0.25
        self.relax_weight = self.relax_weight or 0.20
        self.multi_source = self.multi_source or False
        self.nsources = self.nsources or 1
        self.full_seeding = self.full_seeding or True
        self.seed_rng = self.seed_rng or False
        self.path_to_executeable = self.path_to_executeable or None

    # write file from a template
    def _write_file(self, path: Path, *args, **kwargs):
        self.set_write_defaults_if_needed()

        # set up template for polus script
        pyferebus_script_template = Template(
            textwrap.dedent(
                """
        from pyferebus.executors.trainer import MODEL

        JOB = MODEL(
            jdFile="$jd_file",
            submitToComputeNode=$submit_to_compute_node,
            workingDirectory=$working_directory,
            moveDatasetFiles=$move_dataset_files,
            platform="$platform",
            overwriteWD=$overwrite_wd,
            ncores=$ncores,
            ntasks=$ntasks,
            rerun=$rerun,
            wallTime=$wall_time,
            training=$training,
            validation=$validation,
            nilTest=$nil_test,
            kernel="$kernel",
            prefactor=$prefactor,
            KPM=$kpm,
            populationProps=$population_props,
            maxiter=$max_iter,
            nagents=$nagents,
            nluckyagents=$nluckyagents,
            updatefreq=$update_freq,
            maxdamping=$max_damping,
            mindamping=$min_damping,
            mintheta=$min_theta,
            maxtheta=$max_theta,
            minWN="$min_wn",
            maxWN="$max_wn",
            adecayfactor=$a_decay_factor,
            loss="$loss",
            huber_delta=$huber_delta,
            meanType=$mean_type,
            is_constant_noise=$is_constant_noise,
            stagnationCheckPoint=$stagnation_check_point,
            cmeanRangeFactor=$cmean_range_factor,
            overwritestdout=$overwrite_stout,
            max_reg_weight=$max_reg_weight,
            regNoise=$reg_noise,
            batch_size=$batch_size,
            weights_lambda=$weights_lambda,
            gwo_cycles=$gwo_cycles,
            elitism=$elitism,
            transfer_learning=$transfer_learning,
            split_method="$split_method",
            split_ratio=$split_ratio,
            relax_weight=$relax_weight,
            multisource=$multi_source,
            nsources=$nsources,
            full_seeding=$full_seeding,
            seedRNG=$seed_rng,
            pathToExecutable=$path_to_executeable
        )

        JOB.run()
        """
            )
        )

        # subsitute template values into script
        script_text = pyferebus_script_template.substitute(
            jd_file=self.jd_file,
            submit_to_compute_node=self.submit_to_compute_node,
            working_directory=self.working_directory,
            move_dataset_files=self.move_dataset_files,
            platform=self.platform,
            overwrite_wd=self.overwrite_wd,
            ncores=self.ncores,
            ntasks=self.ntasks,
            rerun=self.rerun,
            wall_time=self.wall_time,
            training=self.training,
            validation=self.validation,
            nil_test=self.nil_test,
            kernel=self.kernel,
            prefactor=self.prefactor,
            kpm=self.kpm,
            population_props=self.population_props,
            max_iter=self.max_iter,
            nagents=self.nagents,
            nluckyagents=self.nluckyagents,
            update_freq=self.update_freq,
            max_damping=self.max_damping,
            min_damping=self.min_damping,
            min_theta=self.min_theta,
            max_theta=self.max_theta,
            min_wn=self.min_wn,
            max_wn=self.max_wn,
            a_decay_factor=self.a_decay_factor,
            loss=self.loss,
            huber_delta=self.huber_delta,
            mean_type=self.mean_type,
            is_constant_noise=self.is_constant_noise,
            stagnation_check_point=self.stagnation_check_point,
            cmean_range_factor=self.cmean_range_factor,
            overwrite_stout=self.overwrite_stout,
            max_reg_weight=self.max_reg_weight,
            reg_noise=self.reg_noise,
            batch_size=self.batch_size,
            weights_lambda=self.weights_lambda,
            gwo_cycles=self.gwo_cycles,
            elitism=self.elitism,
            transfer_learning=self.transfer_learning,
            split_method=self.split_method,
            split_ratio=self.split_ratio,
            relax_weight=self.relax_weight,
            multi_source=self.multi_source,
            nsources=self.nsources,
            full_seeding=self.full_seeding,
            seed_rng=self.seed_rng,
            path_to_executeable=self.path_to_executeable,
        )

        return script_text
