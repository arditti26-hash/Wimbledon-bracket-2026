#!/usr/bin/env python3
"""Wimbledon 2026 Group Bracket Dashboard — scrapes served.bracket.tennis"""

import json, re, urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from html.parser import HTMLParser

PORT = 8767

# ── Edit your group members here ─────────────────────────────────────────────
MEMBERS = [
    'willarditti',
    'jackthesnack21',
    # add more served.bracket.tennis usernames here
]

COLORS = {
    0: {'primary': '#10b981', 'bg': 'rgba(16,185,129,0.12)', 'border': 'rgba(16,185,129,0.25)'},
    1: {'primary': '#3b82f6', 'bg': 'rgba(59,130,246,0.12)',  'border': 'rgba(59,130,246,0.25)'},
    2: {'primary': '#f59e0b', 'bg': 'rgba(245,158,11,0.12)',  'border': 'rgba(245,158,11,0.25)'},
    3: {'primary': '#8b5cf6', 'bg': 'rgba(139,92,246,0.12)',  'border': 'rgba(139,92,246,0.25)'},
    4: {'primary': '#ec4899', 'bg': 'rgba(236,72,153,0.12)',  'border': 'rgba(236,72,153,0.25)'},
    5: {'primary': '#14b8a6', 'bg': 'rgba(20,184,166,0.12)',  'border': 'rgba(20,184,166,0.25)'},
}

TOURNAMENT_SLUG = 'wimbledon-2026'

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Wimbledon 2026 · Group Bracket</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:wght@400;600;700&display=swap" rel="stylesheet">
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --green:  #00512e;
  --green2: #006b3c;
  --purple: #4b006e;
  --gold:   #c9a94b;
  --bg:     #f5f2eb;
  --card:   #ffffff;
  --text:   #1a1a1a;
  --muted:  #6b6b6b;
  --border: #ddd8cc;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
}

/* ── HEADER ── */
header {
  background: var(--green);
  color: #fff;
  padding: 0 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 68px;
  border-bottom: 4px solid var(--gold);
  position: sticky; top: 0; z-index: 10;
}
.logo { display: flex; align-items: center; gap: 14px; }
.logo-badge {
  width: 44px; height: 44px; border-radius: 50%;
  background: var(--gold); display: flex; align-items: center;
  justify-content: center; font-size: 22px; flex-shrink: 0;
}
.logo h1 {
  font-family: 'EB Garamond', Georgia, serif;
  font-size: 1.3rem; font-weight: 700; letter-spacing: 0.04em; line-height: 1.2;
}
.logo span { font-size: 0.72rem; opacity: 0.65; font-family: sans-serif; }
.header-right { display: flex; align-items: center; gap: 10px; }
.live-badge {
  display: flex; align-items: center; gap: 7px;
  background: rgba(201,169,75,0.15); border: 1px solid rgba(201,169,75,0.4);
  padding: 5px 13px; border-radius: 100px;
  font-size: 11px; font-weight: 700; color: var(--gold); letter-spacing: 1px;
  font-family: sans-serif;
}
.live-dot {
  width: 7px; height: 7px; background: var(--gold); border-radius: 50%;
  animation: blink 1.5s ease-in-out infinite;
}
@keyframes blink { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.4;transform:scale(0.7)} }

/* ── MAIN ── */
.wrap { max-width: 860px; margin: 0 auto; padding: 32px 20px 60px; }

/* ── STATUS BAR ── */
.status-bar {
  display: flex; align-items: center; gap: 8px;
  font-size: 0.78rem; font-family: sans-serif; color: var(--muted);
  margin-bottom: 24px;
}
.sdot { width: 7px; height: 7px; border-radius: 50%; background: var(--gold); flex-shrink: 0; }

/* ── SECTION TABS ── */
.tab-bar {
  display: flex; gap: 4px; margin-bottom: 18px;
  border-bottom: 2px solid var(--border);
}
.tab-btn {
  background: none; border: none; cursor: pointer;
  padding: 9px 20px; font-family: sans-serif; font-size: 0.88rem;
  color: var(--muted); border-bottom: 3px solid transparent;
  margin-bottom: -2px; transition: color 0.15s;
}
.tab-btn.active { color: var(--green); border-bottom-color: var(--green); font-weight: 700; }
.tab-btn:hover:not(.active) { color: var(--text); }

