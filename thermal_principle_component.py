
import streamlit.components.v1 as components


def render_thermal_principle_simulation(
    title: str = "Thermal Recovery Principle (Concept Mode)",
    height: int = 760,
    fresh_air_temp_c: float = -5.0,
    exhaust_air_temp_c: float = 24.0,
    recovery_efficiency: float = 0.72,
    airflow_speed: float = 1.0,
):
    """
    Render an animated conceptual heat-recovery / thermal-exchange diagram in Streamlit.
    This version uses clear liquid slugs moving through the ducts rather than flashing gradients.
    """
    recovery_efficiency = max(0.0, min(1.0, float(recovery_efficiency)))
    airflow_speed = max(0.4, min(2.5, float(airflow_speed)))

    delivered_temp = fresh_air_temp_c + (exhaust_air_temp_c - fresh_air_temp_c) * recovery_efficiency
    exhaust_after_exchange = exhaust_air_temp_c - (exhaust_air_temp_c - fresh_air_temp_c) * recovery_efficiency

    duration = 4.6 / airflow_speed
    pulse_duration = 3.8 / airflow_speed

    html = f"""
    <div style="font-family: Inter, Arial, sans-serif; color:#e5e7eb; padding-bottom:12px;">
      <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:12px;">
        <div style="font-size:28px; font-weight:800;">{title}</div>
        <div style="font-size:13px; color:#94a3b8;">Conceptual animated diagram for TAIVAS thermal-resilience mode</div>
      </div>

      <div style="display:grid; grid-template-columns: 1fr 320px; gap:18px; align-items:start;">
        <div style="background:#07111f; border:1px solid #17304d; border-radius:18px; padding:14px;">
          <svg viewBox="0 0 1200 760" width="100%" height="100%" aria-label="animated heat recovery diagram">
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

            <rect x="28" y="24" width="1144" height="706" rx="22" fill="#081220" stroke="#1f3b5a" stroke-width="3"/>
            <text x="70" y="82" fill="#f8fafc" font-size="34" font-weight="800">Conceptual Heat Recovery / Thermal Buffer Flow</text>
            <text x="70" y="118" fill="#94a3b8" font-size="18">Outside air is pre-conditioned by exchange with indoor exhaust before delivery to the protected zone.</text>

            <rect x="250" y="180" width="700" height="360" rx="24" fill="#0b1828" stroke="#39526f" stroke-width="4"/>
            <rect x="270" y="200" width="660" height="320" rx="18" fill="#0d1e30" stroke="#243b53" stroke-width="2"/>

            <rect x="292" y="220" width="280" height="120" rx="14" fill="#0c2940" stroke="#21557a" stroke-width="2"/>
            <rect x="292" y="380" width="280" height="120" rx="14" fill="#0c2940" stroke="#21557a" stroke-width="2"/>
            <rect x="628" y="220" width="280" height="120" rx="14" fill="#3a1719" stroke="#7f1d1d" stroke-width="2"/>
            <rect x="628" y="380" width="280" height="120" rx="14" fill="#3a1719" stroke="#7f1d1d" stroke-width="2"/>

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
            <path d="M52 453 H420 L560 376" fill="none" stroke="url(#coldPipeBase)" stroke-width="30" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M640 376 L774 453 H1148" fill="none" stroke="url(#warmPipeBase)" stroke-width="30" stroke-linecap="round" stroke-linejoin="round"/>

            <!-- Static inner fluid base -->
            <rect x="57" y="251" width="498" height="20" rx="10" fill="#0ea5e9" opacity="0.24"/>
            <rect x="645" y="251" width="498" height="20" rx="10" fill="#fb7185" opacity="0.24"/>
            <path d="M57 453 H420 L560 376" fill="none" stroke="#7dd3fc" stroke-width="18" stroke-linecap="round" stroke-linejoin="round" opacity="0.24"/>
            <path d="M640 376 L774 453 H1143" fill="none" stroke="#fda4af" stroke-width="18" stroke-linecap="round" stroke-linejoin="round" opacity="0.24"/>

            <!-- Clearly moving liquid slugs -->
            <g clip-path="url(#clipTopCold)">
              <rect x="-200" y="251" width="150" height="20" rx="10" fill="url(#coldSlug)" filter="url(#blueGlow)">
                <animate attributeName="x" from="-200" to="600" dur="{duration}s" repeatCount="indefinite"/>
              </rect>
              <rect x="-500" y="251" width="140" height="20" rx="10" fill="url(#coldSlug)" opacity="0.85" filter="url(#blueGlow)">
                <animate attributeName="x" from="-500" to="600" dur="{duration}s" begin="{duration/2:.2f}s" repeatCount="indefinite"/>
              </rect>
            </g>

            <g clip-path="url(#clipTopWarm)">
              <rect x="1240" y="251" width="150" height="20" rx="10" fill="url(#warmSlug)" filter="url(#redGlow)">
                <animate attributeName="x" from="1240" to="540" dur="{duration}s" repeatCount="indefinite"/>
              </rect>
              <rect x="1500" y="251" width="140" height="20" rx="10" fill="url(#warmSlug)" opacity="0.85" filter="url(#redGlow)">
                <animate attributeName="x" from="1500" to="540" dur="{duration}s" begin="{duration/2:.2f}s" repeatCount="indefinite"/>
              </rect>
            </g>

            <!-- Bottom left cold path moving slugs -->
            <g clip-path="url(#clipBottomCold)">
              <path d="M52 453 H420 L560 376" fill="none" stroke="url(#coldSlug)" stroke-width="18" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="125 360" filter="url(#blueGlow)">
                <animate attributeName="stroke-dashoffset" from="0" to="-485" dur="{duration}s" repeatCount="indefinite"/>
              </path>
              <path d="M52 453 H420 L560 376" fill="none" stroke="url(#coldSlug)" stroke-width="18" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="125 360" opacity="0.8" filter="url(#blueGlow)">
                <animate attributeName="stroke-dashoffset" from="-242" to="-727" dur="{duration}s" repeatCount="indefinite"/>
              </path>
            </g>

            <!-- Bottom right warm path moving slugs -->
            <g clip-path="url(#clipBottomWarm)">
              <path d="M640 376 L774 453 H1148" fill="none" stroke="url(#warmSlug)" stroke-width="18" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="125 360" filter="url(#redGlow)">
                <animate attributeName="stroke-dashoffset" from="0" to="485" dur="{duration}s" repeatCount="indefinite"/>
              </path>
              <path d="M640 376 L774 453 H1148" fill="none" stroke="url(#warmSlug)" stroke-width="18" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="125 360" opacity="0.8" filter="url(#redGlow)">
                <animate attributeName="stroke-dashoffset" from="242" to="727" dur="{duration}s" repeatCount="indefinite"/>
              </path>
            </g>

            <text x="58" y="230" fill="#7dd3fc" font-size="22" font-weight="700">Fresh air from outside</text>
            <text x="722" y="228" fill="#fca5a5" font-size="22" font-weight="700">Warm exhaust from inside</text>
            <text x="720" y="502" fill="#fca5a5" font-size="22" font-weight="700">Pre-warmed supply to inside</text>
            <text x="58" y="503" fill="#7dd3fc" font-size="22" font-weight="700">Cooled exhaust to outside</text>

            <!-- Heat transfer pulse -->
            <circle cx="600" cy="360" r="55" fill="#f59e0b" opacity="0.16">
              <animate attributeName="r" values="48;78;48" dur="{pulse_duration}s" repeatCount="indefinite"/>
              <animate attributeName="opacity" values="0.22;0.06;0.22" dur="{pulse_duration}s" repeatCount="indefinite"/>
            </circle>

            <!-- Bottom metrics -->
            <rect x="74" y="560" width="1060" height="108" rx="16" fill="#091827" stroke="#1e3a5f" stroke-width="2"/>
            <text x="110" y="608" fill="#e5e7eb" font-size="20" font-weight="700">Outside air</text>
            <text x="350" y="608" fill="#e5e7eb" font-size="20" font-weight="700">Indoor exhaust</text>
            <text x="635" y="608" fill="#e5e7eb" font-size="20" font-weight="700">Recovery efficiency</text>
            <text x="900" y="608" fill="#e5e7eb" font-size="20" font-weight="700">Delivered supply</text>

            <text x="112" y="640" fill="#7dd3fc" font-size="24" font-weight="800">{fresh_air_temp_c:.1f} °C</text>
            <text x="350" y="640" fill="#fca5a5" font-size="24" font-weight="800">{exhaust_air_temp_c:.1f} °C</text>
            <text x="664" y="640" fill="#fde68a" font-size="24" font-weight="800">{recovery_efficiency*100:.0f}%</text>
            <text x="905" y="640" fill="#f9fafb" font-size="24" font-weight="800">{delivered_temp:.1f} °C</text>
          </svg>
        </div>

        <div style="background:#081220; border:1px solid #17304d; border-radius:18px; padding:16px;">
          <div style="font-size:18px; font-weight:800; margin-bottom:10px;">How to interpret this panel</div>
          <div style="font-size:14px; line-height:1.65; color:#cbd5e1;">
            <b>Blue liquid slugs:</b> outside fresh air entering the protected system.<br>
            <b>Red liquid slugs:</b> warmer indoor exhaust donating thermal energy across the exchanger core.<br>
            <b>Gold pulse:</b> conceptual heat-transfer zone.<br><br>
            This is an <b>illustrative simulation graphic</b> for TAIVAS concept mode. It visualizes thermal recovery logic and how a heat-buffer layer could reduce electrical heating/cooling burden during extreme climate scenarios.
          </div>

          <div style="margin-top:16px; border-top:1px solid #17304d; padding-top:14px;">
            <div style="font-size:16px; font-weight:800; margin-bottom:8px;">Derived concept outputs</div>
            <div style="font-size:14px; line-height:1.7; color:#cbd5e1;">
              Exhaust after exchange: <b>{exhaust_after_exchange:.1f} °C</b><br>
              Conceptual delivered supply: <b>{delivered_temp:.1f} °C</b><br>
              Animation speed factor: <b>{airflow_speed:.2f}x</b>
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
