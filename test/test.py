# SPDX-FileCopyrightText: © 2026 Ayaan Tunio
# SPDX-License-Identifier: Apache-2.0

"""Tests hehe"""

import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, Timer

# ui_in control bits
LOAD = 0x01
OE = 0x02
EN = 0x04

CLOCK_PERIOD_US = 10  # 100 kHz
SETTLE_US = 1  # time allowed for outputs to settle after an input change


def controls(load=False, oe=False, en=False):
    return (LOAD if load else 0) | (OE if oe else 0) | (EN if en else 0)


def count(dut):
    value = dut.uo_out.value
    assert value.is_resolvable, f"uo_out {value} contains X/Z"
    return int(value)


def is_high_z(value):
    return str(value).upper() == "Z" * len(value)


def contended_bus(a, b):
    """Bus value when two devices drive a and b: X where they disagree."""
    return "".join("X" if (a ^ b) >> i & 1 else str(a >> i & 1) for i in reversed(range(8)))


def check_outputs(dut, expected, oe, ext_oe=False, ext_data=0):
    """Check every output against the expected count and control inputs"""
    assert count(dut) == expected, f"uo_out {dut.uo_out.value} != {expected:#04x}"
    assert dut.uio_out.value == expected, f"uio_out {dut.uio_out.value} != {expected:#04x}"
    assert dut.uio_oe.value == (0xFF if oe else 0x00), f"uio_oe {dut.uio_oe.value}"
    bus = dut.uio_bus.value
    if oe and ext_oe:
        want = contended_bus(expected, ext_data)
        assert str(bus).upper() == want, f"bus {bus} != {want} (contention)"
    elif oe:
        assert bus == expected, f"bus {bus} != {expected:#04x}"
    elif ext_oe:
        assert bus == ext_data, f"bus {bus} != {ext_data:#04x}"
    else:
        assert is_high_z(bus), f"bus {bus} is not Hi-Z"


async def start(dut):
    """Start the clock and reset the counter.
    Returns just after a falling clock edge with count = 0,
    outputs disabled and nothing driving the uio bus.
    """
    cocotb.start_soon(Clock(dut.clk, CLOCK_PERIOD_US, unit="us").start())
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.ext_oe.value = 0
    dut.ext_data.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    await FallingEdge(dut.clk)
    dut.rst_n.value = 1
    await FallingEdge(dut.clk)
    check_outputs(dut, 0, oe=False)


async def load_value(dut, value):
    """Drive `value` onto the bus and load it on the next rising edge.

    Returns shortly after the following falling edge, with LOAD low and the
    bus released.
    """
    dut.ui_in.value = controls(load=True)
    dut.ext_data.value = value
    dut.ext_oe.value = 1
    await FallingEdge(dut.clk)
    dut.ui_in.value = 0
    dut.ext_oe.value = 0
    await Timer(SETTLE_US, unit="us")


@cocotb.test()
async def test_reset_is_asynchronous(dut):
    """rst_n clears the count immediately, with no clock edge at all."""
    # Drive the clock by hand so there are provably no clock edges during
    # the resets.
    dut.ena.value = 1
    dut.clk.value = 0
    dut.ui_in.value = 0
    dut.ext_oe.value = 0
    dut.ext_data.value = 0
    dut.rst_n.value = 0
    await Timer(SETTLE_US, unit="us")
    check_outputs(dut, 0, oe=False)

    # One rising edge loads 0xA5
    dut.rst_n.value = 1
    dut.ui_in.value = controls(load=True)
    dut.ext_oe.value = 1
    dut.ext_data.value = 0xA5
    await Timer(SETTLE_US, unit="us")
    dut.clk.value = 1
    await Timer(SETTLE_US, unit="us")
    check_outputs(dut, 0xA5, oe=False, ext_oe=True, ext_data=0xA5)

    dut.ui_in.value = 0
    dut.ext_oe.value = 0
    await Timer(SETTLE_US, unit="us")
    dut.clk.value = 0
    await Timer(SETTLE_US, unit="us")

    dut.rst_n.value = 0
    await Timer(SETTLE_US, unit="us")
    check_outputs(dut, 0, oe=False)

    # With LOAD and EN high, releasing reset still changes nothing until the
    # next rising edge, which then loads the bus
    dut.ui_in.value = controls(load=True, en=True)
    dut.ext_oe.value = 1
    dut.ext_data.value = 0x5A
    await Timer(SETTLE_US, unit="us")
    dut.rst_n.value = 1
    await Timer(SETTLE_US, unit="us")
    check_outputs(dut, 0, oe=False, ext_oe=True, ext_data=0x5A)
    dut.clk.value = 1
    await Timer(SETTLE_US, unit="us")
    check_outputs(dut, 0x5A, oe=False, ext_oe=True, ext_data=0x5A)


