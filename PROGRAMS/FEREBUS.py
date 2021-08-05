import numpy as np
import scipy.optimize as op

import george
from george.kernels import ExpSquaredKernel as RBF
from george.kernels import Matern52Kernel as Matern52

import pandas as pd
import time
from sklearn.metrics import mean_absolute_error

import re
from glob import glob
import math
import sys

SYSTEM_NAME = ""

nAtoms = 0
nFeats = 0
kernel_name = "rbf"

starting_properties = 0
nProperties = 0

trainingSetSize = 0
predictionSetSize = 0

Kernel = RBF

multipole_names = ["q00",
                   "q10", "q11c", "q11s",
                   "q20", "q21c", "q21s", "q22c", "q21s"
                   "q30", "q31c", "q31s", "q32c", "q32s", "q33c", "q33s",
                   "q40", "q41c", "q41s", "q42c", "q42s", "q43c", "q43s", "q44c", "q44s"]

log = open("log.txt", "w+")
sys.stdout = log

def readFINPUT():
    global SYSTEM_NAME
    global trainingSetSize
    global nProperties
    global predictionSetSize
    global starting_properties
    global kernel_name
    global nAtoms
    global nFeats
    global Kernel

    with open("FINPUT.txt", "r") as f:
        lines = f.readlines()

        SYSTEM_NAME = lines[0].strip()
        for line in lines[1:]:
            if line.startswith("natoms") and not nAtoms:
                nAtoms = int(re.findall("\d+", line)[0])
            elif line.startswith("starting_properties") and not starting_properties:
                starting_properties = int(re.findall("\d+", line)[0])
            elif line.startswith("nproperties") and not nProperties:
                nProperties = int(re.findall("\d+", line)[0])
            elif line.startswith("full_training_set") and not trainingSetSize:
                trainingSetSize = int(re.findall("\d+", line)[0])
            elif line.startswith("predictions") and not predictionSetSize:
                predictionSetSize = int(re.findall("\d+", line)[0])
            elif line.startswith("kernel"):
                kernel_name = line.split()[1]
        
        if starting_properties > 0:
            starting_properties -= 1
        if not nProperties:
            nProperties = 1
        if kernel_name == "rbf":
            Kernel = RBF
        elif kernel_name == "matern5" or kernel_name == "matern52":
            Kernel = Matern52
        nFeats = 3*nAtoms - 6

def print_params(params):
            print("GP Params:")
            for param in params:
                print("\t%.12f" % param)

def get_last_line(a):
    line = " "
    for i in a:
        if i != 0:
            line += "%18.12f  " % i
    return line.rstrip() + "\n"

def writeModelFile(gp, moment, atom, trainX_data, trainY_data):
    global SYSTEM_NAME

    atom_num = re.findall("\d+", atom)[0]
    model_fname = SYSTEM_NAME + "_kriging_" + moment + "_" + atom_num.zfill(2) + ".txt"

    params = gp.get_parameter_vector()
    mu = params[0]
    thetas = params[1:]

    if kernel_name == "rbf":
        thetas = 1/(2.0 * np.exp(thetas))
    else:
        thetas = 1/np.exp(thetas)

    p_values = [2.0] * len(thetas)

    cov_mat = gp.get_matrix(trainX_data)
    y_minus_mean = trainY_data - gp.mean.value*np.ones(len(trainY_data))
    weights = np.linalg.solve(cov_mat,y_minus_mean)

    invR = np.linalg.inv(cov_mat)

    if (trainingSetSize**2)%3 != 0:
        invR = invR.flatten()
        invR.resize(3 * math.ceil(len(invR)/3))
    invR = invR.reshape((math.ceil(trainingSetSize**2/3), 3))

    trainX = trainX_data.values
    if (trainingSetSize*nFeats)%3 != 0:
        trainX = trainX.flatten()
        trainX.resize(3 * math.ceil(len(trainX)/3))
    trainX = trainX.reshape((math.ceil(trainingSetSize*nFeats/3), 3))

    with open(model_fname, "w+") as f:
        f.write(" Kriging results and parameters: %s\n" % kernel_name)
        f.write(" ;\n")
        f.write(" Feature%12d\n" % nFeats)
        f.write(" Number_of_training_points%12d\n" % trainingSetSize)
        f.write(" ;\n")
        f.write(" Mu  %16.12f      Sigman_Squared  1.0000E-03\n" % mu)
        f.write(" No_Noise\n")
        f.write(" ;\n")
        f.write(" Theta\n")
        for theta in thetas:
            f.write("   %18.16f\n" % theta)
        f.write(" ;\n")
        f.write(" p\n")
        for p in p_values:
            f.write("   %18.16f\n" % p)
        f.write(" ;\n")
        f.write(" Weights\n")
        for weight in weights:
            f.write(" %18.16f\n" % weight)
        f.write(" ;\n")
        f.write(" R_matrix\n")
        f.write(" Dimension%12d\n" % trainingSetSize)
        for line in invR[:-1]:
            f.write(" %18.12f  %18.12f  %18.12f\n" % tuple(line))
        f.write(get_last_line(invR[-1]))
        f.write(" ;\n")
        f.write(" Property_value_Kriging_centers\n")
        for y in trainY_data:
            f.write(" %18.16f\n" % y)
        f.write(" training_data\n")
        for x in trainX[:-1]:
            f.write(" %18.12f  %18.12f  %18.12f\n" % tuple(x))
        f.write(get_last_line(trainX[-1]))
        f.write(" ;\n")
    print("Wrote Output To: %s" % model_fname)

