
import math
import streamlit.components.v1 as components


def _wrap_html(title: str, body: str, side: str, height: int) -> str:
    return f"""
    <div style="font-family: Inter, Arial, sans-serif; color:#e5e7eb;">
      <div style="display:grid; grid-template-columns: 1fr 320px; gap:18px; align-items:start;">
        <div style="background:#07111f; border:1px solid #17304d; border-radius:18px; padding:14px;">
          {body}
        </div>
        <div style="background:#081220; border:1px solid #17304d; border-radius:18px; padding:16px;">
          <div style="font-size:22px; font-weight:800; margin-bottom:12px;">{title}</div>
          <div style="font-size:14px; line-height:1.7; color:#cbd5e1;">{side}</div>
        </div>
      </div>
    </div>
    """


def render_phase_change_buffer(
    outside_temp_c: float,
    indoor_temp_c: float,
    charge_level: float,
    recovery_efficiency: float,
    height: int = 620,
):
    charge_level = max(0.0, min(1.0, charge_level))
    recovery_efficiency = max(0.0, min(1.0, recovery_efficiency))
    delivered = outside_temp_c + (indoor_temp_c - outside_temp_c) * recovery_efficiency
    pulse = 3.8 - 1.8 * charge_level
    body = f"""
    <svg viewBox="0 0 1200 700" width="100%" height="100%">
      <defs>
        <linearGradient id="coldA" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#38bdf8"/><stop offset="100%" stop-color="#93c5fd"/>
        </linearGradient>
        <linearGradient id="warmA" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#fca5a5"/><stop offset="100%" stop-color="#ef4444"/>
        </linearGradient>
      </defs>
      <rect x="22" y="22" width="1156" height="656" rx="22" fill="#081220" stroke="#1f3b5a" stroke-width="3"/>
      <text x="60" y="72" fill="#f8fafc" font-size="34" font-weight="800">Phase-Change Thermal Buffer (Concept)</text>
      <text x="60" y="108" fill="#94a3b8" font-size="18">Conceptual heat-buffering with latent storage behavior. Not a validated hardware design.</text>

      <rect x="110" y="170" width="980" height="360" rx="26" fill="#0b1828" stroke="#324f72" stroke-width="3"/>
      <rect x="220" y="225" width="260" height="250" rx="26" fill="#0b2033" stroke="#315b86" stroke-width="3"/>
      <text x="268" y="212" fill="#7dd3fc" font-size="24" font-weight="700">Cold-side input</text>
      <rect x="720" y="225" width="260" height="250" rx="26" fill="#39191d" stroke="#7f1d1d" stroke-width="3"/>
      <text x="744" y="212" fill="#fca5a5" font-size="24" font-weight="700">Warm-side return</text>

      <rect x="505" y="178" width="190" height="342" rx="24" fill="#12263b" stroke="#44658c" stroke-width="3"/>
      <text x="525" y="208" fill="#fde68a" font-size="24" font-weight="700">Latent buffer core</text>
      <rect x="540" y="250" width="120" height="200" rx="18" fill="#dbeafe" opacity="{0.25 + 0.55*charge_level:.2f}" stroke="#ffffff" stroke-width="3"/>
      <text x="553" y="360" fill="#111827" font-size="34" font-weight="800">ICE/WATER</text>
      <circle cx="600" cy="350" r="{55 + 30*charge_level:.1f}" fill="#fde68a" opacity="0.18">
        <animate attributeName="r" values="{50 + 25*charge_level:.1f};{70 + 30*charge_level:.1f};{50 + 25*charge_level:.1f}" dur="{pulse:.2f}s" repeatCount="indefinite"/>
        <animate attributeName="opacity" values="0.24;0.08;0.24" dur="{pulse:.2f}s" repeatCount="indefinite"/>
      </circle>

      <path d="M 70 300 L 220 300 L 505 300" fill="none" stroke="url(#coldA)" stroke-width="26" stroke-linecap="round"/>
      <path d="M 695 400 L 980 400 L 1130 400" fill="none" stroke="url(#warmA)" stroke-width="26" stroke-linecap="round"/>
      <path d="M 1130 300 L 980 300 L 695 300" fill="none" stroke="url(#warmA)" stroke-width="26" stroke-linecap="round"/>
      <path d="M 505 400 L 220 400 L 70 400" fill="none" stroke="url(#coldA)" stroke-width="26" stroke-linecap="round"/>

      <circle r="11" fill="#7dd3fc"><animateMotion dur="5.2s" repeatCount="indefinite" path="M 70 300 L 220 300 L 505 300"/></circle>
      <circle r="11" fill="#7dd3fc" opacity="0.85"><animateMotion dur="5.2s" begin="1.6s" repeatCount="indefinite" path="M 505 400 L 220 400 L 70 400"/></circle>
      <circle r="11" fill="#fca5a5"><animateMotion dur="5.2s" repeatCount="indefinite" path="M 1130 300 L 980 300 L 695 300"/></circle>
      <circle r="11" fill="#fca5a5" opacity="0.85"><animateMotion dur="5.2s" begin="1.8s" repeatCount="indefinite" path="M 695 400 L 980 400 L 1130 400"/></circle>

      <rect x="82" y="565" width="1038" height="78" rx="16" fill="#091827" stroke="#1e3a5f" stroke-width="2"/>
      <text x="120" y="610" fill="#7dd3fc" font-size="22" font-weight="800">Outside air: {outside_temp_c:.1f} °C</text>
      <text x="410" y="610" fill="#fca5a5" font-size="22" font-weight="800">Indoor return: {indoor_temp_c:.1f} °C</text>
      <text x="690" y="610" fill="#fde68a" font-size="22" font-weight="800">Buffer charge: {charge_level*100:.0f}%</text>
      <text x="932" y="610" fill="#f8fafc" font-size="22" font-weight="800">Delivered: {delivered:.1f} °C</text>
    </svg>
    """
    side = f"""
    <b>Purpose:</b> visualize latent-heat buffering logic for cold-climate resilience.<br><br>
    <b>Blue path:</b> outside-side cooling/heating flow.<br>
    <b>Red path:</b> indoor return stream contributing recoverable heat.<br>
    <b>Center core:</b> conceptual phase-change buffer state.<br><br>
    Delivered supply estimate: <b>{delivered:.1f} °C</b><br>
    Buffer charge level: <b>{charge_level*100:.0f}%</b><br>
    Recovery efficiency: <b>{recovery_efficiency*100:.0f}%</b><br><br>
    This graphic is a scenario visualization only.
    """
    components.html(_wrap_html("Phase-Change Thermal Buffer", body, side, height), height=height, scrolling=False)


