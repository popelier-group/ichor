# Using ichor's standard auto run

Ichor's auto run is set up to run multiple iterations of the same jobs. For our main use case (standard auto run), we want to run Gaussian, AIMALL, and FEREUBS jobs sequentially in one iteration. The reason why we want to run these programs sequentially is because the output of the programs is required as the input for the next. Once the FEREBUS job is ran, we want to add new points to our training set to make it better (via random/adaptive sampling). We use ichor again to add new points. Additionally, there are several ichor jobs that run between the main Gaussian/AIMALL/FEREBUS jobs that have to do with file management and setting up the jobs that these programs need to run.

## Ways in which ichor can currently run jobs

Ichor can currently submit jobs to the queuing system in three ways:

1. Submitting all jobs for all iterations at once. This has to be done because jobs cannot be submitted only from log-in nodes (submission privileges are not enabled for compute nodes on CSF3). Thus, all jobs for all iterations must be submitted initially before closing the terminal connected to the log-in node. What this means is that ichor needs to change the submission scripts in order to run the correct files for every iteration, thus some additional ichor jobs are needed. This has worked alright in the past, however if doing per-atom models it can lead to a lot of jobs being queued up at the same time (in the order of hundreds of thousands), so it can overload the CSF3 submission system. Thus, we are looking into better ways of submitting files.

2. Submitting jobs for only one iteration. Currently `Drop-In-Compute` is being implemented on CSF3 for our group, where we can submit only one iteration of our jobs into a special folder. There, the jobs will be queued up by the submission system automatically (taking into account jobs that need to hold for other jobs). This will allow us to submit as many adaptive sampling iterations as we want and will drastically reduce the number of queued up jobs on CSF3. This will become the default for jobs submission using ichor on CSF3 once it is implemented fully.

3. `ONLY FOR FFLUXLAB`: This is still ongoing, but since we have admin privileges for ffluxlab, we can change the submission system flags to be able to submit from compute nodes. This will leave us in a similar position to the `Drop-In-Compute`, where we submit jobs for one iteration at a time without having to move files to special folders, etc. that has to be done for `Drop-In-Compute`.


## How ichor's auto run is set up

This is the full set of jobs that must be ran in order to complete one auto run iteration. Once the final adaptive sampling jobs is complete and new points are added to the training set, the next iteration can begin. We define an Enum `IterState` which we can use to set up different jobs on different auto-run iterations. There are three elements of the enum: `First`, `Standard`, and `Last`. We can then run a different set of jobs for each of these states of the auto-run. 

## 1. `IterState.First`
During the first iteration of auto run, we make the initial training set, as well as the validation and sample pool sets. It uses a `.xyz` file that is found in the current directory to make the sets. **This step is only performed once during the first iteration of auto-run.**
The `submit_make_sets_job_to_auto_run` function is ran, which creates a submission script with the name `ICHOR_MAKE_SETS.sh` and submits the submission script to a compute node. **The job id given by the submission system is returned, as following jobs will need to be held while this job finishes.**

This submission script contains an ichor job in which the `make_sets` function from ichor is ran on a compute node. This creates the training set, validation set, and sample pool respectively.

## 2. `IterState.Standard`

Now that we have created our initial sets, we can start running `Standard` auto-run iterations. Each of these `Standard` iterations submits 7 separate jobs, as defined in `func_order`.

```python
func_order = [
    IterStep(
        submit_ichor_gaussian_command_to_auto_run,
        IterUsage.All,
        [IterArgs.TrainingSetLocation],
    ),
    IterStep(
        submit_gaussian_job_to_auto_run, IterUsage.All, [IterArgs.nPoints]
    ),
    IterStep(
        submit_ichor_aimall_command_to_auto_run,
        IterUsage.All,
        [IterArgs.TrainingSetLocation, IterArgs.Atoms],
    ),
    IterStep(
        submit_aimall_job_to_auto_run,
        IterUsage.All,
        [IterArgs.nPoints, IterArgs.Atoms],
    ),
    IterStep(
        make_models,
        IterUsage.All,
        [IterArgs.TrainingSetLocation, IterArgs.Atoms],
    ),
    IterStep(
        submit_ferebus_job_to_auto_run,
        IterUsage.All,
        [IterArgs.FerebusDirectory, IterArgs.Atoms],
    ),
    IterStep(
        submit_ichor_active_learning_job_to_auto_run,
        IterUsage.AllButLast,
        [IterArgs.ModelLocation, IterArgs.SamplePoolLocation],
    ),
]
```

Here are details on what happens in each of the jobs above. The program that runs during each job is given at the beginning.

