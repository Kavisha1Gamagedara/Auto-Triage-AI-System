# Agent 3 manuals

One `.txt` file per vehicle: `<year>_<make>_<model>.txt`. Each procedure is a block separated by a line containing only `---`:

```
[Vehicle: 2019 Honda Civic]
[Source: where the information came from]
Component: Spark Plug
Replacement Procedure:
1. ...
Torque: ...
```

- `[Vehicle: <year> <make> <model>]` and `Component:` are required; the vehicle must be written the same way in every block of a file.
- Only record a torque value if the cited source states it. Otherwise write `Torque: NOT VERIFIED ...` so the agent does not present a guess as a spec.
- OBD-II code diagnostics that apply to any car live in `generic_obd2_dtc.txt`, using `[Vehicle: Generic OBD-II]` and an extra `[DTC: P0171, P0174]` line listing every code the block covers. Each code is indexed exactly, so a query for `P0174` finds the P0171 block even though embeddings are poor at matching bare codes. A car-specific manual (same `[DTC: ...]` line inside a car file) is returned ahead of the generic one.
- After editing, rebuild the database (from this folder's parent):

```bash
python ingest_manuals.py
```

The script wipes and rebuilds the `oem_manuals` collection each run, so it is safe to re-run.
