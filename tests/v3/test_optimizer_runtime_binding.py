from ark.learning.hf_lora import _optimizer


class Parameter:
    requires_grad = True


class Model:
    def parameters(self):
        return [Parameter(), Parameter()]


class Optim:
    observed = None

    class AdamW:
        def __init__(self, parameters, **kwargs):
            Optim.observed = {"parameters": list(parameters), **kwargs}


class Torch:
    optim = Optim


def test_optimizer_uses_every_frozen_adamw_field():
    method = {
        "learning_rate": 0.0001,
        "optimizer_betas": [0.9, 0.999],
        "optimizer_eps": 1e-8,
        "optimizer_weight_decay": 0.01,
        "optimizer_amsgrad": False,
        "optimizer_maximize": False,
    }
    optimizer, parameters = _optimizer(Torch(), Model(), method)
    assert isinstance(optimizer, Optim.AdamW)
    assert len(parameters) == 2
    assert Optim.observed["parameters"] == parameters
    assert Optim.observed["lr"] == 0.0001
    assert Optim.observed["betas"] == (0.9, 0.999)
    assert Optim.observed["eps"] == 1e-8
    assert Optim.observed["weight_decay"] == 0.01
    assert Optim.observed["amsgrad"] is False
    assert Optim.observed["maximize"] is False