def render_ground_thermal_sink(
    server_heat_load: float,
    sink_utilization: float,
    extraction_support: float,
    height: int = 620,
):
    sink_utilization = max(0.0, min(1.0, sink_utilization))
    extraction_support = max(0.0, min(1.0, extraction_support))
    pulse = 4.4 - 1.8 * sink_utilization
    depth_glow = 0.18 + 0.35 * sink_utilization
    body = f"""
    <svg viewBox="0 0 1200 700" width="100%" height="100%">
      <rect x="22" y="22" width="1156" height="656" rx="22" fill="#081220" stroke="#1f3b5a" stroke-width="3"/>
      <text x="60" y="72" fill="#f8fafc" font-size="34" font-weight="800">Ground Thermal Sink (Concept)</text>
      <text x="60" y="108" fill="#94a3b8" font-size="18">Conceptual subsurface heat rejection and geothermal support visualization.</text>

      <rect x="80" y="170" width="1040" height="460" rx="22" fill="#0a1624" stroke="#23405f" stroke-width="2"/>
      <rect x="80" y="170" width="1040" height="110" rx="18" fill="#0f2030"/>
      <text x="110" y="236" fill="#f8fafc" font-size="28" font-weight="800">Protected compute / thermal zone</text>

      <rect x="860" y="205" width="180" height="200" rx="18" fill="#0f2030" stroke="#3d6e9d" stroke-width="3"/>
      <text x="894" y="248" fill="#dbeafe" font-size="24" font-weight="800">Server Core</text>
      <text x="900" y="286" fill="#fca5a5" font-size="24" font-weight="700">Heat load</text>
      <text x="922" y="322" fill="#f8fafc" font-size="32" font-weight="800">{server_heat_load:.1f} MW</text>

      <path d="M 860 360 L 730 360 L 650 320 L 650 520" fill="none" stroke="#f87171" stroke-width="22" stroke-linecap="round"/>
      <path d="M 650 520 L 650 620" fill="none" stroke="#fb7185" stroke-width="24" stroke-linecap="round"/>
      <path d="M 540 620 L 760 620" fill="none" stroke="#fb7185" stroke-width="24" stroke-linecap="round"/>

      <rect x="470" y="330" width="110" height="120" rx="14" fill="#10273e" stroke="#4a76a5" stroke-width="3"/>
      <text x="490" y="398" fill="#dbeafe" font-size="22" font-weight="800">Pump</text>

      <rect x="220" y="260" width="160" height="110" rx="18" fill="#10273e" stroke="#4a76a5" stroke-width="3"/>
      <text x="245" y="320" fill="#fde68a" font-size="24" font-weight="800">Heat Pump</text>
      <path d="M 380 315 L 470 315" fill="none" stroke="#93c5fd" stroke-width="20" stroke-linecap="round"/>
      <path d="M 220 315 L 140 315" fill="none" stroke="#93c5fd" stroke-width="20" stroke-linecap="round"/>

      <rect x="120" y="410" width="900" height="180" rx="18" fill="#111827" stroke="#374151" stroke-width="2"/>
      <text x="150" y="450" fill="#cbd5e1" font-size="26" font-weight="800">Subsurface / bedrock thermal mass</text>
      <circle cx="300" cy="520" r="{70 + 40*sink_utilization:.1f}" fill="#f59e0b" opacity="{depth_glow:.2f}">
        <animate attributeName="r" values="{60 + 30*sink_utilization:.1f};{85 + 45*sink_utilization:.1f};{60 + 30*sink_utilization:.1f}" dur="{pulse:.2f}s" repeatCount="indefinite"/>
      </circle>
      <circle cx="520" cy="535" r="{55 + 35*sink_utilization:.1f}" fill="#fb7185" opacity="{depth_glow*0.85:.2f}">
        <animate attributeName="r" values="{48 + 25*sink_utilization:.1f};{70 + 35*sink_utilization:.1f};{48 + 25*sink_utilization:.1f}" dur="{pulse + 0.6:.2f}s" repeatCount="indefinite"/>
      </circle>
      <circle cx="730" cy="515" r="{65 + 35*sink_utilization:.1f}" fill="#60a5fa" opacity="{0.12 + 0.25*extraction_support:.2f}">
        <animate attributeName="r" values="{55 + 20*extraction_support:.1f};{82 + 28*extraction_support:.1f};{55 + 20*extraction_support:.1f}" dur="{4.6 - 1.6*extraction_support:.2f}s" repeatCount="indefinite"/>
      </circle>

      <rect x="82" y="565" width="1038" height="78" rx="16" fill="#091827" stroke="#1e3a5f" stroke-width="2"/>
      <text x="120" y="610" fill="#fca5a5" font-size="22" font-weight="800">Server heat load: {server_heat_load:.1f} MW</text>
      <text x="430" y="610" fill="#fde68a" font-size="22" font-weight="800">Sink utilization: {sink_utilization*100:.0f}%</text>
      <text x="730" y="610" fill="#93c5fd" font-size="22" font-weight="800">Extraction support: {extraction_support*100:.0f}%</text>
    </svg>
    """
    side = f"""
    <b>Purpose:</b> visualize how a conceptual subsurface sink could absorb waste heat and provide thermal support.<br><br>
    <b>Upper zone:</b> protected compute / thermal system.<br>
    <b>Vertical path:</b> heat rejection route into subsurface mass.<br>
    <b>Blue extraction path:</b> conceptual support back into the protected zone.<br><br>
    Sink utilization: <b>{sink_utilization*100:.0f}%</b><br>
    Extraction support: <b>{extraction_support*100:.0f}%</b><br>
    Server heat load: <b>{server_heat_load:.1f} MW</b><br><br>
    This is an illustrative resilience concept.
    """
    components.html(_wrap_html("Ground Thermal Sink", body, side, height), height=height, scrolling=False)


