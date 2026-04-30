DRAFT_REGIONS = {
    "ally_bans": [
        (0.02, 0.08, 0.22, 0.14),
        (0.27, 0.08, 0.47, 0.14),
        (0.52, 0.08, 0.72, 0.14),
        (0.77, 0.08, 0.97, 0.14),
    ],
    "enemy_bans": [
        (0.02, 0.15, 0.22, 0.21),
        (0.27, 0.15, 0.47, 0.21),
        (0.52, 0.15, 0.72, 0.21),
        (0.77, 0.15, 0.97, 0.21),
    ],
    "ally_picks": [
        (0.01, 0.25, 0.18, 0.38),
        (0.01, 0.39, 0.18, 0.52),
        (0.01, 0.53, 0.18, 0.66),
        (0.01, 0.67, 0.18, 0.80),
        (0.01, 0.81, 0.18, 0.94),
    ],
    "enemy_picks": [
        (0.82, 0.25, 0.99, 0.38),
        (0.82, 0.39, 0.99, 0.52),
        (0.82, 0.53, 0.99, 0.66),
        (0.82, 0.67, 0.99, 0.80),
        (0.82, 0.81, 0.99, 0.94),
    ],
}


def get_pixel_regions(screen_width: int, screen_height: int) -> dict:
    pixel_regions = {}
    for category, slots in DRAFT_REGIONS.items():
        pixel_regions[category] = []
        for x1_pct, y1_pct, x2_pct, y2_pct in slots:
            x1 = int(x1_pct * screen_width)
            y1 = int(y1_pct * screen_height)
            x2 = int(x2_pct * screen_width)
            y2 = int(y2_pct * screen_height)
            pixel_regions[category].append((x1, y1, x2, y2))
    return pixel_regions
