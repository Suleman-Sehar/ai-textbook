# Mapping Loop Diagram

```
Sensor Data → Data Association → State Estimation → Map Update → Localization
     ↑              ↓                  ↓              ↓            ↓
     └────── Correction ←────── Optimization ←────── Fusion ←─────┘
```

## Description

This diagram shows the continuous loop of the SLAM (Simultaneous Localization and Mapping) process. The robot continuously receives sensor data which is associated with existing map features, estimates its current state (position and orientation), updates the environmental map, and refines its localization within that map. The loop also includes feedback mechanisms for correction and optimization, ensuring the map remains accurate and consistent over time.