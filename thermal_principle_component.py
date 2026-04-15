
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
    1) liquid slug speed links to airflow_speed
    2) heat-exchange zone is more visually obvious
    3) conduit thickness / slug size syncs with flow rate
    """
    recovery_efficiency = max(0.0, min(1.0, float(recovery_efficiency)))
    airflow_speed = max(0.4, min(2.5, float(airflow_speed)))

    delivered_temp = fresh_air_temp_c + (exhaust_air_temp_c - fresh_air_temp_c) * recovery_efficiency
    exhaust_after_exchange = exhaust_air_temp_c - (exhaust_air_temp_c - fresh_air_temp_c) * recovery_efficiency

    # Flow-linked visual parameters
    flow_ratio = (airflow_speed - 0.4) / (2.5 - 0.4)  # 0 → 1
    pipe_w = 22 + flow_ratio * 16                      # ~22 → 38
    pipe_w = round(pipe_w, 1)
    inner_w = pipe_w - 10                              # liquid thickness within pipe
    inner_w = max(10, inner_w)

    top_pipe_h = pipe_w
    top_liquid_h = inner_w
    top_y = 260 - top_pipe_h / 2
    top_inner_y = 260 - top_liquid_h / 2

    bottom_y = 458
    bottom_w = pipe_w
    bottom_liquid_w = inner_w

    slug_len = 80 + flow_ratio * 95                    # longer slugs at higher flow
    slug_gap = 210 - flow_ratio * 70                   # smaller gap at higher flow
    dash_total = slug_len + slug_gap

    duration = 5.4 / airflow_speed                    # faster flow → quicker motion
    pulse_duration = 3.4 - flow_ratio * 1.2           # stronger/faster exchange visual

    # More noticeable heat-transfer arrows/intensity with higher recovery
    heat_strength = 0.35 + recovery_efficiency * 0.45
    heat_lines_opacity = 0.20 + recovery_efficiency * 0.45

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

              <linearGradient id="crossTransfer" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#38bdf8"/>
                <stop offset="50%" stop-color="#fde68a"/>
                <stop offset="100%" stop-color="#fb7185"/>
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

              <filter id="amberGlow">
                <feGaussianBlur stdDeviation="4" result="blur"/>
                <feMerge>
                  <feMergeNode in="blur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>

              <clipPath id="clipTopCold">
                <rect x="52" y="{top_y:.1f}" width="508" height="{top_pipe_h:.1f}" rx="{top_pipe_h/2:.1f}"/>
              </clipPath>
              <clipPath id="clipTopWarm">
                <rect x="640" y="{top_y:.1f}" width="508" height="{top_pipe_h:.1f}" rx="{top_pipe_h/2:.1f}"/>
              </clipPath>
              <clipPath id="clipBottomCold">
                <path d="M52 {bottom_y - bottom_w/2:.1f} H420 L560 {376 - bottom_w/2:.1f} V{376 + bottom_w/2:.1f} L426 {bottom_y + bottom_w/2:.1f} H52 Z"/>
              </clipPath>
              <clipPath id="clipBottomWarm">
                <path d="M640 {376 - bottom_w/2:.1f} L774 {bottom_y - bottom_w/2:.1f} H1148 V{bottom_y + bottom_w/2:.1f} H768 L640 {376 + bottom_w/2:.1f} Z"/>
              </clipPath>
            </defs>

            <rect x="28" y="24" width="1144" height="726" rx="22" fill="#081220" stroke="#1f3b5a" stroke-width="3"/>
            <text x="70" y="82" fill="#f8fafc" font-size="34" font-weight="800">Conceptual Heat Recovery / Thermal Buffer Flow</text>
            <text x="70" y="118" fill="#94a3b8" font-size="18">Outside air is pre-conditioned by exchange with indoor exhaust before delivery to the protected zone.</text>

            <!-- Protected frame -->
            <rect x="250" y="180" width="700" height="360" rx="24" fill="#0b1828" stroke="#39526f" stroke-width="4"/>
            <rect x="270" y="200" width="660" height="320" rx="18" fill="#0d1e30" stroke="#243b53" stroke-width="2"/>

            <!-- Side chambers -->
            <rect x="292" y="220" width="280" height="120" rx="14" fill="#0c2940" stroke="#21557a" stroke-width="2"/>
            <rect x="292" y="380" width="280" height="120" rx="14" fill="#0c2940" stroke="#21557a" stroke-width="2"/>
            <rect x="628" y="220" width="280" height="120" rx="14" fill="#3a1719" stroke="#7f1d1d" stroke-width="2"/>
            <rect x="628" y="380" width="280" height="120" rx="14" fill="#3a1719" stroke="#7f1d1d" stroke-width="2"/>

            <!-- Central exchanger -->
            <g transform="translate(600,360) rotate(45)">
              <rect x="-120" y="-120" width="240" height="240" rx="12" fill="#2a2a35" stroke="url(#exchangeGrad)" stroke-width="8"/>
              <rect x="-95" y="-95" width="190" height="190" rx="10" fill="#f8fafc" opacity="0.96"/>
              <path d="M -80 -40 L 80 -40" stroke="#cbd5e1" stroke-width="6" opacity="0.9"/>
              <path d="M -80 -10 L 80 -10" stroke="#cbd5e1" stroke-width="6" opacity="0.9"/>
              <path d="M -80 20 L 80 20" stroke="#cbd5e1" stroke-width="6" opacity="0.9"/>
              <path d="M -80 50 L 80 50" stroke="#cbd5e1" stroke-width="6" opacity="0.9"/>
            </g>

            <!-- Stronger heat-transfer core -->
            <circle cx="600" cy="360" r="54" fill="#f59e0b" opacity="{heat_strength:.2f}" filter="url(#amberGlow)">
              <animate attributeName="r" values="48;88;48" dur="{pulse_duration:.2f}s" repeatCount="indefinite"/>
              <animate attributeName="opacity" values="{heat_strength:.2f};0.10;{heat_strength:.2f}" dur="{pulse_duration:.2f}s" repeatCount="indefinite"/>
            </circle>

            <!-- Cross-transfer arrows / animated effect -->
            <g opacity="{heat_lines_opacity:.2f}">
              <path d="M545 304 Q580 332 600 360 Q620 388 655 416" fill="none" stroke="url(#crossTransfer)" stroke-width="8" stroke-linecap="round">
                <animate attributeName="opacity" values="0.1;0.85;0.1" dur="{pulse_duration:.2f}s" repeatCount="indefinite"/>
              </path>
              <path d="M655 304 Q620 332 600 360 Q580 388 545 416" fill="none" stroke="url(#crossTransfer)" stroke-width="8" stroke-linecap="round">
                <animate attributeName="opacity" values="0.85;0.1;0.85" dur="{pulse_duration:.2f}s" repeatCount="indefinite"/>
              </path>
            </g>

            <!-- Small directional arrows showing energy transfer -->
            <g opacity="{0.28 + recovery_efficiency * 0.45:.2f}">
              <path d="M 554 330 L 566 320 L 566 327 L 582 327 L 582 333 L 566 333 L 566 340 Z" fill="#fde68a">
                <animate attributeName="opacity" values="0.2;0.95;0.2" dur="{pulse_duration:.2f}s" repeatCount="indefinite"/>
              </path>
              <path d="M 646 390 L 634 400 L 634 393 L 618 393 L 618 387 L 634 387 L 634 380 Z" fill="#fde68a">
                <animate attributeName="opacity" values="0.95;0.2;0.95" dur="{pulse_duration:.2f}s" repeatCount="indefinite"/>
              </path>
            </g>

            <!-- Pipe shells (thickness depends on airflow_speed) -->
            <rect x="52" y="{top_y:.1f}" width="508" height="{top_pipe_h:.1f}" rx="{top_pipe_h/2:.1f}" fill="url(#coldPipeBase)"/>
            <rect x="640" y="{top_y:.1f}" width="508" height="{top_pipe_h:.1f}" rx="{top_pipe_h/2:.1f}" fill="url(#warmPipeBase)"/>
            <path d="M52 {bottom_y:.1f} H420 L560 376" fill="none" stroke="url(#coldPipeBase)" stroke-width="{bottom_w:.1f}" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M640 376 L774 {bottom_y:.1f} H1148" fill="none" stroke="url(#warmPipeBase)" stroke-width="{bottom_w:.1f}" stroke-linecap="round" stroke-linejoin="round"/>

            <!-- Static inner fluid base -->
            <rect x="57" y="{top_inner_y:.1f}" width="498" height="{top_liquid_h:.1f}" rx="{top_liquid_h/2:.1f}" fill="#0ea5e9" opacity="0.24"/>
            <rect x="645" y="{top_inner_y:.1f}" width="498" height="{top_liquid_h:.1f}" rx="{top_liquid_h/2:.1f}" fill="#fb7185" opacity="0.24"/>
            <path d="M57 {bottom_y:.1f} H420 L560 376" fill="none" stroke="#7dd3fc" stroke-width="{bottom_liquid_w:.1f}" stroke-linecap="round" stroke-linejoin="round" opacity="0.24"/>
            <path d="M640 376 L774 {bottom_y:.1f} H1143" fill="none" stroke="#fda4af" stroke-width="{bottom_liquid_w:.1f}" stroke-linecap="round" stroke-linejoin="round" opacity="0.24"/>

            <!-- Clearly moving liquid slugs; speed + slug size link to airflow_speed -->
            <g clip-path="url(#clipTopCold)">
              <rect x="-200" y="{top_inner_y:.1f}" width="{slug_len:.1f}" height="{top_liquid_h:.1f}" rx="{top_liquid_h/2:.1f}" fill="url(#coldSlug)" filter="url(#blueGlow)">
                <animate attributeName="x" from="-200" to="630" dur="{duration:.2f}s" repeatCount="indefinite"/>
              </rect>
              <rect x="-540" y="{top_inner_y:.1f}" width="{slug_len * 0.92:.1f}" height="{top_liquid_h:.1f}" rx="{top_liquid_h/2:.1f}" fill="url(#coldSlug)" opacity="0.88" filter="url(#blueGlow)">
                <animate attributeName="x" from="-540" to="630" dur="{duration:.2f}s" begin="{duration/2:.2f}s" repeatCount="indefinite"/>
              </rect>
            </g>

            <g clip-path="url(#clipTopWarm)">
              <rect x="1240" y="{top_inner_y:.1f}" width="{slug_len:.1f}" height="{top_liquid_h:.1f}" rx="{top_liquid_h/2:.1f}" fill="url(#warmSlug)" filter="url(#redGlow)">
                <animate attributeName="x" from="1240" to="520" dur="{duration:.2f}s" repeatCount="indefinite"/>
              </rect>
              <rect x="1510" y="{top_inner_y:.1f}" width="{slug_len * 0.92:.1f}" height="{top_liquid_h:.1f}" rx="{top_liquid_h/2:.1f}" fill="url(#warmSlug)" opacity="0.88" filter="url(#redGlow)">
                <animate attributeName="x" from="1510" to="520" dur="{duration:.2f}s" begin="{duration/2:.2f}s" repeatCount="indefinite"/>
              </rect>
            </g>

            <!-- Bottom paths; slug spacing and thickness link to airflow_speed -->
            <g clip-path="url(#clipBottomCold)">
              <path d="M52 {bottom_y:.1f} H420 L560 376" fill="none" stroke="url(#coldSlug)" stroke-width="{bottom_liquid_w:.1f}" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="{slug_len:.1f} {slug_gap:.1f}" filter="url(#blueGlow)">
                <animate attributeName="stroke-dashoffset" from="0" to="-{dash_total:.1f}" dur="{duration:.2f}s" repeatCount="indefinite"/>
              </path>
              <path d="M52 {bottom_y:.1f} H420 L560 376" fill="none" stroke="url(#coldSlug)" stroke-width="{bottom_liquid_w:.1f}" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="{slug_len * 0.92:.1f} {slug_gap:.1f}" opacity="0.84" filter="url(#blueGlow)">
                <animate attributeName="stroke-dashoffset" from="-{dash_total/2:.1f}" to="-{dash_total * 1.5:.1f}" dur="{duration:.2f}s" repeatCount="indefinite"/>
              </path>
            </g>

            <g clip-path="url(#clipBottomWarm)">
              <path d="M640 376 L774 {bottom_y:.1f} H1148" fill="none" stroke="url(#warmSlug)" stroke-width="{bottom_liquid_w:.1f}" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="{slug_len:.1f} {slug_gap:.1f}" filter="url(#redGlow)">
                <animate attributeName="stroke-dashoffset" from="0" to="{dash_total:.1f}" dur="{duration:.2f}s" repeatCount="indefinite"/>
              </path>
              <path d="M640 376 L774 {bottom_y:.1f} H1148" fill="none" stroke="url(#warmSlug)" stroke-width="{bottom_liquid_w:.1f}" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="{slug_len * 0.92:.1f} {slug_gap:.1f}" opacity="0.84" filter="url(#redGlow)">
                <animate attributeName="stroke-dashoffset" from="{dash_total/2:.1f}" to="{dash_total * 1.5:.1f}" dur="{duration:.2f}s" repeatCount="indefinite"/>
              </path>
            </g>

            <!-- Labels -->
            <text x="58" y="228" fill="#7dd3fc" font-size="22" font-weight="700">Fresh air from outside</text>
            <text x="722" y="226" fill="#fca5a5" font-size="22" font-weight="700">Warm exhaust from inside</text>
            <text x="720" y="515" fill="#fca5a5" font-size="22" font-weight="700">Pre-warmed supply to inside</text>
            <text x="58" y="516" fill="#7dd3fc" font-size="22" font-weight="700">Cooled exhaust to outside</text>

            <!-- Small numeric transformation markers -->
            <rect x="498" y="196" width="122" height="34" rx="9" fill="#102234" stroke="#284b74" stroke-width="1.5"/>
            <text x="559" y="218" text-anchor="middle" fill="#fde68a" font-size="15" font-weight="800">
              η = {recovery_efficiency*100:.0f}%
            </text>

            <rect x="424" y="528" width="150" height="36" rx="10" fill="#102234" stroke="#284b74" stroke-width="1.5"/>
            <text x="499" y="551" text-anchor="middle" fill="#93c5fd" font-size="15" font-weight="800">
              exhaust → {exhaust_after_exchange:.1f} °C
            </text>

            <rect x="662" y="528" width="158" height="36" rx="10" fill="#231519" stroke="#7f1d1d" stroke-width="1.5"/>
            <text x="741" y="551" text-anchor="middle" fill="#fecaca" font-size="15" font-weight="800">
              supply → {delivered_temp:.1f} °C
            </text>

            <!-- Bottom metrics -->
            <rect x="74" y="600" width="1060" height="114" rx="16" fill="#091827" stroke="#1e3a5f" stroke-width="2"/>
            <text x="110" y="647" fill="#e5e7eb" font-size="20" font-weight="700">Outside air</text>
            <text x="350" y="647" fill="#e5e7eb" font-size="20" font-weight="700">Indoor exhaust</text>
            <text x="635" y="647" fill="#e5e7eb" font-size="20" font-weight="700">Recovery efficiency</text>
            <text x="900" y="647" fill="#e5e7eb" font-size="20" font-weight="700">Delivered supply</text>

            <text x="112" y="679" fill="#7dd3fc" font-size="24" font-weight="800">{fresh_air_temp_c:.1f} °C</text>
            <text x="350" y="679" fill="#fca5a5" font-size="24" font-weight="800">{exhaust_air_temp_c:.1f} °C</text>
            <text x="664" y="679" fill="#fde68a" font-size="24" font-weight="800">{recovery_efficiency*100:.0f}%</text>
            <text x="905" y="679" fill="#f9fafb" font-size="24" font-weight="800">{delivered_temp:.1f} °C</text>

            <text x="110" y="704" fill="#94a3b8" font-size="15">Flow rate visual: {airflow_speed:.2f}×</text>
            <text x="350" y="704" fill="#94a3b8" font-size="15">Conduit thickness: {pipe_w:.0f}px</text>
            <text x="635" y="704" fill="#94a3b8" font-size="15">Slug length: {slug_len:.0f}px</text>
            <text x="900" y="704" fill="#94a3b8" font-size="15">Exchange pulse linked to η</text>
          </svg>
        </div>

        <div style="background:#081220; border:1px solid #17304d; border-radius:18px; padding:16px;">
          <div style="font-size:18px; font-weight:800; margin-bottom:10px;">How to interpret this panel</div>
          <div style="font-size:14px; line-height:1.65; color:#cbd5e1;">
            <b>Blue liquid slugs:</b> outside fresh air entering the protected system.<br>
            <b>Red liquid slugs:</b> warmer indoor exhaust donating thermal energy across the exchanger core.<br>
            <b>Gold core + cross arrows:</b> more visible heat transfer / exchange intensity.<br><br>
            This upgraded panel ties <b>flow speed</b>, <b>conduit thickness</b>, and <b>slug size</b> to the system parameter <b>airflow_speed</b>, while the <b>heat-exchange effect</b> scales with <b>recovery_efficiency</b>.
          </div>

          <div style="margin-top:16px; border-top:1px solid #17304d; padding-top:14px;">
            <div style="font-size:16px; font-weight:800; margin-bottom:8px;">Linked visual parameters</div>
            <div style="font-size:14px; line-height:1.75; color:#cbd5e1;">
              Airflow speed: <b>{airflow_speed:.2f}×</b><br>
              Conduit thickness: <b>{pipe_w:.0f}px</b><br>
              Liquid slug length: <b>{slug_len:.0f}px</b><br>
              Recovery efficiency: <b>{recovery_efficiency*100:.0f}%</b>
            </div>
          </div>

          <div style="margin-top:16px; border-top:1px solid #17304d; padding-top:14px;">
            <div style="font-size:16px; font-weight:800; margin-bottom:8px;">Derived concept outputs</div>
            <div style="font-size:14px; line-height:1.7; color:#cbd5e1;">
              Exhaust after exchange: <b>{exhaust_after_exchange:.1f} °C</b><br>
              Conceptual delivered supply: <b>{delivered_temp:.1f} °C</b><br>
              Heat-transfer emphasis: <b>{recovery_efficiency*100:.0f}% linked</b>
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
