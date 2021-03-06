"""
Meta-models for learning.
"""

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

import numpy as np

from ._core import Model

from ..learning import sample
from ..utils.misc import rstate


__all__ = ['MCMC']


def _integrate(parts, grad):
    """
    Helper function to integrate over a function and potentially its
    derivatives.
    """
    if grad:
        return tuple([np.mean(_, axis=0) for _ in zip(*parts)])
    else:
        return np.mean(parts, axis=0)


class MCMC(Model):
    """
    Model which implements MCMC to produce a posterior over parameterized
    models.
    """
    def __init__(self, model, n=100, burn=100, rng=None):
        self._n = n
        self._ndata = 0
        self._burn = burn
        self._rng = rstate(rng)
        self._models = self._sample(model.copy(), burn=True)

    def __iter__(self):
        return iter(self._models)

    def _sample(self, model, burn=False):
        """
        Resample the hyperparameters with burnin if requested."""
        if burn:
            model = sample(model, self._burn, False, self._rng)[-1]
        return sample(model, self._n, False, self._rng)

    def add_data(self, X, Y):
        # add the data
        nprev = self._ndata
        model = self._models.pop()
        model.add_data(X, Y)
        self._ndata += len(X)
        self._models = self._sample(model, burn=(self._ndata > 2*nprev))

    def get_loglike(self):
        return np.mean([m.get_loglike() for m in self._models])

    def sample(self, X, size=None, latent=True, rng=None):
        rng = rstate(rng)
        model = self._models[rng.randint(self._n)]
        return model.sample(X, size, latent, rng)

    def predict(self, X, grad=False):
        # pylint: disable=arguments-differ
        parts = [np.array(a)
                 for a in zip(*[_.predict(X, grad) for _ in self._models])]
        mu_, s2_ = parts[:2]
        mu = np.mean(mu_, axis=0)
        s2 = np.mean(s2_ + (mu_ - mu)**2, axis=0)

        if not grad:
            return mu, s2

        dmu_, ds2_ = parts[2:]
        dmu = np.mean(dmu_, axis=0)
        Dmu = dmu_ - dmu
        ds2 = np.mean(ds2_ +
                      2*mu_[:, :, None] * Dmu -
                      2*mu[None, :, None] * Dmu, axis=0)

        return mu, s2, dmu, ds2

    def get_tail(self, f, X, grad=False):
        parts = [m.get_tail(f, X, grad) for m in self._models]
        return _integrate(parts, grad)

    def get_improvement(self, f, X, grad=False):
        parts = [m.get_improvement(f, X, grad) for m in self._models]
        return _integrate(parts, grad)

    def get_entropy(self, X, grad=False):
        parts = [m.get_entropy(X, grad) for m in self._models]
        return _integrate(parts, grad)

    def sample_f(self, n, rng=None):
        rng = rstate(rng)
        model = self._models[rng.randint(self._n)]
        return model.sample_f(n, rng)
