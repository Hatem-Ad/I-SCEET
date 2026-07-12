import base64
import html
import os
import sys
import textwrap
import streamlit as st

# I-SCEET visual system — Homepage V8 aligned to approved mockup
NAVY_950 = "#06111D"
NAVY_900 = "#0A1725"
NAVY_800 = "#11263B"
PAPER = "#F6F8FB"
SURFACE = "#FFFFFF"
LINE = "#DCE4EC"
TEXT_900 = "#111827"
TEXT_700 = "#435267"
TEXT_500 = "#77869A"
RED = "#EF3340"
SUCCESS = "#3FAE67"
BLUE = "#4389E8"
AMBER = "#E8A02B"
PENDING = "#A8B4C4"

MODULES = ["M1", "M2", "M3", "M4", "M5", "M6"]
MODULE_LABELS = {
    "M1": "HLR Generation",
    "M2": "LLR Generation",
    "M3": "Code Generation",
    "M4": "LLT Generation",
    "M5": "HLT Generation",
    "M6": "Traceability",
}


def _asset_data_uri(filename: str, mime: str = "image/jpeg") -> str:
    path = os.path.join(os.path.dirname(__file__), "assets", filename)
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        payload = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{payload}"


def _current_page_key() -> str:
    main_mod = sys.modules.get("__main__")
    current = os.path.basename(getattr(main_mod, "__file__", "app.py"))
    mapping = {
        "app.py": "home",
        "1_upload.py": "upload",
        "2_pipeline.py": "pipeline",
        "3_revue.py": "review",
        "4_chat_tc.py": "consultation",
        "5_tc_excel.py": "comments",
        "6_historique.py": "history",
    }
    return mapping.get(current, "home")


def _svg(name: str) -> str:
    icons = {
        "home": """<svg viewBox='0 0 24 24'><path d='M3 11.5 12 4l9 7.5'/><path d='M5 10.5V20h14v-9.5'/><path d='M9 20v-6h6v6'/></svg>""",
        "file": """<svg viewBox='0 0 24 24'><path d='M6 3h8l4 4v14H6z'/><path d='M14 3v5h5'/><path d='M9 12h6M9 16h6'/></svg>""",
        "gear": """<svg viewBox='0 0 24 24'><circle cx='12' cy='12' r='3'/><path d='M19 13.5v-3l-2.2-.7a7 7 0 0 0-.6-1.4l1.1-2-2.1-2.1-2 1.1a7 7 0 0 0-1.4-.6L11.5 2h-3l-.7 2.2a7 7 0 0 0-1.4.6l-2-1.1-2.1 2.1 1.1 2a7 7 0 0 0-.6 1.4L.6 10v3l2.2.7a7 7 0 0 0 .6 1.4l-1.1 2 2.1 2.1 2-1.1a7 7 0 0 0 1.4.6l.7 2.2h3l.7-2.2a7 7 0 0 0 1.4-.6l2 1.1 2.1-2.1-1.1-2a7 7 0 0 0 .6-1.4z'/></svg>""",
        "check": """<svg viewBox='0 0 24 24'><circle cx='12' cy='12' r='9'/><path d='m8 12 2.6 2.6L16.5 9'/></svg>""",
        "chat": """<svg viewBox='0 0 24 24'><path d='M4 5h16v11H9l-5 4z'/><path d='M8 10h.01M12 10h.01M16 10h.01'/></svg>""",
        "pencil": """<svg viewBox='0 0 24 24'><path d='m4 20 4.5-1 10-10-3.5-3.5-10 10z'/><path d='m13.8 6.7 3.5 3.5'/></svg>""",
        "grid": """<svg viewBox='0 0 24 24'><rect x='4' y='4' width='16' height='16' rx='2'/><path d='M8 8h2v2H8zM14 8h2v2h-2zM8 14h2v2H8zM14 14h2v2h-2z'/></svg>""",
        "layers": """<svg viewBox='0 0 24 24'><path d='m12 3 9 5-9 5-9-5z'/><path d='m3 12 9 5 9-5M3 16l9 5 9-5'/></svg>""",
        "trend": """<svg viewBox='0 0 24 24'><path d='M4 17 10 11l4 4 6-8'/><path d='M15 7h5v5'/></svg>""",
        "shield": """<svg viewBox='0 0 24 24'><path d='M12 3 20 6v6c0 5-3.2 8-8 9-4.8-1-8-4-8-9V6z'/><path d='m8.5 12 2.2 2.2 4.8-5'/></svg>""",
        "comment": """<svg viewBox='0 0 24 24'><rect x='4' y='5' width='16' height='12' rx='2'/><path d='m8 17-3 3v-3'/></svg>""",
        "folder": """<svg viewBox='0 0 24 24'><path d='M3 7h7l2 2h9v10H3z'/></svg>""",
        "rocket": """<svg viewBox='0 0 24 24'><path d='M14 4c3-1 5-1 6 0 1 1 1 3 0 6l-6 6-6-6z'/><path d='m8 10-3 1-2 4 5-1M14 16l-1 5 4-2 1-3'/><circle cx='15.5' cy='8.5' r='1.5'/></svg>""",
        "document_check": """<svg viewBox='0 0 24 24'><path d='M6 3h8l4 4v14H6z'/><path d='M14 3v5h5'/><path d='m9 15 2 2 4-4'/></svg>""",
        "plane": """<svg viewBox='0 0 24 24'><path d='m2 13 8-2 4-7 2 .5-2 6 6-1 2 1-8 4-2 6-2 .5v-5l-5 1z'/></svg>""",
    }
    return icons[name]


