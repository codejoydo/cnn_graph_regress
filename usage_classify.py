from lib import models_classify, graph, coarsening, utils
import pandas as pd
import numpy as np
import scipy
import matplotlib.pyplot as plt

d = 50
X = np.load('/Neutron9/joyneel.misra/npys/timeSeriesData_normalized_d'+str(d)+'.npy')
X = X.astype(np.float32)
Y = np.load('/Neutron9/joyneel.misra/npys/emotion_scores.npy')
for feat in range(5,Y.shape[1]):
 
    y = Y[:,feat]

    ### PROCESS Y FOR CLASSIFICATION ###
    nclasses = 2
    y = pd.qcut(y, nclasses, labels=[0, 1]).__array__()
    ####################################

    n_train = 700

    X_train = X[:n_train, ...]
    X_val   = X[n_train:, ...]

    y_train = y[:n_train, ...]
    y_val   = y[n_train:, ...]

    A = np.load('/Neutron9/joyneel.misra/npys/meanFC_d'+str(d)+'.npy');
    A = A - np.min(A)
    A = scipy.sparse.csr_matrix(A)
    d = X.shape[1]

    assert A.shape == (d, d)
    print('d = |V| = {}, k|V| < |E| = {}'.format(d, A.nnz))

    graphs, perm = coarsening.coarsen(A, levels=3, self_connections=False)

    X_train = coarsening.perm_data(X_train, perm)
    X_val = coarsening.perm_data(X_val, perm)

    L = [graph.laplacian(A, normalized=True) for A in graphs]
    L = [elem.astype(np.float32) for elem in L]

    params = dict()
    params['dir_name']       = 'demo'
    params['num_epochs']     = 10
    params['batch_size']     = 40
    params['eval_frequency'] = 100

    # Building blocks.
    params['filter']         = 'chebyshev5'
    params['brelu']          = 'b1relu'
    params['pool']           = 'apool1'

    # Number of attributes in target.
    C = np.max(y)+1

    # Architecture.
    params['F']              = [32]  # Number of graph convolutional filters.
    params['K']              = [20]  # Polynomial orders.
    params['p']              = [2]    # Pooling sizes.
    params['M']              = [512, C]  # Output dimensionality of fully connected layers.
    #params['F']              = [32, 64]  # Number of graph convolutional filters.
    #params['K']              = [20, 20]  # Polynomial orders.
    #params['p']              = [4, 2]    # Pooling sizes.
    #params['M']              = [512, C]  # Output dimensionality of fully connected layers.

    # Optimization.
    params['regularization'] = 5e-4
    params['dropout']        = 1
    params['learning_rate']  = 1e-3
    params['decay_rate']     = 0.95 # 0.95
    params['momentum']       = 0.9
    params['decay_steps']    = n_train / params['batch_size']

    # Data
    params['time_steps'] = X.shape[2]

    model = models_classify.cgcnn(L, **params)
    accuracy, loss, t_step = model.fit(X_train, y_train, X_val, y_val)
