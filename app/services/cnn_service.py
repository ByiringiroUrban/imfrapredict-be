import random

def detect_visual_defects(structure_name: str) -> list[dict]:
    """
    Simulates a Convolutional Neural Network (CNN) inference model running defect
    detection (e.g. YOLO/VGG) on satellite/drone or camera inspection images.
    
    Returns a list of detected bounding boxes with confidence levels.
    """
    defects = []
    name_lower = structure_name.lower()
    
    # Deterministic simulations based on structure names to represent realistic Kigali scans
    if "nyabugogo" in name_lower:
        defects = [
            {
                "type": "crack",
                "label": "Structural Fissure",
                "confidence": 0.912,
                "box": [120, 240, 200, 310], # [ymin, xmin, ymax, xmax] relative pixels
                "severity": "high"
            },
            {
                "type": "spalling",
                "label": "Concrete Spalling",
                "confidence": 0.845,
                "box": [320, 150, 410, 290],
                "severity": "critical"
            }
        ]
    elif "gatsata" in name_lower:
        defects = [
            {
                "type": "erosion",
                "label": "Embankment Erosion",
                "confidence": 0.941,
                "box": [80, 50, 250, 480],
                "severity": "critical"
            }
        ]
    elif "nyabarongo" in name_lower:
        defects = [
            {
                "type": "corrosion",
                "label": "Truss Steel Corrosion",
                "confidence": 0.887,
                "box": [150, 200, 220, 420],
                "severity": "critical"
            },
            {
                "type": "crack",
                "label": "Minor Abutment Crack",
                "confidence": 0.654,
                "box": [450, 100, 480, 180],
                "severity": "low"
            }
        ]
    elif "kanombe" in name_lower:
        defects = [
            {
                "type": "pothole",
                "label": "Asphalt Pothole",
                "confidence": 0.876,
                "box": [220, 340, 290, 440],
                "severity": "medium"
            }
        ]
    elif "kicukiro" in name_lower:
        # Flyover is very new, minor or no defects
        defects = [
            {
                "type": "pothole",
                "label": "Surface Wearing",
                "confidence": 0.521,
                "box": [180, 400, 210, 440],
                "severity": "low"
            }
        ]
    else:
        # Default fallback
        defects = [
            {
                "type": "crack",
                "label": "Surface Hairline Crack",
                "confidence": 0.723,
                "box": [100, 100, 150, 200],
                "severity": "low"
            }
        ]
        
    return defects
