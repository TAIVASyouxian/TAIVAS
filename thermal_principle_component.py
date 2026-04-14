
import streamlit as st
import streamlit.components.v1 as components


def render_thermal_principle_simulation(
    title: str = "Thermal Recovery Principle (Concept Mode)",
    height: int = 520,
    fresh_air_temp_c: float = -5.0,
    exhaust_air_temp_c: float = 24.0,
    recovery_efficiency: float = 0.72,
    airflow_speed: float = 1.0,
):
    """
    Render an animated conceptual heat-recovery / thermal-exchange diagram in Streamlit.

    Parameters
    ----------
    title : str
        Component title shown above the animated diagram.
    height : int
        Height of the HTML component.
    fresh_air_temp_c : float
        Outside incoming air temperature.
    exhaust_air_temp_c : float
        Indoor exhaust air temperature.
    recovery_efficiency : float
        0.0 to 1.0 conceptual heat recovery effectiveness.
    airflow_speed : float
        0.5 to 2.0 animation speed multiplier.
    """
    recovery_efficiency = max(0.0, min(1.0, float(recovery_efficiency)))
    airflow_speed = max(0.4, min(2.5, float(airflow_speed)))

    delivered_temp = fresh_air_temp_c + (exhaust_air_temp_c - fresh_air_temp_c) * recovery_efficiency
    exhaust_after_exchange = exhaust_air_temp_c - (exhaust_air_temp_c - fresh_air_temp_c) * recovery_efficiency

    dot_duration = 6.0 / airflow_speed
    pulse_duration = 3.8 / airflow_speed

    html = f"""
    <div style="font-family: Inter, Arial, sans-serif; color: #e5e7eb;">
      <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:12px;">
        <div style="font-size:28px; font-weight:800;">{title}</div>
        <div style="font-size:13px; color:#94a3b8;">Conceptual animated diagram for TAIVAS thermal-resilience mode</div>
      </div>

      <div style="display:grid; grid-template-columns: 1fr 320px; gap:18px; align-items:start;">
        <div style="background:#07111f; border:1px solid #17304d; border-radius:18px; padding:14px;">
          <svg viewBox="0 0 1200 720" width="100%" height="100%" aria-label="animated heat recovery diagram">
            <defs>
              <linearGradient id="coldGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#38bdf8"/>
                <stop offset="100%" stop-color="#93c5fd"/>
              </linearGradient>
              <linearGradient id="warmGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#fca5a5"/>
                <stop offset="100%" stop-color="#ef4444"/>
              </linearGradient>
              <linearGradient id="exchangeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#fde68a"/>
                <stop offset="100%" stop-color="#f59e0b"/>
              </linearGradient>
              <filter id="glowBlue">
                <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
                <feMerge>
                  <feMergeNode in="coloredBlur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
              <filter id="glowRed">
                <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
                <feMerge>
                  <feMergeNode in="coloredBlur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
              <marker id="arrowBlue" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="9" markerHeight="9" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#38bdf8"></path>
              </marker>
              <marker id="arrowRed" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="9" markerHeight="9" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#f87171"></path>
              </marker>
            </defs>

            <rect x="28" y="24" width="1144" height="650" rx="22" fill="#081220" stroke="#1f3b5a" stroke-width="3"/>
            <text x="70" y="82" fill="#f8fafc" font-size="34" font-weight="800">Conceptual Heat Recovery / Thermal Buffer Flow</text>
            <text x="70" y="118" fill="#94a3b8" font-size="18">Outside air is pre-conditioned by exchange with indoor exhaust before delivery to the protected zone.</text>

            <!-- Main housing -->
            <rect x="250" y="180" width="700" height="360" rx="24" fill="#0b1828" stroke="#39526f" stroke-width="4"/>
            <rect x="270" y="200" width="660" height="320" rx="18" fill="#0d1e30" stroke="#243b53" stroke-width="2"/>

            <!-- Internal sections -->
            <rect x="292" y="220" width="280" height="120" rx="14" fill="#0c2940" stroke="#21557a" stroke-width="2"/>
            <rect x="292" y="380" width="280" height="120" rx="14" fill="#0c2940" stroke="#21557a" stroke-width="2"/>
            <rect x="628" y="220" width="280" height="120" rx="14" fill="#3a1719" stroke="#7f1d1d" stroke-width="2"/>
            <rect x="628" y="380" width="280" height="120" rx="14" fill="#3a1719" stroke="#7f1d1d" stroke-width="2"/>

            <!-- Heat exchanger core -->
            <g transform="translate(600,360) rotate(45)">
              <rect x="-120" y="-120" width="240" height="240" rx="12" fill="#2a2a35" stroke="url(#exchangeGrad)" stroke-width="8"/>
              <rect x="-95" y="-95" width="190" height="190" rx="10" fill="#f8fafc" opacity="0.95"/>
              <path d="M -80 -10 L 80 -10" stroke="#cbd5e1" stroke-width="6" opacity="0.9"/>
              <path d="M -80 20 L 80 20" stroke="#cbd5e1" stroke-width="6" opacity="0.9"/>
              <path d="M -80 50 L 80 50" stroke="#cbd5e1" stroke-width="6" opacity="0.9"/>
              <path d="M -80 -40 L 80 -40" stroke="#cbd5e1" stroke-width="6" opacity="0.9"/>
            </g>

            <!-- Duct paths -->
            <path d="M 60 260 L 250 260 L 430 260 L 560 320" fill="none" stroke="url(#coldGrad)" stroke-width="26" stroke-linecap="round" marker-end="url(#arrowBlue)" filter="url(#glowBlue)"/>
            <path d="M 640 400 L 770 460 L 950 460 L 1140 460" fill="none" stroke="url(#warmGrad)" stroke-width="26" stroke-linecap="round" marker-end="url(#arrowRed)" filter="url(#glowRed)"/>
            <path d="M 1140 260 L 950 260 L 770 260 L 640 320" fill="none" stroke="url(#warmGrad)" stroke-width="26" stroke-linecap="round" marker-end="url(#arrowRed)" filter="url(#glowRed)"/>
            <path d="M 560 400 L 430 460 L 250 460 L 60 460" fill="none" stroke="url(#coldGrad)" stroke-width="26" stroke-linecap="round" marker-end="url(#arrowBlue)" filter="url(#glowBlue)"/>

            <!-- Direction labels -->
            <text x="58" y="230" fill="#7dd3fc" font-size="22" font-weight="700">Fresh air from outside</text>
            <text x="825" y="228" fill="#fca5a5" font-size="22" font-weight="700">Warm exhaust from inside</text>
            <text x="818" y="502" fill="#fca5a5" font-size="22" font-weight="700">Pre-warmed supply to inside</text>
            <text x="58" y="503" fill="#7dd3fc" font-size="22" font-weight="700">Cooled exhaust to outside</text>

            <!-- Animated particles -->
            <circle r="10" fill="#7dd3fc">
              <animateMotion dur="{dot_duration}s" repeatCount="indefinite" path="M 60 260 L 250 260 L 430 260 L 560 320"/>
            </circle>
            <circle r="10" fill="#7dd3fc" opacity="0.9">
              <animateMotion dur="{dot_duration}s" begin="1.2s" repeatCount="indefinite" path="M 60 260 L 250 260 L 430 260 L 560 320"/>
            </circle>
            <circle r="10" fill="#7dd3fc" opacity="0.85">
              <animateMotion dur="{dot_duration}s" begin="2.4s" repeatCount="indefinite" path="M 560 400 L 430 460 L 250 460 L 60 460"/>
            </circle>

            <circle r="10" fill="#fca5a5">
              <animateMotion dur="{dot_duration}s" repeatCount="indefinite" path="M 1140 260 L 950 260 L 770 260 L 640 320"/>
            </circle>
            <circle r="10" fill="#fca5a5" opacity="0.9">
              <animateMotion dur="{dot_duration}s" begin="1.4s" repeatCount="indefinite" path="M 1140 260 L 950 260 L 770 260 L 640 320"/>
            </circle>
            <circle r="10" fill="#fca5a5" opacity="0.85">
              <animateMotion dur="{dot_duration}s" begin="2.8s" repeatCount="indefinite" path="M 640 400 L 770 460 L 950 460 L 1140 460"/>
            </circle>

            <!-- Exchange pulse -->
            <circle cx="600" cy="360" r="55" fill="#f59e0b" opacity="0.15">
              <animate attributeName="r" values="48;78;48" dur="{pulse_duration}s" repeatCount="indefinite"/>
              <animate attributeName="opacity" values="0.22;0.06;0.22" dur="{pulse_duration}s" repeatCount="indefinite"/>
            </circle>

            <!-- Mini gauges -->
            <rect x="74" y="560" width="1060" height="78" rx="16" fill="#091827" stroke="#1e3a5f" stroke-width="2"/>
            <text x="110" y="608" fill="#e5e7eb" font-size="20" font-weight="700">Outside air</text>
            <text x="350" y="608" fill="#e5e7eb" font-size="20" font-weight="700">Indoor exhaust</text>
            <text x="635" y="608" fill="#e5e7eb" font-size="20" font-weight="700">Recovery efficiency</text>
            <text x="900" y="608" fill="#e5e7eb" font-size="20" font-weight="700">Delivered supply</text>

            <text x="112" y="635" fill="#7dd3fc" font-size="24" font-weight="800">{fresh_air_temp_c:.1f} °C</text>
            <text x="350" y="635" fill="#fca5a5" font-size="24" font-weight="800">{exhaust_air_temp_c:.1f} °C</text>
            <text x="664" y="635" fill="#fde68a" font-size="24" font-weight="800">{recovery_efficiency*100:.0f}%</text>
            <text x="905" y="635" fill="#f9fafb" font-size="24" font-weight="800">{delivered_temp:.1f} °C</text>
          </svg>
        </div>

        <div style="background:#081220; border:1px solid #17304d; border-radius:18px; padding:16px;">
          <div style="font-size:18px; font-weight:800; margin-bottom:10px;">How to interpret this panel</div>
          <div style="font-size:14px; line-height:1.65; color:#cbd5e1;">
            <b>Blue stream:</b> outside fresh air entering the protected system.<br>
            <b>Red stream:</b> warmer indoor exhaust donating thermal energy across the exchanger core.<br>
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
