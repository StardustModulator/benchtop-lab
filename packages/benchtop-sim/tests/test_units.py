# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Unit conversion between LeRobot units (degrees, gripper 0-100) and MuJoCo actuator targets (radians)."""

from __future__ import annotations

import math

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from benchtop_sim.so101 import JOINT_LIMITS
from benchtop_sim.units import CTRL_MAX, CTRL_MIN, LEROBOT_MAX, LEROBOT_MIN, ctrl_to_lerobot, lerobot_to_ctrl

in_range_lerobot = st.tuples(
    *(st.floats(limit.lerobot_min, limit.lerobot_max, allow_nan=False) for limit in JOINT_LIMITS)
)
in_range_ctrl = st.tuples(
    *(st.floats(limit.ctrl_min, limit.ctrl_max, allow_nan=False) for limit in JOINT_LIMITS)
)
any_finite = st.lists(st.floats(-1e6, 1e6, allow_nan=False), min_size=6, max_size=6)


@given(in_range_lerobot)
def test_lerobot_to_ctrl_and_back_round_trips(values: tuple[float, ...]) -> None:
    np.testing.assert_allclose(ctrl_to_lerobot(lerobot_to_ctrl(values)), values, rtol=0, atol=1e-9)


@given(in_range_ctrl)
def test_ctrl_to_lerobot_and_back_round_trips(ctrl: tuple[float, ...]) -> None:
    np.testing.assert_allclose(lerobot_to_ctrl(ctrl_to_lerobot(ctrl)), ctrl, rtol=0, atol=1e-12)


@given(any_finite)
def test_targets_are_always_within_actuator_limits(values: list[float]) -> None:
    ctrl = lerobot_to_ctrl(values)
    assert np.all(ctrl >= CTRL_MIN)
    assert np.all(ctrl <= CTRL_MAX)


@given(any_finite)
def test_clipping_equals_clipping_in_lerobot_units_first(values: list[float]) -> None:
    clipped_first = np.clip(values, LEROBOT_MIN, LEROBOT_MAX)
    np.testing.assert_allclose(lerobot_to_ctrl(values), lerobot_to_ctrl(clipped_first), rtol=0, atol=1e-12)


@given(in_range_lerobot, in_range_lerobot)
def test_conversion_is_monotonic_per_joint(a: tuple[float, ...], b: tuple[float, ...]) -> None:
    lower, upper = np.minimum(a, b), np.maximum(a, b)
    assert np.all(lerobot_to_ctrl(lower) <= lerobot_to_ctrl(upper))


def test_arm_joints_are_degrees_to_radians() -> None:
    ctrl = lerobot_to_ctrl([90.0, -45.0, 30.0, -60.0, 120.0, 50.0])
    np.testing.assert_allclose(ctrl[:5], np.deg2rad([90.0, -45.0, 30.0, -60.0, 120.0]))


def test_zero_degrees_is_zero_radians_mid_range() -> None:
    np.testing.assert_array_equal(lerobot_to_ctrl([0, 0, 0, 0, 0, 0])[:5], np.zeros(5))


def test_gripper_endpoints_map_to_actuator_range() -> None:
    assert lerobot_to_ctrl([0, 0, 0, 0, 0, 0])[5] == CTRL_MIN[5] == pytest.approx(-0.17453)
    assert lerobot_to_ctrl([0, 0, 0, 0, 0, 100])[5] == pytest.approx(CTRL_MAX[5], abs=1e-15)
    assert lerobot_to_ctrl([0, 0, 0, 0, 0, 50])[5] == pytest.approx((CTRL_MIN[5] + CTRL_MAX[5]) / 2)


def test_gripper_is_not_treated_as_degrees() -> None:
    # 100 "degrees" would be 1.745 rad only by coincidence of the range; 50 separates the two readings.
    assert lerobot_to_ctrl([0, 0, 0, 0, 0, 50])[5] != pytest.approx(math.radians(50))


def test_out_of_range_targets_are_clipped() -> None:
    ctrl = lerobot_to_ctrl([500.0, -500.0, 0.0, 0.0, 0.0, 250.0])
    assert ctrl[0] == CTRL_MAX[0]
    assert ctrl[1] == CTRL_MIN[1]
    assert ctrl[5] == CTRL_MAX[5]
    assert lerobot_to_ctrl([0, 0, 0, 0, 0, -20.0])[5] == CTRL_MIN[5]


def test_readings_beyond_a_limit_are_reported_not_clipped() -> None:
    reading = ctrl_to_lerobot([0, 0, 0, 0, 0, CTRL_MIN[5] - 0.01])
    assert reading[5] < 0.0
    assert ctrl_to_lerobot([2.0, 0, 0, 0, 0, 0])[0] == pytest.approx(math.degrees(2.0))


def test_batches_convert_row_by_row() -> None:
    rng = np.random.default_rng(7)
    batch = rng.uniform(LEROBOT_MIN, LEROBOT_MAX, size=(4, 3, 6))
    ctrl = lerobot_to_ctrl(batch)
    assert ctrl.shape == (4, 3, 6)
    np.testing.assert_array_equal(ctrl[2, 1], lerobot_to_ctrl(batch[2, 1]))
    np.testing.assert_allclose(ctrl_to_lerobot(ctrl), batch, atol=1e-9)


def test_inputs_are_not_modified_and_outputs_are_float64() -> None:
    action = np.array([10, 20, 30, 40, 50, 60], dtype=np.float32)
    before = action.copy()
    ctrl = lerobot_to_ctrl(action)
    np.testing.assert_array_equal(action, before)
    assert ctrl.dtype == np.float64
    radians = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
    before = radians.copy()
    assert ctrl_to_lerobot(radians).dtype == np.float64
    np.testing.assert_array_equal(radians, before)


def test_limit_arrays_are_read_only_and_consistent() -> None:
    for array in (CTRL_MIN, CTRL_MAX, LEROBOT_MIN, LEROBOT_MAX):
        assert array.shape == (6,)
        with pytest.raises(ValueError, match="read-only"):
            array[0] = 0.0
    np.testing.assert_allclose(lerobot_to_ctrl(LEROBOT_MIN), CTRL_MIN, atol=1e-12)
    np.testing.assert_allclose(lerobot_to_ctrl(LEROBOT_MAX), CTRL_MAX, atol=1e-12)


@pytest.mark.parametrize("bad", [[1.0, 2.0, 3.0], np.zeros((6, 5)), 3.0, []])
@pytest.mark.parametrize("convert", [lerobot_to_ctrl, ctrl_to_lerobot])
def test_wrong_shape_is_rejected_with_the_joint_order(bad: object, convert: object) -> None:
    assert callable(convert)
    with pytest.raises(ValueError, match=r"6 values on its last axis.*shoulder_pan.*gripper.*got shape"):
        convert(bad)


@pytest.mark.parametrize("bad_value", [math.nan, math.inf, -math.inf])
@pytest.mark.parametrize("convert", [lerobot_to_ctrl, ctrl_to_lerobot])
def test_non_finite_values_are_rejected(bad_value: float, convert: object) -> None:
    assert callable(convert)
    with pytest.raises(ValueError, match="NaN or infinity"):
        convert([0.0, 0.0, bad_value, 0.0, 0.0, 0.0])
