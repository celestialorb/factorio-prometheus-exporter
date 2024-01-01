# factorio-prometheus-exporter

A mod for Factorio to produce a variety of Prometheus metrics.

## Design

This project produces two artifacts: the first being a ZIP archive of the
Factorio mod, and the second being a container image to read in the output of
the mod and expose Prometheus metrics on a web endpoint.
