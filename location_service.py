import os
import re
import json

_LOCATIONS_CACHE = None

def _load_locations():
    global _LOCATIONS_CACHE
    if _LOCATIONS_CACHE is not None:
        return _LOCATIONS_CACHE
    
    js_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'js', 'location_data.js')
    if not os.path.exists(js_path):
        _LOCATIONS_CACHE = []
        return _LOCATIONS_CACHE

    try:
        with open(js_path, 'r', encoding='utf-8') as f:
            text = f.read()
        m = re.search(r'const INDIA_LOCATIONS\s*=\s*(\[.*?\]);', text, re.DOTALL)
        if m:
            _LOCATIONS_CACHE = json.loads(m.group(1))
        else:
            _LOCATIONS_CACHE = []
    except Exception as e:
        print(f"Error loading location_data.js: {e}")
        _LOCATIONS_CACHE = []
    return _LOCATIONS_CACHE

def lookup_district(query: str):
    """
    Finds state and default PIN code for a given district name or alias.
    Returns dict with keys: district, state, pincode, or None.
    """
    if not query or not isinstance(query, str):
        return None
    clean = re.sub(r'[^a-z0-9]', '', query.lower())
    if len(clean) < 2:
        return None

    locations = _load_locations()
    
    # 1. Exact district name match
    for loc in locations:
        if re.sub(r'[^a-z0-9]', '', loc['district'].lower()) == clean:
            return loc

    # 2. Exact alias match
    for loc in locations:
        if any(re.sub(r'[^a-z0-9]', '', a.lower()) == clean for a in loc.get('aliases', [])):
            return loc

    # 3. Starts with match
    for loc in locations:
        if re.sub(r'[^a-z0-9]', '', loc['district'].lower()).startswith(clean):
            return loc

    # 4. Alias starts with
    for loc in locations:
        if any(re.sub(r'[^a-z0-9]', '', a.lower()).startswith(clean) for a in loc.get('aliases', [])):
            return loc

    # 5. Contains substring
    for loc in locations:
        if clean in re.sub(r'[^a-z0-9]', '', loc['district'].lower()):
            return loc

    return None

def lookup_pincode(pincode: str):
    """
    Finds district and state for a given PIN code.
    """
    if not pincode:
        return None
    digits = re.sub(r'\D', '', str(pincode).strip())
    if len(digits) < 3:
        return None

    locations = _load_locations()
    # 1. Exact 6-digit match
    for loc in locations:
        if loc['pincode'] == digits:
            return loc

    # 2. Prefix match
    if len(digits) >= 3:
        prefix = digits[:3]
        for loc in locations:
            if loc['pincode'].startswith(prefix):
                return loc

    return None
