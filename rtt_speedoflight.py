"""
RTT vs. Speed-of-Light
Networks Assignment — Measurement & Geography

Run with: python rtt_speedoflight.py   (no sudo needed)
Requires: pip install requests matplotlib numpy
"""

import math, time, os, requests, numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import urllib.request

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

TARGETS = {
    # Original targets (Google TLDs)
    "Tokyo":            {"url": "http://www.google.co.jp",   "coords": (35.6762,  139.6503), "continent": "Asia"},
    "São Paulo":        {"url": "http://www.google.com.br",  "coords": (-23.5505, -46.6333), "continent": "S. America"},
    "Lagos":            {"url": "http://www.google.com.ng",  "coords": (6.5244,     3.3792), "continent": "Africa"},
    "Frankfurt":        {"url": "http://www.google.de",      "coords": (50.1109,    8.6821), "continent": "Europe"},
    "Sydney":           {"url": "http://www.google.com.au",  "coords": (-33.8688, 151.2093), "continent": "Oceania"},
    "Mumbai":           {"url": "http://www.google.co.in",   "coords": (19.0760,   72.8777), "continent": "Asia"},
    "London (Google)":  {"url": "http://www.google.co.uk",   "coords": (51.5074,   -0.1278), "continent": "Europe"},
    "Singapore":        {"url": "http://www.google.com.sg",  "coords": (1.3521,   103.8198), "continent": "Asia"},
    # Additional university targets
    "Sendai":           {"url": "http://www.tohoku.ac.jp",   "coords": (38.2682,  140.8694), "continent": "Asia"},
    "Seoul":            {"url": "http://www.snu.ac.kr",      "coords": (37.4600,  126.9521), "continent": "Asia"},
    "New Delhi":        {"url": "http://www.iitd.ac.in",     "coords": (28.5450,   77.1926), "continent": "Asia"},
    "Santiago":         {"url": "http://www.uchile.cl",      "coords": (-33.4569, -70.6483), "continent": "S. America"},
    "Johannesburg":     {"url": "http://www.wits.ac.za",     "coords": (-26.1900,  28.0300), "continent": "Africa"},
    "Berlin":           {"url": "http://www.fu-berlin.de",   "coords": (52.4537,   13.2939), "continent": "Europe"},
    "London":           {"url": "http://www.imperial.ac.uk", "coords": (51.4988,   -0.1749), "continent": "Europe"},
    "Canberra":         {"url": "http://www.anu.edu.au",     "coords": (-35.2809,  149.1300), "continent": "Oceania"},
}

PROBES           = 15
FIBER_SPEED_KM_S = 200_000
FIGURES_DIR      = "figures"

CONTINENT_COLORS = {
    "Asia":      "#e63946",
    "S. America":"#2a9d8f",
    "Africa":    "#e9c46a",
    "Europe":    "#457b9d",
    "Oceania":   "#a8dadc",
}

# ─────────────────────────────────────────────
# TASK 1 — MEASURE RTTs
# ─────────────────────────────────────────────

def measure_rtt(url: str, probes: int = PROBES) -> dict:
    """
    Measure RTT to `url` using HTTP requests.
    """
    samples = []
    lost    = 0

    for _ in range(probes):
        try:
            start = time.perf_counter()
            urllib.request.urlopen(url, timeout=100)
            elapsed_ms = (time.perf_counter() - start) * 1000
            samples.append(elapsed_ms)
        except Exception:
            lost += 1
        time.sleep(0.2)

    if not samples:
        return {"min_ms": None, "mean_ms": None, "median_ms": None,
                "loss_pct": 100.0, "samples": []}

    arr = np.array(samples)
    return {
        "min_ms":    float(np.min(arr)),
        "mean_ms":   float(np.mean(arr)),
        "median_ms": float(np.median(arr)),
        "loss_pct":  (lost / probes) * 100,
        "samples":   samples,
    }


# ─────────────────────────────────────────────
# TASK 2 — HAVERSINE + INEFFICIENCY
# ─────────────────────────────────────────────

def great_circle_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Compute great-circle distance in km using the Haversine formula.
    """
    R = 6371

    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    dlat   = math.radians(lat2 - lat1)
    dlon   = math.radians(lon2 - lon1)

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def get_my_location() -> tuple[float, float, str]:
    """Return (lat, lon, city) for this machine's public IP."""
    try:
        r = requests.get("https://ipinfo.io/json", timeout=5).json()
        lat, lon = map(float, r["loc"].split(","))
        return lat, lon, r.get("city", "Your Location")
    except Exception:
        print("Could not auto-detect location. Defaulting to Boston.")
        return 42.3601, -71.0589, "Boston"


def compute_inefficiency(results: dict, src_lat: float, src_lon: float) -> dict:
    """
    Annotate each city in results with distance, theoretical min RTT,
    inefficiency ratio, and high-inefficiency flag.
    """
    for city, data in results.items():
        city_lat, city_lon = data["coords"]
        dist_km = great_circle_km(src_lat, src_lon, city_lat, city_lon)
        theoretical_min_ms = (dist_km / FIBER_SPEED_KM_S) * 2 * 1000

        median_ms = data.get("median_ms")
        if median_ms is not None:
            ratio = median_ms / theoretical_min_ms
            high  = ratio > 3.0
        else:
            ratio = None
            high  = False

        data["distance_km"]        = dist_km
        data["theoretical_min_ms"] = theoretical_min_ms
        data["inefficiency_ratio"] = ratio
        data["high_inefficiency"]  = high

    return results


