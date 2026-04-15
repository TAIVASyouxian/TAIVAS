
import streamlit.components.v1 as components

try:
    from thermal_principle_component import render_thermal_principle_simulation as _base_thermal_principle
except Exception:
    _base_thermal_principle = None


def render_thermal_principle_simulation(*args, **kwargs):
    if _base_thermal_principle is not None:
        return _base_thermal_principle(*args, **kwargs)

    fallback = """
    <div style="font-family: Inter, Arial, sans-serif; color:#e5e7eb; padding:12px;">
      <div style="font-size:26px; font-weight:800; margin-bottom:8px;">Thermal Recovery Principle (Concept Mode)</div>
      <div style="font-size:14px; color:#cbd5e1; line-height:1.6;">
        The thermal principle component could not be loaded. Please make sure
        <b>thermal_principle_component.py</b> is in the project root next to your main app file.
      </div>
    </div>
    """
    components.html(fallback, height=220, scrolling=False)


def _wrap_card(title: str, subtitle: str, svg_html: str, side_html: str = "", height: int = 720):
    html = f"""
    <div style="font-family: Inter, Arial, sans-serif; color:#e5e7eb; padding-bottom:12px;">
      <div style="margin-bottom:10px;">
        <div style="font-size:28px; font-weight:800; line-height:1.2;">{title}</div>
        <div style="font-size:14px; color:#94a3b8; margin-top:6px;">{subtitle}</div>
      </div>
      <div style="display:grid; grid-template-columns: 1fr 320px; gap:18px; align-items:start;">
        <div style="background:#07111f; border:1px solid #17304d; border-radius:18px; padding:14px; overflow:hidden;">
          {svg_html}
        </div>
        <div style="background:#081220; border:1px solid #17304d; border-radius:18px; padding:16px;">
          {side_html}
        </div>
      </div>
    </div>
    """
    components.html(html, height=height, scrolling=False)


