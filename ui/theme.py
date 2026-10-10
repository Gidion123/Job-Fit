"""JobFit v3 visual design for Streamlit: design tokens, Streamlit overrides and small HTML helpers.

Rendering only, no business logic. Every HTML block goes through ``st.html`` (no Markdown processing,
sanitized by the frontend), and every piece of text that comes from a CV, a job posting or the API is
escaped with ``esc`` first, so untrusted text can never add markup, links or remote images.

Widgets are styled through their stable test ids and through keyed containers (``st-key-<key>``):
keys starting with ``jfpanel`` render as a white panel, ``jfrow`` as a job row, ``jfnarrow`` and
``jfmedium`` limit the reading width, and so on (see CSS below).
"""
from __future__ import annotations

import html as _html

import streamlit as st

from texts import t

# Icon paths from the design (24x24, stroke icons).
ICONS = {
    'check': 'M5 12l4 4L19 6', 'arrow': 'M5 12h14m-6-6 6 6-6 6', 'back': 'M19 12H5m6-6-6 6 6 6',
    'upload': 'M12 16V3m-5 5 5-5 5 5M4 15v5h16v-5', 'file': 'M14 2H5v20h14V7l-5-5zm0 0v5h5M8 12h8M8 16h6',
    'shield': 'M12 3 4 6v6c0 5 8 9 8 9s8-4 8-9V6l-8-3zm-4 9 3 3 5-6',
    'search': 'M21 21l-5-5M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0',
    'info': 'M12 10v7m0-10v.1M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0', 'minus': 'M5 12h14',
    'clock': 'M12 8v5l3 2M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0', 'alert': 'm12 3 10 18H2L12 3zm0 6v5m0 3v.1',
    'location': 'M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0zm-5 0a3 3 0 1 1-6 0 3 3 0 0 1 6 0',
    'briefcase': 'M8 6V3h8v3M3 6h18v15H3V6zm0 6h18m-11-2v4h4v-4',
    'layers': 'm12 3 10 5-10 5L2 8l10-5zm-10 9 10 5 10-5M2 16l10 5 10-5',
}


def esc(text) -> str:
    """Untrusted text as inert HTML text (quotes too, so it is safe inside attributes)."""
    return _html.escape(str(text if text is not None else ''), quote=True)


def icon(name: str, cls: str = '') -> str:
    """A design icon. The frontend's HTML sanitizer drops inline <svg>, so the icon is a CSS mask (see icon_css)."""
    return f'<span class="jf-icon jf-i-{name if name in ICONS else "info"} {cls}" aria-hidden="true"></span>'


def icon_css() -> str:
    rules = []
    for name, path in ICONS.items():
        svg = (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' "
               f"stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><path d='{path}'/></svg>")
        data = svg.replace('<', '%3C').replace('>', '%3E').replace('#', '%23').replace('"', "'")
        rules.append(f'.jf-i-{name}{{--jf-i:url("data:image/svg+xml,{data}")}}')
    return '\n'.join(rules)


def html(markup: str) -> None:
    """One HTML block (never Markdown)."""
    st.html(markup)


BADGES = {'MATCH': ('supported', 'check'), 'PARTIAL': ('partial', 'clock'), 'NO_MATCH': ('', 'minus'),
          'UNVERIFIED': ('info', 'info'), 'CONFLICT': ('conflict', 'alert')}


def badge(status: str | None) -> str:
    key = status if status in BADGES else 'UNVERIFIED'
    cls, name = BADGES[key]
    return f'<span class="jf-tag {cls}">{icon(name)}{esc(t("badge." + key))}</span>'


def tag(text: str, cls: str = '', icon_name: str | None = None) -> str:
    return f'<span class="jf-tag {cls}">{icon(icon_name) if icon_name else ""}{text}</span>'


def notice(text_html: str, kind: str = 'info') -> str:
    """``text_html`` is trusted copy (may hold <strong>); escape untrusted parts before passing them."""
    name = {'error': 'alert', 'warn': 'alert', 'success': 'check'}.get(kind, 'info')
    return f'<div class="jf-notice {kind}">{icon(name)}<div class="jf-notice-body">{text_html}</div></div>'


