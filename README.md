# Efficient Calibration of Embedded MPC

This repository contains the Python code to reproduce the results of the paper "Efficient Calibration of Embedded MPC" by Marco Forgione and Dario Piga

The following fitting methods for State-Space (SS) and Input-Output (IO) neural dynamical models are developed based on

 * One-step prediction error minimization
 * Open-loop simulation error minimization
 * Multistep simulation error minimization

## Example folders: 
The examples performed are the following:

* `` RLC_example``: nonlinear RLC circuit thoroughly discussed in the paper
* `` CSTR_example``: CSTR system from 
* `` cartpole_example``: cart-pole system

For the RLC example, the main scripts are:

 *   ``symbolic_RLC.m``: Symbolic manipulation of the RLC model, constant definition
 * ``RLC_generate_id.py``:  generate the identification dataset 
 * ``RLC_generate_val.py``: generate the validation dataset 
 *  ``RLC_SS_fit_1step.py``: SS model, one-step prediction error minimization
 *  ``RLC_SS_fit_simerror.py``: SS model, open-loop simulation error minimization
 *  ``RLC_SS_fit_multistep.py``: SS model, multistep simulation error minimization
 *  ``RLC_SS_eval_sim.py``: SS model, evaluate the simulation performance of the identified models, produce relevant plots  and model statistics
 *  ``RLC_IO_fit_1step.py``: IO model, one-step prediction error minimization
 *  ``RLC_IO_fit_multistep.py``: IO model, multistep simulation error minimization
 *  ``RLC_IO_eval_sim.py``: IO model, evaluate the simulation performance of the identified models, produce relevant plots  and model statistics
 *   ``RLC_OE_comparison.m``: Linear Output Error (OE) model fit in Matlab
  
Simulations were performed on a Python 3.7 conda environment with

 * numpy
 * scipy
 * matplotlib
 * pandas
 * sympy
 * numba
 * pytorch
 
These dependencies may be installed through the commands:
```
conda install numpy scipy matplotlib pandas
```
