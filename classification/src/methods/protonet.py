# This code is modified from https://github.com/jakesnell/prototypical-networks 

import torch
import torch.nn as nn
from torch.autograd import Variable
import numpy as np
from classification.src import MetaTemplate


class ProtoNet(MetaTemplate):
    def __init__(self, model_func, n_way, n_support):
        super(ProtoNet, self).__init__(model_func, n_way, n_support)
        self.loss_fn = nn.CrossEntropyLoss()

    def set_forward(self, x, is_feature=False):
        """
        Computes classification scores for query data in x
        Args:
            x (torch.Tensor): shape (n_way, n_support+n_query, (dim)) input data
            is_feature (bool): whether input data is an image (False) or a feature vector (True)

        Returns:
            torch.Tensor: shape(n_query*n_way, n_way), classification prediction for each query data
        """
        z_support, z_query = self.parse_feature(x, is_feature)

        z_support = z_support.contiguous()
        z_proto = z_support.view(self.n_way, self.n_support, -1).mean(1)  # the shape of z is [n_data, n_dim]
        z_query = z_query.contiguous().view(self.n_way * self.n_query, -1)

        dists = euclidean_dist(z_query, z_proto)
        scores = -dists
        return scores

    def set_forward_loss(self, x):
        """
        Compute loss from classification of query data in x
        Args:
            x (torch.Tensor): shape (n_way, n_support+n_query, (dim)) input data

        Returns:
            torch.Tensor: shape(1), loss from classification
        """
        y_query = torch.from_numpy(np.repeat(range(self.n_way), self.n_query))
        y_query = Variable(y_query.cuda())

        scores = self.set_forward(x)

        return self.loss_fn(scores, y_query)


def euclidean_dist(x, y):
    # x: N x D
    # y: M x D
    n = x.size(0)
    m = y.size(0)
    d = x.size(1)
    assert d == y.size(1)

    x = x.unsqueeze(1).expand(n, m, d)
    y = y.unsqueeze(0).expand(n, m, d)

    return torch.pow(x - y, 2).sum(2)