def writePyModelFile(gp, atom, trainX_data, trainY_data):
    np.savetxt("trainX_data.csv", trainX_data, delimiter=",")
    np.savetxt("trainY_data.csv", trainY_data, delimiter=",")
    np.savetxt("params.csv", gp.get_parameter_vector(), delimiter=",")
    np.savetxt("mu.csv", np.array(gp.mean.value), delimiter=",")

def writePredictionsFile(log_likelihood, atom, moment, testY_data, predictions, mse_values):
    global SYSTEM_NAME

    fname = SYSTEM_NAME + "_kriging_" + atom + "_" + moment + "_PREDICTIONS.txt"
    errors = np.absolute(testY_data-predictions)
    with open(fname, "w+") as f:
        f.write(" Optimised Log Likelihood\n")
        f.write(" %18.12f\n\n" % log_likelihood)
        f.write(" Normalised %s values:\n" % moment)
        f.write("        Actual              Predicted                Abs err              MSE\n")
        for actual, predicted, abs_err, mse in zip(testY_data, predictions, errors, mse_values):
            f.write("%16.8f%21.8f%21.9f%21.9f\n" % (actual, predicted, abs_err, mse))

def trainGP(fname):
    global trainingSetSize
    global nProperties
    global predictionSetSize
    global nFeats
    global Kernel

    atom = fname.split("_")[0]

    training_set = pd.read_csv(fname, header=None, delim_whitespace=True)
    print("Read Training Set: %s" % fname)
    print(training_set.head())
    print()

    trainX = training_set.iloc[:trainingSetSize,:nFeats]
    testX = training_set.iloc[trainingSetSize:trainingSetSize+predictionSetSize, :nFeats]

    params = [1.0] * nFeats
    kernel =  Kernel(params, ndim=nFeats)

    for prop in range(starting_properties, nProperties):
        moment = multipole_names[prop]
        print("Training Atom %s for moment: %s" % (atom, moment))
        trainY = training_set.iloc[:trainingSetSize,nFeats + prop]

        gp = george.GP(kernel, mean=np.mean(trainY), fit_mean=True, white_noise=np.log(1e-30), fit_white_noise=False)
        gp.compute(trainX)

        # Define the objective function (negative log-likelihood in this case).
        def nll(p):
            gp.set_parameter_vector(p)
            ll = gp.log_likelihood(trainY, quiet=True)
            return -ll if np.isfinite(ll) else 1e25

        # And the gradient of the objective function.
        def grad_nll(p):
            gp.set_parameter_vector(p)
            return -gp.grad_log_likelihood(trainY, quiet=True)

        start_time = time.time()
        # Run the optimization routine.
        p0 = gp.get_parameter_vector()
        print_params(gp.get_parameter_vector())
        results = op.minimize(nll, gp.get_parameter_vector(), method = "BFGS", jac=grad_nll)

        print()

        # Update the kernel and print the final log-likelihood.
        gp.set_parameter_vector(results.x)
        gp.recompute()
        print_params(gp.get_parameter_vector())
        print()
        print("Training Time: %.2fs" % (time.time() - start_time))

        writeModelFile(gp, moment, atom, trainX, trainY)
        # writePyModelFile(gp, atom, trainX, trainY)
        print()

        if predictionSetSize > 0:
            testY = training_set.iloc[trainingSetSize:trainingSetSize+predictionSetSize, nFeats + prop]

            log_likelihood = gp.log_likelihood(trainY, quiet=True)

            preds, var = gp.predict(trainY, testX, return_cov=False, return_var=True)
            writePredictionsFile(log_likelihood, atom, moment, testY, preds, var)

if __name__ == "__main__":
    readFINPUT()
    print("Read FINPUT.txt")
    print("Number of training points: %d" % trainingSetSize)
    print("Number of predictions:     %d" % predictionSetSize)
    print()

    training_sets = glob("*_TRAINING_SET.txt")
    for training_set in training_sets:
        trainGP(training_set)