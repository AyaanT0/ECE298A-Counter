![](../../workflows/gds/badge.svg) ![](../../workflows/docs/badge.svg) ![](../../workflows/test/badge.svg)

# 8 bit Programmable Counter

Hello Professor John Long :)

This is the 8 bit binary up counter w/ async reset, sync load, tri state outputs, and its for GF180.

- `rst_n` clears the count immediately (does not wait for clock)
- LOAD (`ui[0]`) loads the value on the DATA bus (`uio[7:0]`) on the next rising clock edge. While OE = 1 the bus is ignored and LOAD holds the count
- OE (`ui[1]`) puts the count onto the DATA bus, unless OE = 0 then the bus is high impedance
- EN (`ui[2]`) makes the counter count up on each rising clk edge
- COUNT (`uo[7:0]`) shows the count

Design is in [src/counter.v](src/counter.v) and [src/project.v](src/project.v). The cocotb tests are in [test/](test/), and the GitHub Actions build the GF180 layout, run the tests on the RTL and on the gate level netlist

- [Read the documentation for project](docs/info.md)

## Running the tests

With iverilog and the Python packages in [test/requirements.txt](test/requirements.txt) installed:

```sh
cd test
make -B
```

See [test/README.md](test/README.md) for the gate level simulation and for viewing the waveforms.

## What is Tiny Tapeout?

Tiny Tapeout is an educational project that aims to make it easier and cheaper than ever to get your digital and analog designs manufactured on a real chip.

To learn more and get started, visit https://tinytapeout.com.

## Enable GitHub actions to build the results page

- [Enabling GitHub Pages](https://tinytapeout.com/faq/#my-github-action-is-failing-on-the-pages-part)

## Resources

- [FAQ](https://tinytapeout.com/faq/)
- [Digital design lessons](https://tinytapeout.com/digital_design/)
- [Learn how semiconductors work](https://tinytapeout.com/siliwiz/)
- [Join the community](https://tinytapeout.com/discord)
- [Build your design locally](https://www.tinytapeout.com/guides/local-hardening/)
