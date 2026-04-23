# Test Simulation Mathematical Model Documentation

## Overview

The Test simulation models a realistic 5-tower mine communication network with 30-day temporal dynamics. The simulation captures tower power consumption, battery state-of-charge (SOC), user demand, coverage dynamics, and environmental factors to provide realistic operational insights for mine telecommunications systems.

**Simulation Parameters:**
- Duration: 30 days
- Time step: 5 minutes
- Number of towers: 15 (dynamically repositioned daily)
- Grid size: 1000m × 1000m
- Season: Summer

---

## 1. Temperature Model

### References

- Parton, W.J., Logan, J.A., “A Model for Diurnal Variation in Soil and Air Temperature,” Agricultural Meteorology, 1981  
  https://doi.org/10.1016/0002-1571(81)90013-4  

- Wilks, D.S., *Statistical Methods in the Atmospheric Sciences* (sinusoidal + noise climate models)  
  https://doi.org/10.1016/C2017-0-03921-6  

---

## 2. User Demand Model

### References

- Barford, P., Kline, J., Plonka, D., Ron, A., “A Signal Analysis of Network Traffic Anomalies”  
  (diurnal traffic periodicity modeling using sinusoidal patterns)  
  https://doi.org/10.1145/1015467.1015498  

- 3GPP TR 36.814, “Further advancements for E-UTRA physical layer aspects”  
  (traffic variation and load models)  
  https://www.3gpp.org/ftp/Specs/archive/36_series/36.814/  

---

## 3. Coverage Model

### References

- Rappaport, T.S., *Wireless Communications: Principles and Practice*, Chapter: Path Loss Models  
  https://doi.org/10.1109/9780470545850  

- Goldsmith, A., *Wireless Communications*, Section: Large-scale fading & coverage  
  https://doi.org/10.1017/CBO9780511841224  

---

## 4. Terrain Model

### References

- Rappaport, T.S., *Wireless Communications*, Log-normal shadowing model (Gaussian variation in dB)  
  https://doi.org/10.1109/9780470545850  

- ITU-R P.1812, “A path-specific propagation prediction method”  
  (terrain-dependent propagation variability)  
  https://www.itu.int/rec/R-REC-P.1812  

---

## 5. Battery Model

### References

- Auer, G. et al., “How Much Energy is Needed to Run a Wireless Network?” IEEE Wireless Communications  
  (base station power = fixed + load-dependent + PA losses)  
  https://doi.org/10.1109/MWC.2011.6155877  

- EARTH Project Deliverable D2.3  
  (Base station power model: P = P0 + ΔP·load)  
  https://www.ict-earth.eu/publications/deliverables/deliverable-d2-3  

- Plett, G.L., *Battery Management Systems*, Volume 1  
  (SOC update, efficiency modeling)  
  https://artechhouse.com/Battery-Management-Systems-P2036.aspx  

- Vetter, J. et al., “Ageing mechanisms in lithium-ion batteries”  
  https://doi.org/10.1016/j.jpowsour.2004.11.020  

---

## 6. Load Sharing Model

### References

- Kelly, F.P., “Charging and Rate Control for Elastic Traffic”  
  (proportional fairness allocation model)  
  https://doi.org/10.1002/ett.4460080106  

- Mo, J., Walrand, J., “Fair End-to-End Window-Based Congestion Control”  
  (resource allocation proportional to weights)  
  https://doi.org/10.1109/90.769765  

---

## 7. Tower Positioning & User Assignment

### References

- MacQueen, J., “Some Methods for Classification and Analysis of Multivariate Observations” (K-means)  
  https://projecteuclid.org/euclid.bsmsp/1200512992  

- Daskin, M.S., *Network and Discrete Location*  
  (facility location optimization theory)  
  https://doi.org/10.1002/9780470172599  

---

## 8. Noise and Uncertainty

### References

- Papoulis, A., *Probability, Random Variables, and Stochastic Processes*  
  (Gaussian noise modeling)  
  https://doi.org/10.1036/0073660116  

- Kay, S., *Fundamentals of Statistical Signal Processing*  
  (noise in measurement systems)  
  https://doi.org/10.1016/C2009-0-22388-1  

---