def render_phase_change_buffer_concept(
    heat_load_mw: float = 25.1,
    buffer_state_pct: float = 72.0,
    demand_reduction_pct: float = 11.0,
    reserve_bonus_hours: float = 6.0,
    height: int = 720,
):
    core_w = 220
    side_html = f"""
      <div style="font-size:18px; font-weight:800; margin-bottom:10px;">How to interpret this panel</div>
      <div style="font-size:14px; line-height:1.65; color:#cbd5e1;">
        <b>Blue liquid loop:</b> cold-side storage circulation.<br>
        <b>Red liquid loop:</b> heat recovery / discharge circulation.<br>
        <b>Center tank:</b> conceptual phase-change storage block.<br><br>
        The liquid fill is clipped inside the conduit boundary so it reads like
        <b>contained coolant flow</b>, not particles or leakage.
      </div>
      <div style="margin-top:16px; border-top:1px solid #17304d; padding-top:14px;">
        <div style="font-size:16px; font-weight:800; margin-bottom:8px;">Derived concept outputs</div>
        <div style="font-size:14px; line-height:1.7; color:#cbd5e1;">
          Buffer state: <b>{buffer_state_pct:.0f}%</b><br>
          Demand reduction: <b>{demand_reduction_pct:.1f}%</b><br>
          Reserve bonus: <b>{reserve_bonus_hours:.1f} h</b>
        </div>
      </div>
    """
    svg = f"""
    <svg viewBox="0 0 1200 620" width="100%" height="100%" aria-label="phase change thermal buffer concept">
      <defs>
        <linearGradient id="pcmBluePipe" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#082f49"/><stop offset="100%" stop-color="#0c4a6e"/>
        </linearGradient>
        <linearGradient id="pcmRedPipe" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#4c0519"/><stop offset="100%" stop-color="#7f1d1d"/>
        </linearGradient>
        <linearGradient id="pcmBlueLiquid" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#0ea5e9"/>
          <stop offset="25%" stop-color="#67e8f9"/>
          <stop offset="50%" stop-color="#ecfeff"/>
          <stop offset="75%" stop-color="#7dd3fc"/>
          <stop offset="100%" stop-color="#0284c7"/>
          <animateTransform attributeName="gradientTransform" type="translate" values="-220 0;220 0;-220 0" dur="3.0s" repeatCount="indefinite"/>
        </linearGradient>
        <linearGradient id="pcmRedLiquid" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#ef4444"/>
          <stop offset="25%" stop-color="#fda4af"/>
          <stop offset="50%" stop-color="#fff1f2"/>
          <stop offset="75%" stop-color="#fb7185"/>
          <stop offset="100%" stop-color="#be123c"/>
          <animateTransform attributeName="gradientTransform" type="translate" values="220 0;-220 0;220 0" dur="3.0s" repeatCount="indefinite"/>
        </linearGradient>
        <mask id="pcmTopBlueMask"><rect x="90" y="226" width="370" height="28" rx="14" fill="white"/></mask>
        <mask id="pcmTopRedMask"><rect x="740" y="226" width="370" height="28" rx="14" fill="white"/></mask>
        <mask id="pcmBottomRedMask"><rect x="90" y="416" width="370" height="28" rx="14" fill="white"/></mask>
        <mask id="pcmBottomBlueMask"><rect x="740" y="416" width="370" height="28" rx="14" fill="white"/></mask>
      </defs>

      <rect x="20" y="20" width="1160" height="580" rx="22" fill="#081220" stroke="#274a72" stroke-width="3"/>
      <rect x="460" y="170" width="280" height="230" rx="26" fill="#0c1a2c" stroke="#4f7cac" stroke-width="4"/>
      <text x="600" y="220" text-anchor="middle" fill="#f8fafc" font-size="34" font-weight="800">PCM Buffer</text>
      <text x="600" y="258" text-anchor="middle" fill="#93c5fd" font-size="22" font-weight="700">Latent heat storage</text>

      <rect x="90" y="226" width="370" height="28" rx="14" fill="url(#pcmBluePipe)"/>
      <rect x="740" y="226" width="370" height="28" rx="14" fill="url(#pcmRedPipe)"/>
      <rect x="90" y="416" width="370" height="28" rx="14" fill="url(#pcmRedPipe)"/>
      <rect x="740" y="416" width="370" height="28" rx="14" fill="url(#pcmBluePipe)"/>

      <rect x="92" y="230" width="366" height="20" rx="10" fill="url(#pcmBlueLiquid)" mask="url(#pcmTopBlueMask)"/>
      <rect x="742" y="230" width="366" height="20" rx="10" fill="url(#pcmRedLiquid)" mask="url(#pcmTopRedMask)"/>
      <rect x="92" y="420" width="366" height="20" rx="10" fill="url(#pcmRedLiquid)" mask="url(#pcmBottomRedMask)"/>
      <rect x="742" y="420" width="366" height="20" rx="10" fill="url(#pcmBlueLiquid)" mask="url(#pcmBottomBlueMask)"/>

      <rect x="120" y="110" width="{core_w}" height="132" rx="22" fill="#0d1e30" stroke="#4f89c6" stroke-width="3"/>
      <text x="{120 + core_w/2}" y="160" text-anchor="middle" fill="#f8fafc" font-size="28" font-weight="800">Server Core</text>
      <text x="{120 + core_w/2}" y="198" text-anchor="middle" fill="#fca5a5" font-size="22" font-weight="700">Heat load</text>
      <text x="{120 + core_w/2}" y="234" text-anchor="middle" fill="#ffffff" font-size="30" font-weight="800">{heat_load_mw:.1f} MW</text>

      <rect x="860" y="110" width="220" height="132" rx="22" fill="#0d1e30" stroke="#4f89c6" stroke-width="3"/>
      <text x="970" y="158" text-anchor="middle" fill="#f8fafc" font-size="26" font-weight="800">Buffer State</text>
      <text x="970" y="206" text-anchor="middle" fill="#fde68a" font-size="30" font-weight="800">{buffer_state_pct:.0f}%</text>

      <rect x="70" y="500" width="1060" height="72" rx="16" fill="#091827" stroke="#1e3a5f" stroke-width="2"/>
      <rect x="92" y="515" width="310" height="42" rx="10" fill="#0d1e30" stroke="#264c75" stroke-width="1.5"/>
      <rect x="445" y="515" width="310" height="42" rx="10" fill="#0d1e30" stroke="#264c75" stroke-width="1.5"/>
      <rect x="798" y="515" width="310" height="42" rx="10" fill="#0d1e30" stroke="#264c75" stroke-width="1.5"/>

      <text x="247" y="543" text-anchor="middle" fill="#d9f99d" font-size="16" font-weight="800">Demand reduction: {demand_reduction_pct:.1f}%</text>
      <text x="600" y="543" text-anchor="middle" fill="#bfdbfe" font-size="16" font-weight="800">Reserve bonus: {reserve_bonus_hours:.1f} h</text>
      <text x="953" y="543" text-anchor="middle" fill="#fca5a5" font-size="16" font-weight="800">Peak smoothing active</text>
    </svg>
    """
    _wrap_card("Phase-Change Thermal Buffer (Concept)",
               "Conceptual latent-heat buffering and charge/discharge visualization.",
               svg, side_html, height=height)


