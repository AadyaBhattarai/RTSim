"""
Route file generation utilities for creating SUMO route files.
"""

import os
import re
from typing import List, Tuple, Optional, Dict, Any


class RouteGenerator:
    """
    Generates SUMO route files for platooning and car-following simulations.
    
    Creates route files based on template files with various parameter combinations
    including vehicle counts, gaps, tau values, acceleration, and sigma values.
    """
    
    def __init__(
        self,
        base_simulation_dir: str,
        output_dir: str = "generated_routes"
    ):
        """
        Initialize the route generator.
        
        Args:
            base_simulation_dir: Base directory containing template route files
            output_dir: Directory to store generated route files
        """
        self.base_simulation_dir = base_simulation_dir
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
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
        
        Args:
            models: List of vehicle model names
            truck_counts: List of truck counts per platoon
            min_gaps: List of minimum gap values in meters
            sigma_tau_pairs: List of (sigma, tau) parameter pairs
            accels: List of acceleration values
            
        Returns:
            List of paths to generated route files
        """
        generated_files = []
        
        for model in models:
            for count in truck_counts:
                for variant in ['lower', 'upper']:
                    if count == 1:
                        # Single truck: no gap variation
                        files = self._generate_single_truck_routes(
                            model, count, variant, sigma_tau_pairs, accels
                        )
                    else:
                        # Multiple trucks: iterate over gap values
                        files = self._generate_multi_truck_routes(
                            model, count, variant, min_gaps, sigma_tau_pairs, accels
                        )
                    generated_files.extend(files)
                    
        print(f"Generated {len(generated_files)} route files")
        return generated_files
    
    def _generate_single_truck_routes(
        self,
        model: str,
        count: int,
        variant: str,
        sigma_tau_pairs: List[Tuple[float, float]],
        accels: List[float]
    ) -> List[str]:
        """Generate routes for single-truck configurations."""
        generated = []
        
        template_path = os.path.join(
            self.base_simulation_dir, model, f"{count}truck", "90", variant, "grade01.rou.xml"
        )
        
        if not os.path.exists(template_path):
            return generated
            
        with open(template_path, 'r') as f:
            template_content = f.read()
            
        # Extract vehicle length from template
        length = self._extract_length(template_content)
        
        for sigma, tau in sigma_tau_pairs:
            for accel in accels:
                filename = self._create_route_filename(
                    model, count, variant, 0, tau, accel, length, sigma
                )
                output_path = os.path.join(self.output_dir, filename)
                
                with open(output_path, 'w') as f:
                    f.write(template_content)
                    
                generated.append(output_path)
                
        return generated
    
    def _generate_multi_truck_routes(
        self,
        model: str,
        count: int,
        variant: str,
        min_gaps: List[float],
        sigma_tau_pairs: List[Tuple[float, float]],
        accels: List[float]
    ) -> List[str]:
        """Generate routes for multi-truck configurations."""
        generated = []
        
        for gap in min_gaps:
            template_path = os.path.join(
                self.base_simulation_dir, model, f"{count}truck", "90",
                str(int(gap)), variant, "grade01.rou.xml"
            )
            
            if not os.path.exists(template_path):
                continue
                
            with open(template_path, 'r') as f:
                template_content = f.read()
                
            length = self._extract_length(template_content)
            
            for sigma, tau in sigma_tau_pairs:
                for accel in accels:
                    filename = self._create_route_filename(
                        model, count, variant, gap, tau, accel, length, sigma
                    )
                    output_path = os.path.join(self.output_dir, filename)
                    
                    with open(output_path, 'w') as f:
                        f.write(template_content)
                        
                    generated.append(output_path)
                    
        return generated
    
    def _extract_length(self, content: str) -> str:
        """Extract vehicle length from route file content."""
        match = re.search(r'length="([\d\.]+)"', content)
        return match.group(1) if match else "10.0"
    
    def _create_route_filename(
        self,
        model: str,
        count: int,
        variant: str,
        min_gap: float,
        tau: float,
        accel: float,
        length: str,
        sigma: float
    ) -> str:
        """Create a standardized route filename."""
        return (
            f"route_{model}_{count}truck_{variant}"
            f"_minGap_{min_gap}"
            f"_tau_{tau}"
            f"_accel_{accel}"
            f"_length_{length}"
            f"_sigma_{sigma}.rou.xml"
        )
    
    def generate_car_following_routes(
        self,
        models: List[str],
        vehicle_counts: List[int],
        min_gaps: List[float],
        sigma_tau_pairs: List[Tuple[float, float]],
        accels: List[float]
    ) -> List[str]:
        """
        Generate route files for car-following simulations.
        
        Uses the same structure as platooning routes but with car-following prefix.
        
        Args:
            models: List of vehicle model names
            vehicle_counts: List of vehicle counts
            min_gaps: List of minimum gap values in meters
            sigma_tau_pairs: List of (sigma, tau) parameter pairs
            accels: List of acceleration values
            
        Returns:
            List of paths to generated route files
        """
        # Reuse platooning route generation with different output naming
        return self.generate_platooning_routes(
            models, vehicle_counts, min_gaps, sigma_tau_pairs, accels
        )
    
    def parse_route_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Parse parameters from a route filename.
        
        Args:
            filename: Route filename to parse
            
        Returns:
            Dictionary of parsed parameters or None if parsing fails
        """
        pattern = re.compile(
            r'^route_(\w+)_(\d+)truck_(lower|upper)_minGap_([\d\.]+)_tau_([\d\.]+)'
            r'_accel_([\d\.]+)_length_([\d\.]+)_sigma_([\d\.]+)\.rou\.xml$'
        )
        
        match = pattern.match(os.path.basename(filename))
        if not match:
            return None
            
        model, n, variant, min_gap, tau, accel, length, sigma = match.groups()
        
        return {
            'model': model,
            'truck_count': int(n),
            'variant': variant,
            'min_gap': float(min_gap),
            'tau': float(tau),
            'accel': float(accel),
            'length': float(length),
            'sigma': float(sigma),
        }
    
    def list_generated_routes(self) -> List[str]:
        """
        List all generated route files.
        
        Returns:
            List of paths to route files
        """
        routes = []
        for filename in os.listdir(self.output_dir):
            if filename.endswith('.rou.xml'):
                routes.append(os.path.join(self.output_dir, filename))
        return sorted(routes)
    
    def clean_routes(self) -> None:
        """Remove all generated route files."""
        for filename in os.listdir(self.output_dir):
            if filename.endswith('.rou.xml'):
                os.remove(os.path.join(self.output_dir, filename))
        print(f"Cleaned route files from {self.output_dir}")
    
    def get_route_count(self) -> int:
        """Get the number of generated route files."""
        return len([f for f in os.listdir(self.output_dir) if f.endswith('.rou.xml')])
