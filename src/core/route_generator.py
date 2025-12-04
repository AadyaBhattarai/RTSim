"""
Route file generation for platooning and car following simulations.
"""

import os
import re
from typing import List, Tuple


class RouteGenerator:
    """Generates route files for both platooning and car following simulations."""
    
    def __init__(self, base_dir: str, output_dir: str = "generated_routes"):
        """
        Args:
            base_dir: Base directory containing template route files
            output_dir: Directory to store generated route files
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
        Generate route files for PLATOONING simulations.
        
        Template path: {base_dir}/{model}/{count}truck/90/{gap}/{variant}/grade01.rou.xml
        Output pattern: route_{model}_{count}truck_{variant}_minGap_{gap}_tau_{tau}_accel_{accel}_length_{length}_sigma_{sigma}.rou.xml
        """
        files = []
        
        for model in models:
            for count in truck_counts:
                for variant in ['lower', 'upper']:
                    if count == 1:
                        tpl_path = os.path.join(self.base_dir, model, f"{count}truck", "90", variant, "grade01.rou.xml")
                        if not os.path.exists(tpl_path):
                            continue
                        
                        with open(tpl_path, 'r') as f:
                            txt = f.read()
                        
                        length = self._extract_length(txt)
                        
                        for sigma, tau in sigma_tau_pairs:
                            for accel in accels:
                                name = f"route_{model}_{count}truck_{variant}_minGap_0_tau_{tau}_accel_{accel}_length_{length}_sigma_{sigma}.rou.xml"
                                out_path = os.path.join(self.output_dir, name)
                                with open(out_path, 'w') as f:
                                    f.write(txt)
                                files.append(out_path)
                    else:
                        for gap in min_gaps:
                            tpl_path = os.path.join(self.base_dir, model, f"{count}truck", "90", str(int(gap)), variant, "grade01.rou.xml")
                            if not os.path.exists(tpl_path):
                                continue
                            
                            with open(tpl_path, 'r') as f:
                                txt = f.read()
                            
                            length = self._extract_length(txt)
                            
                            for sigma, tau in sigma_tau_pairs:
                                for accel in accels:
                                    name = f"route_{model}_{count}truck_{variant}_minGap_{gap}_tau_{tau}_accel_{accel}_length_{length}_sigma_{sigma}.rou.xml"
                                    out_path = os.path.join(self.output_dir, name)
                                    with open(out_path, 'w') as f:
                                        f.write(txt)
                                    files.append(out_path)
        
        print(f"Generated {len(files)} platooning route files")
        return files
    
    @staticmethod
    def parse_platooning_route(route_file: str) -> dict:
        """
        Parse parameters from a PLATOONING route filename.
        
        Pattern: route_{model}_{count}truck_{variant}_minGap_{gap}_tau_{tau}_accel_{accel}_length_{length}_sigma_{sigma}.rou.xml
        """
        pattern = re.compile(
            r'^route_(\w+)_(\d+)truck_(lower|upper)_minGap_([\d\.]+)_tau_([\d\.]+)'
            r'_accel_([\d\.]+)_length_([\d\.]+)_sigma_([\d\.]+)\.rou\.xml$'
        )
        
        match = pattern.match(os.path.basename(route_file))
        if not match:
            return None
            
        model, n_str, variant, minGap_str, tau_str, accel_str, length_str, sigma_str = match.groups()
        
        return {
            'model': model,
            'truck_count': int(n_str),
            'variant': variant,
            'minGap': float(minGap_str),
            'tau': float(tau_str),
            'accel': float(accel_str),
            'length': float(length_str),
            'sigma': float(sigma_str),
        }
    
    # =========================================================================
    # CAR FOLLOWING ROUTES
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
        Generate route files for CAR FOLLOWING simulations.
        
        Template path: {base_dir}/{model}/{count}truck/{variant}/grade2.rou.xml
        Output pattern: route_{model}_{count}truck_{variant}_sigma_{sigma}_tau_{tau}_accel_{accel}_maxSpeed_{speed}_minGap_{gap}.rou.xml
        """
        files = []
        
        for model in models:
            for count in truck_counts:
                for variant in ['lower', 'upper']:
                    tpl_path = os.path.join(self.base_dir, model, f"{count}truck", variant, "grade2.rou.xml")
                    if not os.path.exists(tpl_path):
                        continue
                    
                    with open(tpl_path, 'r') as f:
                        base_txt = f.read()
                    
                    if count == 1:
                        # Single truck - no minGap iteration
                        for sigma, tau in sigma_tau_pairs:
                            for accel in accels:
                                for speed in speeds:
                                    speed_ms = speed / 3.6
                                    txt = base_txt
                                    txt = re.sub(r'sigma="[^"]+"', f'sigma="{sigma}"', txt)
                                    txt = re.sub(r'tau="[^"]+"', f'tau="{tau}"', txt)
                                    txt = re.sub(r'accel="[^"]+"', f'accel="{accel}"', txt)
                                    txt = re.sub(r'maxSpeed="[^"]+"', f'maxSpeed="{speed_ms}"', txt)
                                    txt = re.sub(r'departSpeed="[^"]+"', f'departSpeed="{speed_ms}"', txt)
                                    
                                    name = f"route_{model}_{count}truck_{variant}_sigma_{sigma}_tau_{tau}_accel_{accel}_maxSpeed_{speed}_minGap_0.rou.xml"
                                    out_path = os.path.join(self.output_dir, name)
                                    with open(out_path, 'w') as f:
                                        f.write(txt)
                                    files.append(out_path)
                    else:
                        # Multiple trucks - iterate minGap
                        for gap in min_gaps:
                            for sigma, tau in sigma_tau_pairs:
                                for accel in accels:
                                    for speed in speeds:
                                        speed_ms = speed / 3.6
                                        txt = base_txt
                                        txt = re.sub(r'sigma="[^"]+"', f'sigma="{sigma}"', txt)
                                        txt = re.sub(r'tau="[^"]+"', f'tau="{tau}"', txt)
                                        txt = re.sub(r'accel="[^"]+"', f'accel="{accel}"', txt)
                                        txt = re.sub(r'maxSpeed="[^"]+"', f'maxSpeed="{speed_ms}"', txt)
                                        txt = re.sub(r'departSpeed="[^"]+"', f'departSpeed="{speed_ms}"', txt)
                                        txt = re.sub(r'minGap="[^"]+"', f'minGap="{gap}"', txt)
                                        
                                        name = f"route_{model}_{count}truck_{variant}_sigma_{sigma}_tau_{tau}_accel_{accel}_maxSpeed_{speed}_minGap_{gap}.rou.xml"
                                        out_path = os.path.join(self.output_dir, name)
                                        with open(out_path, 'w') as f:
                                            f.write(txt)
                                        files.append(out_path)
        
        print(f"Generated {len(files)} car following route files")
        return files
    
    @staticmethod
    def parse_car_following_route(route_file: str) -> dict:
        """
        Parse parameters from a CAR FOLLOWING route filename.
        
        Pattern: route_{model}_{count}truck_{variant}_sigma_{sigma}_tau_{tau}_accel_{accel}_maxSpeed_{speed}_minGap_{gap}.rou.xml
        """
        pattern = re.compile(
            r'^route_(\w+)_(\d+)truck_(lower|upper)_sigma_([\d\.]+)_tau_([\d\.]+)'
            r'_accel_([\d\.]+)_maxSpeed_([\d\.]+)_minGap_([\d\.]+)\.rou\.xml$'
        )
        
        match = pattern.match(os.path.basename(route_file))
        if not match:
            return None
        
        model, cnt_str, variant, sigma_str, tau_str, accel_str, speed_str, gap_str = match.groups()
        
        return {
            'model': model,
            'truck_count': int(cnt_str),
            'variant': variant,
            'sigma': float(sigma_str),
            'tau': float(tau_str),
            'accel': float(accel_str),
            'speed': int(float(speed_str)),
            'minGap': float(gap_str),
        }
    
    # =========================================================================
    # COMMON METHODS
    # =========================================================================
    
    def _extract_length(self, content: str) -> str:
        """Extract vehicle length from route file content."""
        match = re.search(r'length="([\d\.]+)"', content)
        return match.group(1) if match else "10.0"
    
    def list_routes(self) -> List[str]:
        """List all generated route files."""
        return [os.path.join(self.output_dir, f) for f in os.listdir(self.output_dir) if f.endswith('.rou.xml')]
    
    def clean(self) -> None:
        """Remove all generated route files."""
        for f in os.listdir(self.output_dir):
            if f.endswith('.rou.xml'):
                os.remove(os.path.join(self.output_dir, f))
