# -*- coding: utf-8 -*-
"""
Created on Mon Aug  5 11:00:29 2019

@author: marco
"""
import torch
import torch.nn as nn
import numpy as np
from torch.jit import Final

class NeuralStateSpaceModel(nn.Module):

    n_x: Final[int]
    n_u: Final[int]
    n_feat: Final[int]

    def __init__(self, n_x, n_u, n_feat=64, init_small=True):
        super(NeuralStateSpaceModel, self).__init__()
        self.n_x = n_x
        self.n_u = n_u
        self.n_feat = n_feat
        self.net = nn.Sequential(
            nn.Linear(n_x+n_u, n_feat),  # 2 states, 1 input
            nn.ReLU(),
            nn.Linear(n_feat, n_x)
        )

        if init_small:
            for m in self.net.modules():
                if isinstance(m, nn.Linear):
                    nn.init.normal_(m.weight, mean=0, std=1e-4)
                    nn.init.constant_(m.bias, val=0)
    
    def forward(self, X,U):
        XU = torch.cat((X,U),-1)
        DX = self.net(XU)
        return DX


class NeuralStateSpaceModel2Hidden(nn.Module):
    n_x: Final[int]
    n_u: Final[int]
    n_feat: Final[int]

    def __init__(self, n_x, n_u, n_feat=32):
        super(NeuralStateSpaceModel2Hidden, self).__init__()
        self.n_x = n_x
        self.n_u = n_u
        self.n_feat = n_feat
        self.net = nn.Sequential(
            nn.Linear(n_x + n_u, n_feat),  # 2 states, 1 input
            nn.Linear(n_feat, n_feat),
            nn.ReLU(),
            nn.Linear(n_feat, n_x)
        )

        #for m in self.net.modules():
        #    if isinstance(m, nn.Linear):
        #        nn.init.normal_(m.weight, mean=0, std=1e-4)
        #        nn.init.constant_(m.bias, val=0)

    def forward(self, X, U):
        XU = torch.cat((X, U), -1)
        DX = self.net(XU)
        return DX


class NeuralStateSpaceModelLin(nn.Module):
    def __init__(self, AL, BL):
        super(NeuralStateSpaceModelLin, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(3, 64),  # 2 states, 1 input
            nn.ReLU(),
            nn.Linear(64,2)
        )

        self.AL = nn.Linear(2,2, bias=False)
        self.AL.weight = torch.nn.Parameter(torch.tensor(AL.astype(np.float32)), requires_grad=False)
        self.BL = nn.Linear(1,2, bias=False)
        self.BL.weight = torch.nn.Parameter(torch.tensor(BL.astype(np.float32)), requires_grad=False)


        for m in self.net.modules():
            if isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, mean=0, std=1e-2)
                nn.init.constant_(m.bias, val=0)
    
    def forward(self, X,U):
        XU = torch.cat((X, U), -1)
        DX = self.net(XU)
        DX += self.AL(X) + self.BL(U)
        return DX   


class StateSpaceModelLin(nn.Module):
    def __init__(self, AL, BL):
        super(StateSpaceModelLin, self).__init__()

        self.AL = nn.Linear(2,2, bias=False)
        self.AL.weight = torch.nn.Parameter(torch.tensor(AL.astype(np.float32)), requires_grad=False)
        self.BL = nn.Linear(1,2, bias=False)
        self.BL.weight = torch.nn.Parameter(torch.tensor(BL.astype(np.float32)), requires_grad=False)
    
    def forward(self, X,U):
        DX = self.AL(X) + self.BL(U)
        return DX   


class CartPoleStateSpaceModel(nn.Module):
    def __init__(self, Ts, init_small=True):
        super(CartPoleStateSpaceModel, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(5, 64),  # 4 states, 1 input
            nn.ReLU(),
            #nn.Linear(64,32), # 2 state equations (the other 2 are fixed by basic physics)
            #nn.ReLU(),
            nn.Linear(64, 2),  # 2 state equations (the other 2 are fixed by basic physics)
        )

        if init_small:
            for m in self.net.modules():
                if isinstance(m, nn.Linear):
                    nn.init.normal_(m.weight, mean=0, std=1e-3)
                    nn.init.constant_(m.bias, val=0)

        self.AL = nn.Linear(4,4, bias=False)
        self.AL.weight = torch.nn.Parameter(torch.tensor([[0., Ts, 0., 0.],
                                                          [0., 0., 0., 0.],
                                                          [0., 0., 0., Ts],
                                                          [0., 0., 0., 0.]]), requires_grad=False)
        self.WL = nn.Linear(2,4, bias=False)
        self.WL.weight = torch.nn.Parameter(torch.tensor([[0., 0.],
                                                          [1., 0.],
                                                          [0., 0.],
                                                          [0., 1.]]), requires_grad=False)

    def forward(self, X, U):
        XU = torch.cat((X,U),-1)
        FX_TMP = self.net(XU)
        DX = (self.WL(FX_TMP) + self.AL(X))
        return DX


class CartPoleDeepStateSpaceModel(nn.Module):
    def __init__(self, Ts, init_small=True):
        super(CartPoleDeepStateSpaceModel, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(5, 64),  # 4 states, 1 input
            nn.ELU(),
            nn.Linear(64,32), # 2 state equations (the other 2 are fixed by basic physics)
            nn.ELU(),
            #nn.Linear(32, 32),  # 2 state equations (the other 2 are fixed by basic physics)
            #nn.ReLU(),
            nn.Linear(32,2)
        )

        if init_small:
            for m in self.net.modules():
                if isinstance(m, nn.Linear):
                    nn.init.normal_(m.weight, mean=0, std=1e-4)
                    nn.init.constant_(m.bias, val=0)

        self.AL = nn.Linear(4,4, bias=False)
        self.AL.weight = torch.nn.Parameter(torch.tensor([[0., Ts, 0., 0.],
                                                          [0., 0., 0., 0.],
                                                          [0., 0., 0., Ts],
                                                          [0., 0., 0., 0.]]), requires_grad=False)
        self.WL = nn.Linear(2,4, bias=False)
        self.WL.weight = torch.nn.Parameter(torch.tensor([[0., 0.],
                                                          [1., 0.],
                                                          [0., 0.],
                                                          [0., 1.]]), requires_grad=False)

    def forward(self, X, U):
        XU = torch.cat((X,U),-1)
        FX_TMP = self.net(XU)
        DX = (self.WL(FX_TMP) + self.AL(X))
        return DX