/* ── LEADERBOARD CARD ── */
.card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: 14px; overflow: hidden; margin-bottom: 24px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.07);
}
.card-header {
  padding: 16px 20px 13px; border-bottom: 1px solid var(--border);
  display: flex; align-items: center; justify-content: space-between;
}
.card-title {
  font-family: 'EB Garamond', Georgia, serif;
  font-size: 1.1rem; font-weight: 700; color: var(--green);
}
.card-sub { font-size: 0.74rem; font-family: sans-serif; color: var(--muted); margin-top: 3px; }

/* ── TABLE ── */
.lb-table { width: 100%; border-collapse: collapse; font-family: sans-serif; }
.lb-table th {
  text-align: left; padding: 9px 14px;
  font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.07em;
  color: var(--muted); border-bottom: 2px solid var(--border);
  background: var(--bg);
}
.lb-table th.right, .lb-table td.right { text-align: right; }
.lb-table td {
  padding: 13px 14px; border-bottom: 1px solid var(--border);
  font-size: 0.92rem; vertical-align: middle;
}
.lb-table tr:last-child td { border-bottom: none; }
.lb-table tr:hover td { background: #f9f6ef; }

.rank-cell { color: var(--muted); font-size: 0.82rem; width: 40px; }
.rank-cell.gold { color: var(--gold); font-size: 1rem; }

/* ── PLAYER ROW STYLING ── */
.player-name {
  font-weight: 700; font-size: 0.95rem;
}
.name-link { text-decoration: none; }
.name-link:hover { text-decoration: underline; }

.score-pill {
  display: inline-block; padding: 3px 10px; border-radius: 14px;
  font-size: 0.82rem; font-weight: 700;
}
.pill-atp      { background: #e8f4ee; color: #1a6b3c; }
.pill-wta      { background: #f3e8f4; color: #6b1a6b; }
.pill-combined { background: #fff3dc; color: #7a5a00; }
.pill-none     { background: #f0f0f0; color: #aaa; }

.bar-wrap { margin-top: 5px; height: 3px; background: #e8e4dc; border-radius: 2px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 2px; transition: width 0.8s ease; }

/* ── SCORING RULES ── */
.rules-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
  gap: 10px; padding: 16px;
}
.rule-item {
  background: var(--bg); border-radius: 9px; padding: 11px 12px;
  text-align: center; border: 1px solid var(--border);
}
.rule-round { font-size: 0.68rem; font-family: sans-serif; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }
.rule-pts { font-size: 1.4rem; font-weight: 700; color: var(--green); font-family: 'EB Garamond', Georgia, serif; }
.rule-note { font-size: 0.66rem; font-family: sans-serif; color: var(--muted); margin-top: 2px; }
.rules-bonuses { padding: 0 16px 16px; display: flex; flex-wrap: wrap; gap: 8px; }
.bonus-tag {
  background: #fff8e6; border: 1px solid #e8d89a; border-radius: 7px;
  padding: 5px 11px; font-size: 0.77rem; font-family: sans-serif; color: #7a5a00;
}

/* ── EMPTY / ERROR ── */
.info-block {
  text-align: center; padding: 52px 20px; font-family: sans-serif; color: var(--muted);
}
.info-block .icon { font-size: 2.5rem; margin-bottom: 10px; }
.info-block h2 { font-size: 1.1rem; color: var(--green); margin-bottom: 6px; }
.info-block p { font-size: 0.88rem; line-height: 1.55; max-width: 360px; margin: 0 auto; }

.footer {
  text-align: center; font-family: sans-serif; font-size: 0.75rem;
  color: var(--muted); margin-top: 16px;
}

/* ── RESPONSIVE ── */
@media (max-width: 560px) {
  header { height: auto; padding: 12px 14px; flex-wrap: wrap; gap: 10px; }
  .lb-table th:nth-child(3), .lb-table td:nth-child(3),
  .lb-table th:nth-child(4), .lb-table td:nth-child(4) { display: none; }
}
</style>
</head>
<body>

<header>
  <div class="logo">
    <div class="logo-badge">🎾</div>
    <div>
      <h1>Wimbledon 2026 · Bracket Pick'em</h1>
      <span>served.bracket.tennis · live standings</span>
    </div>
  </div>
  <div class="header-right">
    <div class="live-badge"><div class="live-dot"></div>LIVE</div>
  </div>
</header>

<div class="wrap">
  <div class="status-bar">
    <div class="sdot"></div>
    <span id="status-text">Loading…</span>
  </div>

  <div class="tab-bar">
    <button class="tab-btn active" onclick="switchTab('combined')">Combined</button>
    <button class="tab-btn" onclick="switchTab('atp')">ATP — Men's</button>
    <button class="tab-btn" onclick="switchTab('wta')">WTA — Women's</button>
  </div>

  <div class="card">
    <div class="card-header">
      <div>
        <div class="card-title" id="section-title">Combined Standings</div>
        <div class="card-sub" id="section-sub">ATP + WTA · served.bracket.tennis</div>
      </div>
    </div>
    <table class="lb-table">
      <thead>
        <tr>
          <th>#</th>
          <th>Player</th>
          <th>ATP</th>
          <th>WTA</th>
          <th class="right">Combined</th>
        </tr>
      </thead>
      <tbody id="lb-body">
        <tr><td colspan="5" style="padding:32px;text-align:center;color:#aaa;font-family:sans-serif">Loading…</td></tr>
      </tbody>
    </table>
  </div>

  <!-- SCORING RULES -->
  <div class="card">
    <div class="card-header">
      <div>
        <div class="card-title">Scoring Rules</div>
        <div class="card-sub">Points per correct pick · served.bracket.tennis</div>
      </div>
    </div>
    <div class="rules-grid">
      <div class="rule-item"><div class="rule-round">Round 1</div><div class="rule-pts">10</div><div class="rule-note">pts / pick</div></div>
      <div class="rule-item"><div class="rule-round">Round 2</div><div class="rule-pts">20</div><div class="rule-note">pts / pick</div></div>
      <div class="rule-item"><div class="rule-round">Round 3</div><div class="rule-pts">30</div><div class="rule-note">pts / pick</div></div>
      <div class="rule-item"><div class="rule-round">Round 4</div><div class="rule-pts">40</div><div class="rule-note">pts / pick</div></div>
      <div class="rule-item"><div class="rule-round">Quarters</div><div class="rule-pts">60</div><div class="rule-note">pts / pick</div></div>
      <div class="rule-item"><div class="rule-round">Semis</div><div class="rule-pts">80</div><div class="rule-note">pts / pick</div></div>
      <div class="rule-item"><div class="rule-round">Final</div><div class="rule-pts">100</div><div class="rule-note">pts / champion</div></div>
    </div>
    <div class="rules-bonuses">
      <div class="bonus-tag">🏆 Unseeded upset = double points</div>
      <div class="bonus-tag">📊 Seed gap bonus: +1pt per seed difference</div>
      <div class="bonus-tag">🔢 Tiebreaker: closest to total games in men's final</div>
    </div>
  </div>

  <div class="footer" id="footer"></div>
</div>

<script>
const COLORS = __COLORS_JSON__;
const SLUG   = '__SLUG__';
let currentTab = 'combined';
let allData = null;

async function loadData() {
  try {
    const res = await fetch('/api/data');
    if (!res.ok) throw new Error('HTTP ' + res.status);
    allData = await res.json();
    render();
    document.getElementById('footer').textContent = 'Scores from served.bracket.tennis · Updated: ' + allData.updated;
  } catch(e) {
    document.getElementById('status-text').textContent = 'Error loading data — ' + e.message;
  }
}

function switchTab(tab) {
  currentTab = tab;
  document.querySelectorAll('.tab-btn').forEach((b, i) => {
    b.classList.toggle('active', ['combined','atp','wta'][i] === tab);
  });
  const map = {
    combined: ['Combined Standings', 'ATP + WTA · served.bracket.tennis'],
    atp:      ["Men's Draw (ATP)",   'Individual ATP bracket scores'],
    wta:      ["Women's Draw (WTA)", 'Individual WTA bracket scores'],
  };
  document.getElementById('section-title').textContent = map[tab][0];
  document.getElementById('section-sub').textContent   = map[tab][1];
  render();
}

function render() {
  if (!allData) return;
  const players = allData.players;
  const tab = currentTab;

  const sorted = [...players].sort((a, b) => {
    const va = tab === 'atp' ? a.atp : tab === 'wta' ? a.wta : (a.combined ?? -1);
    const vb = tab === 'atp' ? b.atp : tab === 'wta' ? b.wta : (b.combined ?? -1);
    return (vb ?? -1) - (va ?? -1);
  });

  const maxScore = sorted.reduce((m, p) => {
    const v = tab === 'atp' ? p.atp : tab === 'wta' ? p.wta : p.combined;
    return Math.max(m, v ?? 0);
  }, 1);

  const tbody = document.getElementById('lb-body');

  const hasAny = players.some(p => p.combined !== null || p.atp !== null);
  if (!hasAny) {
    tbody.innerHTML = `<tr><td colspan="5" style="padding:36px;text-align:center;color:#aaa;font-family:sans-serif">
      Scores not yet available — make sure your usernames on served.bracket.tennis match exactly.
    </td></tr>`;
    document.getElementById('status-text').textContent = 'No scores found · ' + allData.updated;
    return;
  }

  tbody.innerHTML = sorted.map((p, i) => {
    const rank  = i + 1;
    const c     = COLORS[p.color_idx] || COLORS[0];
    const score = tab === 'atp' ? p.atp : tab === 'wta' ? p.wta : p.combined;
    const pct   = score != null ? Math.round((score / maxScore) * 100) : 0;
    const bracketUrl = `https://served.bracket.tennis/tournaments/${SLUG}/combined/brackets/${encodeURIComponent(p.username)}`;

    const atpPill  = p.atp  != null ? `<span class="score-pill pill-atp">${p.atp.toLocaleString()}</span>`   : `<span class="score-pill pill-none">–</span>`;
    const wtaPill  = p.wta  != null ? `<span class="score-pill pill-wta">${p.wta.toLocaleString()}</span>`   : `<span class="score-pill pill-none">–</span>`;
    const combPill = p.combined != null ? `<span class="score-pill pill-combined">${p.combined.toLocaleString()}</span>` : `<span class="score-pill pill-none">–</span>`;

    return `<tr>
      <td class="rank-cell ${rank<=3?'gold':''}">${rank<=3 ? ['🥇','🥈','🥉'][rank-1] : rank}</td>
      <td>
        <div class="player-name"><a class="name-link" href="${bracketUrl}" target="_blank" rel="noopener" style="color:${c.primary}">${esc(p.username)}</a></div>
        <div class="bar-wrap"><div class="bar-fill" style="width:${pct}%;background:${c.primary}"></div></div>
      </td>
      <td>${atpPill}</td>
      <td>${wtaPill}</td>
      <td class="right">${combPill}</td>
    </tr>`;
  }).join('');

  document.getElementById('status-text').textContent = `Live · last updated ${allData.updated}`;
}

function esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

loadData();
setInterval(loadData, 5 * 60 * 1000); // refresh every 5 minutes
</script>
</body>
</html>"""


# ── HTML template injection ────────────────────────────────────────────────────

def build_html():
    colors_for_js = {str(k): v for k, v in COLORS.items()}
    html = HTML.replace('__COLORS_JSON__', json.dumps(colors_for_js))
    html = html.replace('__SLUG__', TOURNAMENT_SLUG)
    return html


# ── Scrape served.bracket.tennis ──────────────────────────────────────────────

class LeaderboardParser(HTMLParser):
    """
    Walks the HTML of the served.bracket.tennis leaderboard page and collects
    username → {atp, wta, combined} score data.

    The page structure uses table rows where each row links to
    /tournaments/<slug>/<section>/brackets/<username>
    and contains score cells.
    """
    def __init__(self, members):
        super().__init__()
        self.members_lower = {m.lower(): m for m in members}
        self.scores = {m: {'atp': None, 'wta': None, 'combined': None} for m in members}
        self._current_row_user = None
        self._current_row_section = None
        self._in_cell = False
        self._cell_text = ''
        self._cells = []
        self._in_row = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'tr':
            self._in_row = True
            self._cells = []
            self._current_row_user = None
            self._current_row_section = None
        elif tag == 'a' and 'href' in attrs:
            href = attrs['href']
            m = re.search(r'/(atp|wta|combined)/brackets/([^/?#]+)', href, re.I)
            if m:
                section = m.group(1).lower()
                username = urllib.request.unquote(m.group(2))
                canonical = self.members_lower.get(username.lower())
                if canonical:
                    self._current_row_user = canonical
                    self._current_row_section = section
        elif tag in ('td', 'th'):
            self._in_cell = True
            self._cell_text = ''

    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self._in_cell:
            self._cells.append(self._cell_text.strip())
            self._in_cell = False
            self._cell_text = ''
        elif tag == 'tr':
            if self._current_row_user and self._current_row_section:
                # Find first numeric cell value
                for cell in self._cells:
                    clean = cell.replace(',', '').strip()
                    if clean.isdigit():
                        val = int(clean)
                        self.scores[self._current_row_user][self._current_row_section] = val
                        break
            self._in_row = False

    def handle_data(self, data):
        if self._in_cell:
            self._cell_text += data


def fetch_leaderboard_html():
    url = f'https://served.bracket.tennis/tournaments/{TOURNAMENT_SLUG}/leaderboard'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible)'})
    with urllib.request.urlopen(req, timeout=12) as r:
        return r.read().decode('utf-8', errors='replace')


def fetch_scores():
    """Fetch and parse scores for all MEMBERS from served.bracket.tennis."""
    html = fetch_leaderboard_html()
    parser = LeaderboardParser(MEMBERS)
    parser.feed(html)
    scores = parser.scores

    # Fallback: also try regex scan on raw HTML for "username ... NNN" patterns
    text = re.sub(r'<[^>]+>', ' ', html)
    for member in MEMBERS:
        s = scores[member]
        # Try to find combined pattern: username ... NNN+NNN=NNN
        pattern = re.escape(member) + r'[^<\n]*?(\d[\d,]+)\s*\+\s*(\d[\d,]+)\s*=\s*(\d[\d,]+)'
        m = re.search(pattern, text, re.I)
        if m:
            if s['atp']      is None: s['atp']      = int(m.group(1).replace(',',''))
            if s['wta']      is None: s['wta']      = int(m.group(2).replace(',',''))
            if s['combined'] is None: s['combined'] = int(m.group(3).replace(',',''))

    # Derive combined from atp+wta if still missing
    for member in MEMBERS:
        s = scores[member]
        if s['combined'] is None and s['atp'] is not None and s['wta'] is not None:
            s['combined'] = s['atp'] + s['wta']

    return scores


def get_data():
    scores = fetch_scores()

    players = []
    for i, member in enumerate(MEMBERS):
        s = scores[member]
        players.append({
            'username': member,
            'atp':      s['atp'],
            'wta':      s['wta'],
            'combined': s['combined'],
            'color_idx': i % len(COLORS),
        })

    # Sort by combined (desc), then atp
    players.sort(key=lambda p: (-(p['combined'] or -1), -(p['atp'] or -1)))

    return {
        'players': players,
        'updated': datetime.now().strftime('%b %d, %Y · %I:%M:%S %p'),
    }


# ── HTTP Server ───────────────────────────────────────────────────────────────

BUILT_HTML = build_html().encode('utf-8')

class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def send_body(self, body: bytes, content_type: str, status: int = 200):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith('/api/data'):
            try:
                data = get_data()
                body = json.dumps(data).encode()
                self.send_body(body, 'application/json')
            except Exception as e:
                self.send_body(str(e).encode(), 'text/plain', 500)
        else:
            self.send_body(BUILT_HTML, 'text/html; charset=utf-8')

    def log_message(self, fmt, *args):
        pass  # suppress server log noise


if __name__ == '__main__':
    print(f'🎾 Wimbledon 2026 Bracket Dashboard')
    print(f'   Running at http://localhost:{PORT}')
    print(f'   Tracking {len(MEMBERS)} players: {", ".join(MEMBERS)}')
    print(f'   Refreshes every 5 minutes from served.bracket.tennis')
    print(f'   Press Ctrl+C to stop\n')
    HTTPServer(('', PORT), Handler).serve_forever()
