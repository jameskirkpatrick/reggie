import os
import numpy as np
import mwhutils.plotting as mp

import reggie as rg


if __name__ == '__main__':
    cdir = os.path.abspath(os.path.dirname(__file__))
    data = np.load(os.path.join(cdir, 'xy.npz'))

    X = data['X']
    Y = data['y']
    U = np.linspace(X.min(), X.max(), 100)[:, None]

    # create the GP and optimize the model
    gp = rg.BasicGP(0.1, 1.0, 0.1)
    gp.add_data(X, Y)
    gp.optimize()

    # create a sparse model
    gp = gp.switch_inference('fitc', U)
    gp.optimize()

    # get the posterior moments
    x = np.linspace(X.min(), X.max(), 500)
    mu, s2 = gp.predict(x[:, None])

    # plot the posterior
    fig = mp.figure()
    fig.hold()
    fig.plot_banded(x, mu, 2*np.sqrt(s2))
    fig.scatter(X.ravel(), Y)
    fig.set_xlabel('inputs, X')
    fig.set_ylabel('outputs, Y')
    fig.draw()

    # show the figure
    mp.show()
