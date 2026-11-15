# MISSION LAIKA: THE RED HORIZON - Science Document

## NASA Science Systems

The game ships with curated NASA science data from three systems mentioned on the briefing slides:

### RADLAB + DONKI (Radiation and Real Measurements)
- **URL**: https://ccmc.gsfc.nasa.gov/tools/DONKI/
- **Status**: Offline/cached during gameplay
- **Metrics displayed in-game**:
  - Mars surface dose: ~0.64 mSv/day
  - Solar particle event: Watch the DONKI feed for real-time alerts
- **In-game relevance**: Influences difficulty settings (hard mode has stricter radiation hazards, shorter timers)

### OSDR (Office of Spaceflight Health and Medicine)
- **URL**: https://osdr.nasa.gov/
- **Status**: Offline/cached
- **Metrics displayed in-game**:
  - Bone density loss: ~1-1.5% per month without exercise loading
  - Muscle loss: Significant reduction without regular physical activity
- **In-game relevance**: Exercise challenge (bicycle) reinforces the importance of regular loading. Hibernation mode protects against bone density loss effects.

### MARS TREK (Real Mars Data)
- **URL**: https://trek.nasa.gov/mars/
- **Status**: Offline/cached
- **Metrics displayed in-game**:
  - Survey sites: Gale Crater (referenced in Level 3)
  - Night low temperature: -125°C (Level 3 cold alert)
  - Mars wind patterns: Dust storms can reach 100 km/h at the surface; upper-atmosphere winds are faster but gentle in force due to thin atmosphere
  - Mars gravity: 3.71 m/s² (38% of Earth, Level 1 exercise mechanic)
- **In-game relevance**: Level 3 photography mission uses real Mars terrain concepts. Sandstorm mechanics based on real dust storm behavior. Cold mechanics based on real Mars nighttime temperatures.

## Cached Science Data

The game bundles cached science values so it runs fully offline:

- **File**: `data/science.json`
- **Systems array**: Three system objects with id, name, role, url, status, and metrics
- **Facts array**: Free-form science facts
- **Updated field**: "bundled" (indicates cached values, not live feed)

When `tools/fetch_science.py` runs online, it can refresh the `data/science.json` with latest DONKI events. The game then uses the cached values and never touches the network.

## Verification

All science values are verified against NASA open data sources. The game does not make claims beyond what is publicly documented. Cached values are updated periodically but the game functions identically whether online or offline.

## Verification Status
- ✓ Mars surface dose: ~0.64 mSv/day (verified against NASA PDS)
- ✓ Bone density loss rates: 1-1.5%/month (verified against NASA HRP)
- ✓ Mars night temperatures: -125°C at equinox (verified against MARS TREK)
- ✓ Solar particle event monitoring via DONKI (verified against NASA CCMC)