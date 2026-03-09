"""
Route file generation for platooning and car-following simulations.

Route files define vehicle types and their properties. This module takes
template route files and generates parameterized variants by modifying
sigma, tau, acceleration, speed, and minGap values in the XML.

Key difference between modes:
- Platooning:     templates organized by model/count/speed/gap/bound
- Car-following:  templates organized by model/count/bound
                  (speed/sigma/tau/accel set via regex substitution)
"""

import os
import re
from typing import List, Tuple, Optional


class RouteGenerator:
    """Generates route files for both simulation modes."""

    def __init__(self, base_dir: str, output_dir: str = "generated_routes"):
        """
        Args:
            base_dir:   Directory containing template route files
            output_dir: Directory to write generated route files
        """
        self.base_dir = base_dir
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    # =========================================================================
    # PLATOONING ROUTES
    # =========================================================================

    def generate_platooning_routes(
        self,
        models: List[str],
        truck_counts: List[int],
        min_gaps: List[float],
        sigma_tau_pairs: List[Tuple[float, float]],
        accels: List[float]
    ) -> List[str]:
        """
        Generate route files for platooning simulations.

        Template structure:
            {base_dir}/{model}/{count}truck/90/{gap}/{variant}/grade01.rou.xml

        For single vehicles (count=1), there is no gap subfolder:
            {base_dir}/{model}/1truck/90/{variant}/grade01.rou.xml

        The template is copied as-is (vehicle types reference PHEMlight
        emission files that already have position-specific Cd values).
        Sigma/tau/accel are encoded in the output filename for tracking.

        Output filename pattern:
            route_{model}_{count}truck_{variant}_minGap_{gap}_tau_{tau}_accel_{accel}_length_{length}_sigma_{sigma}.rou.xml
        """
        files = []

        for model in models:
            for count in truck_counts:
                for variant in ['lower', 'upper']:
                    if count == 1:
                        tpl_path = os.path.join(
                            self.base_dir, model, f"{count}truck",
                            "90", variant, "grade01.rou.xml"
                        )
                        if not os.path.exists(tpl_path):
                            continue

                        with open(tpl_path, 'r') as f:
                            txt = f.read()
                        length = self._extract_length(txt)

                        for sigma, tau in sigma_tau_pairs:
                            for accel in accels:
                                name = (
                                    f"route_{model}_{count}truck_{variant}"
                                    f"_minGap_0"
                                    f"_tau_{tau}"
                                    f"_accel_{accel}"
                                    f"_length_{length}"
                                    f"_sigma_{sigma}.rou.xml"
                                )
                                out_path = os.path.join(self.output_dir, name)
                                with open(out_path, 'w') as f:
                                    f.write(txt)
                                files.append(out_path)
                    else:
                        for gap in min_gaps:
                            tpl_path = os.path.join(
                                self.base_dir, model, f"{count}truck",
                                "90", str(int(gap)), variant, "grade01.rou.xml"
                            )
                            if not os.path.exists(tpl_path):
                                continue

                            with open(tpl_path, 'r') as f:
                                txt = f.read()
                            length = self._extract_length(txt)

                            for sigma, tau in sigma_tau_pairs:
                                for accel in accels:
                                    name = (
                                        f"route_{model}_{count}truck_{variant}"
                                        f"_minGap_{gap}"
                                        f"_tau_{tau}"
                                        f"_accel_{accel}"
                                        f"_length_{length}"
                                        f"_sigma_{sigma}.rou.xml"
                                    )
                                    out_path = os.path.join(self.output_dir, name)
                                    with open(out_path, 'w') as f:
                                        f.write(txt)
                                    files.append(out_path)

        print(f"  Generated {len(files)} platooning route files")
        return files

    @staticmethod
    def parse_platooning_route(route_file: str) -> Optional[dict]:
        """
        Extract parameters from a platooning route filename.

        Returns dict with: model, truck_count, variant, minGap, tau,
                          accel, length, sigma
        """
        pattern = re.compile(
            r'^route_(\w+)_(\d+)truck_(lower|upper)_minGap_([\d\.]+)'
            r'_tau_([\d\.]+)_accel_([\d\.]+)_length_([\d\.]+)'
            r'_sigma_([\d\.]+)\.rou\.xml$'
        )
        match = pattern.match(os.path.basename(route_file))
        if not match:
            return None

        g = match.groups()
        return {
            'model': g[0],
            'truck_count': int(g[1]),
            'variant': g[2],
            'minGap': float(g[3]),
            'tau': float(g[4]),
            'accel': float(g[5]),
            'length': float(g[6]),
            'sigma': float(g[7]),
        }

    # =========================================================================
    # CAR-FOLLOWING ROUTES
    # =========================================================================

    def generate_car_following_routes(
        self,
        models: List[str],
        truck_counts: List[int],
        sigma_tau_pairs: List[Tuple[float, float]],
        accels: List[float],
        speeds: List[int],
        min_gaps: List[float]
    ) -> List[str]:
        """
        Generate route files for car-following simulations.

        Template structure:
            {base_dir}/{model}/{count}truck/{variant}/grade2.rou.xml

        Unlike platooning, car-following templates do NOT have speed or gap
        subfolders. Instead, speed/sigma/tau/accel/minGap are injected
        into the XML via regex substitution.

        Output filename pattern:
            route_{model}_{count}truck_{variant}_sigma_{sigma}_tau_{tau}_accel_{accel}_maxSpeed_{speed}_minGap_{gap}.rou.xml
        """
        files = []

        for model in models:
            for count in truck_counts:
                for variant in ['lower', 'upper']:
                    tpl_path = os.path.join(
                        self.base_dir, model, f"{count}truck",
                        variant, "grade2.rou.xml"
                    )
                    if not os.path.exists(tpl_path):
                        continue

                    with open(tpl_path, 'r') as f:
                        base_txt = f.read()

                    gap_list = [0] if count == 1 else min_gaps

                    for gap in gap_list:
                        for sigma, tau in sigma_tau_pairs:
                            for accel in accels:
                                for speed in speeds:
                                    speed_ms = speed / 3.6

                                    # Re-read template each time to avoid
                                    # cumulative regex replacements
                                    txt = base_txt
                                    txt = re.sub(r'sigma="[^"]+"', f'sigma="{sigma}"', txt)
                                    txt = re.sub(r'tau="[^"]+"', f'tau="{tau}"', txt)
                                    txt = re.sub(r'accel="[^"]+"', f'accel="{accel}"', txt)
                                    txt = re.sub(r'maxSpeed="[^"]+"', f'maxSpeed="{speed_ms}"', txt)
                                    txt = re.sub(r'departSpeed="[^"]+"', f'departSpeed="{speed_ms}"', txt)

                                    if count > 1:
                                        txt = re.sub(r'minGap="[^"]+"', f'minGap="{gap}"', txt)

                                    name = (
                                        f"route_{model}_{count}truck_{variant}"
                                        f"_sigma_{sigma}"
                                        f"_tau_{tau}"
                                        f"_accel_{accel}"
                                        f"_maxSpeed_{speed}"
                                        f"_minGap_{gap}.rou.xml"
                                    )
                                    out_path = os.path.join(self.output_dir, name)
                                    with open(out_path, 'w') as f:
                                        f.write(txt)
                                    files.append(out_path)

        print(f"  Generated {len(files)} car-following route files")
        return files

    @staticmethod
    def parse_car_following_route(route_file: str) -> Optional[dict]:
        """
        Extract parameters from a car-following route filename.

        Returns dict with: model, truck_count, variant, sigma, tau,
                          accel, speed, minGap
        """
        pattern = re.compile(
            r'^route_(\w+)_(\d+)truck_(lower|upper)'
            r'_sigma_([\d\.]+)_tau_([\d\.]+)_accel_([\d\.]+)'
            r'_maxSpeed_([\d\.]+)_minGap_([\d\.]+)\.rou\.xml$'
        )
        match = pattern.match(os.path.basename(route_file))
        if not match:
            return None

        g = match.groups()
        return {
            'model': g[0],
            'truck_count': int(g[1]),
            'variant': g[2],
            'sigma': float(g[3]),
            'tau': float(g[4]),
            'accel': float(g[5]),
            'speed': int(float(g[6])),
            'minGap': float(g[7]),
        }

    # =========================================================================
    # COMMON
    # =========================================================================

    def _extract_length(self, content: str) -> str:
        """Extract vehicle length from route file XML content."""
        match = re.search(r'length="([\d\.]+)"', content)
        return match.group(1) if match else "10.0"