def heading(title: str, desc: str = '', eyebrow: str = '', right: str = '') -> str:
    """Page heading; arguments are trusted copy or already escaped."""
    return ('<div class="jf-page-heading"><div>'
            + (f'<div class="jf-eyebrow">{eyebrow}</div>' if eyebrow else '')
            + f'<div class="jf-h1" role="heading" aria-level="1">{title}</div>'
            + (f'<p class="jf-lead-sm">{desc}</p>' if desc else '')
            + f'</div>{right}</div>')


def feature(key: str, english: str) -> str:
    """The design's bilingual eyebrow: the Indonesian name plus the English product term."""
    if st.session_state.get('lang', 'id') == 'id':
        return f'{esc(t(key))} · <span lang="en">{esc(english)}</span>'
    return esc(t(key))


def sublabel(english: str) -> str:
    """The English product term under an Indonesian heading (Indonesian interface only)."""
    if st.session_state.get('lang', 'id') == 'id':
        return f'<span class="jf-small jf-muted" lang="en">{esc(english)}</span>'
    return ''


def steps(current: int) -> str:
    items = []
    for i, label in enumerate((t('steps.1'), t('steps.2'), t('steps.3'))):
        state = 'active' if i == current else 'done' if i < current else ''
        number = '✓' if i < current else str(i + 1)
        aria = ' aria-current="step"' if i == current else ''
        items.append(f'<li class="{state}"{aria}><span class="jf-step-number">{number}</span>'
                     f'<span>{esc(label)}</span></li>')
    return f'<ol class="jf-steps">{"".join(items)}</ol>'


def section_head(title: str, meta: str = '') -> str:
    return (f'<div class="jf-section-head"><div class="jf-h2" role="heading" aria-level="2">{title}</div>'
            + (f'<span class="jf-small jf-muted">{meta}</span>' if meta else '') + '</div>')


def quota_html(used: int, limit: int = 3) -> str:
    text = t('quota.empty') if used >= limit else t('quota', left=limit - used, limit=limit)
    return f'<span class="jf-quota">{esc(text)}</span>'


def empty_state(title: str, text: str) -> str:
    return (f'<div class="jf-empty">{icon("search")}<div class="jf-h2" role="heading" aria-level="2">{esc(title)}'
            f'</div><p>{esc(text)}</p></div>')


def blockquote(text) -> str:
    return f'<blockquote class="jf-quote">“{esc(text)}”</blockquote>'


def processing(title: str, stages: list[str], elapsed: int | None, extra: str = '') -> str:
    """The waiting screen: the stages this operation goes through (no invented percentage) and real elapsed time."""
    items = ''.join(f'<li><span class="jf-process-dot">{i + 1}</span><span>{esc(s)}</span></li>'
                    for i, s in enumerate(stages))
    time_text = t('proc.elapsed.start') if not elapsed else t('proc.elapsed', n=elapsed)
    return (f'<section class="jf-process" aria-live="polite">{icon("file")}'
            f'<div class="jf-h1" role="heading" aria-level="1">{esc(title)}</div>'
            f'<p class="jf-muted">{esc(t("proc.sub"))}</p>'
            f'<div class="jf-row jf-mt6"><span class="jf-spinner" aria-hidden="true"></span>'
            f'<span role="status">{esc(extra or time_text)}</span></div>'
            f'<ol class="jf-process-list">{items}</ol>'
            f'<p class="jf-small jf-muted">{esc(t("proc.honest"))}{" · " + esc(time_text) if extra else ""}</p>'
            f'</section>')


