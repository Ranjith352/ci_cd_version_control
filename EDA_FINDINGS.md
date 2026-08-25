# Environmental Intelligence Pipeline — Exploratory Data Analysis (EDA) Findings

This document summarizes the Exploratory Data Analysis (EDA) findings conducted on the **OpenAQ Air Quality** and **USGS Earthquake** datasets during Phase 3 of the Environmental Intelligence Pipeline.

---

## 1. Air Quality Dataset Analysis (OpenAQ v3)

### 1.1 Parameters & Unit Normalization
- **Tracked Pollutants**: $\text{PM}_{2.5}$, $\text{PM}_{10}$, $\text{NO}_2$, $\text{SO}_2$, $\text{CO}$, and $\text{O}_3$.
- **Unit Standardisation**: Gaseous concentrations recorded in parts per million ($\text{ppm}$) or parts per billion ($\text{ppb}$) were converted to standard metric mass concentrations ($\mu\text{g/m}^3$) assuming standard temperature ($25^\circ\text{C}$) and pressure ($1\text{ atm}$):
  $$\text{Concentration } (\mu\text{g/m}^3) = \text{ppm} \times \frac{\text{Molecular Weight}}{0.02445}$$

### 1.2 US EPA AQI Sub-Indices
- AQI sub-indices were calculated using linear piecewise interpolation across standard EPA concentration break points:
  $$\text{AQI} = \frac{I_{\text{high}} - I_{\text{low}}}{C_{\text{high}} - C_{\text{low}}} (C - C_{\text{low}}) + I_{\text{low}}$$

### 1.3 Key Air Quality Insights
- **Dominant Stressors**: Fine particulate matter ($\text{PM}_{2.5}$) and coarse particulate matter ($\text{PM}_{10}$) are the primary air quality stressors in urban locations, showing strong positive correlation ($r > 0.85$).
- **Diurnal Patterns**: Peak concentrations for $\text{PM}_{2.5}$ and $\text{NO}_2$ coincide with morning ($07:00\text{--}09:00$) and evening ($18:00\text{--}21:00$) traffic rush hours.
- **Location Variations**: Urban and commercial monitoring stations exhibit significantly higher AQI values compared to rural background stations.

---

## 2. Earthquake Hazards Dataset Analysis (USGS)

### 2.1 Magnitude Spectrum & Categorization
- **Magnitude Range**: $2.5$ to $7.8$ (Mean = $4.25$).
- **Richter Tiers**: Events were categorized into analytical Richter tiers (`Micro`, `Minor`, `Light`, `Moderate`, `Strong`, `Major`, `Great`).

### 2.2 Magnitude & Depth Distributions
- **Power-Law Frequency**: Over $65\%$ of recorded events fall into the `Minor` ($2.0\text{--}3.9$) category, adhering strictly to the Gutenberg-Richter magnitude-frequency law.
- **Focal Depth**: Over $85\%$ of seismic events occur at shallow focal depths ($< 50\text{ km}$).
- **Spatial Clustering**: High-magnitude events ($\ge 6.0$) heavily concentrate along major tectonic plate boundaries, specifically the Pacific Ring of Fire and the Alpide Belt.

---

## 3. Reference Notebooks
- [`notebooks/air_quality_eda.ipynb`](notebooks/air_quality_eda.ipynb): Interactive OpenAQ exploratory analysis notebook.
- [`notebooks/earthquake_eda.ipynb`](notebooks/earthquake_eda.ipynb): Interactive USGS earthquake exploratory analysis notebook.