@cocotb.test()
async def test_reset_overrides_load_and_count(dut):
    """While rst_n is low the count stays 0, even with LOAD and EN high."""
    await start(dut)
    await load_value(dut, 0x5A)
    check_outputs(dut, 0x5A, oe=False)

    # Assert reset in the middle of the low clock phase. It takes effect
    # before the next rising edge.
    await Timer(SETTLE_US, unit="us")
    dut.rst_n.value = 0
    await Timer(SETTLE_US, unit="us")
    assert count(dut) == 0

    dut.ui_in.value = controls(load=True, en=True)
    dut.ext_oe.value = 1
    dut.ext_data.value = 0xFF
    for _ in range(5):
        await FallingEdge(dut.clk)
        assert count(dut) == 0, "reset must override load and count"

    # After reset is released, counting resumes on the next rising edge
    dut.ui_in.value = controls(en=True)
    dut.ext_oe.value = 0
    dut.rst_n.value = 1
    await FallingEdge(dut.clk)
    check_outputs(dut, 1, oe=False)


@cocotb.test()
async def test_counts_up_and_wraps(dut):
    """With EN = 1 the counter steps through 0..255 and wraps back to 0."""
    await start(dut)
    dut.ui_in.value = controls(en=True)
    for expected in list(range(1, 256)) + [0, 1, 2]:
        await FallingEdge(dut.clk)
        check_outputs(dut, expected, oe=False)


@cocotb.test()
async def test_count_enable(dut):
    """With EN = 0 the counter holds its value."""
    await start(dut)
    await load_value(dut, 0x7E)
    for _ in range(5):
        await FallingEdge(dut.clk)
        check_outputs(dut, 0x7E, oe=False)

    dut.ui_in.value = controls(en=True)
    for expected in (0x7F, 0x80, 0x81):
        await FallingEdge(dut.clk)
        check_outputs(dut, expected, oe=False)

    dut.ui_in.value = 0
    for _ in range(5):
        await FallingEdge(dut.clk)
        check_outputs(dut, 0x81, oe=False)