def render_ground_thermal_sink_concept(
    cooling_offset_pct: float = 14.0,
    sink_utilization_pct: float = 63.0,
    saturation_risk_pct: float = 21.0,
    height: int = 720,
):
    side_html = f"""
      <div style="font-size:18px; font-weight:800; margin-bottom:10px;">How to interpret this panel</div>
      <div style="font-size:14px; line-height:1.65; color:#cbd5e1;">
        <b>Upper chamber:</b> facility thermal load zone.<br>
        <b>Lower bedrock:</b> conceptual ground thermal sink.<br>
        <b>Blue liquid columns:</b> heat rejection into subsurface mass.<br><br>
        The liquid is clipped inside vertical conduits so it reads like <b>sealed coolant flow</b>.
      </div>
      <div style="margin-top:16px; border-top:1px solid #17304d; padding-top:14px;">
        <div style="font-size:16px; font-weight:800; margin-bottom:8px;">Derived concept outputs</div>
        <div style="font-size:14px; line-height:1.7; color:#cbd5e1;">
          Cooling offset: <b>{cooling_offset_pct:.1f}%</b><br>
          Sink utilization: <b>{sink_utilization_pct:.0f}%</b><br>
          Saturation risk: <b>{saturation_risk_pct:.0f}%</b>
        </div>
      </div>
    """
    util_width = max(40, int(960 * sink_utilization_pct / 100))
    svg = f"""
    <svg viewBox="0 0 1200 620" width="100%" height="100%">
      <defs>
        <linearGradient id="groundPipe" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="#082f49"/><stop offset="100%" stop-color="#0c4a6e"/>
        </linearGradient>
        <linearGradient id="groundLiquid" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="#0ea5e9"/>
          <stop offset="25%" stop-color="#67e8f9"/>
          <stop offset="50%" stop-color="#ecfeff"/>
          <stop offset="75%" stop-color="#7dd3fc"/>
          <stop offset="100%" stop-color="#0284c7"/>
          <animateTransform attributeName="gradientTransform" type="translate" values="0 -180;0 180;0 -180" dur="2.8s" repeatCount="indefinite"/>
        </linearGradient>
        <mask id="groundMaskL"><rect x="449" y="220" width="22" height="220" rx="11" fill="white"/></mask>
        <mask id="groundMaskR"><rect x="729" y="220" width="22" height="220" rx="11" fill="white"/></mask>
      </defs>
      <rect x="20" y="20" width="1160" height="580" rx="22" fill="#081220" stroke="#274a72" stroke-width="3"/>
      <rect x="90" y="80" width="1020" height="150" rx="22" fill="#0d1e30" stroke="#4f89c6" stroke-width="3"/>
      <text x="145" y="130" fill="#f8fafc" font-size="30" font-weight="800">Facility Thermal Zone</text>
      <text x="145" y="170" fill="#fca5a5" font-size="22" font-weight="700">Waste heat routed downward for buffering</text>

      <rect x="90" y="300" width="1020" height="220" rx="22" fill="#111827" stroke="#334155" stroke-width="2"/>
      <text x="145" y="350" fill="#e5e7eb" font-size="30" font-weight="800">Ground Thermal Sink</text>
      <text x="145" y="390" fill="#93c5fd" font-size="22" font-weight="700">Subsurface heat absorption concept</text>

      <rect x="449" y="220" width="22" height="220" rx="11" fill="url(#groundPipe)"/>
      <rect x="729" y="220" width="22" height="220" rx="11" fill="url(#groundPipe)"/>
      <rect x="452" y="223" width="16" height="214" rx="8" fill="url(#groundLiquid)" mask="url(#groundMaskL)"/>
      <rect x="732" y="223" width="16" height="214" rx="8" fill="url(#groundLiquid)" mask="url(#groundMaskR)"/>

      <rect x="110" y="540" width="980" height="36" rx="10" fill="#0d1e30" stroke="#264c75" stroke-width="1.5"/>
      <rect x="120" y="546" width="{util_width}" height="24" rx="8" fill="#0ea5e9"/>
      <text x="600" y="565" text-anchor="middle" fill="#e5e7eb" font-size="16" font-weight="800">Sink utilization {sink_utilization_pct:.0f}%</text>

      <rect x="95" y="240" width="280" height="42" rx="10" fill="#0d1e30" stroke="#264c75" stroke-width="1.5"/>
      <text x="235" y="267" text-anchor="middle" fill="#d9f99d" font-size="16" font-weight="800">Cooling offset: {cooling_offset_pct:.1f}%</text>

      <rect x="825" y="240" width="250" height="42" rx="10" fill="#0d1e30" stroke="#264c75" stroke-width="1.5"/>
      <text x="950" y="267" text-anchor="middle" fill="#fca5a5" font-size="16" font-weight="800">Saturation risk: {saturation_risk_pct:.0f}%</text>
    </svg>
    """
    _wrap_card("Ground Thermal Sink (Concept)",
               "Conceptual ground-coupled cooling and subsurface heat buffering visualization.",
               svg, side_html, height=height)