def _sidebar_brand():
    active = st.session_state.get("active_project")

    logo_uri = _asset_data_uri("isceet_logo.png", "image/png")
    logo_html = (
        f"<img class='isc-brand-logo' src='{logo_uri}' "
        "alt='I-SCEET — Intelligent Safety-Critical Engineering Environment Toolchain'>"
        if logo_uri
        else "<div class='isc-brand-name'>I-SCEET</div>"
    )

    project_html = ""
    if active:
        project_name = html.escape(str(active.get("name", "—")))
        dal_level = html.escape(str(active.get("dal_level", "—")))
        project_html = (
            "<div class='isc-side-project'>"
            "<div class='k'>Active project</div>"
            f"<div class='v'>{project_name}</div>"
            f"<div class='meta'>DAL {dal_level} · controlled workspace</div>"
            "</div>"
        )

    st.sidebar.markdown(
        f"<div class='isc-brand-block'>{logo_html}{project_html}</div>",
        unsafe_allow_html=True,
    )


def _sidebar_nav():
    active = _current_page_key()
    items = [
        ("home", "./", "home", "", "Accueil"),
        ("upload", "./upload", "file", "01", "Inputs & projet"),
        ("pipeline", "./pipeline", "gear", "02", "Pipeline M1 → M6"),
        ("review", "./revue", "check", "03", "Revue & baseline"),
        ("consultation", "./chat_tc", "chat", "04", "Consultation"),
        ("comments", "./tc_excel", "pencil", "05", "Technical comments"),
        ("history", "./historique", "grid", "06", "Historique"),
    ]

    nav_html = ["<div class='isc-side-section'>Navigation</div>"]
    for idx, (key, href, icon, num, label) in enumerate(items):
        if idx == 1:
            nav_html.append("<div class='isc-side-section isc-workspace-heading'>Workspaces</div>")
        cls = "isc-side-link active" if key == active else "isc-side-link"
        number = f"<span class='isc-nav-num'>{num}</span>" if num else ""
        nav_html.append(
            f"<a class='{cls}' href='{href}' target='_self'><span class='isc-nav-icon'>{_svg(icon)}</span>{number}<span class='isc-nav-label'>{label}</span></a>"
        )

    nav_html.append(
        """
        <div class='isc-side-section isc-status-heading'>Platform status</div>
        <div class='isc-status-card'>
          <div class='isc-status-row'><span class='isc-status-dot'></span><strong>System operational</strong></div>
          <div class='isc-status-sub'>All services are running normally.</div>
        </div>
        <div class='isc-side-footer'>
          <div class='aircraft-disc'>""" + _svg("plane") + """</div>
          <div><strong>I-SCEET v2.1.0</strong><br><span>© 2026 · Engineering assurance platform</span></div>
        </div>
        """
    )
    st.sidebar.markdown("".join(nav_html), unsafe_allow_html=True)



def _refresh_active_project_from_session():
    """Refresh an already selected project without auto-selecting one.

    A fresh Streamlit browser session must start with no active project. A
    project becomes active only when the user explicitly activates it from
    Workspace 06 (Historique). Once selected, Streamlit session state keeps it
    available while navigating between pages in the same session.
    """
    active = st.session_state.get("active_project")
    if not active or active.get("id") is None:
        return None
    try:
        from Backend.db import get_project
        fresh = get_project(active["id"])
        if fresh:
            st.session_state["active_project"] = fresh
            return fresh
        st.session_state.pop("active_project", None)
    except Exception:
        return active
    return None


