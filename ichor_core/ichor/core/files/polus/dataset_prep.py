import textwrap
from pathlib import Path
from string import Template
from typing import Optional, Union

from ichor.core.files.file import File, WriteFile


def _one_size(size, default: int) -> int:
    """Returns the size of the validation or the test set as one number.

    The script splits the geometries into a training, a validation and a test set of
    given sizes, and works out whether those three fit in the geometries there are, so
    each of them has to be a number rather than a list of them. A list of one is still
    accepted, as that is what the sampler itself is given.

    :param size: The size which was asked for, or None for the default.
    :param default: The size to use when none was asked for.
    """

    if size is None:
        return default

    if isinstance(size, (list, tuple)):
        return int(size[0]) if size else default

    return int(size)


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
        val_size: Optional[int] = None,
        test_size: Optional[int] = None,
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
        # one size each, unlike the training set, which is written out at every size it
        # is given so that the models can be compared across them
        self.val_size: Optional[int] = val_size
        self.test_size: Optional[int] = test_size

    def set_write_defaults_if_needed(
        self,
    ):
        self.train_size = self.train_size or [1000]
        self.outlier_prop = self.outlier_prop or "iqa"
        self.outlier_method = self.outlier_method or "extrZS"
        self.system_name = self.system_name or "molecule"
        self.q00_threshold = self.q00_threshold or 0.005
        self.props = self.props or '["iqa"]'
        self.val_size = _one_size(self.val_size, 250)
        self.test_size = _one_size(self.test_size, 1000)

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
            VALID = $valid_size
            TEST = $test_size
            OUT = "DATASETS"
            # where the q00 filter leaves the geometries which came through it
            FILTERED_DIR = os.path.join(cwd, "filtered", "FILTERED-BY-Q00")


            def geometries_in(directory):
                \"\"\"How many geometries a folder of per-atom csv files holds.

                Every csv in it has one row per geometry (and one header row), and every
                atom has the same geometries, so the rows of the first file are the count.
                \"\"\"

                for name in sorted(os.listdir(directory)):
                    path = os.path.join(directory, name)
                    if not os.path.isfile(path):
                        continue
                    with open(path) as csv_file:
                        return max(0, sum(1 for _ in csv_file) - 1)

                return 0


            def sizes_which_fit(train, valid, test, available):
                \"\"\"Scales the three set sizes down, in proportion, until they fit in the
                geometries there are.

                The outlier filter and the q00 filter both throw geometries out before
                anything is split up, so what the sizes were chosen against (the geometries
                in the csv files) is more than what the sampler is left with. The three sets
                are taken one after another out of the same pool, so what has to fit is
                their total: asking for more than that gets no error from the sampler, it
                simply slices past the end of what it has and the last set comes back short
                or empty.

                Scaling in proportion keeps the split the sizes were asked for (a 50/20/20
                split of 900 geometries stays a 50/20/20 split when only 850 come through
                the filters) rather than taking the shortfall out of one set.
                \"\"\"

                requested = train + valid + test
                if requested <= available:
                    return train, valid, test

                if available < 3:
                    raise ValueError(
                        "Only %d geometries came through the outlier and q00 filters, "
                        "which is not enough for a training, a validation and a test set. "
                        "Loosen the q00 threshold or calculate more geometries."
                        % available
                    )

                factor = available / requested
                scaled = [max(1, int(size * factor)) for size in (train, valid, test)]
                # flooring each of them can still leave the total a geometry or two over,
                # which comes off the largest set as that is the one it shows least in
                while sum(scaled) > available:
                    scaled[scaled.index(max(scaled))] -= 1

                return tuple(scaled)

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

            available = geometries_in(FILTERED_DIR)
            print("POLUS: Geometries left after filtering  %d" % available)

            # each training set size is a split of its own, so each of them is scaled
            # against the geometries there are on its own as well
            already_written = []
            for train_size in TRAIN:

                train, valid, test = sizes_which_fit(train_size, VALID, TEST, available)

                if (train, valid, test) != (train_size, VALID, TEST):
                    print(
                        "POLUS: Sizes %d/%d/%d need %d geometries but only %d came "
                        "through the filters, so they were scaled to %d/%d/%d "
                        "(train/valid/test)"
                        % (
                            train_size, VALID, TEST, train_size + VALID + TEST,
                            available, train, valid, test,
                        )
                    )

                # two requested sizes can scale to the same one, which would otherwise
                # mean the second split overwriting the first
                if (train, valid, test) in already_written:
                    print(
                        "POLUS: Skipping a training set size of %d, as it scales to the "
                        "same %d/%d/%d split as one which has already been written"
                        % (train_size, train, valid, test)
                    )
                    continue
                already_written.append((train, valid, test))

                outdir = os.path.join(OUT,"TRAIN-"+str(train))
                job4=SeqSampler(
                    inputDir=FILTERED_DIR,
                    valTest=$val_test,
                    allProps=$all_props,
                    randomSelect=$random_select,
                    fromBottom=$from_bottom,
                    props=$props,
                    systemName="$system_name",
                    outputDir=outdir,
                    trainSize=train,
                    validSize=[valid],
                    testSize=[test]
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
