import os
import cv2
import numpy as np
import trimesh
from shapely.geometry import Polygon
import logging

logger = logging.getLogger(__name__)

def generate_mesh_from_image_path(image_path: str, output_path: str):
    """
    Reads an image, uses OpenCV edge detection to extract the silhouette, 
    and extrudes it into a 3D mesh (.obj).
    """
    try:
        logger.info(f"Processing image with OpenCV for {image_path}")
        
        # 1. Load image in grayscale
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError("Failed to decode image")
            
        # 2. Resize to a manageable resolution for fast processing (e.g. max 800px)
        max_dim = 800
        h, w = img.shape
        if max(h, w) > max_dim:
            scale_factor = max_dim / max(h, w)
            img = cv2.resize(img, (int(w * scale_factor), int(h * scale_factor)))
            
        # 3. Apply Gaussian Blur to smooth noise
        blurred = cv2.GaussianBlur(img, (5, 5), 0)
        
        # 4. Otsu's thresholding to separate foreground/background
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # 5. Morphological closing to fill small holes inside the object
        kernel = np.ones((5,5), np.uint8)
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=3)
        
        # 6. Find Contours
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            raise ValueError("No structure found in image")
            
        # Use largest contour
        contour = max(contours, key=cv2.contourArea)
        
        # Simplify contour for cleaner 3D geometry
        epsilon = 0.005 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        if len(approx) < 3:
            raise ValueError("Contour too simple to form a polygon")
            
        # Extract 2D points
        points = approx.reshape(-1, 2).astype(float)
        
        # Normalize and scale to a fixed 3D size
        x_min, y_min = points.min(axis=0)
        x_max, y_max = points.max(axis=0)
        width = x_max - x_min
        height = y_max - y_min
        
        if width == 0 or height == 0:
            raise ValueError("Invalid object dimensions")
            
        scale = 10.0 / max(width, height)
        
        # Center and flip Y (OpenCV is Y-down, 3D is Y-up)
        points[:, 0] = (points[:, 0] - (x_min + width/2)) * scale
        points[:, 1] = -(points[:, 1] - (y_min + height/2)) * scale
        
        # Create Polygon
        poly = Polygon(points)
        if not poly.is_valid:
            poly = poly.buffer(0) # Fix self-intersections
            if poly.geom_type == 'MultiPolygon':
                # Use the largest polygon by area
                poly = max(poly.geoms, key=lambda p: p.area)
            
        logger.info("Extruding 3D mesh")
        # Extrude by 2 units depth
        mesh = trimesh.creation.extrude_polygon(poly, height=2.0)
        
        # Center the mesh on Z
        mesh.apply_translation([0, 0, -1.0])
        
        # Ensure output directory exists
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        
        # Export to OBJ
        mesh.export(output_path)
        logger.info(f"Successfully generated mesh at {output_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error generating 3D mesh: {e}")
        return False
