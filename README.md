# Bridge Progress Tracker

A simple Streamlit dashboard that visualizes the construction progress of a bridge in southern Chile using Google Earth Engine (GEE) Sentinel‑2 imagery. It displays a side‑by‑side comparison of a start (T₀) and current (T₁) mosaic, computes a linear extrapolation to predict completion, and shows key metrics.

---

## 📁 Repository Structure

```
~/apps/idb-geo/
├── app.py                # Streamlit app source
├── pyproject.toml        # Poetry project definition
├── README.md             # (this file)
└── .streamlit/           # optional Streamlit config
```

---

## 🚀 Quickstart

1. **Clone the repo**
   ```bash
   git clone https://github.com/baltierra/idb-geo.git
   cd idb-geo
   ```

2. **Install dependencies with Poetry**
   ```bash
   # Initialize (if not already):
   poetry init --no-interaction \
     --name idb-geo --python="^3.10" \
     --description "Bridge Progress Tracker using GEE and Streamlit"

   # Add runtime packages:
   poetry add \
     streamlit pandas geopandas geemap earthengine-api \
     scikit-learn streamlit-folium folium python-dateutil setuptools

   # Install deps without installing the root package:
   poetry install --no-root

   # Activate the venv:
   poetry shell
   ```

3. **Authenticate Earth Engine**
   ```bash
   poetry run earthengine authenticate
   ```
   Follow the URL instructions; this writes your credentials to `~/.config/earthengine/`.

4. **Run locally**
   ```bash
   streamlit run app.py --server.port 8501 --server.address 0.0.0.0
   ```
   Browse to `http://<VM_IP>:8501` (e.g. `http://149.165.170.125:8501`).

---

## ⚙️ Deployment as a systemd Service

Create **`/etc/systemd/system/idb-geo.service`**:

```ini
[Unit]
Description=IDB‑GEO Bridge Progress Dashboard
After=network.target

[Service]
Type=simple
User=exouser
Group=exouser
Environment=HOME=/home/exouser
WorkingDirectory=/home/exouser/apps/idb-geo
ExecStart=/usr/bin/env poetry run streamlit run app.py \
  --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable idb-geo.service
sudo systemctl start idb-geo.service
```

View live logs:
```bash
sudo journalctl -u idb-geo.service -f
```

---

## 🛠 Usage

- **Sidebar**: Adjust “Current % complete” slider to reflect the bridge’s reported progress.
- **Metrics**: See start/current dates, current percentage, predicted completion date, and days remaining.
- **Map**: Swipe between T₀ and T₁ mosaics over a 2 km buffer around the bridge.
- **Extrapolation chart**: Toggle on to view the linear fit of progress vs. time.

---

## 📄 License

This project is released under the MIT License. See [LICENSE](LICENSE) for details.

---

*Maintained by Fabián A. Araneda-Baltierra*

