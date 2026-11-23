# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Facts about the installed PyTorch and the Hugging Face login, for `benchtop doctor` and the fingerprint."""

from dataclasses import dataclass

__all__ = ["HubLogin", "TorchInfo", "hub_login", "torch_info"]


@dataclass(frozen=True, slots=True)
class TorchInfo:
    """The installed PyTorch and the accelerators it can use.

    Attributes:
        version: PyTorch version, e.g. `2.15.0+cpu`.
        cuda_available: Whether a CUDA device is usable.
        cuda_device: Name of the first CUDA device, if any.
        mps_available: Whether Apple's Metal backend is usable.
        device: The device Benchtop Lab would pick by default: `cuda`, then `mps`, then `cpu`.
    """

    version: str
    cuda_available: bool
    cuda_device: str | None
    mps_available: bool
    device: str


def torch_info() -> TorchInfo:
    """Import PyTorch and report its version and usable devices.

    Returns:
        The version, CUDA and MPS availability and the default device.

    Raises:
        ImportError: If PyTorch is not installed or cannot be loaded.
    """
    import torch  # noqa: PLC0415  (lazy: importing torch takes over a second)

    cuda = bool(torch.cuda.is_available())
    mps = bool(torch.backends.mps.is_available())
    return TorchInfo(
        version=str(torch.__version__),
        cuda_available=cuda,
        cuda_device=str(torch.cuda.get_device_name(0)) if cuda else None,
        mps_available=mps,
        device="cuda" if cuda else "mps" if mps else "cpu",
    )


@dataclass(frozen=True, slots=True)
class HubLogin:
    """Whether a Hugging Face token is configured on this machine. Never holds the token itself.

    Attributes:
        logged_in: Whether a token was found (environment variable or the `hf auth login` token file).
    """

    logged_in: bool


def hub_login() -> HubLogin:
    """Check for a locally configured Hugging Face token without contacting the Hub.

    The token is only tested for presence; it is never returned, logged or sent anywhere.

    Returns:
        Whether a token is configured.

    Raises:
        ImportError: If `huggingface_hub` is not installed.
    """
    from huggingface_hub import get_token  # noqa: PLC0415  (lazy: keeps `import benchtop_core.compat` cheap)

    return HubLogin(logged_in=bool(get_token()))
