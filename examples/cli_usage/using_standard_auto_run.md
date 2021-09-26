# Using ichor's standard auto run

Ichor's auto run is set up to run multiple iterations of the same jobs. For our main use case (standard auto run), we want to run Gaussian, AIMALL, and FEREUBS jobs sequentially in one iteration. The reason why we want to run these programs sequentially is because the output of the programs is required as the input for the next. Once the FEREBUS job is ran, we want to add new points to our training set to make it better (via random/adaptive sampling). We use ichor again to add new points. Additionally, there are several ichor jobs that run between the main Gaussian/AIMALL/FEREBUS jobs that have to do with file management and setting up the jobs that these programs need to run.

## How ichor's auto run is set up

This is the full set of jobs that must be ran in order to complete one auto run iteration. Once the final adaptive sampling jobs is complete and new points are added to the training set, the next iteration can begin.

## 1.

## 2.

## 3.

## 4.

## 5.

## 6.

## 7.