def inject_theme():
    _refresh_active_project_from_session()
    hero_bg = _asset_data_uri("hero_aircraft_runway.png", "image/png") or _asset_data_uri("hero_aircraft_runway.jpg") or _asset_data_uri("home_aircraft_world.jpg")

    st.markdown(
        textwrap.dedent(
            """
            <style>#MainMenu,footer{visibility:hidden}[data-testid='stSidebarNav']{display:none}
            header[data-testid='stHeader']{display:none}[data-testid='stToolbar']{display:none}</style>
            <link rel='preconnect' href='https://fonts.googleapis.com'>
            <link rel='preconnect' href='https://fonts.gstatic.com' crossorigin>
            <link href='https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Manrope:wght@500;600;700;800&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap' rel='stylesheet'>
            """
        ),
        unsafe_allow_html=True,
    )

    st.markdown(
        textwrap.dedent(
            f"""
            <style>
              :root{{--navy-950:{NAVY_950};--navy-900:{NAVY_900};--navy-800:{NAVY_800};--paper:{PAPER};--surface:{SURFACE};--line:{LINE};--text-900:{TEXT_900};--text-700:{TEXT_700};--text-500:{TEXT_500};--red:{RED};--success:{SUCCESS};--blue:{BLUE};--amber:{AMBER};--pending:{PENDING};}}
              html,body,[data-testid='stAppViewContainer']{{font-family:'IBM Plex Sans',sans-serif}}
              h1,h2,h3,h4,h5{{font-family:'Space Grotesk',sans-serif!important;color:{TEXT_900}!important}}
              .isc-hero-title,.isc-brand-name{{font-family:'Space Grotesk',sans-serif!important}}
              .isc-kicker,.isc-rail-label,.isc-side-section,.isc-metric-label{{font-family:'Manrope',sans-serif!important}}
              code,.isc-tech,.isc-nav-num{{font-family:'IBM Plex Mono',monospace!important}}
              /* Preserve Streamlit / Material icon fonts */
              .material-symbols-rounded,
              .material-symbols-outlined,
              [class*='material-symbols']{{
                font-family:'Material Symbols Rounded','Material Symbols Outlined'!important;
                font-weight:normal!important;
                font-style:normal!important;
                line-height:1!important;
                letter-spacing:normal!important;
                text-transform:none!important;
                white-space:nowrap!important;
                word-wrap:normal!important;
                direction:ltr!important;
                -webkit-font-feature-settings:'liga'!important;
                -webkit-font-smoothing:antialiased!important;
              }}
              /* History / expander cards */
              [data-testid='stExpander']{{
                background:#FFFFFF;
                border:1px solid #DCE4EC;
                border-radius:14px;
                overflow:hidden;
                margin-bottom:.72rem;
                box-shadow:0 6px 18px rgba(15,29,44,.035);
              }}
              [data-testid='stExpander'] summary{{
                min-height:54px;
                padding:.78rem 1rem!important;
                display:flex;
                align-items:center;
              }}
              [data-testid='stExpander'] summary p{{
                margin:0!important;
                font-family:'IBM Plex Sans',sans-serif!important;
                font-size:.92rem!important;
                font-weight:500!important;
                color:#182231!important;
                line-height:1.35!important;
              }}
              [data-testid='stExpander'] details[open] summary{{
                border-bottom:1px solid #E7EDF3;
                background:#FBFCFE;
              }}
              /* History — artefacts and SCI register text */
              [data-testid='stExpander'] [data-testid='stMarkdownContainer'],
              [data-testid='stExpander'] [data-testid='stMarkdownContainer'] p,
              [data-testid='stExpander'] [data-testid='stMarkdownContainer'] strong{{
                color:#182231!important;
                opacity:1!important;
              }}
              [data-testid='stExpander'] [data-testid='stCaptionContainer'],
              [data-testid='stExpander'] [data-testid='stCaptionContainer'] p,
              [data-testid='stExpander'] [data-testid='stCaptionContainer'] span{{
                color:#435267!important;
                opacity:1!important;
              }}
              [data-testid='stExpander'] .isc-eyebrow{{
                color:#182231!important;
                opacity:1!important;
                font-weight:700!important;
              }}
              [data-testid='stAppViewContainer']{{background:radial-gradient(circle at 88% 8%,rgba(110,164,214,.08),transparent 27%),linear-gradient(180deg,#FBFCFE 0%,var(--paper) 100%)}}
              [data-testid='stHeader']{{height:56px;background:rgba(255,255,255,.92);backdrop-filter:blur(16px);border-bottom:1px solid rgba(220,227,234,.80)}}
              .block-container{{max-width:1320px;padding:1rem 1.2rem 3rem!important}}
              /* Remove default Streamlit sidebar header/spacer */
              [data-testid='stSidebarHeader']{{display:none!important;height:0!important;min-height:0!important;padding:0!important;margin:0!important;border:0!important}}
              [data-testid='stLogoSpacer']{{display:none!important;height:0!important;min-height:0!important}}
              [data-testid='stSidebarCollapseButton']{{display:none!important}}
              /* Sidebar dimensions and brand */
              section[data-testid='stSidebar']{{width:318px!important;min-width:318px!important;max-width:318px!important;background:linear-gradient(180deg,#06111E 0%,#071A2B 100%);border-right:1px solid rgba(255,255,255,.07)}}
              [data-testid='stSidebarContent']{{width:318px!important;padding-top:0!important;margin-top:0!important}}
              section[data-testid='stSidebar'] .block-container{{padding-top:0!important;margin-top:0!important}}
              section[data-testid='stSidebar'] [data-testid='stVerticalBlock']{{gap:0!important}}
              .isc-brand-block{{padding:.75rem .9rem .3rem;margin-top:0}}
              .isc-brand-logo{{display:block;width:100%;max-width:238px;height:auto;object-fit:contain;object-position:left top;filter:drop-shadow(0 10px 18px rgba(0,0,0,.14))}}
              .isc-brand-name{{color:#fff;font-size:1.55rem;font-weight:700;line-height:1;letter-spacing:-.035em}}
              .isc-side-project{{margin-top:.9rem;padding-top:.8rem;border-top:1px solid rgba(255,255,255,.08)}}
              .isc-side-project .k{{color:#718296;text-transform:uppercase;letter-spacing:.14em;font-size:.62rem;font-weight:700}}
              .isc-side-project .v{{color:#fff;font-size:.84rem;font-weight:600;margin-top:.28rem}}
              .isc-side-project .meta{{color:#73869A;font-size:.69rem;margin-top:.15rem}}
              /* Sidebar navigation */
              .isc-side-section{{color:#7E8CA0;text-transform:uppercase;letter-spacing:.16em;font-size:.68rem;font-weight:800;margin:1rem 1rem .5rem}}
              .isc-workspace-heading{{margin-top:1.25rem}}
              .isc-side-link{{position:relative;display:grid;grid-template-columns:28px 30px 1fr;align-items:center;gap:.55rem;margin:.38rem 1rem;padding:.86rem .95rem;border-radius:14px;text-decoration:none!important;color:#E3EBF4;background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.05);transition:.15s ease}}
              .isc-side-link:first-of-type{{grid-template-columns:28px 1fr}}
              .isc-side-link:hover{{background:rgba(255,255,255,.075);border-color:rgba(255,255,255,.09)}}
              .isc-side-link.active{{background:linear-gradient(90deg,rgba(255,255,255,.08),rgba(255,255,255,.045));border-color:rgba(255,255,255,.08)}}
              .isc-side-link.active::before{{content:'';position:absolute;left:-1px;top:0;bottom:0;width:3px;background:var(--red);border-radius:3px 0 0 3px}}
              .isc-nav-icon{{width:24px;height:24px;display:grid;place-items:center;color:#A8B9CA}}
              .isc-nav-icon svg{{width:22px;height:22px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}}
              .isc-nav-num{{color:var(--red);font-size:.88rem;font-weight:600}}
              .isc-nav-label{{font-size:.96rem;font-weight:500;color:#E8EEF5;white-space:nowrap}}
              .isc-side-link.active .isc-nav-label{{font-weight:600;color:#fff}}
              .isc-status-heading{{margin-top:2rem}}
              .isc-status-card{{margin:.35rem 1rem 0;padding:1rem 1.05rem;background:rgba(255,255,255,.045);border:1px solid rgba(255,255,255,.07);border-radius:14px}}
              .isc-status-row{{display:flex;align-items:center;gap:.55rem;color:#DDE8F2;font-size:.85rem}}
              .isc-status-dot{{width:8px;height:8px;background:#53C86B;border-radius:50%;box-shadow:0 0 0 4px rgba(83,200,107,.08)}}
              .isc-status-sub{{color:#73869A;font-size:.68rem;margin:.42rem 0 0 1.05rem}}
              .isc-side-footer{{display:flex;align-items:center;gap:.8rem;margin:2rem 1rem 1rem;color:#7E8FA4;font-size:.68rem}}
              .isc-side-footer strong{{color:#AAB8C8;font-size:.72rem}}
              .aircraft-disc{{width:42px;height:42px;border-radius:50%;background:rgba(255,255,255,.055);display:grid;place-items:center;color:#E8EEF5}}
              .aircraft-disc svg{{width:23px;height:23px;fill:none;stroke:currentColor;stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round}}
              /* Topbar */
              .isc-topbar{{display:flex;align-items:center;justify-content:space-between;margin:.15rem 0 .82rem;padding:0 .15rem;color:#5C6C82}}
              .isc-topbar-left,.isc-topbar-right{{display:flex;align-items:center;gap:.85rem}}
              .isc-burger{{font-size:1.65rem;line-height:1;color:#55657A;font-weight:600}}
              .isc-topbar-plane{{font-size:1rem;color:#6A7C93}}
              .isc-topbar-text{{font-family:'IBM Plex Sans',sans-serif;font-size:1rem;font-weight:500;color:#4E5F75}}
              .isc-topbar-more{{font-size:1.28rem;line-height:1;color:#4E5F75}}
              /* Hero */
              .isc-hero{{position:relative;overflow:hidden;min-height:372px;border-radius:28px;padding:3rem 3rem 2.7rem;margin:0 0 1.35rem;background:#091827;box-shadow:0 22px 52px rgba(17,34,52,.10);border:1px solid rgba(15,34,53,.08)}}
              .isc-hero::before{{content:'';position:absolute;inset:0;z-index:0;background-image:linear-gradient(90deg,rgba(5,17,30,.965) 0%,rgba(5,17,30,.88) 34%,rgba(5,17,30,.54) 55%,rgba(5,17,30,.18) 78%,rgba(5,17,30,.06) 100%),url('{hero_bg}');background-repeat:no-repeat,no-repeat;background-position:center center,68% 56%;background-size:100% 100%,cover;filter:saturate(.92) contrast(1.01)}}
              .isc-hero::after{{content:'';position:absolute;right:-7%;bottom:-23%;width:38%;height:38%;background:linear-gradient(135deg,#EF3A44,#B81D29);clip-path:polygon(100% 0,0 100%,100% 100%);opacity:.98;z-index:0}}
              .isc-hero-content{{position:relative;z-index:1;max-width:655px}}
              .isc-kicker{{color:#F4454D;text-transform:uppercase;font-size:.75rem;letter-spacing:.25em;font-weight:800;margin-bottom:1rem}}
              .isc-hero-title{{font-size:2.92rem;font-weight:700;line-height:1.02;letter-spacing:-.046em;color:#fff;max-width:635px;margin:0}}
              .isc-hero-title .dot{{color:var(--red)}}
              .isc-hero-rule{{width:42px;height:2px;background:rgba(255,255,255,.34);margin:1.6rem 0 1.18rem}}
              .isc-hero-tag{{color:rgba(235,242,248,.84);font-size:1rem;line-height:1.63;max-width:640px}}
              .isc-product-name{{color:rgba(220,230,240,.56);font-family:'Manrope',sans-serif;font-size:.72rem;font-weight:600;margin-top:1.15rem;letter-spacing:.01em}}
              .isc-dal-badge{{min-width:110px;background:rgba(9,19,31,.48);border:1px solid rgba(255,255,255,.15);border-radius:18px;padding:.8rem .95rem;backdrop-filter:blur(15px)}}
              .isc-dal-badge .lbl{{color:#91A4B9;text-transform:uppercase;letter-spacing:.15em;font-size:.63rem}}
              .isc-dal-badge .val{{font-family:'Space Grotesk',sans-serif;font-size:1.35rem;font-weight:700;color:#fff;margin-top:.15rem}}
              /* Pipeline */
              .isc-rail-wrap{{background:rgba(255,255,255,.97);border:1px solid var(--line);border-radius:24px;padding:1.25rem 1.35rem 1.35rem;box-shadow:0 12px 30px rgba(15,29,44,.05);margin:.55rem 0 1.3rem}}
              .isc-rail-label{{color:#6D7A8D;font-size:.72rem;text-transform:uppercase;letter-spacing:.17em;font-weight:800;margin-bottom:.9rem}}
              .isc-rail{{display:flex;gap:12px;align-items:stretch}}
              .isc-rail .seg{{flex:1;position:relative;border-radius:16px;background:linear-gradient(180deg,#FCFDFE,#F7F9FC);border:1px solid #DCE4ED;padding:.9rem .45rem .8rem;text-align:center;min-height:96px}}
              .isc-rail .seg:not(:last-child)::after{{content:'';position:absolute;top:50%;right:-13px;width:13px;border-top:1px dashed #CBD5E1}}
              .isc-rail .bar{{width:100%;height:5px;border-radius:999px;margin-bottom:.62rem}}
              .isc-rail .lbl{{font-family:'Space Grotesk',sans-serif;font-size:1rem;font-weight:500;color:#70819A}}
              .isc-rail .desc{{color:#536479;font-size:.72rem;margin-top:.32rem}}
              /* Metrics */
              .isc-metric-card{{min-height:144px;background:rgba(255,255,255,.98);border:1px solid var(--line);border-radius:20px;padding:1.12rem 1.18rem;box-shadow:0 12px 28px rgba(15,29,44,.045);display:flex;gap:.95rem;align-items:flex-start}}
              .isc-metric-icon{{width:48px;height:48px;border-radius:15px;display:grid;place-items:center;flex:0 0 48px}}
              .isc-metric-icon svg{{width:27px;height:27px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}}
              .isc-metric-icon.red{{background:#FFF0F1;color:#E4343A}}.isc-metric-icon.blue{{background:#EEF4FF;color:#4A83E5}}.isc-metric-icon.green{{background:#EDF8F0;color:#45A468}}.isc-metric-icon.amber{{background:#FFF7E9;color:#E09A27}}
              .isc-metric-label{{color:#718198;text-transform:uppercase;letter-spacing:.13em;font-size:.63rem;font-weight:800}}
              .isc-metric-value{{font-family:'Space Grotesk',sans-serif;color:#101827;font-size:1.82rem;font-weight:700;line-height:1.05;margin-top:.38rem}}
              .isc-metric-sub{{color:#8290A2;font-size:.76rem;margin-top:.5rem}}
              /* Native Streamlit metrics — History page */
              [data-testid='stMetric']{{
                background:#FFFFFF!important;
                color:#111827!important;
              }}
              [data-testid='stMetricLabel'],
              [data-testid='stMetricLabel'] p,
              [data-testid='stMetricLabel'] div,
              [data-testid='stMetricLabel'] span{{
                color:#435267!important;
                opacity:1!important;
              }}
              [data-testid='stMetricValue'],
              [data-testid='stMetricValue'] div,
              [data-testid='stMetricValue'] span{{
                color:#111827!important;
                opacity:1!important;
              }}
              [data-testid='stMetricDelta'],
              [data-testid='stMetricDelta'] div{{
                color:#435267!important;
              }}
              /* Primary actions */
              .isc-section-title{{color:#61718A;text-transform:uppercase;letter-spacing:.16em;font-family:'Manrope',sans-serif;font-size:.7rem;font-weight:800;margin:.25rem 0 .72rem}}
              .isc-action-card{{display:flex;align-items:center;gap:1rem;min-height:116px;background:#fff;border:1px solid var(--line);border-radius:20px;padding:1.05rem 1.15rem;text-decoration:none!important;box-shadow:0 12px 28px rgba(15,29,44,.045);transition:.16s ease;color:inherit}}
              .isc-action-card:hover{{transform:translateY(-2px);border-color:#C7D2DE;box-shadow:0 16px 34px rgba(15,29,44,.075)}}
              .isc-action-icon{{width:54px;height:54px;border-radius:16px;display:grid;place-items:center;flex:0 0 54px}}
              .isc-action-icon svg{{width:30px;height:30px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}}
              .isc-action-icon.red{{background:#FFF0F1;color:#E4343A}}.isc-action-icon.blue{{background:#EEF4FF;color:#4A83E5}}.isc-action-icon.green{{background:#EDF8F0;color:#45A468}}.isc-action-icon.amber{{background:#FFF7E9;color:#E09A27}}
              .isc-action-copy{{min-width:0;flex:1}}
              .isc-action-title{{font-family:'Space Grotesk',sans-serif;color:#182231;font-size:1rem;font-weight:600;margin:.05rem 0 .28rem}}
              .isc-action-desc{{color:#758297;font-size:.76rem;line-height:1.45}}
              .isc-action-arrow{{color:#607086;font-size:1.55rem;margin-left:auto}}
              /* Native Streamlit controls — keep the light aviation theme coherent */
              [data-testid='stTextInput'] input,
              [data-testid='stTextArea'] textarea,
              [data-testid='stNumberInput'] input,
              [data-testid='stDateInput'] input,
              [data-baseweb='select'] > div{{
                background:#FFFFFF!important;
                color:{TEXT_900}!important;
                border-color:#DCE4EC!important;
                border-radius:12px!important;
                box-shadow:none!important;
              }}
              [data-testid='stTextInput'] input::placeholder,
              [data-testid='stTextArea'] textarea::placeholder{{color:#96A3B3!important;opacity:1!important}}
              [data-testid='stFileUploader'] section,
              [data-testid='stFileUploaderDropzone']{{
                background:#FFFFFF!important;
                border:1px dashed #BFD0E2!important;
                border-radius:16px!important;
                color:{TEXT_700}!important;
              }}
              [data-testid='stFileUploader'] button{{
                background:#F2F6FA!important;
                color:{TEXT_900}!important;
                border:1px solid #D7E1EB!important;
                box-shadow:none!important;
              }}
              [data-testid='stFileUploaderFile']{{
                background:#F7F9FC!important;
                color:{TEXT_900}!important;
                border:1px solid #DCE4EC!important;
                border-radius:12px!important;
              }}
              [data-testid='stFileUploaderFile'] p,
              [data-testid='stFileUploaderFile'] small{{color:{TEXT_700}!important}}
              [data-testid='stFileUploader'] svg{{color:#52657B!important;fill:none!important}}
              [data-testid='stFileUploader'] [data-testid='stBaseButton-secondary']{{
                background:#F2F6FA!important;
                color:{TEXT_900}!important;
              }}
              [data-baseweb='popover'],
              [role='listbox']{{background:#FFFFFF!important;color:{TEXT_900}!important}}
              [role='option']{{background:#FFFFFF!important;color:{TEXT_900}!important}}
              [role='option']:hover{{background:#F2F6FA!important}}

              /* Warning / information messages — readable dark text */
              [data-testid='stAlert'],
              [data-testid='stAlert'] p,
              [data-testid='stAlert'] div,
              [data-testid='stAlert'] span,
              [data-testid='stAlert'] strong{{
                color:#111827!important;
                opacity:1!important;
              }}
              [data-testid='stAlert'] ::selection{{
                background:#D6E4FF!important;
                color:#111827!important;
              }}

              /* Other components kept compatible */
              .isc-surface{{background:#fff;border:1px solid var(--line);border-radius:20px;padding:1.1rem 1.2rem;box-shadow:0 10px 26px rgba(15,29,44,.04)}}
              .isc-page-header{{margin-top:.75rem!important;margin-bottom:1rem!important}}
              /* Red buttons — white text and icons */
              .stButton>button,
              .stDownloadButton>button,
              [data-testid='stButton'] button,
              [data-testid='stDownloadButton'] button{{
                background:linear-gradient(180deg,var(--red),#BE212A)!important;
                color:#FFFFFF!important;
                border:none!important;
                border-radius:13px!important;
                font-weight:700!important;
              }}
              .stButton>button p,
              .stButton>button span,
              .stButton>button div,
              .stDownloadButton>button p,
              .stDownloadButton>button span,
              .stDownloadButton>button div,
              [data-testid='stButton'] button *,
              [data-testid='stDownloadButton'] button *{{
                color:#FFFFFF!important;
              }}
              .stButton>button svg,
              .stDownloadButton>button svg,
              [data-testid='stButton'] button svg,
              [data-testid='stDownloadButton'] button svg{{
                color:#FFFFFF!important;
                stroke:#FFFFFF!important;
              }}


              /* Final button override — History expanders and native Streamlit buttons */
              [data-testid='stButton'] button:not(:disabled),
              [data-testid='stDownloadButton'] button:not(:disabled),
              [data-testid='stExpander'] [data-testid='stButton'] button:not(:disabled),
              [data-testid='stExpander'] [data-testid='stDownloadButton'] button:not(:disabled) {{
                background:linear-gradient(180deg,#EF3340 0%,#C9212B 100%)!important;
                border:1px solid #C9212B!important;
                color:#FFFFFF!important;
                opacity:1!important;
              }}

              [data-testid='stButton'] button [data-testid='stMarkdownContainer'],
              [data-testid='stButton'] button [data-testid='stMarkdownContainer'] p,
              [data-testid='stButton'] button [data-testid='stMarkdownContainer'] span,
              [data-testid='stDownloadButton'] button [data-testid='stMarkdownContainer'],
              [data-testid='stDownloadButton'] button [data-testid='stMarkdownContainer'] p,
              [data-testid='stDownloadButton'] button [data-testid='stMarkdownContainer'] span,
              [data-testid='stExpander'] [data-testid='stButton'] button [data-testid='stMarkdownContainer'],
              [data-testid='stExpander'] [data-testid='stButton'] button [data-testid='stMarkdownContainer'] p,
              [data-testid='stExpander'] [data-testid='stButton'] button [data-testid='stMarkdownContainer'] span,
              [data-testid='stExpander'] [data-testid='stDownloadButton'] button [data-testid='stMarkdownContainer'],
              [data-testid='stExpander'] [data-testid='stDownloadButton'] button [data-testid='stMarkdownContainer'] p,
              [data-testid='stExpander'] [data-testid='stDownloadButton'] button [data-testid='stMarkdownContainer'] span {{
                color:#FFFFFF!important;
                -webkit-text-fill-color:#FFFFFF!important;
                opacity:1!important;
              }}

              /* Disabled button: visible but clearly inactive */
              [data-testid='stButton'] button:disabled,
              [data-testid='stExpander'] [data-testid='stButton'] button:disabled {{
                background:#94A3B8!important;
                border-color:#94A3B8!important;
                color:#FFFFFF!important;
                opacity:.78!important;
              }}

              [data-testid='stButton'] button:disabled [data-testid='stMarkdownContainer'],
              [data-testid='stButton'] button:disabled [data-testid='stMarkdownContainer'] p,
              [data-testid='stExpander'] [data-testid='stButton'] button:disabled [data-testid='stMarkdownContainer'],
              [data-testid='stExpander'] [data-testid='stButton'] button:disabled [data-testid='stMarkdownContainer'] p {{
                color:#FFFFFF!important;
                -webkit-text-fill-color:#FFFFFF!important;
              }}

              /* SCI Register — native dataframe white theme */
              [data-testid='stDataFrame']{{
                background:#FFFFFF!important;
                border:1px solid #DCE4EC!important;
                border-radius:12px!important;
                overflow:hidden!important;
                color:#111827!important;
              }}
              [data-testid='stDataFrame'] > div,
              [data-testid='stDataFrame'] div[role='grid'],
              [data-testid='stDataFrame'] div[role='row'],
              [data-testid='stDataFrame'] div[role='gridcell']{{
                background-color:#FFFFFF!important;
                color:#111827!important;
              }}
              [data-testid='stDataFrame'] div[role='columnheader']{{
                background-color:#F3F6F9!important;
                color:#182231!important;
                font-weight:600!important;
              }}
              [data-testid='stDataFrame'] div[role='gridcell']{{
                border-color:#DCE4EC!important;
              }}

              /* SCI Register — custom HTML table fallback */
              .isc-sci-table-wrap{{
                width:100%!important;
                max-height:360px;
                overflow:auto;
                background:#FFFFFF!important;
                border:1px solid #DCE4EC!important;
                border-radius:12px!important;
                box-shadow:0 8px 20px rgba(15,29,44,.035)!important;
              }}
              .isc-sci-table{{
                width:100%!important;
                border-collapse:collapse!important;
                background:#FFFFFF!important;
                color:#111827!important;
                font-size:.82rem!important;
              }}
              .isc-sci-table thead th{{
                position:sticky;
                top:0;
                z-index:1;
                background:#F3F6F9!important;
                color:#182231!important;
                text-align:left!important;
                font-weight:700!important;
                padding:.72rem .78rem!important;
                border-bottom:1px solid #DCE4EC!important;
                white-space:nowrap!important;
              }}
              .isc-sci-table tbody td{{
                background:#FFFFFF!important;
                color:#111827!important;
                padding:.7rem .78rem!important;
                border-bottom:1px solid #E8EDF3!important;
                vertical-align:top!important;
              }}
              .isc-sci-table tbody tr:last-child td{{border-bottom:none!important}}
              .isc-sci-table tbody tr:hover td{{background:#F8FAFC!important}}

              .stPageLink a{{border-radius:14px!important}}
              @media(max-width:1050px){{section[data-testid='stSidebar']{{width:280px!important;min-width:280px!important;max-width:280px!important}}[data-testid='stSidebarContent']{{width:280px!important}}.block-container{{max-width:100%!important}}.isc-topbar{{margin-bottom:.55rem}}.isc-hero{{min-height:340px;padding:2.4rem 2.2rem}}.isc-hero-title{{font-size:2.25rem}}}}
              @media(max-width:800px){{.isc-rail{{flex-wrap:wrap}}.isc-rail .seg{{min-width:30%}}.isc-side-link{{grid-template-columns:26px 28px 1fr}}}}
            </style>
            """
        ),
        unsafe_allow_html=True,
    )
    _sidebar_brand()
    _sidebar_nav()
