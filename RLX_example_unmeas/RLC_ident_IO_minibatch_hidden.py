import pandas as pd
import numpy as np
import torch
import torch.optim as optim
import time
import matplotlib.pyplot as plt
import os
import sys
import scipy.linalg

sys.path.append(os.path.join(".."))
from torchid.iofitter import NeuralIOSimulator
from torchid.util import RunningAverageMeter
from torchid.iomodels import NeuralIOModel
from torchid.util import get_torch_regressor_mat

if __name__ == '__main__':

    COL_T = ['time']
    COL_X = ['V_C', 'I_L']
    COL_U = ['V_IN']
    COL_Y = ['V_C']
    df_X = pd.read_csv(os.path.join("data", "RLC_data_sat_FE.csv"))

    t = np.array(df_X[COL_T], dtype=np.float32)
    y = np.array(df_X[COL_Y], dtype=np.float32)
    x = np.array(df_X[COL_X], dtype=np.float32)
    u = np.array(df_X[COL_U], dtype=np.float32)

    N = np.shape(y)[0]
    Ts = t[1] - t[0]
    t_fit = 2e-3
    n_fit = int(t_fit//Ts)#x.shape[0]
    num_iter = 10
    test_freq = 1

    n_a = 2 # autoregressive coefficients for y
    n_b = 2 # autoregressive coefficients for u
    n_max = np.max((n_a, n_b)) # delay

    # Batch learning parameters
    seq_len = 100  # int(n_fit/10)
    batch_size = (n_fit - n_a) // seq_len

    std_noise_V = 0.0 * 5.0
    std_noise_I = 0.0 * 0.5
    std_noise = np.array([std_noise_V, std_noise_I])

    x_noise = np.copy(x) + np.random.randn(*x.shape)*std_noise
    x_noise = x_noise.astype(np.float32)
    y_noise = x_noise[:,[0]]

    # Build fit data
    u_fit = u[0:n_fit]
    y_fit = y[0:n_fit]
    y_meas_fit = y_noise[0:n_fit]

    h_fit = np.copy(y_meas_fit)
    h_fit = np.vstack((np.zeros(n_a).reshape(-1, 1), h_fit)).astype(np.float32)
    v_fit = np.copy(u_fit)
    v_fit = np.vstack((np.zeros(n_b).reshape(-1, 1), v_fit)).astype(np.float32)

    phi_fit_y = scipy.linalg.toeplitz(h_fit, h_fit[0:n_a])[n_max - 1:-1, :] # regressor 1
    phi_fit_u = scipy.linalg.toeplitz(v_fit, v_fit[0:n_a])[n_max - 1:-1, :]
    phi_fit = np.hstack((phi_fit_y, phi_fit_u))

    # To pytorch tensors
    phi_fit_u_torch = torch.tensor(phi_fit_u)
    h_fit_torch = torch.tensor(h_fit, requires_grad=True) # this is an optimization variable!
    phi_fit_y_torch = get_torch_regressor_mat(h_fit_torch.view(-1), n_a)
    y_meas_fit_torch = torch.tensor(y_meas_fit)
    u_fit_torch = torch.tensor(u_fit)

    # Setup model an simulator
    io_model = NeuralIOModel(n_a=n_a, n_b=n_b, n_feat=64)
    io_solution = NeuralIOSimulator(io_model)
    #io_solution.io_model.load_state_dict(torch.load(os.path.join("models", "model_IO_1step_nonoise.pkl")))
    params = list(io_solution.io_model.parameters()) + [h_fit_torch]
    optimizer = optim.Adam(params, lr=1e-4)
    end = time.time()
    loss_meter = RunningAverageMeter(0.97)


    def get_batch(batch_size, seq_len):
        num_train_samples = y_meas_fit_torch.shape[0]
        batch_s = np.random.choice(np.arange(num_train_samples - seq_len, dtype=np.int64), batch_size, replace=False) # batch start indices
        batch_idx = batch_s[:, np.newaxis] + np.arange(seq_len) # batch all indices
        batch_y_seq = phi_fit_y_torch[batch_s]
        batch_u_seq = phi_fit_u_torch[batch_s]
        batch_y_meas = y_meas_fit_torch[batch_idx]
        batch_u = u_fit_torch[batch_idx]
        batch_h = h_fit_torch[batch_idx]
        return batch_u, batch_y_meas, batch_h, batch_y_seq, batch_u_seq, batch_s

    with torch.no_grad():
        batch_u, batch_y_meas, batch_h, batch_y_seq, batch_u_seq, batch_s = get_batch(batch_size, seq_len)
        batch_y_pred = io_solution.f_sim_minibatch(batch_u, batch_y_seq, batch_u_seq)
        err = batch_y_meas[:, 0:, :] - batch_y_pred[:, 0:, :]
        loss = torch.mean((err) ** 2)
        loss_scale = np.float32(loss)

    ii = 2
    for itr in range(0, num_iter):
        print('a')
        optimizer.zero_grad()
        
        phi_fit_y_torch = get_torch_regressor_mat(h_fit_torch.view(-1), n_a)

        # Predict
        batch_u, batch_y_meas, batch_h, batch_y_seq, batch_u_seq, batch_s = get_batch(batch_size, seq_len)
        batch_y_pred = io_solution.f_sim_minibatch(batch_u, batch_y_seq, batch_u_seq)

        # Compute loss
        err_consistency = batch_y_pred[:,:,:] - batch_h[:,:,:]
        loss_consistency = torch.mean((err_consistency)**2)/loss_scale

        err_fit = batch_y_pred[:,:,:] - batch_y_meas[:,:,:]
        loss_fit = torch.mean((err_fit)**2)/loss_scale

        loss = loss_consistency + loss_fit

        # Optimization step
        loss.backward()
        optimizer.step()

        loss_meter.update(loss.item())

        # Print message
        if itr % test_freq == 0:
            print('Iter {:04d} | Total Loss {:.6f}'.format(itr, loss.item()))
            ii += 1
            #with torch.no_grad():
                #y_pred_torch = io_solution.f_onestep(phi_fit_torch) #func(x_true_torch, u_torch)
                #err = y_pred_torch - y_meas_fit_torch[n_max:, :]
                #loss = torch.mean((err) ** 2)  # torch.mean(torch.sq(batch_x[:,1:,:] - batch_x_pred[:,1:,:]))
                #print('Iter {:04d} | Total Loss {:.6f}'.format(itr, loss.item()))
                #ii += 1
        end = time.time()

    if not os.path.exists("models"):
        os.makedirs("models")
