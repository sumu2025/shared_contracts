"""
Version management utilities.
"""

import re
from typing import Dict, Tuple, Optional
from packaging import version


def get_version(version_str: str) -> Dict[str, int]:
    """
    Parse a version string into its components.
    
    Args:
        version_str: Version string (e.g., "1.2.3")
        
    Returns:
        Dictionary with major, minor, and patch versions
        
    Raises:
        ValueError: If the version string is invalid
    """
    pattern = r"^(\d+)\.(\d+)\.(\d+)(?:-([\w.-]+))?(?:\+([\w.-]+))?$"
    match = re.match(pattern, version_str)
    
    if not match:
        raise ValueError(f"Invalid version string: {version_str}")
    
    major, minor, patch = map(int, match.groups()[:3])
    prerelease = match.group(4)
    build = match.group(5)
    
    result = {
        "major": major,
        "minor": minor,
        "patch": patch,
    }
    
    if prerelease:
        result["prerelease"] = prerelease
    
    if build:
        result["build"] = build
    
    return result


def compare_versions(version1: str, version2: str) -> int:
    """
    Compare two semantic version strings.
    
    Args:
        version1: First version string
        version2: Second version string
        
    Returns:
        -1 if version1 < version2, 0 if equal, 1 if version1 > version2
        
    Raises:
        ValueError: If either version string is invalid
    """
    v1 = version.parse(version1)
    v2 = version.parse(version2)
    
    if v1 < v2:
        return -1
    elif v1 > v2:
        return 1
    else:
        return 0


def is_compatible_version(
    current_version: str,
    min_version: Optional[str] = None,
    max_version: Optional[str] = None,
) -> bool:
    """
    Check if a version is compatible with specified constraints.
    
    Args:
        current_version: Version to check
        min_version: Minimum version (inclusive)
        max_version: Maximum version (exclusive)
        
    Returns:
        Whether the version is compatible
        
    Raises:
        ValueError: If any version string is invalid
    """
    v_current = version.parse(current_version)
    
    if min_version is not None:
        v_min = version.parse(min_version)
        if v_current < v_min:
            return False
    
    if max_version is not None:
        v_max = version.parse(max_version)
        if v_current >= v_max:
            return False
    
    return True