def page_header(eyebrow: str, title: str, subtitle: str | None = None):
    if subtitle is None:
        subtitle = "Controlled generation, review and certification traceability."
    st.markdown(
f"""
        <div class='isc-surface isc-page-header'>
          <div class='isc-kicker'>{eyebrow}</div>
          <div style="font-family:'Space Grotesk',sans-serif;font-size:1.9rem;font-weight:700;color:{TEXT_900}">{title}</div>
          <div style="color:{TEXT_500};font-size:.9rem;line-height:1.55;margin-top:.45rem">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def module_rail(done: set, current: str = None, label: str = "Pipeline status", light: bool = False):
    segs = ""
    for module in MODULES:
        color = RED if module == current else SUCCESS if module in done else LINE
        segs += (
            f"<div class='seg'><div class='bar' style='background:{color}'></div>"
            f"<div class='lbl'>{module}</div><div class='desc'>{MODULE_LABELS[module]}</div></div>"
        )
    st.markdown(
        f"<div class='isc-rail-wrap'><div class='isc-rail-label'>{label}</div><div class='isc-rail'>{segs}</div></div>",
        unsafe_allow_html=True,
    )


def metric_card(icon: str, icon_kind: str, label: str, value: str, subtitle: str):
    icon_map = {
        "projects": _svg("layers"),
        "pipeline": _svg("trend"),
        "reviews": _svg("shield"),
        "comments": _svg("comment"),
    }
    st.markdown(
        f"""
        <div class='isc-metric-card'>
          <div class='isc-metric-icon {icon_kind}'>{icon_map.get(icon, icon)}</div>
          <div><div class='isc-metric-label'>{label}</div><div class='isc-metric-value'>{value}</div><div class='isc-metric-sub'>{subtitle}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
def action_card(icon: str, icon_kind: str, title: str, desc: str, href: str):
    icon_map = {
        "folder": _svg("folder"),
        "rocket": _svg("rocket"),
        "review": _svg("document_check"),
        "consultation": _svg("chat"),
        "comments": _svg("pencil"),
        "history": _svg("grid"),
    }
    st.markdown(
f"""
        <a class='isc-action-card' href='{href}' target='_self'>
          <div class='isc-action-icon {icon_kind}'>{icon_map.get(icon, icon)}</div>
          <div class='isc-action-copy'><div class='isc-action-title'>{title}</div><div class='isc-action-desc'>{desc}</div></div>
          <div class='isc-action-arrow'>›</div>
        </a>
        """,
        unsafe_allow_html=True,
    )


def badge(text: str, kind: str = "neutral") -> str:
    colors = {
        "success": ("#2C8A5A", "rgba(44,138,90,.08)"),
        "warning": ("#B9811E", "rgba(185,129,30,.09)"),
        "danger": (RED, "rgba(228,52,58,.08)"),
        "neutral": (PENDING, "rgba(154,168,186,.10)"),
    }
    fg, bg = colors.get(kind, colors["neutral"])
    return f"<span style='display:inline-flex;padding:.32rem .68rem;border-radius:999px;border:1px solid {fg}33;background:{bg};color:{fg};font-size:.72rem;font-weight:700'>{text}</span>"




def render_sci_table(
    rows: list[dict],
    columns: list[str] | None = None,
    width: str | int = "stretch",
    max_height: int = 360,
) -> None:
    """Render the SCI register as a deterministic white HTML table.

    This avoids Streamlit's canvas-based dataframe renderer, whose dark
    theme cannot always be overridden reliably with CSS.
    """
    if not rows:
        st.info("Aucune entrée dans le SCI Register.")
        return

    if columns is None:
        columns = list(rows[0].keys())

    if width == "stretch":
        width_css = "100%"
    elif isinstance(width, int):
        width_css = f"{width}px"
    else:
        width_css = str(width)

    header_html = "".join(
        f"<th>{html.escape(str(column))}</th>" for column in columns
    )

    body_rows = []
    for row in rows:
        cells = "".join(
            f"<td>{html.escape(str(row.get(column, '—')))}</td>"
            for column in columns
        )
        body_rows.append(f"<tr>{cells}</tr>")

    table_html = (
        f"<div class='isc-sci-table-wrap' "
        f"style='width:{html.escape(width_css)};max-height:{int(max_height)}px'>"
        "<table class='isc-sci-table'>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        "</table></div>"
    )

    st.markdown(table_html, unsafe_allow_html=True)

def nav_card(num: str, title: str, desc: str):
    st.markdown(
        f"""
        <div style='background:#fff;border:1px solid {LINE};border-radius:20px;padding:1.1rem 1.2rem;min-height:170px'>
          <div style="color:{RED};font-family:'IBM Plex Mono',monospace;font-size:.72rem;font-weight:600">{num}</div>
          <div style="font-family:'Space Grotesk',sans-serif;font-size:1rem;font-weight:600;color:{TEXT_900};margin:.9rem 0 .45rem">{title}</div>
          <div style='color:{TEXT_700};font-size:.86rem;line-height:1.55'>{desc}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )