import textwrap
from pathlib import Path
from string import Template
from typing import Optional, Union

from ichor.core.files.file import File, WriteFile


class DatasetPrepScript(WriteFile, File):
    _filetype = ".py"

    def __init__(
        self,
        path: Union[Path, str],
        outlier_input_dir: Union[
            Path,
            str,
        ],
        train_size: Optional[list[int]] = None,
        outlier_prop: Optional[str] = None,
        outlier_method: Optional[str] = None,
        iqa_all_props: bool = True,
        system_name: Optional[str] = None,
        geom_ids: Optional[str] = None,
        q00_threshold: Optional[int] = None,
        val_test: bool = False,
        all_props: bool = False,
        random_select: bool = False,
        from_bottom: bool = True,
        props: Optional[list[str]] = None,
        val_size: Optional[list[int]] = None,
        test_size: Optional[list[int]] = None,
    ):

        File.__init__(self, path)

        self.outlier_input_dir = Path(outlier_input_dir)
        self.train_size: Optional[list[int]] = train_size
        self.outlier_prop: Optional[str] = outlier_prop
        self.outlier_method: Optional[str] = outlier_method
        self.iqa_all_props: bool = iqa_all_props
        self.system_name: Optional[str] = system_name
        self.geom_ids: Optional[str] = geom_ids
        self.q00_threshold: Optional[int] = q00_threshold
        self.val_test: bool = val_test
        self.all_props: bool = all_props
        self.random_select: bool = random_select
        self.from_bottom: bool = from_bottom
        self.props: Optional[list[str]] = props
        self.val_size: Optional[list[int]] = val_size
        self.test_size: Optional[list[int]] = test_size

    def set_write_defaults_if_needed(
        self,
    ):
        self.train_size = self.train_size or [1000]
        self.outlier_prop = self.outlier_prop or "iqa"
        self.outlier_method = self.outlier_method or "extrZS"
        self.system_name = self.system_name or "molecule"
        self.q00_threshold = self.q00_threshold or 0.005
        self.props = (
            self.props
            or f'["iqa","q00","q10","q11c","q11s","q20","q21s","q21c","q22s","q22c"]'
        )
        self.val_size = self.val_size or [250]
        self.test_size = self.test_size or [1000]

    # write file from a template
    def _write_file(self, path: Path, *args, **kwargs):
        self.set_write_defaults_if_needed()

        # set up template for polus script
        dataset_prep_script_template = Template(
            textwrap.dedent(
                """
            from polus.samplers.SEQ.Seq import SeqSampler
            from polus.filters.RecoveryManager import IqaFilter, Q00Filter, DualFilter
            from polus.filters.outliers import Odd
            from polus.filters.iqa_correction import iqa_correct
            from polus.filters.iqa_correction import iqa_correct
            import os
            import shutil

            cwd = os.getcwd()
            TRAIN = $train_size
            OUT = "DATASETS"

            # Outlier removal
            outlier_job = Odd(
                inputDir="$outlier_input_dir",
                outputDir="OUTLIER_CHECK",
                prop="$outlier_prop",
                method = "$outlier_method"
            )
            outlier_job.Execute()

            # IQA correction 
            iqa_corr_job = iqa_correct(
                inputDir="OUTLIER_CHECK",
                allProps=$iqa_all_props,
                system_name="$system_name",
                outputDir=None, 
                working_directory=None,
                geom_IDs=$geom_ids,
            )
            iqa_corr_job.write_raw_and_corrected_atomic_iqa_energies()
            iqa_corr_job.write_corrected_reference_data()

            # Recovery test filter
            q00_job = Q00Filter(
                threshold=$q00_threshold,
                systemName="$system_name",
                inputDir="corr_ref_data"
            )
            q00_job.Execute()

            # Sampling
            if not os.path.isdir(OUT):
                os.mkdir(OUT)
            for train_size in TRAIN:
                outdir = os.path.join(OUT,"TRAIN-"+str(train_size))
                job4=SeqSampler(
                    inputDir=os.path.join(cwd,"filtered/FILTERED-BY-Q00"),
                    valTest=$val_test,
                    allProps=$all_props,
                    randomSelect=$random_select,
                    fromBottom=$from_bottom,
                    props=$props,
                    systemName="$system_name",
                    outputDir=outdir,
                    trainSize=train_size,
                    validSize=[$valid_size],
                    testSize=[$test_size]
                )
                print(job4.inputDir)
                job4.Execute()


        """
            )
        )

        # subsitute template values into script
        script_text = dataset_prep_script_template.substitute(
            train_size=self.train_size,
            outlier_input_dir=self.outlier_input_dir,
            outlier_prop=self.outlier_prop,
            outlier_method=self.outlier_method,
            iqa_all_props=self.iqa_all_props,
            system_name=self.system_name,
            geom_ids=self.geom_ids,
            q00_threshold=self.q00_threshold,
            val_test=self.val_test,
            all_props=self.all_props,
            random_select=self.random_select,
            from_bottom=self.from_bottom,
            props=self.props,
            valid_size=self.val_size,
            test_size=self.test_size,
        )

        return script_text
