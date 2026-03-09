"""
Network generation from OpenDRIVE files.

Generates one SUMO .net.xml file per slope value by modifying
the elevation parameter 'b' in the OpenDRIVE XML before conversion.
"""

import os
import re
import subprocess
from typing import List, Tuple


class NetworkGenerator:
    """Generates SUMO networks from OpenDRIVE files with varying slopes."""

    def __init__(self, output_dir: str = "networks"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_networks(
        self,
        input_file: str,
        base_output: str,
        slopes: List[float]
    ) -> List[Tuple[float, str]]:
        """
        Generate one SUMO network per slope value.

        The slope is set by modifying the 'b' parameter in the OpenDRIVE
        elevation profile:
            <elevation s="0.0" a="0.0" b="0.08" c="0.0" d="0.0"/>
        where b = rise per unit distance (0.08 = 8% grade).

        Args:
            input_file:  Path to base OpenDRIVE (.xodr) file
            base_output: Base name for output network files
            slopes:      List of slope values (e.g., [0.0, 0.06, 0.08])

        Returns:
            List of (slope, network_path) tuples
        """
        nets = []

        for slope in slopes:
            out_file = os.path.join(
                self.output_dir, f"{base_output}_slope_{slope}.net.xml"
            )

            with open(input_file, 'r') as f:
                data = f.read()

            # Replace the elevation 'b' parameter
            data = re.sub(r'b=".*?"', f'b="{slope}"', data)

            tmp = os.path.join(self.output_dir, "temp.xodr")
            with open(tmp, 'w') as f:
                f.write(data)

            try:
                subprocess.run(
                    f"netconvert --opendrive-files {tmp} --ignore-errors -o {out_file}",
                    shell=True, check=True, capture_output=True
                )
                nets.append((slope, out_file))
                print(f"  Generated network: slope={slope} -> {out_file}")
            except subprocess.CalledProcessError as e:
                print(f"  Error generating network for slope {slope}: {e}")
            finally:
                if os.path.exists(tmp):
                    os.remove(tmp)

        return nets
