# HemoLink AI — licence and credits

Copyright (C) 2026 the HemoLink AI team.

HemoLink AI is free software: you can redistribute it and/or modify it under the terms of the **GNU Affero General
Public License version 3 or (at your option) any later version** (see `LICENSE`). It is distributed WITHOUT ANY
WARRANTY. It is a student prototype and **not a medical device**.

Why AGPL: HemoScan reads PDFs with **PyMuPDF**, which is licensed under AGPL-3.0. Anyone who runs a modified HemoLink
as a website must offer its source code to users — the app shows a **Source code** link (set `HEMOLINK_SOURCE_URL`).

## Third-party parts

| Part | Licence | Notes |
|---|---|---|
| PyMuPDF (Artifex) | AGPL-3.0 (or commercial) | PDF reading in HemoScan |
| Leaflet 1.9.4 (`static/vendor/leaflet`) | BSD-2-Clause | Maps |
| OpenStreetMap tiles and Nominatim | ODbL data; tile and search usage policies | Keep "© OpenStreetMap contributors" |
| MOH Malaysia / National Blood Centre donation data (`data/donations_state.csv`) | CC BY 4.0 | Source: KKMNOW / data-darah-public |
| FastAPI, scikit-learn, pandas, httpx, pywebpush, cryptography, RapidOCR … | MIT / BSD / Apache-2.0 | See `requirements.txt` |