def render_distributed_thermal_control_concept(
    node_availability_pct: float = 82.0,
    rerouting_efficiency_pct: float = 74.0,
    damage_ratio_pct: float = 18.0,
    protected_core_pct: float = 86.0,
    height: int = 720,
):
    side_html = f"""
      <div style="font-size:18px; font-weight:800; margin-bottom:10px;">How to interpret this panel</div>
      <div style="font-size:14px; line-height:1.65; color:#cbd5e1;">
        <b>Blue liquid links:</b> primary active control paths.<br>
        <b>Red liquid links:</b> emergency rerouting paths.<br>
        <b>Muted gray links:</b> inactive branches.<br><br>
        Fault marks are softened so the routing remains visually dominant.
      </div>
      <div style="margin-top:16px; border-top:1px solid #17304d; padding-top:14px;">
        <div style="font-size:16px; font-weight:800; margin-bottom:8px;">Derived concept outputs</div>
        <div style="font-size:14px; line-height:1.7; color:#cbd5e1;">
          Node availability: <b>{node_availability_pct:.0f}%</b><br>
          Rerouting efficiency: <b>{rerouting_efficiency_pct:.0f}%</b><br>
          Protected core: <b>{protected_core_pct:.0f}%</b>
        </div>
      </div>
    """
    svg = f"""
    <svg viewBox="0 0 1200 620" width="100%" height="100%">
      <defs>
        <linearGradient id="ctrlBlueLiquid" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#0ea5e9"/>
          <stop offset="25%" stop-color="#67e8f9"/>
          <stop offset="50%" stop-color="#ecfeff"/>
          <stop offset="75%" stop-color="#7dd3fc"/>
          <stop offset="100%" stop-color="#0284c7"/>
          <animateTransform attributeName="gradientTransform" type="translate" values="-220 0;220 0;-220 0" dur="2.6s" repeatCount="indefinite"/>
        </linearGradient>
        <linearGradient id="ctrlRedLiquid" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#ef4444"/>
          <stop offset="25%" stop-color="#fda4af"/>
          <stop offset="50%" stop-color="#fff1f2"/>
          <stop offset="75%" stop-color="#fb7185"/>
          <stop offset="100%" stop-color="#be123c"/>
          <animateTransform attributeName="gradientTransform" type="translate" values="220 0;-220 0;220 0" dur="2.6s" repeatCount="indefinite"/>
        </linearGradient>
      </defs>
      <rect x="20" y="20" width="1160" height="580" rx="22" fill="#081220" stroke="#274a72" stroke-width="3"/>
      <rect x="70" y="90" width="1060" height="360" rx="20" fill="#07111f" stroke="#31567f" stroke-width="2"/>

      <g stroke="#64748b" stroke-width="10" stroke-linecap="round" opacity="0.75">
        <line x1="160" y1="180" x2="340" y2="180"/><line x1="340" y1="180" x2="520" y2="180"/><line x1="520" y1="180" x2="700" y2="180"/><line x1="700" y1="180" x2="880" y2="180"/>
        <line x1="160" y1="300" x2="340" y2="300"/><line x1="340" y1="300" x2="520" y2="300"/><line x1="520" y1="300" x2="700" y2="300"/><line x1="700" y1="300" x2="880" y2="300"/>
        <line x1="160" y1="420" x2="340" y2="420"/><line x1="340" y1="420" x2="520" y2="420"/><line x1="520" y1="420" x2="700" y2="420"/><line x1="700" y1="420" x2="880" y2="420"/>
        <line x1="160" y1="180" x2="160" y2="300"/><line x1="160" y1="300" x2="160" y2="420"/>
        <line x1="340" y1="180" x2="340" y2="300"/><line x1="340" y1="300" x2="340" y2="420"/>
        <line x1="520" y1="180" x2="520" y2="300"/><line x1="520" y1="300" x2="520" y2="420"/>
        <line x1="700" y1="180" x2="700" y2="300"/><line x1="700" y1="300" x2="700" y2="420"/>
        <line x1="880" y1="180" x2="880" y2="300"/><line x1="880" y1="300" x2="880" y2="420"/>
      </g>

      <path d="M 160 180 H 340 L 520 300 H 700 H 880" stroke="#0a4765" stroke-width="18" fill="none" stroke-linecap="round"/>
      <path d="M 160 420 H 340 L 520 300 L 700 180 H 880" stroke="#5b141f" stroke-width="18" fill="none" stroke-linecap="round"/>
      <path d="M 160 180 H 340 L 520 300 H 700 H 880" stroke="url(#ctrlBlueLiquid)" stroke-width="12" fill="none" stroke-linecap="round"/>
      <path d="M 160 420 H 340 L 520 300 L 700 180 H 880" stroke="url(#ctrlRedLiquid)" stroke-width="12" fill="none" stroke-linecap="round"/>

      <g stroke="#7f1d1d" stroke-width="5" opacity="0.18">
        <line x1="314" y1="274" x2="366" y2="326"/><line x1="366" y1="274" x2="314" y2="326"/>
        <line x1="674" y1="394" x2="726" y2="446"/><line x1="726" y1="394" x2="674" y2="446"/>
      </g>

      <g>
        <circle cx="160" cy="180" r="28" fill="#1e293b" stroke="#94a3b8" stroke-width="4"/>
        <circle cx="340" cy="180" r="28" fill="#1e293b" stroke="#94a3b8" stroke-width="4"/>
        <circle cx="520" cy="180" r="28" fill="#1e293b" stroke="#94a3b8" stroke-width="4"/>
        <circle cx="700" cy="180" r="28" fill="#1e293b" stroke="#94a3b8" stroke-width="4"/>
        <circle cx="880" cy="180" r="28" fill="#1e293b" stroke="#94a3b8" stroke-width="4"/>
        <circle cx="160" cy="300" r="28" fill="#1e293b" stroke="#94a3b8" stroke-width="4"/>
        <circle cx="340" cy="300" r="28" fill="#1e293b" stroke="#94a3b8" stroke-width="4"/>
        <circle cx="520" cy="300" r="34" fill="#34d399" stroke="#f8fafc" stroke-width="4"/>
        <circle cx="700" cy="300" r="28" fill="#1e293b" stroke="#94a3b8" stroke-width="4"/>
        <circle cx="880" cy="300" r="28" fill="#1e293b" stroke="#94a3b8" stroke-width="4"/>
        <circle cx="160" cy="420" r="28" fill="#1e293b" stroke="#94a3b8" stroke-width="4"/>
        <circle cx="340" cy="420" r="28" fill="#1e293b" stroke="#94a3b8" stroke-width="4"/>
        <circle cx="520" cy="420" r="28" fill="#1e293b" stroke="#94a3b8" stroke-width="4"/>
        <circle cx="700" cy="420" r="28" fill="#1e293b" stroke="#94a3b8" stroke-width="4"/>
        <circle cx="880" cy="420" r="28" fill="#1e293b" stroke="#94a3b8" stroke-width="4"/>
      </g>

      <text x="520" y="308" text-anchor="middle" fill="#07111f" font-size="18" font-weight="900">CORE</text>

      <rect x="60" y="488" width="1080" height="72" rx="16" fill="#091827" stroke="#1e3a5f" stroke-width="2"/>
      <rect x="85" y="503" width="250" height="42" rx="10" fill="#0d1e30" stroke="#264c75" stroke-width="1.5"/>
      <rect x="360" y="503" width="250" height="42" rx="10" fill="#0d1e30" stroke="#264c75" stroke-width="1.5"/>
      <rect x="635" y="503" width="250" height="42" rx="10" fill="#0d1e30" stroke="#264c75" stroke-width="1.5"/>
      <rect x="910" y="503" width="205" height="42" rx="10" fill="#0d1e30" stroke="#264c75" stroke-width="1.5"/>

      <text x="210" y="530" text-anchor="middle" fill="#ecfccb" font-size="16" font-weight="800">Node availability: {node_availability_pct:.0f}%</text>
      <text x="485" y="530" text-anchor="middle" fill="#bfdbfe" font-size="16" font-weight="800">Rerouting efficiency: {rerouting_efficiency_pct:.0f}%</text>
      <text x="760" y="530" text-anchor="middle" fill="#fca5a5" font-size="16" font-weight="800">Damage ratio: {damage_ratio_pct:.0f}%</text>
      <text x="1012" y="530" text-anchor="middle" fill="#86efac" font-size="16" font-weight="800">Core safe: {protected_core_pct:.0f}%</text>
    </svg>
    """
    _wrap_card("Distributed Thermal Control Layer (Concept)",
               "Conceptual modular routing and partial-damage tolerance visualization.",
               svg, side_html, height=height)