@cocotb.test()
async def test_load_is_synchronous(dut):
    """LOAD copies the bus into the counter on a rising clock edge only."""
    await start(dut)
    dut.ui_in.value = controls(en=True)
    for _ in range(3):
        await FallingEdge(dut.clk)
    check_outputs(dut, 3, oe=False)

    # Raise LOAD (with EN) just after a falling edge: nothing may change
    # before the next rising edge.
    dut.ui_in.value = controls(load=True, en=True)
    dut.ext_oe.value = 1
    dut.ext_data.value = 0xC3
    await Timer(CLOCK_PERIOD_US // 2 - SETTLE_US, unit="us")
    assert count(dut) == 3, "LOAD changed the count without a clock edge"

    # Load has priority over counting
    await FallingEdge(dut.clk)
    check_outputs(dut, 0xC3, oe=False, ext_oe=True, ext_data=0xC3)

    # Holding LOAD high loads the bus on every rising edge
    for value in (0x00, 0xFF, 0x55, 0xAA):
        dut.ext_data.value = value
        await FallingEdge(dut.clk)
        check_outputs(dut, value, oe=False, ext_oe=True, ext_data=value)

    # Counting resumes from the loaded value
    dut.ui_in.value = controls(en=True)
    dut.ext_oe.value = 0
    await FallingEdge(dut.clk)
    check_outputs(dut, 0xAB, oe=False)


@cocotb.test()
async def test_load_every_value(dut):
    """Every 8-bit value can be loaded from any other value, LOAD beats EN,
    the loaded value holds with EN = 0, and counting continues from it."""
    await start(dut)
    for value in range(256):
        # Start from a different value, so the load really changes the count
        other = value ^ 0xA5
        await load_value(dut, other)
        check_outputs(dut, other, oe=False)

        dut.ui_in.value = controls(load=True, en=True)
        dut.ext_oe.value = 1
        dut.ext_data.value = value
        await FallingEdge(dut.clk)
        check_outputs(dut, value, oe=False, ext_oe=True, ext_data=value)

        dut.ui_in.value = 0
        dut.ext_oe.value = 0
        await FallingEdge(dut.clk)
        check_outputs(dut, value, oe=False)

        dut.ui_in.value = controls(en=True)
        await FallingEdge(dut.clk)
        check_outputs(dut, (value + 1) % 256, oe=False)
        dut.ui_in.value = 0


@cocotb.test()
async def test_tristate_outputs(dut):
    """OE drives the count onto the uio bus; with OE = 0 the bus is Hi-Z."""
    await start(dut)
    await load_value(dut, 0x3C)

    # Outputs disabled: every uio pad is an input and nothing drives the bus
    check_outputs(dut, 0x3C, oe=False)

    # OE takes effect immediately, without a clock edge
    await Timer(SETTLE_US, unit="us")
    dut.ui_in.value = controls(oe=True)
    await Timer(SETTLE_US, unit="us")
    check_outputs(dut, 0x3C, oe=True)
    dut.ui_in.value = 0
    await Timer(SETTLE_US, unit="us")
    check_outputs(dut, 0x3C, oe=False)

    # While the outputs are disabled another device can use the bus, and the
    # counter does not load it without LOAD
    dut.ext_oe.value = 1
    dut.ext_data.value = 0x99
    for _ in range(3):
        await FallingEdge(dut.clk)
        check_outputs(dut, 0x3C, oe=False, ext_oe=True, ext_data=0x99)
    dut.ext_oe.value = 0

    # The counter keeps counting while its outputs are Hi-Z
    dut.ui_in.value = controls(en=True)
    for expected in range(0x3D, 0x47):
        await FallingEdge(dut.clk)
        check_outputs(dut, expected, oe=False)

    # Enabling the outputs shows the current count, which keeps counting
    dut.ui_in.value = controls(oe=True, en=True)
    await Timer(SETTLE_US, unit="us")
    check_outputs(dut, 0x46, oe=True)
    for expected in range(0x47, 0x51):
        await FallingEdge(dut.clk)
        check_outputs(dut, expected, oe=True)


@cocotb.test()
async def test_load_with_outputs_enabled(dut):
    """While OE = 1 the counter ignores the bus, so LOAD holds the count
    (LOAD still beats EN), even if another device drives the bus too."""
    await start(dut)
    await load_value(dut, 0x81)
    dut.ui_in.value = controls(load=True, oe=True, en=True)
    for _ in range(3):
        await FallingEdge(dut.clk)
        check_outputs(dut, 0x81, oe=True)

    # Bus contention: an external device drives the opposite of every bit,
    # so the whole bus is X. The count must not be affected, with or
    # without EN.
    dut.ext_oe.value = 1
    dut.ext_data.value = 0x7E
    for en in (True, False):
        dut.ui_in.value = controls(load=True, oe=True, en=en)
        await Timer(SETTLE_US, unit="us")
        check_outputs(dut, 0x81, oe=True, ext_oe=True, ext_data=0x7E)
        for _ in range(3):
            await FallingEdge(dut.clk)
            check_outputs(dut, 0x81, oe=True, ext_oe=True, ext_data=0x7E)

    # Once LOAD is released the counter counts on from the held value
    dut.ext_oe.value = 0
    dut.ui_in.value = controls(oe=True, en=True)
    await FallingEdge(dut.clk)
    check_outputs(dut, 0x82, oe=True)


@cocotb.test()
async def test_outputs_enabled_during_reset(dut):
    """OE still controls the bus during reset: it drives the reset count (0)
    while OE = 1 and is Hi-Z while OE = 0."""
    await start(dut)
    await load_value(dut, 0x96)
    dut.ui_in.value = controls(oe=True)
    await Timer(SETTLE_US, unit="us")
    check_outputs(dut, 0x96, oe=True)

    dut.rst_n.value = 0
    await Timer(SETTLE_US, unit="us")
    check_outputs(dut, 0, oe=True)
    for _ in range(3):
        await FallingEdge(dut.clk)
        check_outputs(dut, 0, oe=True)

    dut.ui_in.value = 0
    await Timer(SETTLE_US, unit="us")
    check_outputs(dut, 0, oe=False)
    dut.rst_n.value = 1
    await FallingEdge(dut.clk)
    check_outputs(dut, 0, oe=False)


@cocotb.test()
async def test_unused_inputs_ignored(dut):
    """ui_in[7:3] has no effect: every pattern, combined with every
    LOAD/OE/EN combination, behaves like the reference model."""
    await start(dut)
    expected = 0
    data = 0x5A
    for unused in range(32):
        for ctrl in range(8):
            load, oe, en = bool(ctrl & LOAD), bool(ctrl & OE), bool(ctrl & EN)
            # The external device drives the bus for every LOAD, which
            # includes bus contention while OE = 1
            ext_oe = load
            data = (data * 5 + 0x3B) % 256
            dut.ui_in.value = ctrl | (unused << 3)
            dut.ext_oe.value = int(ext_oe)
            dut.ext_data.value = data
            await Timer(SETTLE_US, unit="us")
            check_outputs(dut, expected, oe, ext_oe, data)

            await FallingEdge(dut.clk)
            if load:
                expected = expected if oe else data
            elif en:
                expected = (expected + 1) % 256
            check_outputs(dut, expected, oe, ext_oe, data)


@cocotb.test()
async def test_random_against_model(dut):
    """Random LOAD/OE/EN/reset/bus activity checked against a reference model."""
    rng = random.Random(298)
    await start(dut)
    expected = 0

    for _ in range(3000):
        load = rng.random() < 0.2
        oe = rng.random() < 0.5
        en = rng.random() < 0.7
        reset = rng.random() < 0.02
        # The external device always drives the bus for a load while OE = 0,
        # and sometimes at other times, including while OE = 1 (contention).
        ext_oe = (load and not oe) or rng.random() < 0.3
        ext_data = rng.randrange(256)
        unused = rng.randrange(32) << 3  # ui_in[7:3] must be ignored

        dut.ui_in.value = controls(load, oe, en) | unused
        dut.ext_oe.value = int(ext_oe)
        dut.ext_data.value = ext_data
        await Timer(SETTLE_US, unit="us")
        check_outputs(dut, expected, oe, ext_oe, ext_data)

        if reset:
            dut.rst_n.value = 0
            await Timer(SETTLE_US, unit="us")
            expected = 0
            assert count(dut) == 0

        await FallingEdge(dut.clk)
        if not reset:
            if load:
                # While OE = 1 the counter ignores the bus and holds
                expected = expected if oe else ext_data
            elif en:
                expected = (expected + 1) % 256
        check_outputs(dut, expected, oe, ext_oe, ext_data)
        dut.rst_n.value = 1
