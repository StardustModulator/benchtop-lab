# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""`torch_info()`, `hub_login()` and the `load_policy()` stub."""

import dataclasses
from importlib import metadata

import huggingface_hub
import pytest
import torch

from benchtop_core import compat
from benchtop_core.errors import BenchtopError

SECRET = "hf_" + "x" * 34  # a fake token; never a real one


def test_torch_info_matches_the_installed_torch() -> None:
    info = compat.torch_info()
    assert info.version == torch.__version__
    assert info.version.split("+")[0] == metadata.version("torch").split("+")[0]
    assert info.device in {"cpu", "cuda", "mps"}
    assert (info.cuda_device is not None) == info.cuda_available


@pytest.mark.parametrize(
    ("cuda", "mps", "device"),
    [(False, False, "cpu"), (True, False, "cuda"), (False, True, "mps"), (True, True, "cuda")],
)
def test_default_device_prefers_cuda_then_mps(
    monkeypatch: pytest.MonkeyPatch, cuda: bool, mps: bool, device: str
) -> None:
    monkeypatch.setattr(torch.cuda, "is_available", lambda: cuda)
    monkeypatch.setattr(torch.cuda, "get_device_name", lambda index: f"Test GPU {index}")
    monkeypatch.setattr(torch.backends.mps, "is_available", lambda: mps)
    info = compat.torch_info()
    assert (info.device, info.cuda_available, info.mps_available) == (device, cuda, mps)
    assert info.cuda_device == ("Test GPU 0" if cuda else None)


def test_hub_login_reports_presence_and_never_carries_the_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(huggingface_hub, "get_token", lambda: SECRET)
    login = compat.hub_login()
    assert login.logged_in
    assert SECRET not in repr(login)
    assert [field.name for field in dataclasses.fields(login)] == ["logged_in"]


@pytest.mark.parametrize("token", [None, ""])
def test_hub_login_without_a_token(monkeypatch: pytest.MonkeyPatch, token: str | None) -> None:
    monkeypatch.setattr(huggingface_hub, "get_token", lambda: token)
    assert not compat.hub_login().logged_in


def test_load_policy_is_a_stub_with_an_actionable_error() -> None:
    with pytest.raises(BenchtopError, match="not available yet") as caught:
        compat.load_policy("outputs/train/act/checkpoints/last/pretrained_model", device="cpu")
    assert "lerobot-eval" in caught.value.fix
    assert "pretrained_model" in caught.value.what


def test_loaded_policy_protocol_is_structural() -> None:
    class Constant:
        device = "cpu"

        def reset(self) -> None:
            return None

        def act(self, observation: dict[str, object]) -> list[float]:
            return [0.0] * 6

    assert isinstance(Constant(), compat.LoadedPolicy)
    assert not isinstance(object(), compat.LoadedPolicy)


def test_benchtop_error_carries_what_cause_and_fix() -> None:
    error = BenchtopError("It broke.", cause="a loose cable.", fix="run: benchtop doctor")
    assert (error.what, error.cause, error.fix) == ("It broke.", "a loose cable.", "run: benchtop doctor")
    assert str(error) == "It broke. Likely cause: a loose cable. Next step: run: benchtop doctor"
