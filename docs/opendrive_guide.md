# OpenDRIVE File Guide

## What is OpenDRIVE?

OpenDRIVE (.xodr) is an open file format for describing road networks. SUMO can convert OpenDRIVE files to its native network format using `netconvert`.

## Example OpenDRIVE File Structure

```xml
<?xml version="1.0" standalone="yes"?>
<OpenDRIVE>
    <header revMajor="1" revMinor="6" name="" version="1.00" 
            date="Wed Aug 14 19:23:52 2019" 
            north="0.0" south="0.0" east="0.0" west="0.0">
    </header>
    
    <road rule="RHT" name="" length="1600.0" id="1" junction="-1">
        <link>
        </link>
        
        <type s="0.0" type="town" country="DE"/>
        
        <planView>
            <geometry s="0.0" x="-47.17" y="0.73" hdg="0.0" length="1600.0">
                <line/>
            </geometry>
        </planView>
        
        <elevationProfile>
            <elevation s="0.0" a="0.0" b="0.02" c="0.0" d="0.0"/>
        </elevationProfile>
        
        <lanes>
            <laneSection s="0.0">
                <left>
                    <lane id="2" type="border" level="false">
                        <width sOffset="0.0" a="1.0" b="0.0" c="0.0" d="0.0"/>
                    </lane>
                    <lane id="1" type="driving" level="false">
                        <width sOffset="0.0" a="4.0" b="0.0" c="0.0" d="0.0"/>
                    </lane>
                </left>
                <center>
                    <lane id="0" type="none" level="false"/>
                </center>
                <right>
                    <lane id="-1" type="driving" level="false">
                        <width sOffset="0.0" a="4.0" b="0.0" c="0.0" d="0.0"/>
                    </lane>
                    <lane id="-2" type="border" level="false">
                        <width sOffset="0.0" a="1.0" b="0.0" c="0.0" d="0.0"/>
                    </lane>
                </right>
            </laneSection>
        </lanes>
    </road>
</OpenDRIVE>
```

## Key Parameters to Modify

### 1. Road Length

The road length is defined in **two places** (both should match):

```xml
<road ... length="1600.0" ...>
```

```xml
<geometry ... length="1600.0">
```

**Example:** `length="1600.0"` = 1600 meters road

### 2. Slope/Grade (Elevation)

The slope is controlled by the **`b` parameter** in the elevation profile:

```xml
<elevationProfile>
    <elevation s="0.0" a="0.0" b="0.02" c="0.0" d="0.0"/>
</elevationProfile>
```

| Parameter | Meaning |
|-----------|---------|
| `a` | Initial elevation (starting height) |
| **`b`** | **Slope/grade** (rise per unit distance) |
| `c` | Quadratic curvature |
| `d` | Cubic curvature |

**Slope Examples:**

| `b` Value | Grade | Description |
|-----------|-------|-------------|
| 0.0 | 0% | Flat road |
| 0.02 | 2% | Gentle incline |
| 0.04 | 4% | Moderate incline |
| 0.08 | 8% | Steep incline |
| 0.10 | 10% | Very steep |
| 0.20 | 20% | Extreme grade |

### 3. Lane Width

Lane width is defined in the `<width>` element:

```xml
<lane id="-1" type="driving" level="false">
    <width sOffset="0.0" a="4.0" b="0.0" c="0.0" d="0.0"/>
</lane>
```

Here `a="4.0"` means the lane is **4 meters wide**.

## How NetworkGenerator Modifies Slope

The code uses regex to replace the `b` value:

```python
# Replace slope value in OpenDRIVE file
data = re.sub(r'b=".*?"', f'b="{slope}"', data)

# Convert to SUMO network
subprocess.run(f"netconvert --opendrive-files temp.xodr -o output.net.xml")
```

This generates multiple network files, one for each slope value.

## Manually Creating Networks

### Change Slope

1. Open your `.xodr` file
2. Find: `<elevation s="0.0" a="0.0" b="0.02" c="0.0" d="0.0"/>`
3. Change `b="0.02"` to your desired slope (e.g., `b="0.08"` for 8%)
4. Save and convert:

```bash
netconvert --opendrive-files myfile.xodr --ignore-errors -o network.net.xml
```

### Change Road Length

1. Open your `.xodr` file
2. Find and change both:
   - `<road ... length="1600.0" ...>`
   - `<geometry ... length="1600.0">`
3. Save and convert

## File Structure Summary

```
OpenDRIVE File
├── header (metadata)
└── road
    ├── length="1600.0"          ← ROAD LENGTH
    ├── planView
    │   └── geometry length      ← MUST MATCH ROAD LENGTH
    ├── elevationProfile
    │   └── elevation b="0.02"   ← SLOPE (2%)
    └── lanes
        ├── left lanes
        ├── center
        └── right lanes
            └── width a="4.0"    ← LANE WIDTH (4m)
```
