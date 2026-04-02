# Browser Demo

This is a tiny static browser demo for the current public controller benchmark
release.

Build the demo data from the tracked benchmark bundle:

```bash
node packages/controller-benchmark/examples/browser-demo/build-demo-data.mjs
```

Then serve the directory:

```bash
cd packages/controller-benchmark/examples/browser-demo
python3 -m http.server 8000
```

Open:

```text
http://localhost:8000
```