# ------------------------------------------------------------------------------------------------- CSS --------
CSS = """
:root{--canvas:#F7F8FA;--surface:#FFF;--text:#182230;--text-muted:#526174;--border:#D8DEE8;--input-border:#7D899A;
--primary:#2458A6;--primary-hover:#19427D;--focus:#1D4ED8;--information:#294E7C;--information-bg:#EDF3FC;
--supported:#176448;--supported-bg:#EDF7F1;--partial:#805700;--partial-bg:#FFF7DF;--no-evidence:#526174;
--no-evidence-bg:#EEF1F5;--conflict:#9A3D20;--conflict-bg:#FFF0E9;--destructive:#B42332;--destructive-bg:#FFF0F1;
--radius-sm:4px;--radius:8px;--radius-lg:12px;--control:48px;--shadow:0 12px 40px #1822300d;
--font:'IBM Plex Sans','Segoe UI',system-ui,-apple-system,sans-serif}
@font-face{font-family:'IBM Plex Sans';src:url('app/static/IBMPlexSans.ttf') format('truetype');font-weight:100 700;
font-style:normal;font-display:swap}

/* ---- app shell ---- */
html,body,.stApp,[data-testid="stAppViewContainer"]{background:var(--canvas)!important;color:var(--text);
font-family:var(--font)}
.stApp,.stApp p,.stApp label,.stApp input,.stApp textarea,.stApp button,.stApp select{font-family:var(--font)}
[data-testid="stHeader"],[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],
[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stStatusWidget"]{display:none!important}
[data-testid="stMainBlockContainer"]{max-width:1264px;padding:0 32px 32px!important}
[data-testid="stMain"]{padding-top:0}
.stApp [data-testid="stVerticalBlock"]{gap:16px}

/* ---- typography inside HTML blocks ---- */
.jf-h1{font-size:clamp(28px,3vw,32px);line-height:1.2;font-weight:600;letter-spacing:-.03em;text-wrap:balance;
color:var(--text)}
.jf-h2{font-size:24px;line-height:1.2;font-weight:600;letter-spacing:-.02em;color:var(--text)}
.jf-h3{font-size:20px;line-height:1.25;font-weight:600;color:var(--text)}
.jf-h4{font-size:16px;line-height:1.3;font-weight:600;color:var(--text)}
.jf p{margin:0;max-width:75ch}
.jf{color:var(--text);font-size:16px;line-height:1.6}
.jf-small{font-size:14px}.jf-muted{color:var(--text-muted)}
.jf-eyebrow{font-size:14px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--text-muted)}
.jf-icon{display:inline-block;flex:none;width:20px;height:20px;background-color:currentColor;vertical-align:-4px;
-webkit-mask:var(--jf-i) center/contain no-repeat;mask:var(--jf-i) center/contain no-repeat}
.jf-mt4{margin-top:16px!important}.jf-mt6{margin-top:24px!important}.jf-mb4{margin-bottom:16px!important}
.jf-row{display:flex;align-items:center;gap:12px}
.jf-cluster{display:flex;flex-wrap:wrap;align-items:center;gap:8px}
.jf-page-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:24px;margin:8px 0 16px}
.jf-page-heading .jf-eyebrow{margin-bottom:12px}
.jf-lead-sm{margin-top:12px!important;color:var(--text-muted)}
.jf-section-head{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap}
.jf-quota{font-size:14px;color:var(--text-muted);white-space:nowrap}

/* ---- tags, notices, quotes ---- */
.jf-tag{display:inline-flex;align-items:center;gap:8px;max-width:100%;padding:4px 8px;background:var(--no-evidence-bg);
color:var(--no-evidence);border-radius:var(--radius-sm);font-size:14px;font-weight:500;line-height:1.5;white-space:nowrap}
.jf-tag .jf-icon{width:16px;height:16px;vertical-align:0}
.jf-tag.supported{background:var(--supported-bg);color:var(--supported)}
.jf-tag.partial{background:var(--partial-bg);color:var(--partial)}
.jf-tag.conflict{background:var(--conflict-bg);color:var(--conflict)}
.jf-tag.info{background:var(--information-bg);color:var(--information)}
.jf-notice{display:flex;align-items:flex-start;gap:12px;padding:16px;background:var(--information-bg);
color:var(--information);border-radius:var(--radius);font-size:14px;line-height:1.6}
.jf-notice .jf-icon{margin-top:2px}
.jf-notice.error{background:var(--destructive-bg);color:var(--destructive)}
.jf-notice.warn{background:var(--partial-bg);color:var(--partial)}
.jf-notice.success{background:var(--supported-bg);color:var(--supported)}
.jf-notice ul{margin:8px 0 0;padding-left:20px}
.jf-quote{margin:12px 0 0;padding:16px;background:var(--canvas);border-radius:var(--radius-sm);border:0;
font-size:16px;line-height:1.65;overflow-wrap:anywhere;max-width:75ch;color:var(--text);font-style:normal}
.jf-quote-label{display:block;margin-top:16px;font-size:14px;font-weight:500;color:var(--text-muted)}

/* ---- landing ---- */
.jf-display{font-size:clamp(36px,4.3vw,52px);line-height:1.12;letter-spacing:-.04em;font-weight:600;
margin:16px 0 24px;max-width:16ch;color:var(--text);text-wrap:balance}
.jf-lead{font-size:18px!important;color:var(--text-muted);max-width:46ch!important}
.jf-privacy-line{display:flex;align-items:center;gap:8px;font-size:14px;color:var(--text-muted)}
.jf-evidence-preview{background:#fff;border:1px solid var(--border);border-radius:var(--radius-lg);box-shadow:var(--shadow)}
.jf-preview-top{padding:16px 24px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;gap:12px}
.jf-preview-body{padding:24px}.jf-preview-body .jf-h3{margin:12px 0 16px}
.jf-preview-foot{display:flex;align-items:center;gap:8px;padding:16px 24px;border-top:1px solid var(--border);
color:var(--text-muted);font-size:14px}
.jf-how{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:32px;padding-top:32px;margin-top:16px;
border-top:1px solid var(--border)}
.jf-how .jf-number{display:block;font-size:14px;color:var(--primary);font-weight:600;margin-bottom:12px}
.jf-how .jf-h3{font-size:18px;margin-bottom:8px}.jf-how p{font-size:14px;color:var(--text-muted)}

/* ---- setup steps ---- */
.jf-steps{display:flex;flex-wrap:wrap;gap:24px;margin:8px 0 24px!important;padding:0!important;list-style:none}
.jf-steps li{display:flex;align-items:center;gap:8px;color:var(--text-muted);font-size:14px;margin:0}
.jf-step-number{display:grid;place-items:center;flex:none;width:28px;height:28px;border:1px solid var(--input-border);
border-radius:50%;font-variant-numeric:tabular-nums}
.jf-steps .active{color:var(--primary);font-weight:600}
.jf-steps .active .jf-step-number{color:#fff;background:var(--primary);border-color:var(--primary)}
.jf-steps .done .jf-step-number{color:var(--supported);background:var(--supported-bg);border-color:var(--supported)}

/* ---- upload, preview ---- */
.jf-upload-head{text-align:center;color:var(--primary)}
.jf-upload-head .jf-icon{width:32px;height:32px;margin:0 auto 8px;display:block}
.jf-upload-head .jf-h2{margin-bottom:4px}.jf-upload-head p{margin:0 auto!important;color:var(--text-muted)}
.jf-preview-text{white-space:pre-wrap;overflow-wrap:anywhere;font:16px/1.65 var(--font);max-height:480px;overflow-y:auto;
border:1px solid var(--border);padding:24px;border-radius:var(--radius);background:#fff;margin:0;color:var(--text)}
.jf-field-label{font-weight:500;display:block;margin:8px 0}

/* ---- processing ---- */
.jf-process{max-width:680px;margin:16px auto;padding:48px;background:#fff;border:1px solid var(--border);
border-radius:var(--radius-lg)}
.jf-process>.jf-icon{width:24px;height:24px}
.jf-process .jf-h1{margin:24px 0 16px}
.jf-spinner{display:block;width:32px;height:32px;border:3px solid var(--border);border-top-color:var(--primary);
border-radius:50%;animation:jf-spin 1s linear infinite;flex:none}
.jf-process-list{list-style:none;padding:0!important;margin:32px 0;display:grid;gap:16px}
.jf-process-list li{display:flex;align-items:center;gap:12px;color:var(--text-muted);margin:0}
.jf-process-dot{display:grid;place-items:center;flex:none;width:24px;height:24px;border:1px solid var(--border);
border-radius:50%;font-size:12px}
@keyframes jf-spin{to{transform:rotate(360deg)}}

/* ---- ready ---- */
.jf-ready-summary{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:16px 0;
border-bottom:1px solid var(--border)}
.jf-choice-head p{margin-top:12px!important;color:var(--text-muted)}
.jf-choice-head .jf-h2{margin-top:16px}

/* ---- results ---- */
.jf-job-title{display:flex;align-items:flex-start;justify-content:space-between;gap:16px}
.jf-company{margin-top:4px!important;color:var(--text-muted)}
.jf-job-number{display:block;color:var(--text-muted);font-size:14px;font-variant-numeric:tabular-nums;white-space:nowrap}
.jf-metadata{display:flex;flex-wrap:wrap;gap:8px 16px;margin-top:12px;font-size:14px;color:var(--text-muted)}
.jf-metadata>span{display:flex;align-items:center;gap:4px}
.jf-metadata .jf-icon{width:16px;height:16px;vertical-align:0}
.jf-empty{text-align:center;padding:48px 24px;background:#fff;border:1px solid var(--border);border-radius:var(--radius-lg)}
.jf-empty>.jf-icon{width:32px;height:32px;margin:0 auto 16px;display:block;color:var(--text-muted)}
.jf-empty p{margin:12px auto 0!important;color:var(--text-muted)}

/* ---- analysis ---- */
.jf-coverage{display:grid;grid-template-columns:auto 1fr;gap:32px;align-items:center;padding:32px;background:#fff;
border:1px solid var(--border);border-radius:var(--radius-lg)}
.jf-coverage-value{display:block;font-size:clamp(48px,6vw,72px);font-weight:500;letter-spacing:-.05em;line-height:1;
font-variant-numeric:tabular-nums;white-space:nowrap;color:var(--text)}
.jf-coverage-value span{font-size:32px}
.jf-coverage p{margin-top:8px!important}
.jf-coverage .jf-disclaimer{font-weight:500;color:var(--text)}
.jf-requirements{background:#fff;border:1px solid var(--border);border-radius:var(--radius-lg)}
.jf-requirement{padding:24px;border-bottom:1px solid var(--border)}
.jf-requirement:last-child{border-bottom:0}
.jf-requirement-head{display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px}
.jf-requirement .jf-h3{font-size:18px;margin-bottom:4px;overflow-wrap:anywhere}
.jf-requirement p{margin-top:12px!important;color:var(--text-muted);font-size:14px}
.jf-requirement p.jf-flagged{color:var(--partial);background:var(--partial-bg);padding:8px 12px;border-radius:var(--radius-sm)}
.jf-overview{padding:24px;border:1px solid var(--border);border-radius:var(--radius-lg);background:#fff}
.jf-overview .jf-h4{margin-bottom:12px}
.jf-overview ul{padding-left:20px;margin:0;color:var(--text-muted);font-size:14px}
.jf-overview li{margin:0}.jf-overview li+li{margin-top:8px}
.jf-overview .jf-group+.jf-group{border-top:1px solid var(--border);margin-top:24px;padding-top:24px}
.jf-fact{padding:24px;background:var(--information-bg);border-radius:var(--radius)}
.jf-fact.conflict{background:var(--conflict-bg)}
.jf-fact .jf-h3{font-size:18px;margin:12px 0}
.jf-fact ul{margin:8px 0 0;padding-left:20px}

/* ---- coach ---- */
.jf-coach-item{padding:24px 0 8px;border-top:1px solid var(--border)}
.jf-coach-item .jf-h3{margin-top:12px;font-size:18px;overflow-wrap:anywhere}
.jf-coach-item .jf-description{margin-top:12px!important;color:var(--text-muted)}
.jf-draft{white-space:pre-wrap;padding:24px;border:1px solid var(--border);background:var(--canvas);
border-radius:var(--radius);overflow-wrap:anywhere}

/* ---- market ---- */
.jf-metric-row{display:grid;grid-template-columns:200px 1fr 64px;align-items:center;gap:16px;margin-top:16px}
.jf-bar-track{height:8px;background:var(--no-evidence-bg);border-radius:4px}
.jf-bar{height:8px;background:var(--primary);border-radius:4px}

/* ---- footer ---- */
.st-key-jf_footer{border-top:1px solid var(--border);margin-top:32px;padding-top:16px}
.st-key-jf_footer [data-testid="stBaseButton-tertiary"] p{font-size:14px;text-decoration:underline;text-underline-offset:4px}

/* ---- keyed Streamlit containers ---- */
.st-key-jf_topbar{background:var(--surface);box-shadow:0 0 0 100vmax var(--surface);clip-path:inset(0 -100vmax);
padding:12px 0;border-bottom:1px solid var(--border);margin-bottom:8px}
.st-key-jf_nav{border-bottom:1px solid var(--border);margin-top:-16px;margin-bottom:16px}
[class*="st-key-jfnarrow"]{max-width:800px;width:100%;margin-inline:auto}
[class*="st-key-jfmedium"]{max-width:960px;width:100%;margin-inline:auto}
[class*="st-key-jfpanel"],[class*="st-key-jfrow"],[class*="st-key-jfchoice"],[class*="st-key-jfrefine"],
[class*="st-key-jfmodal_card"],[class*="st-key-jfcoachform"]{background:var(--surface);border:1px solid var(--border);
border-radius:var(--radius-lg);padding:32px}
[class*="st-key-jfrow"]{padding:24px;border-radius:var(--radius-lg)}
[class*="st-key-jfrefine"]{padding:16px;border-radius:var(--radius)}
[class*="st-key-jfcoachform"]{padding:24px;border-radius:var(--radius)}
[class*="st-key-jfchoice_main"]{border-color:var(--primary);background:var(--information-bg)}
[class*="st-key-jfupload"]{background:var(--surface);border:1px dashed var(--input-border);border-radius:var(--radius-lg);
padding:40px 32px}
[class*="st-key-jfmodal_wrap"]{position:fixed!important;inset:0;z-index:999990;background:#18223080;display:flex!important;
flex-direction:column!important;align-items:center!important;justify-content:center!important;padding:16px;
width:100vw!important;height:100vh!important;max-width:none!important;margin:0!important}
[class*="st-key-jfmodal_wrap"]>*{width:100%!important;display:flex!important;justify-content:center!important;
align-items:center!important}
[class*="st-key-jfmodal_card"]{width:min(600px,calc(100vw - 32px))!important;max-height:calc(100vh - 48px);
overflow-y:auto;box-shadow:var(--shadow);flex:none!important}

/* ---- buttons ---- */
.stApp [data-testid^="stBaseButton-"],.stApp [data-testid^="stBaseLinkButton-"],
.stApp [data-testid="stDownloadButton"] button{min-height:var(--control);padding:8px 24px;border-radius:var(--radius);
font-weight:500;font-size:16px;box-shadow:none}
.stApp [data-testid^="stBaseButton-"] p,.stApp [data-testid^="stBaseLinkButton-"] p{font-weight:500;font-size:16px}
.stApp [data-testid="stBaseButton-primary"],.stApp [data-testid="stBaseButton-primaryFormSubmit"],
.stApp [data-testid="stBaseLinkButton-primary"]{background:var(--primary);border:1px solid var(--primary);color:#fff}
.stApp [data-testid="stBaseButton-primary"]:hover,.stApp [data-testid="stBaseButton-primaryFormSubmit"]:hover{
background:var(--primary-hover);border-color:var(--primary-hover);color:#fff}
.stApp [data-testid="stBaseButton-secondary"],.stApp [data-testid="stBaseButton-secondaryFormSubmit"],
.stApp [data-testid="stBaseLinkButton-secondary"],.stApp [data-testid="stDownloadButton"] button{background:var(--surface);
border:1px solid var(--input-border);color:var(--text)}
.stApp [data-testid="stBaseButton-secondary"]:hover,.stApp [data-testid="stBaseLinkButton-secondary"]:hover,
.stApp [data-testid="stDownloadButton"] button:hover{background:var(--information-bg);color:var(--primary-hover);
border-color:var(--input-border)}
.stApp [data-testid="stBaseButton-tertiary"],.stApp [data-testid="stBaseLinkButton-tertiary"]{color:var(--primary);
padding-inline:12px;background:transparent;border:1px solid transparent}
.stApp [data-testid="stBaseButton-tertiary"]:hover{color:var(--primary-hover);background:var(--canvas)}
.stApp button:disabled,.stApp [data-testid^="stBaseButton-"]:disabled{opacity:.55;cursor:not-allowed}
.stApp button:focus-visible,.stApp a:focus-visible,.stApp input:focus-visible,.stApp textarea:focus-visible,
.stApp summary:focus-visible{outline:3px solid var(--focus)!important;outline-offset:3px}
[class*="st-key-jfrow"] [data-testid^="stBaseButton-"],[class*="st-key-jfrow"] [data-testid^="stBaseLinkButton-"],
.st-key-jf_topbar [data-testid^="stBaseButton-"]{min-height:44px;padding:8px 16px}
[class*="st-key-jfdanger"] [data-testid^="stBaseButton-"]{background:var(--destructive);border-color:var(--destructive);
color:#fff}
[class*="st-key-jfdanger"] [data-testid^="stBaseButton-"]:hover{filter:brightness(.9);background:var(--destructive);color:#fff}
/* header */
.st-key-jf_brand [data-testid^="stBaseButton-"]{padding:0;min-height:44px;color:var(--text);background:transparent}
.st-key-jf_brand [data-testid^="stBaseButton-"] p{font-size:24px!important;font-weight:600!important;letter-spacing:-.06em;color:var(--text)}
.st-key-jf_brand [data-testid="stIconMaterial"]{background:var(--text);color:#fff;border-radius:var(--radius);
width:36px;height:36px;display:grid;place-items:center;font-size:24px;margin-right:4px}
.st-key-jf_brandtag{border-left:1px solid var(--border);padding-left:16px;color:var(--text-muted);font-size:14px}
.st-key-jf_topbar [data-testid="stBaseButton-tertiary"]{color:var(--text-muted);font-size:14px}
.st-key-jf_topbar [data-testid="stBaseButton-tertiary"] p{font-size:14px;font-weight:400}
[class*="st-key-jflang_on"] [data-testid^="stBaseButton-"]{color:var(--primary)!important;background:var(--canvas)!important}
[class*="st-key-jflang_on"] [data-testid^="stBaseButton-"] p{font-weight:600!important}
/* product nav */
.st-key-jf_nav [data-testid^="stBaseButton-"]{min-height:56px;border:0;border-bottom:3px solid transparent;border-radius:0;
background:none;color:var(--text-muted);padding:12px 8px}
.st-key-jf_nav [data-testid^="stBaseButton-"]:hover{background:var(--canvas);color:var(--primary-hover)}
.st-key-jf_nav [class*="st-key-jfnav_on"] [data-testid^="stBaseButton-"]{color:var(--primary);
border-bottom-color:var(--primary)}

/* ---- form controls ---- */
.stApp [data-testid="stWidgetLabel"] p,.stApp [data-testid="stWidgetLabel"] label{font-size:16px;font-weight:500;
color:var(--text)}
.stApp [data-testid="stTextInputRootElement"],.stApp [data-testid="stTextAreaRootElement"],
.stApp [data-testid="stSelectbox"] [role="group"]{border-radius:var(--radius)!important;
border-color:var(--input-border)!important;background:#fff!important;color:var(--text)}
.stApp [data-testid="stTextInputRootElement"] input,.stApp [data-testid="stTextAreaRootElement"] textarea,
.stApp [data-testid="stSelectbox"] [role="group"] input{background:#fff!important;font-size:16px;color:var(--text)}
.stApp [data-testid="stTextInputRootElement"],.stApp [data-testid="stSelectbox"] [role="group"]{min-height:48px}
.stApp [data-testid="stTextAreaRootElement"] textarea{line-height:1.6}
.stApp [data-testid="stCheckbox"] label p{font-size:16px;color:var(--text)}
.stApp [data-testid="stCaptionContainer"]{color:var(--text-muted)}
[data-testid="stFileUploaderDropzone"]{background:var(--canvas);border:1px solid var(--border);border-radius:var(--radius)}
[data-testid="stExpander"] details{border:0;border-top:1px solid var(--border);border-radius:0;background:transparent}
[data-testid="stExpander"] summary{font-weight:500;min-height:44px;padding-inline:0}
[data-testid="stExpander"] summary p{font-size:16px;font-weight:500}
[data-testid="stExpander"] summary:hover{color:var(--primary-hover)}
[data-testid="stExpanderDetails"]{padding-inline:0}
[data-testid="stForm"]{border:0;padding:0}
[data-testid="stCode"] pre{background:var(--canvas);border:1px solid var(--border);border-radius:var(--radius)}
[data-testid="stCode"] code{font-family:var(--font);font-size:15px;white-space:pre-wrap}
[data-testid="stAlertContainer"]{border-radius:var(--radius)}
[data-testid="stToast"]{background:var(--text);color:#fff}

/* ---- responsive ---- */
@media(max-width:1023px){.st-key-jf_brandtag{display:none}}
@media(max-width:767px){[data-testid="stMainBlockContainer"]{padding:0 16px 24px!important}
.st-key-jf_topbar{gap:2px!important;flex-wrap:nowrap!important}
.st-key-jf_topbar [data-testid^="stBaseButton-"]{padding:4px 6px!important;min-height:44px}
.st-key-jf_topbar [data-testid="stBaseButton-tertiary"] p{font-size:12px!important}
.st-key-jf_topbar [data-testid="stBaseButton-tertiary"] [data-testid="stIconMaterial"]{display:none}
.st-key-jf_brand [data-testid^="stBaseButton-"] p{font-size:22px!important}
.st-key-jf_brand [data-testid="stIconMaterial"]{display:grid!important;width:32px;height:32px;font-size:20px}
.st-key-jf_nav{gap:4px!important;flex-wrap:nowrap!important}
.st-key-jf_nav [data-testid^="stBaseButton-"]{padding:8px 6px;min-height:48px}
.st-key-jf_nav [data-testid^="stBaseButton-"] p{font-size:14px}
.st-key-nav_cv [data-testid^="stBaseButton-"] p{font-size:12px}
.jf-display{font-size:40px;max-width:20ch}
.jf-how{grid-template-columns:1fr;gap:24px}.jf-coverage{gap:24px;padding:24px}.jf-coverage-value{font-size:56px}
[class*="st-key-jfpanel"],[class*="st-key-jfchoice"],[class*="st-key-jfmodal_card"],.jf-process{padding:24px}
[class*="st-key-jfrow"]{padding:24px 16px}.jf-page-heading{flex-direction:column;gap:12px}
.jf-steps{gap:12px}.jf-steps li{font-size:12px;gap:4px}.jf-step-number{width:24px;height:24px}
.jf-metric-row{grid-template-columns:120px 1fr 48px;gap:12px}.jf-preview-text{padding:16px}
[class*="st-key-jfupload"]{padding:32px 16px}}
@media(max-width:374px){.st-key-open_help{display:none}.jf-coverage{grid-template-columns:1fr}.jf-tag{font-size:12px}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important}}
"""


def inject() -> None:
    """The stylesheet; a style-only st.html takes no space in the layout."""
    st.html(f'<style>{CSS}\n{icon_css()}</style>')