def render_distributed_thermal_control(
    node_availability: float,
    rerouting_efficiency: float,
    damage_ratio: float,
    height: int = 620,
):
    node_availability = max(0.0, min(1.0, node_availability))
    rerouting_efficiency = max(0.0, min(1.0, rerouting_efficiency))
    damage_ratio = max(0.0, min(1.0, damage_ratio))
    core_green = "#34d399" if node_availability > 0.65 else "#f59e0b" if node_availability > 0.4 else "#ef4444"
    body = f"""
    <svg viewBox="0 0 1200 700" width="100%" height="100%">
      <rect x="22" y="22" width="1156" height="656" rx="22" fill="#081220" stroke="#1f3b5a" stroke-width="3"/>
      <text x="60" y="72" fill="#f8fafc" font-size="34" font-weight="800">Distributed Thermal Control Layer (Concept)</text>
      <text x="60" y="108" fill="#94a3b8" font-size="18">Conceptual modular routing and partial-damage tolerance visualization.</text>
      <rect x="90" y="150" width="1020" height="490" rx="24" fill="#0b1828" stroke="#324f72" stroke-width="3"/>

      <g stroke="#4b5563" stroke-width="10" fill="none">
        <path d="M 240 250 L 420 250 L 600 250 L 780 250 L 960 250"/>
        <path d="M 240 390 L 420 390 L 600 390 L 780 390 L 960 390"/>
        <path d="M 240 530 L 420 530 L 600 530 L 780 530 L 960 530"/>
        <path d="M 240 250 L 240 390 L 240 530"/>
        <path d="M 420 250 L 420 390 L 420 530"/>
        <path d="M 600 250 L 600 390 L 600 530"/>
        <path d="M 780 250 L 780 390 L 780 530"/>
        <path d="M 960 250 L 960 390 L 960 530"/>
      </g>

      <path d="M 240 250 L 420 250 L 600 390 L 780 390 L 960 390" stroke="#7dd3fc" stroke-width="{12 + 10*rerouting_efficiency:.1f}" fill="none" stroke-linecap="round"/>
      <path d="M 240 530 L 420 530 L 600 390 L 780 250 L 960 250" stroke="#fca5a5" stroke-width="{10 + 10*rerouting_efficiency:.1f}" fill="none" stroke-linecap="round"/>
      <circle r="10" fill="#7dd3fc"><animateMotion dur="{5.6 - 2.4*rerouting_efficiency:.2f}s" repeatCount="indefinite" path="M 240 250 L 420 250 L 600 390 L 780 390 L 960 390"/></circle>
      <circle r="10" fill="#fca5a5"><animateMotion dur="{5.8 - 2.2*rerouting_efficiency:.2f}s" repeatCount="indefinite" path="M 240 530 L 420 530 L 600 390 L 780 250 L 960 250"/></circle>

      <g>
        <circle cx="240" cy="250" r="28" fill="#1f2937" stroke="#9ca3af" stroke-width="4"/>
        <circle cx="420" cy="250" r="28" fill="#1f2937" stroke="#9ca3af" stroke-width="4"/>
        <circle cx="600" cy="250" r="28" fill="#1f2937" stroke="#9ca3af" stroke-width="4"/>
        <circle cx="780" cy="250" r="28" fill="#1f2937" stroke="#9ca3af" stroke-width="4"/>
        <circle cx="960" cy="250" r="28" fill="#1f2937" stroke="#9ca3af" stroke-width="4"/>

        <circle cx="240" cy="390" r="28" fill="#1f2937" stroke="#9ca3af" stroke-width="4"/>
        <circle cx="420" cy="390" r="28" fill="#1f2937" stroke="#9ca3af" stroke-width="4"/>
        <circle cx="600" cy="390" r="34" fill="{core_green}" stroke="#f8fafc" stroke-width="5"/>
        <circle cx="780" cy="390" r="28" fill="#1f2937" stroke="#9ca3af" stroke-width="4"/>
        <circle cx="960" cy="390" r="28" fill="#1f2937" stroke="#9ca3af" stroke-width="4"/>

        <circle cx="240" cy="530" r="28" fill="#1f2937" stroke="#9ca3af" stroke-width="4"/>
        <circle cx="420" cy="530" r="28" fill="#1f2937" stroke="#9ca3af" stroke-width="4"/>
        <circle cx="600" cy="530" r="28" fill="#1f2937" stroke="#9ca3af" stroke-width="4"/>
        <circle cx="780" cy="530" r="28" fill="#1f2937" stroke="#9ca3af" stroke-width="4"/>
        <circle cx="960" cy="530" r="28" fill="#1f2937" stroke="#9ca3af" stroke-width="4"/>
      </g>

      <g opacity="{damage_ratio:.2f}">
        <line x1="420" y1="390" x2="470" y2="440" stroke="#ef4444" stroke-width="10"/>
        <line x1="470" y1="390" x2="420" y2="440" stroke="#ef4444" stroke-width="10"/>
        <line x1="780" y1="530" x2="830" y2="580" stroke="#ef4444" stroke-width="10"/>
        <line x1="830" y1="530" x2="780" y2="580" stroke="#ef4444" stroke-width="10"/>
      </g>

      <text x="565" y="397" fill="#081220" font-size="20" font-weight="800">CORE</text>
      <rect x="82" y="565" width="1038" height="78" rx="16" fill="#091827" stroke="#1e3a5f" stroke-width="2"/>
      <text x="120" y="610" fill="#d1fae5" font-size="22" font-weight="800">Node availability: {node_availability*100:.0f}%</text>
      <text x="430" y="610" fill="#93c5fd" font-size="22" font-weight="800">Rerouting efficiency: {rerouting_efficiency*100:.0f}%</text>
      <text x="770" y="610" fill="#fca5a5" font-size="22" font-weight="800">Damage ratio: {damage_ratio*100:.0f}%</text>
    </svg>
    """
    side = f"""
    <b>Purpose:</b> illustrate modular thermal control and route redirection under partial damage.<br><br>
    <b>Center node:</b> protected critical core.<br>
    <b>Crossed nodes:</b> degraded modules / unavailable paths.<br>
    <b>Highlighted paths:</b> conceptual rerouting behavior.<br><br>
    Node availability: <b>{node_availability*100:.0f}%</b><br>
    Rerouting efficiency: <b>{rerouting_efficiency*100:.0f}%</b><br>
    Damage ratio: <b>{damage_ratio*100:.0f}%</b><br><br>
    This is a topology concept, not a physical routing blueprint.
    """
    components.html(_wrap_html("Distributed Thermal Control Layer", body, side, height), height=height, scrolling=False)


