
import streamlit.components.v1 as components


def render_thermal_principle_simulation(
    title: str = "Thermal Recovery Principle (Concept Mode)",
    height: int = 780,
    fresh_air_temp_c: float = -5.0,
    exhaust_air_temp_c: float = 24.0,
    recovery_efficiency: float = 0.72,
    airflow_speed: float = 1.0,
):
    """
    Render an animated conceptual heat-recovery / thermal-exchange diagram in Streamlit.

    Upgrades in this version:
    1) Liquid speed is linked to the airflow_speed parameter.
    2) Heat-exchange intensity is made more visible and scales with recovery_efficiency.
    3) Flow thickness / visible flow rate scales with airflow_speed.
    """
    recovery_efficiency = max(0.0, min(1.0, float(recovery_efficiency)))
    airflow_speed = max(0.4, min(2.5, float(airflow_speed)))

    delivered_temp = fresh_air_temp_c + (exhaust_air_temp_c - fresh_air_temp_c) * recovery_efficiency
    exhaust_after_exchange = exhaust_air_temp_c - (exhaust_air_temp_c - fresh_air_temp_c) * recovery_efficiency

    # Animation speeds
    duration = 4.8 / airflow_speed
    pulse_duration = 3.8 / max(0.8, airflow_speed * 0.9)

    # Flow thickness linked to airflow speed
    speed_norm = (airflow_speed - 0.4) / (2.5 - 0.4)
    inner_thickness = 12 + speed_norm * 10      # 12 → 22 px
    inner_round = inner_thickness / 2
    top_inner_y = 261 - inner_thickness / 2
    top_inner_h = inner_thickness

    # Slug length linked to airflow speed
    slug_len = 120 + speed_norm * 70            # 120 → 190 px

    # Heat exchange visibility linked to efficiency
    exch_norm = recovery_efficiency
    pulse_base_radius = 46 + exch_norm * 18
    pulse_max_radius = 74 + exch_norm * 26
    pulse_base_opacity = 0.12 + exch_norm * 0.12
    exch_arrow_opacity = 0.15 + exch_norm * 0.55
    exch_arrow_count = 2 + int(round(exch_norm * 3))   # 2 → 5

    # Useful strings for SVG interpolation
    outer_stroke = 30
    outer_radius = outer_stroke / 2

    def eff_label(eff):
        if eff >= 0.8:
            return "High thermal recovery"
        elif eff >= 0.55:
            return "Moderate thermal recovery"
        else:
            return "Low thermal recovery"

    html = f"""
    <div style="font-family: Inter, Arial, sans-serif; color:#e5e7eb; padding-bottom:12px;">
      <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:12px;">
        <div style="font-size:28px; font-weight:800;">{title}</div>
        <div style="font-size:13px; color:#94a3b8;">Conceptual animated diagram for TAIVAS thermal-resilience mode</div>
      </div>

      <div style="display:grid; grid-template-columns: 1fr 320px; gap:18px; align-items:start;">
        <div style="background:#07111f; border:1px solid #17304d; border-radius:18px; padding:14px;">
          <svg viewBox="0 0 1200 780" width="100%" height="100%" aria-label="animated heat recovery diagram">
            <defs>
              <linearGradient id="coldPipeBase" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#08324b"/>
                <stop offset="100%" stop-color="#0b4f74"/>
              </linearGradient>

              <linearGradient id="warmPipeBase" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#5a1020"/>
                <stop offset="100%" stop-color="#8f1730"/>
              </linearGradient>

              <linearGradient id="coldSlug" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#0891b2"/>
                <stop offset="45%" stop-color="#67e8f9"/>
                <stop offset="55%" stop-color="#ecfeff"/>
                <stop offset="100%" stop-color="#0ea5e9"/>
              </linearGradient>

              <linearGradient id="warmSlug" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#dc2626"/>
                <stop offset="45%" stop-color="#fda4af"/>
                <stop offset="55%" stop-color="#fff1f2"/>
                <stop offset="100%" stop-color="#fb7185"/>
              </linearGradient>

              <linearGradient id="exchangeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#fde68a"/>
                <stop offset="100%" stop-color="#f59e0b"/>
              </linearGradient>

              <linearGradient id="exchangeArrow" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#fca5a5"/>
                <stop offset="50%" stop-color="#fde68a"/>
                <stop offset="100%" stop-color="#93c5fd"/>
              </linearGradient>

              <filter id="blueGlow">
                <feGaussianBlur stdDeviation="3.5" result="blur"/>
                <feMerge>
                  <feMergeNode in="blur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>

              <filter id="redGlow">
                <feGaussianBlur stdDeviation="3.5" result="blur"/>
                <feMerge>
                  <feMergeNode in="blur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>

              <filter id="goldGlow">
                <feGaussianBlur stdDeviation="6" result="blur"/>
                <feMerge>
                  <feMergeNode in="blur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>

              <clipPath id="clipTopCold">
                <rect x="52" y="246" width="508" height="30" rx="15"/>
              </clipPath>
              <clipPath id="clipTopWarm">
                <rect x="640" y="246" width="508" height="30" rx="15"/>
              </clipPath>
              <clipPath id="clipBottomCold">
                <path d="M52 438 H420 L560 360 V392 L426 468 H52 Z"/>
              </clipPath>
              <clipPath id="clipBottomWarm">
                <path d="M640 360 L774 438 H1148 V468 H768 L640 392 Z"/>
              </clipPath>
            </defs>

            <rect x="28" y="24" width="1144" height="726" rx="22" fill="#081220" stroke="#1f3b5a" stroke-width="3"/>
            <text x="70" y="82" fill="#f8fafc" font-size="34" font-weight="800">Conceptual Heat Recovery / Thermal Buffer Flow</text>
            <text x="70" y="118" fill="#94a3b8" font-size="18">
              Outside air is pre-conditioned by exchange with indoor exhaust before delivery to the protected zone.
            </text>

            <rect x="250" y="180" width="700" height="360" rx="24" fill="#0b1828" stroke="#39526f" stroke-width="4"/>
            <rect x="270" y="200" width="660" height="320" rx="18" fill="#0d1e30" stroke="#243b53" stroke-width="2"/>

            <!-- Side zones -->
            <rect x="292" y="220" width="280" height="120" rx="14" fill="#0c2940" stroke="#21557a" stroke-width="2"/>
            <rect x="292" y="380" width="280" height="120" rx="14" fill="#0c2940" stroke="#21557a" stroke-width="2"/>
            <rect x="628" y="220" width="280" height="120" rx="14" fill="#3a1719" stroke="#7f1d1d" stroke-width="2"/>
            <rect x="628" y="380" width="280" height="120" rx="14" fill="#3a1719" stroke="#7f1d1d" stroke-width="2"/>

            <!-- Heat exchanger core -->
            <g transform="translate(600,360) rotate(45)">
              <rect x="-120" y="-120" width="240" height="240" rx="12" fill="#2a2a35" stroke="url(#exchangeGrad)" stroke-width="8"/>
              <rect x="-95" y="-95" width="190" height="190" rx="10" fill="#f8fafc" opacity="0.96"/>
              <path d="M -80 -40 L 80 -40" stroke="#cbd5e1" stroke-width="6" opacity="0.9"/>
              <path d="M -80 -10 L 80 -10" stroke="#cbd5e1" stroke-width="6" opacity="0.9"/>
              <path d="M -80 20 L 80 20" stroke="#cbd5e1" stroke-width="6" opacity="0.9"/>
              <path d="M -80 50 L 80 50" stroke="#cbd5e1" stroke-width="6" opacity="0.9"/>
            </g>

            <!-- Pipe shells -->
            <rect x="52" y="246" width="508" height="30" rx="15" fill="url(#coldPipeBase)"/>
            <rect x="640" y="246" width="508" height="30" rx="15" fill="url(#warmPipeBase)"/>
            <path d="M52 453 H420 L560 376" fill="none" stroke="url(#coldPipeBase)" stroke-width="{outer_stroke}" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M640 376 L774 453 H1148" fill="none" stroke="url(#warmPipeBase)" stroke-width="{outer_stroke}" stroke-linecap="round" stroke-linejoin="round"/>

            <!-- Static inner flow base (thickness follows airflow_speed) -->
            <rect x="57" y="{top_inner_y:.1f}" width="498" height="{top_inner_h:.1f}" rx="{inner_round:.1f}" fill="#0ea5e9" opacity="0.26"/>
            <rect x="645" y="{top_inner_y:.1f}" width="498" height="{top_inner_h:.1f}" rx="{inner_round:.1f}" fill="#fb7185" opacity="0.26"/>
            <path d="M57 453 H420 L560 376" fill="none" stroke="#7dd3fc" stroke-width="{inner_thickness:.1f}" stroke-linecap="round" stroke-linejoin="round" opacity="0.24"/>
            <path d="M640 376 L774 453 H1143" fill="none" stroke="#fda4af" stroke-width="{inner_thickness:.1f}" stroke-linecap="round" stroke-linejoin="round" opacity="0.24"/>

            <!-- Moving liquid slugs (speed follows airflow_speed) -->
            <g clip-path="url(#clipTopCold)">
              <rect x="-240" y="{top_inner_y:.1f}" width="{slug_len:.1f}" height="{top_inner_h:.1f}" rx="{inner_round:.1f}" fill="url(#coldSlug)" filter="url(#blueGlow)">
                <animate attributeName="x" from="-240" to="620" dur="{duration:.2f}s" repeatCount="indefinite"/>
              </rect>
              <rect x="-560" y="{top_inner_y:.1f}" width="{slug_len*0.92:.1f}" height="{top_inner_h:.1f}" rx="{inner_round:.1f}" fill="url(#coldSlug)" opacity="0.85" filter="url(#blueGlow)">
                <animate attributeName="x" from="-560" to="620" dur="{duration:.2f}s" begin="{duration/2:.2f}s" repeatCount="indefinite"/>
              </rect>
            </g>

            <g clip-path="url(#clipTopWarm)">
              <rect x="1240" y="{top_inner_y:.1f}" width="{slug_len:.1f}" height="{top_inner_h:.1f}" rx="{inner_round:.1f}" fill="url(#warmSlug)" filter="url(#redGlow)">
                <animate attributeName="x" from="1240" to="520" dur="{duration:.2f}s" repeatCount="indefinite"/>
              </rect>
              <rect x="1560" y="{top_inner_y:.1f}" width="{slug_len*0.92:.1f}" height="{top_inner_h:.1f}" rx="{inner_round:.1f}" fill="url(#warmSlug)" opacity="0.85" filter="url(#redGlow)">
                <animate attributeName="x" from="1560" to="520" dur="{duration:.2f}s" begin="{duration/2:.2f}s" repeatCount="indefinite"/>
              </rect>
            </g>

            <g clip-path="url(#clipBottomCold)">
              <path d="M52 453 H420 L560 376" fill="none" stroke="url(#coldSlug)" stroke-width="{inner_thickness:.1f}" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="{slug_len:.1f} 360" filter="url(#blueGlow)">
                <animate attributeName="stroke-dashoffset" from="0" to="-520" dur="{duration:.2f}s" repeatCount="indefinite"/>
              </path>
              <path d="M52 453 H420 L560 376" fill="none" stroke="url(#coldSlug)" stroke-width="{inner_thickness:.1f}" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="{slug_len*0.92:.1f} 360" opacity="0.8" filter="url(#blueGlow)">
                <animate attributeName="stroke-dashoffset" from="-260" to="-780" dur="{duration:.2f}s" repeatCount="indefinite"/>
              </path>
            </g>

            <g clip-path="url(#clipBottomWarm)">
              <path d="M640 376 L774 453 H1148" fill="none" stroke="url(#warmSlug)" stroke-width="{inner_thickness:.1f}" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="{slug_len:.1f} 360" filter="url(#redGlow)">
                <animate attributeName="stroke-dashoffset" from="0" to="520" dur="{duration:.2f}s" repeatCount="indefinite"/>
              </path>
              <path d="M640 376 L774 453 H1148" fill="none" stroke="url(#warmSlug)" stroke-width="{inner_thickness:.1f}" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="{slug_len*0.92:.1f} 360" opacity="0.8" filter="url(#redGlow)">
                <animate attributeName="stroke-dashoffset" from="260" to="780" dur="{duration:.2f}s" repeatCount="indefinite"/>
              </path>
            </g>

            <!-- Labels -->
            <text x="58" y="230" fill="#7dd3fc" font-size="22" font-weight="700">Fresh air from outside</text>
            <text x="722" y="228" fill="#fca5a5" font-size="22" font-weight="700">Warm exhaust from inside</text>
            <text x="710" y="502" fill="#fca5a5" font-size="22" font-weight="700">Pre-warmed supply to inside</text>
            <text x="58" y="503" fill="#7dd3fc" font-size="22" font-weight="700">Cooled exhaust to outside</text>

            <!-- Heat exchange intensification (scales with recovery_efficiency) -->
            <circle cx="600" cy="360" r="{pulse_base_radius:.1f}" fill="#f59e0b" opacity="{pulse_base_opacity:.2f}" filter="url(#goldGlow)">
              <animate attributeName="r" values="{pulse_base_radius:.1f};{pulse_max_radius:.1f};{pulse_base_radius:.1f}" dur="{pulse_duration:.2f}s" repeatCount="indefinite"/>
              <animate attributeName="opacity" values="{pulse_base_opacity:.2f};{max(0.05, pulse_base_opacity*0.35):.2f};{pulse_base_opacity:.2f}" dur="{pulse_duration:.2f}s" repeatCount="indefinite"/>
            </circle>

            <!-- Cross-exchanger energy transfer arrows -->
            <g opacity="{exch_arrow_opacity:.2f}" filter="url(#goldGlow)">
              <path d="M 690 280 L 620 320" stroke="url(#exchangeArrow)" stroke-width="8" stroke-linecap="round" fill="none"/>
              <polygon points="615,323 626,311 629,326" fill="#fde68a"/>

              <path d="M 720 330 L 640 360" stroke="url(#exchangeArrow)" stroke-width="8" stroke-linecap="round" fill="none"/>
              <polygon points="635,362 646,351 648,366" fill="#fde68a"/>
            </g>

            {"<g opacity='{:.2f}' filter='url(#goldGlow)'><path d='M 705 390 L 620 402' stroke='url(#exchangeArrow)' stroke-width='8' stroke-linecap='round' fill='none'/><polygon points='615,402 628,394 628,409' fill='#fde68a'/></g>".format(exch_arrow_opacity*0.95) if exch_arrow_count >= 3 else ""}

            {"<g opacity='{:.2f}' filter='url(#goldGlow)'><path d='M 660 245 L 600 290' stroke='url(#exchangeArrow)' stroke-width='7' stroke-linecap='round' fill='none'/><polygon points='596,294 607,282 610,297' fill='#fde68a'/></g>".format(exch_arrow_opacity*0.85) if exch_arrow_count >= 4 else ""}

            {"<g opacity='{:.2f}' filter='url(#goldGlow)'><path d='M 745 438 L 650 420' stroke='url(#exchangeArrow)' stroke-width='7' stroke-linecap='round' fill='none'/><polygon points='646,419 660,414 657,429' fill='#fde68a'/></g>".format(exch_arrow_opacity*0.85) if exch_arrow_count >= 5 else ""}

            <!-- Indicator bars showing parameter-linked behavior -->
            <rect x="78" y="564" width="1040" height="134" rx="16" fill="#091827" stroke="#1e3a5f" stroke-width="2"/>

            <text x="110" y="600" fill="#e5e7eb" font-size="20" font-weight="700">Outside air</text>
            <text x="314" y="600" fill="#e5e7eb" font-size="20" font-weight="700">Indoor exhaust</text>
            <text x="555" y="600" fill="#e5e7eb" font-size="20" font-weight="700">Recovery efficiency</text>
            <text x="806" y="600" fill="#e5e7eb" font-size="20" font-weight="700">Airflow speed</text>
            <text x="980" y="600" fill="#e5e7eb" font-size="20" font-weight="700">Delivered supply</text>

            <text x="112" y="632" fill="#7dd3fc" font-size="24" font-weight="800">{fresh_air_temp_c:.1f} °C</text>
            <text x="318" y="632" fill="#fca5a5" font-size="24" font-weight="800">{exhaust_air_temp_c:.1f} °C</text>
            <text x="560" y="632" fill="#fde68a" font-size="24" font-weight="800">{recovery_efficiency*100:.0f}%</text>
            <text x="813" y="632" fill="#c4b5fd" font-size="24" font-weight="800">{airflow_speed:.2f}×</text>
            <text x="988" y="632" fill="#f9fafb" font-size="24" font-weight="800">{delivered_temp:.1f} °C</text>

            <text x="555" y="666" fill="#93c5fd" font-size="15" font-weight="700">{eff_label(recovery_efficiency)}</text>
            <text x="790" y="666" fill="#93c5fd" font-size="15" font-weight="700">Faster speed → quicker / thicker flow</text>

            <!-- Airflow / flow thickness indicator -->
            <rect x="756" y="676" width="208" height="10" rx="5" fill="#152739" stroke="#284b74" stroke-width="1"/>
            <rect x="756" y="676" width="{208 * speed_norm:.1f}" height="10" rx="5" fill="#a78bfa"/>
            <text x="970" y="685" fill="#94a3b8" font-size="12">flow rate / thickness</text>
          </svg>
        </div>

        <div style="background:#081220; border:1px solid #17304d; border-radius:18px; padding:16px;">
          <div style="font-size:18px; font-weight:800; margin-bottom:10px;">How to interpret this panel</div>
          <div style="font-size:14px; line-height:1.65; color:#cbd5e1;">
            <b>Blue liquid slugs:</b> outside fresh air entering the protected system.<br>
            <b>Red liquid slugs:</b> warmer indoor exhaust donating thermal energy across the exchanger core.<br>
            <b>Gold pulse + arrows:</b> conceptual heat-transfer intensity, linked to <b>recovery_efficiency</b>.<br><br>
            This is an <b>illustrative simulation graphic</b> for TAIVAS concept mode. It visualizes thermal recovery logic and how a heat-buffer layer could reduce electrical heating/cooling burden during extreme climate scenarios.
          </div>

          <div style="margin-top:16px; border-top:1px solid #17304d; padding-top:14px;">
            <div style="font-size:16px; font-weight:800; margin-bottom:8px;">Parameter-linked behavior</div>
            <div style="font-size:14px; line-height:1.75; color:#cbd5e1;">
              <b>Airflow speed</b> increases:
              <ul style="margin-top:6px; margin-bottom:10px; padding-left:18px;">
                <li>liquid slug movement speed</li>
                <li>visible flow thickness</li>
                <li>slug length / flow-rate impression</li>
              </ul>
              <b>Recovery efficiency</b> increases:
              <ul style="margin-top:6px; margin-bottom:0; padding-left:18px;">
                <li>heat-exchange pulse intensity</li>
                <li>cross-core transfer arrows</li>
                <li>delivered supply temperature</li>
              </ul>
            </div>
          </div>

          <div style="margin-top:16px; border-top:1px solid #17304d; padding-top:14px;">
            <div style="font-size:16px; font-weight:800; margin-bottom:8px;">Derived concept outputs</div>
            <div style="font-size:14px; line-height:1.7; color:#cbd5e1;">
              Exhaust after exchange: <b>{exhaust_after_exchange:.1f} °C</b><br>
              Conceptual delivered supply: <b>{delivered_temp:.1f} °C</b><br>
              Liquid animation duration: <b>{duration:.2f} s</b><br>
              Visible flow thickness: <b>{inner_thickness:.1f} px</b>
            </div>
          </div>

          <div style="margin-top:16px; background:#0d1e30; border:1px solid #284b74; border-radius:14px; padding:12px;">
            <div style="font-size:13px; color:#fde68a; font-weight:700; margin-bottom:6px;">Model boundary</div>
            <div style="font-size:13px; line-height:1.6; color:#cbd5e1;">
              This panel is a conceptual visualization, not a validated hardware design or a physical engineering guarantee.
            </div>
          </div>
        </div>
      </div>
    </div>
    """
    components.html(html, height=height, scrolling=False)