# ─────────────────────────────────────────────
# TASK 3 — PLOTS
# ─────────────────────────────────────────────

def make_plots(results: dict):
    """
    Produce two figures saved to FIGURES_DIR/.
    """
    os.makedirs(FIGURES_DIR, exist_ok=True)
    valid  = {c: d for c, d in results.items() if d.get("median_ms") is not None}
    cities = sorted(valid, key=lambda c: valid[c]["distance_km"])

    # ── Figure 1: Grouped bar chart ───────────
    fig, ax = plt.subplots(figsize=(11, 6))

    x       = np.arange(len(cities))
    width   = 0.35
    medians = [valid[c]["median_ms"]        for c in cities]
    theors  = [valid[c]["theoretical_min_ms"] for c in cities]

    bars1 = ax.bar(x - width / 2, medians, width, label="Measured Median RTT",    color="#457b9d")
    bars2 = ax.bar(x + width / 2, theors,  width, label="Theoretical Minimum RTT", color="#a8dadc", edgecolor="#457b9d")

    ax.set_xticks(x)
    ax.set_xticklabels(cities, rotation=20, ha="right")
    ax.set_xlabel("City (sorted by distance from source)")
    ax.set_ylabel("RTT (ms)")
    ax.set_title("Measured vs. Theoretical Minimum RTT by City")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(f"{FIGURES_DIR}/fig1_rtt_comparison.png", dpi=150, bbox_inches="tight")
    plt.close()

    # ── Figure 2: Scatter plot ─────────────────
    fig, ax = plt.subplots(figsize=(10, 7))

    # Dashed theoretical minimum line
    max_dist = max(valid[c]["distance_km"] for c in cities)
    dist_line = np.linspace(0, max_dist * 1.05, 300)
    theor_line = (dist_line / FIBER_SPEED_KM_S) * 2 * 1000
    ax.plot(dist_line, theor_line, "k--", linewidth=1.5, label="Theoretical minimum", zorder=1)

    # Scatter points colored by continent
    for city in cities:
        d      = valid[city]
        color  = CONTINENT_COLORS.get(d["continent"], "#888888")
        ax.scatter(d["distance_km"], d["median_ms"], color=color, s=90, zorder=3)
        ax.annotate(
            city,
            (d["distance_km"], d["median_ms"]),
            textcoords="offset points",
            xytext=(6, 4),
            fontsize=9,
        )

    # Continent legend patches
    seen_continents = {valid[c]["continent"] for c in cities}
    patches = [
        mpatches.Patch(color=CONTINENT_COLORS[cont], label=cont)
        for cont in sorted(seen_continents)
        if cont in CONTINENT_COLORS
    ]
    patches.append(plt.Line2D([0], [0], linestyle="--", color="black", label="Theoretical minimum"))
    ax.legend(handles=patches, loc="upper left")

    ax.set_xlabel("Great-Circle Distance (km)")
    ax.set_ylabel("Measured Median RTT (ms)")
    ax.set_title("RTT vs. Great-Circle Distance from Source")
    ax.grid(linestyle="--", alpha=0.4)

    plt.tight_layout()
    plt.savefig(f"{FIGURES_DIR}/fig2_distance_scatter.png", dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Figures saved to {FIGURES_DIR}/")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    src_lat, src_lon, src_city = get_my_location()
    print(f"Your location: {src_city} ({src_lat:.4f}, {src_lon:.4f})\n")

    results = {}
    for city, info in TARGETS.items():
        print(f"Probing {city} ({info['url']}) ...", end=" ", flush=True)
        stats = measure_rtt(info["url"])
        results[city] = {**stats, "coords": info["coords"], "continent": info["continent"]}
        med = stats.get("median_ms")
        print(f"median={med:.1f} ms  loss={stats['loss_pct']:.0f}%" if med else "unreachable")

    results = compute_inefficiency(results, src_lat, src_lon)

    print(f"\n{'City':<14} {'Dist km':>8} {'Median ms':>10} {'Theor. ms':>10} {'Ratio':>7}")
    print("─" * 55)
    for city, d in sorted(results.items(), key=lambda x: x[1].get("distance_km", 0)):
        dist  = d.get("distance_km", 0)
        med   = d.get("median_ms")
        theor = d.get("theoretical_min_ms")
        ratio = d.get("inefficiency_ratio")
        flag  = " ⚠️" if d.get("high_inefficiency") else ""
        print(f"{city:<14} {dist:>8.0f} "
              f"{(f'{med:.1f}' if med else 'N/A'):>10} "
              f"{(f'{theor:.1f}' if theor else 'N/A'):>10} "
              f"{(f'{ratio:.2f}' if ratio else 'N/A'):>7}{flag}")

    make_plots(results)

if __name__ == "__main__":
    main()