def render_harvesting_buffering(
    wind_input: float,
    solar_input: float,
    hydro_input: float,
    buffer_fill: float,
    priority_shift: float,
    height: int = 620,
):
    wind_input = max(0.0, min(1.0, wind_input))
    solar_input = max(0.0, min(1.0, solar_input))
    hydro_input = max(0.0, min(1.0, hydro_input))
    buffer_fill = max(0.0, min(1.0, buffer_fill))
    priority_shift = max(0.0, min(1.0, priority_shift))
    body = f"""
    <svg viewBox="0 0 1200 700" width="100%" height="100%">
      <rect x="22" y="22" width="1156" height="656" rx="22" fill="#081220" stroke="#1f3b5a" stroke-width="3"/>
      <text x="60" y="72" fill="#f8fafc" font-size="34" font-weight="800">Distributed Energy Harvesting & Buffering (Concept)</text>
      <text x="60" y="108" fill="#94a3b8" font-size="18">Conceptual multi-source capture, shared buffering, and critical-load preservation logic.</text>

      <circle cx="210" cy="270" r="75" fill="#0f2030" stroke="#315b86" stroke-width="4"/>
      <text x="150" y="278" fill="#7dd3fc" font-size="28" font-weight="800">WIND</text>
      <circle cx="210" cy="470" r="75" fill="#0f2030" stroke="#315b86" stroke-width="4"/>
      <text x="146" y="478" fill="#fde68a" font-size="28" font-weight="800">SOLAR</text>
      <circle cx="410" cy="470" r="75" fill="#0f2030" stroke="#315b86" stroke-width="4"/>
      <text x="352" y="478" fill="#93c5fd" font-size="28" font-weight="800">HYDRO</text>

      <rect x="520" y="205" width="180" height="320" rx="22" fill="#10273e" stroke="#4a76a5" stroke-width="4"/>
      <text x="552" y="242" fill="#dbeafe" font-size="28" font-weight="800">BUFFER</text>
      <rect x="555" y="{480 - 180*buffer_fill:.1f}" width="110" height="{180*buffer_fill:.1f}" rx="14" fill="#34d399" opacity="0.85"/>
      <text x="565" y="565" fill="#d1fae5" font-size="24" font-weight="800">{buffer_fill*100:.0f}% full</text>

      <rect x="800" y="180" width="270" height="120" rx="18" fill="#10273e" stroke="#4a76a5" stroke-width="3"/>
      <text x="830" y="245" fill="#f8fafc" font-size="28" font-weight="800">CRITICAL CORE</text>
      <rect x="800" y="355" width="270" height="120" rx="18" fill="#291b1b" stroke="#7f1d1d" stroke-width="3"/>
      <text x="836" y="420" fill="#fca5a5" font-size="28" font-weight="800">NONCRITICAL LOAD</text>

      <path d="M 285 270 L 520 300" stroke="#7dd3fc" stroke-width="{12 + 10*wind_input:.1f}" fill="none" stroke-linecap="round"/>
      <path d="M 270 470 L 520 400" stroke="#fde68a" stroke-width="{12 + 10*solar_input:.1f}" fill="none" stroke-linecap="round"/>
      <path d="M 485 470 L 520 440" stroke="#93c5fd" stroke-width="{12 + 10*hydro_input:.1f}" fill="none" stroke-linecap="round"/>

      <path d="M 700 285 L 800 240" stroke="#34d399" stroke-width="{12 + 12*(1-priority_shift):.1f}" fill="none" stroke-linecap="round"/>
      <path d="M 700 420 L 800 415" stroke="#f87171" stroke-width="{8 + 12*(1-priority_shift):.1f}" fill="none" stroke-linecap="round" opacity="{0.55 + 0.35*(1-priority_shift):.2f}"/>
      <path d="M 700 350 L 800 240" stroke="#60a5fa" stroke-width="{8 + 14*priority_shift:.1f}" fill="none" stroke-linecap="round"/>

      <circle r="9" fill="#7dd3fc"><animateMotion dur="{6.0 - 2.5*wind_input:.2f}s" repeatCount="indefinite" path="M 285 270 L 520 300"/></circle>
      <circle r="9" fill="#fde68a"><animateMotion dur="{6.2 - 2.5*solar_input:.2f}s" repeatCount="indefinite" path="M 270 470 L 520 400"/></circle>
      <circle r="9" fill="#93c5fd"><animateMotion dur="{6.1 - 2.5*hydro_input:.2f}s" repeatCount="indefinite" path="M 485 470 L 520 440"/></circle>
      <circle r="10" fill="#34d399"><animateMotion dur="{4.8 - 2.0*priority_shift:.2f}s" repeatCount="indefinite" path="M 700 350 L 800 240"/></circle>

      <rect x="82" y="565" width="1038" height="78" rx="16" fill="#091827" stroke="#1e3a5f" stroke-width="2"/>
      <text x="116" y="610" fill="#7dd3fc" font-size="20" font-weight="800">Wind: {wind_input*100:.0f}%</text>
      <text x="316" y="610" fill="#fde68a" font-size="20" font-weight="800">Solar: {solar_input*100:.0f}%</text>
      <text x="530" y="610" fill="#93c5fd" font-size="20" font-weight="800">Hydro: {hydro_input*100:.0f}%</text>
      <text x="742" y="610" fill="#34d399" font-size="20" font-weight="800">Buffer fill: {buffer_fill*100:.0f}%</text>
      <text x="945" y="610" fill="#f8fafc" font-size="20" font-weight="800">Priority shift: {priority_shift*100:.0f}%</text>
    </svg>
    """
    side = f"""
    <b>Purpose:</b> show multi-source harvesting feeding a shared buffer, with priority shifted toward critical operations.<br><br>
    <b>Sources:</b> wind, solar, hydro conceptual inflows.<br>
    <b>Buffer:</b> shared resilience pool.<br>
    <b>Priority shift:</b> how strongly support is redirected toward critical functions over noncritical loads.<br><br>
    Buffer fill: <b>{buffer_fill*100:.0f}%</b><br>
    Priority shift: <b>{priority_shift*100:.0f}%</b><br><br>
    This is a resilience strategy visualization, not a plant-control screen.
    """
    components.html(_wrap_html("Distributed Energy Harvesting & Buffering", body, side, height), height=height, scrolling=False)
