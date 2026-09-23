# Testbench for the 8 bit programmable counter

This testbench uses cocotb to drive the design and check its outputs.

- [tb.v](tb.v) instantiates `tt_um_ayaant0_counter` and models the `uio` pads as a tristate bus. `ext_oe` and `ext_data` act as an external device on the bus, and `uio_bus` is the value on the pins, including Z and X.
- [test.py](test.py) holds the tests. They only use the top level signals, so they run on the RTL and on the gate level netlist

## How to run

To run the RTL simulation:

```sh
make -B
```

To run the gate level sim, harden project and copy netlist of `tt_um_ayaant0_counter` to `gate_level_netlist.v`. `PDK_ROOT` has to point to the gf180 PDK install for the standard cell models. The GitHub Actions `gl_test` job sets all of this up automatically.

Then run:

```sh
make -B GATES=yes
```

If you wish to save the waveform in VCD format instead of FST format, edit tb.v to use `$dumpfile("tb.vcd");` and then run:

```sh
make -B FST=
```

This will generate `tb.vcd` instead of `tb.fst`.

## How to view the waveform file

Using GTKWave

```sh
gtkwave tb.fst tb.gtkw
```

Using Surfer

```sh
surfer tb.fst
```