def render_distributed_harvesting_buffering_concept(
    diversification_score: float = 78.0,
    reserve_gain_hours: float = 7.5,
    shortfall_reduction_pct: float = 16.0,
    core_preservation_hours: float = 18.0,
    height: int = 720,
):
    side_html = f"""
      <div style="font-size:18px; font-weight:800; margin-bottom:10px;">How to interpret this panel</div>
      <div style="font-size:14px; line-height:1.65; color:#cbd5e1;">
        <b>Source conduits:</b> solar, wind, hydro, and reserve inputs.<br>
        <b>Buffer pool:</b> central balancing and storage layer.<br>
        <b>Priority stream:</b> preserved flow into the critical core.<br><br>
        Source streams use stronger liquid colors so each path reads more clearly at a glance.
      </div>
      <div style="margin-top:16px; border-top:1px solid #17304d; padding-top:14px;">
        <div style="font-size:16px; font-weight:800; margin-bottom:8px;">Derived concept outputs</div>
        <div style="font-size:14px; line-height:1.7; color:#cbd5e1;">
          Diversification score: <b>{diversification_score:.0f}</b><br>
          Reserve gain: <b>{reserve_gain_hours:.1f} h</b><br>
          Core preservation: <b>{core_preservation_hours:.1f} h</b>
        </div>
      </div>
    """
    svg = f"""
    <svg viewBox="0 0 1200 620" width="100%" height="100%">
      <defs>
        <linearGradient id="harvestGold" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#f59e0b"/>
          <stop offset="25%" stop-color="#fcd34d"/>
          <stop offset="50%" stop-color="#fff7d6"/>
          <stop offset="75%" stop-color="#fbbf24"/>
          <stop offset="100%" stop-color="#b45309"/>
          <animateTransform attributeName="gradientTransform" type="translate" values="-180 0;180 0;-180 0" dur="2.7s" repeatCount="indefinite"/>
        </linearGradient>
        <linearGradient id="harvestWind" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#0ea5e9"/>
          <stop offset="25%" stop-color="#67e8f9"/>
          <stop offset="50%" stop-color="#ecfeff"/>
          <stop offset="75%" stop-color="#7dd3fc"/>
          <stop offset="100%" stop-color="#0284c7"/>
          <animateTransform attributeName="gradientTransform" type="translate" values="-180 0;180 0;-180 0" dur="2.5s" repeatCount="indefinite"/>
        </linearGradient>
        <linearGradient id="harvestHydro" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#2563eb"/>
          <stop offset="25%" stop-color="#93c5fd"/>
          <stop offset="50%" stop-color="#eff6ff"/>
          <stop offset="75%" stop-color="#60a5fa"/>
          <stop offset="100%" stop-color="#1d4ed8"/>
          <animateTransform attributeName="gradientTransform" type="translate" values="-180 0;180 0;-180 0" dur="2.9s" repeatCount="indefinite"/>
        </linearGradient>
        <linearGradient id="harvestCore" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#22c55e"/>
          <stop offset="25%" stop-color="#86efac"/>
          <stop offset="50%" stop-color="#f0fdf4"/>
          <stop offset="75%" stop-color="#4ade80"/>
          <stop offset="100%" stop-color="#15803d"/>
          <animateTransform attributeName="gradientTransform" type="translate" values="-180 0;180 0;-180 0" dur="2.2s" repeatCount="indefinite"/>
        </linearGradient>
      </defs>
      <rect x="20" y="20" width="1160" height="580" rx="22" fill="#081220" stroke="#274a72" stroke-width="3"/>

      <circle cx="180" cy="170" r="58" fill="#0d1e30" stroke="#f59e0b" stroke-width="4"/>
      <text x="180" y="177" text-anchor="middle" fill="#fef3c7" font-size="22" font-weight="800">Solar</text>
      <circle cx="180" cy="330" r="58" fill="#0d1e30" stroke="#0ea5e9" stroke-width="4"/>
      <text x="180" y="337" text-anchor="middle" fill="#dbeafe" font-size="22" font-weight="800">Wind</text>
      <circle cx="180" cy="490" r="58" fill="#0d1e30" stroke="#2563eb" stroke-width="4"/>
      <text x="180" y="497" text-anchor="middle" fill="#dbeafe" font-size="22" font-weight="800">Hydro</text>

      <rect x="430" y="180" width="260" height="250" rx="28" fill="#0d1e30" stroke="#4f89c6" stroke-width="4"/>
      <text x="560" y="245" text-anchor="middle" fill="#f8fafc" font-size="30" font-weight="800">Buffer Pool</text>
      <text x="560" y="286" text-anchor="middle" fill="#93c5fd" font-size="20" font-weight="700">Multi-source balancing</text>

      <rect x="890" y="235" width="190" height="135" rx="22" fill="#0d1e30" stroke="#34d399" stroke-width="4"/>
      <text x="985" y="288" text-anchor="middle" fill="#ecfdf5" font-size="26" font-weight="800">Critical Core</text>
      <text x="985" y="326" text-anchor="middle" fill="#86efac" font-size="18" font-weight="700">Preserved output</text>

      <path d="M 240 170 C 310 170, 340 210, 430 245" fill="none" stroke="#6b4d13" stroke-width="16" stroke-linecap="round"/>
      <path d="M 240 330 C 310 330, 340 320, 430 305" fill="none" stroke="#0a4765" stroke-width="16" stroke-linecap="round"/>
      <path d="M 240 490 C 310 490, 340 410, 430 365" fill="none" stroke="#1e40af" stroke-width="16" stroke-linecap="round"/>
      <path d="M 690 305 C 760 305, 800 305, 890 305" fill="none" stroke="#166534" stroke-width="18" stroke-linecap="round"/>

      <path d="M 240 170 C 310 170, 340 210, 430 245" fill="none" stroke="url(#harvestGold)" stroke-width="10" stroke-linecap="round"/>
      <path d="M 240 330 C 310 330, 340 320, 430 305" fill="none" stroke="url(#harvestWind)" stroke-width="10" stroke-linecap="round"/>
      <path d="M 240 490 C 310 490, 340 410, 430 365" fill="none" stroke="url(#harvestHydro)" stroke-width="10" stroke-linecap="round"/>
      <path d="M 690 305 C 760 305, 800 305, 890 305" fill="none" stroke="url(#harvestCore)" stroke-width="12" stroke-linecap="round"/>

      <rect x="70" y="540" width="1060" height="40" rx="12" fill="#091827" stroke="#1e3a5f" stroke-width="2"/>
      <text x="205" y="566" text-anchor="middle" fill="#fde68a" font-size="16" font-weight="800">Diversification: {diversification_score:.0f}</text>
      <text x="470" y="566" text-anchor="middle" fill="#bfdbfe" font-size="16" font-weight="800">Reserve gain: {reserve_gain_hours:.1f} h</text>
      <text x="760" y="566" text-anchor="middle" fill="#fca5a5" font-size="16" font-weight="800">Shortfall reduction: {shortfall_reduction_pct:.1f}%</text>
      <text x="1010" y="566" text-anchor="middle" fill="#86efac" font-size="16" font-weight="800">Core preserved: {core_preservation_hours:.1f} h</text>
    </svg>
    """
    _wrap_card("Distributed Energy Harvesting & Buffering (Concept)",
               "Conceptual multi-source harvesting and critical-core preservation visualization.",
               svg, side_html, height=height)


def render_distributed_energy_harvesting_buffering_concept(*args, **kwargs):
    return render_distributed_harvesting_buffering_concept(*args, **kwargs)
