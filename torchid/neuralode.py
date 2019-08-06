import torch
import torch.nn as nn
import numpy as np
 
        
class NeuralODE():
    def __init__(self, ss_model):
        self.ss_model = ss_model

    def f_ARX(self, X, U):
        X_pred = torch.empty(X.shape)
        X_pred[0,:] = X[0,:]
        DX = self.ss_model(X[0:-1], U[0:-1])
        X_pred[1:,:] = X[0:-1,:] + DX
        return X_pred

    def f_ARX_consistency_loss(self, X_hidden, U):
        DX = self.ss_model(X_hidden[0:-1], U[0:-1])
        loss = torch.mean((X_hidden[1:,:] - (X_hidden[0:-1,:] + DX) ) **2)
        return loss

    def f_OE(self, x0, u):
        N = np.shape(u)[0]
        nx = np.shape(x0)[0]

        X = torch.empty((N,nx))
        xstep = x0
        for i in range(N):
            X[i,:] = xstep
            ustep = u[i]
            dx = self.ss_model(xstep, ustep)
            xstep = xstep + dx
        return X

    def f_OE_minibatch(self, x0_batch, U_batch):
        len_batch = x0_batch.shape[0]
        n_x = x0_batch.shape[1]
        T_batch = U_batch.shape[1]
        
        X_pred = torch.empty((len_batch, T_batch, n_x))
        xstep = x0_batch
        for i in range(T_batch):
            X_pred[:,i,:] = xstep
            ustep = U_batch[:,i,:]
            dx = self.ss_model(xstep, ustep)
            xstep = xstep + dx
        return X_pred

    def f_ODE(self,t,x,u):
        x = torch.tensor(x.reshape(1,-1).astype(np.float32))
        u = torch.tensor(u.reshape(1,-1).astype(np.float32))
        return np.array(self.nn_derivative(x,u)).ravel().astype(np.float64)


class RunningAverageMeter(object):
    """Computes and stores the average and current value"""

    def __init__(self, momentum=0.99):
        self.momentum = momentum
        self.reset()

    def reset(self):
        self.val = None
        self.avg = 0

    def update(self, val):
        if self.val is None:
            self.avg = val
        else:
            self.avg = self.avg * self.momentum + val * (1 - self.momentum)
        self.val = val