1. `ichor`. During the first step, the `submit_ichor_gaussian_command_to_auto_run` function is ran. It makes an `ICHOR_GAUSSIAN.sh` submission script to which an ichor command is added. This ichor command will run the `submit_gjfs` function on a compute node on the training set directory. **It is important to node that the `submit_gjfs` function is only used in auto run to write out the datafile - a file containing the input names (paths) of files that need to be ran through Gaussian, as well as the names (paths) of their respective Gaussian output files. `submit_gjfs` will submit the Gaussian jobs if ran from a login node, but since we are calling the function from a compute node, it will not submit any jobs. It will only write out the datafile. The next job is the one that submits the Gaussian jobs (given the datafile that was written in this job).** Finally the job id of this job is returned and the next job is held until this one is finished.

2. `Gaussian`. Now that the datafile is written to disk, we can run a Gaussian job that will run an array job for all the `.gjf` files that were written out in the datafile in the previous step. A submission script with the name `GAUSSIAN.sh` is submitted to the queueing system and is held until the previous job is finished. It runs the Gaussian program on the datafile that was specified in the previous job (the datafile's is the same as `GLOBALS.UID`, this way we can make unique names for every datafile). **It is important to note that a new unique id is set for `GLOBALS.UID` after setting up the submission script file. This means that subsequent files that need to be ran through programs will be written to a new datafile (with the same names as the new `GLOBALS.UID`).** Finally the job id of this job is returned and the next job is held until this one is finished.

3. `ichor`. Now that we have ran our Gaussian jobs and have Gaussian output files, we need to submit these Gaussian output files to AIMALL. To do this, we have to make a new datafile containing the names of the Gaussian outputs. A submission script with the name `ICHOR_AIMALL.sh` is submitted to the queueing system and is held until the previous job is finished. It runs the `submit_wfns` function (defined in ichor) on a compute node on the training set directory. **Again, it is important to note that the `submit_wfns` function is only used to write out the datafile here. Since the function is ran from a compute node, no new jobs are submitted. If `submit_wfns` is ran from a compute node, it will submit the jobs to the queuing system as well.** Finally the job id of this job is returned and the next job is held until this one is finished.

4. `AIMALL`. We have a new datafile (with a new name) containing the paths to the input and output files AIMALL needs to read in/write to. A submission script with the name `AIMALL.sh` is submitted to the queueing system and is held until the previous job is finished. It runs the AIMALL program on the files specified in the datafile (which was written out in the previous step.). **It is important to note that a new unique id is set for `GLOBALS.UID` after setting up the submission script file. This means that subsequent files that need to be ran through programs will be written to a new datafile (with the same names as the new `GLOBALS.UID`).** Finally the job id of this job is returned and the next job is held until this one is finished.

5. `ichor`. Now that we have AIMALL outputs, we must make GP models for topological atoms given the AIMALL output. A submission script with the name `ICHOR_FEREBUS.sh` is submitted to the queueing system and is held until the previous job is finished. This script runs the `make_models` function (defined in ichor) from a compute node. It writes out the datafile FEREBUS needs to make GP models for topological atoms. It also writes out a `.toml` file which contains is a configuration file for FEREBUS. **Again, it is important to note that the `submit_wfns` function is only used to write out the datafile here. Since the function is ran from a compute node, no new jobs are submitted. If `submit_wfns` is ran from a compute node, it will submit the jobs to the queuing system as well.** Finally the job id of this job is returned and the next job is held until this one is finished.

6. `FEREBUS`. After writing out the datafile, we submit a new job called `FEREBUS.sh` which makes the GP models using the FEREBUS program. FEREBUS reads is configuration file from the `.toml` file written in the previous step, as well as the input files from the datafile written in the previous step. **It is important to note that a new unique id is set for `GLOBALS.UID` after setting up the submission script file. This means that subsequent files that need to be ran through programs will be written to a new datafile (with the same names as the new `GLOBALS.UID`).** Finally the job id of this job is returned and the next job is held until this one is finished.

7. `ichor`. After GP models are made with FEREBUS, the program writes out `.model` files which contain parameters and other information needed to make predictions. The final step submits the submission script named `ICHOR_ACTIVE_LEARNING.sh`. In this submission script the function `active_learning` (defined in ichor) is ran. It adds new points from the sample pool to the training set using some kind of `ActiveLearning` method. These methods add points based on some criteria such as variance or expected improvement, but can also be set up to add points randomly to the training set. After this iteration is done, we have added new points to the training set and we can start the next iteration, where we run the new points through Gaussian/AIMALL, etc. using the steps described above. **Note that only the new points need to be ran through Gaussian and AIMALL as we already have the information for the old points. Thus, the datafiles are only going to contain the names (paths) of the new points.** The `.sh` submission scripts are then overwritten to contain the appropriate new datafiles (whose name is set to `GLOBALS.UID`). **This ichor job does not need datafiles, it only uses the `.model` files written out to disk with FEREBUS in the previous step. **Also note that this `IterStep` is not ran on the very last adaptive sampling iteration (`IterUsage` is set to `IterUsage.AllButLast`). This is because we do not want to add a new point to the training set  on the very last step (since it will only be added to the training set, but it will not be ran through Gaussian/AIMALL/FEREBUS because there is no next adaptive sampling itearation.**