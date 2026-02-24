# File: ~/JJs-MediaCraft/src/ffmpeg/encoding_profiles.py

import sys
import os

# Sets the path for shared utils imports 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'utils')))
from debug import debug_print

# Dictionary for Codec profiles with added pixel format

encoding_profiles = {
    "0": {"codec": "prores_ks", "profile_v": "0", "name": "ProRes422Proxy", "display_name": "ProRes 422 (Proxy)", "pix_fmt": "yuv422p10le", "vendor": "apl0"},
    "1": {"codec": "prores_ks", "profile_v": "1", "name": "ProRes422LT", "display_name": "ProRes 422 (LT)", "pix_fmt": "yuv422p10le", "vendor": "apl0"},
    "2": {"codec": "prores_ks", "profile_v": "2", "name": "ProRes422", "display_name": "ProRes 422 (Normal)", "pix_fmt": "yuv422p10le", "vendor": "apl0"},
    "3": {"codec": "prores_ks", "profile_v": "3", "name": "ProRes422HQ", "display_name": "ProRes 422 (HQ)", "pix_fmt": "yuv422p10le", "vendor": "apl0"},
    "4": {"codec": "prores_ks", "profile_v": "4", "name": "ProRes4444","display_name": "ProRes 4444 (Can Include Alpha)", "pix_fmt": "yuva444p10le", "vendor": "apl0"},  # 4:4:4 with alpha
    "5": {"codec": "prores_ks", "profile_v": "5", "name": "ProRes4444XQ", "display_name": "ProRes 4444 (XQ - Can Inlcude Alpha)", "pix_fmt": "yuva444p10le", "vendor": "apl0"},  # 4:4:4 with alpha
    "6": {"codec": "hap", "name": "HAP", "display_name": "HAP"},
    "7": {"codec": "hap", "name": "HAP_Alpha", "display_name": "HAP Alpha", "format": "hap_alpha"},
    "8": {"codec": "hap", "name": "HAP_Q", "display_name": "HAP Q", "format": "hap_q"},
    "9": {"codec": "libx264", "name": "H.264", "display_name": "H.264 MP4", "format": "h264", "pix_fmt": "yuv420p"}
}

def display_profiles():
    debug_print("Running display_profiles Function...")
    """Display available encoding profiles."""
    print()
    for key, value in encoding_profiles.items():
        print(f"{key} - {value['display_name']}")