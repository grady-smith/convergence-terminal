/**
 * ConvergenceTerminal Frontend Controller
 * Minimalist, high-performance client feed renderer and sparkline engine.
 */

// ─── State ────────────────────────────────────────────────────────────────────
let allSignals = [];
let activeCategory = 'All Signals';
let searchQuery = '';
let onlyUrgent = false;
let lastGeneratedAt = null;

// ─── Color palette by category ────────────────────────────────────────────────
const CATEGORY_STYLES = {
  'Bitcoin': {
    badgeBg: 'bg-amber-950/80',
    badgeText: 'text-amber-400',
    badgeBorder: 'border-amber-500/50',
    accentBorder: 'border-l-amber-400',
    sparkColor: '#f59e0b'
  },
  'Compute, Power & The Grid': {
    badgeBg: 'bg-orange-950/60',
    badgeText: 'text-orange-400',
    badgeBorder: 'border-orange-500/30',
    accentBorder: 'border-l-orange-500',
    sparkColor: '#f97316'
  },
  'Agentic Rails & Settlement': {
    badgeBg: 'bg-sky-950/60',
    badgeText: 'text-sky-400',
    badgeBorder: 'border-sky-500/30',
    accentBorder: 'border-l-sky-500',
    sparkColor: '#38bdf8'
  },
  'Macro Plumbing & Balance Sheets': {
    badgeBg: 'bg-emerald-950/60',
    badgeText: 'text-emerald-400',
    badgeBorder: 'border-emerald-500/30',
    accentBorder: 'border-l-emerald-500',
    sparkColor: '#10b981'
  },
  'Autonomous Intelligence': {
    badgeBg: 'bg-purple-950/60',
    badgeText: 'text-purple-400',
    badgeBorder: 'border-purple-500/30',
    accentBorder: 'border-l-purple-500',
    sparkColor: '#a855f7'
  }
};

// ─── Sparkline ─────────────────────────────────────────────────────────────────

/**
 * Zero-dependency SVG sparkline generator.
 */
function renderSparkline(points, width = 76, height = 20, strokeColor = '#f59e0b') {
  if (!points || points.length < 2) return '';
  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;
  const step = width / (points.length - 1);

  const coords = points.map((p, i) => {
    const x = (i * step).toFixed(1);
    const y = (height - ((p - min) / range) * (height - 4) - 2).toFixed(1);
    return `${x},${y}`;
  });

  return `
    <svg class="sparkline inline-block overflow-visible" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
      <polyline 
        fill="none" 
        stroke="${strokeColor}" 
        stroke-width="2" 
        stroke-linecap="round" 
        stroke-linejoin="round" 
        points="${coords.join(' ')}" 
      />
    </svg>
  `;
}

// ─── Utilities ─────────────────────────────────────────────────────────────────

function formatRelativeTime(isoString) {
  try {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    if (diffHours < 1) return 'Just now';
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  } catch (e) {
    return 'Recent';
  }
}

// ─── Data loading ──────────────────────────────────────────────────────────────

async function loadSignals(isBackgroundPoll = false) {
  const container = document.getElementById('signals-container');
  try {
    const response = await fetch('data.json?t=' + Date.now());
    if (!response.ok) throw new Error('HTTP ' + response.status);
    const payload = await response.json();
    
    if (isBackgroundPoll) {
      if (lastGeneratedAt && payload.generated_at && payload.generated_at !== lastGeneratedAt) {
        showUpdateToast();
      }
      return;
    }

    lastGeneratedAt = payload.generated_at;
    const rawItems = payload.items || [];
    const seenUrls = new Set();
    const seenContents = new Set();
    const deduped = [];

    for (const item of rawItems) {
      const url = item.source_url;
      const isSpecificPost = item.source_url_type === 'post' && url && url !== '#';
      const urlKey = isSpecificPost ? url.toLowerCase() : null;
      const headline = item.elevated_intelligence?.signal_headline || '';
      let contentKey = `${item.entity?.handle || ''}:${headline.toLowerCase()}`;
      if (headline === 'Signal Awaiting Classification') {
        contentKey += `:${(item.raw_summary || '').substring(0, 60).toLowerCase()}`;
      }

      if (urlKey && seenUrls.has(urlKey)) continue;
      if (seenContents.has(contentKey)) continue;

      if (urlKey) seenUrls.add(urlKey);
      seenContents.add(contentKey);
      deduped.push(item);
    }

    allSignals = deduped;
    
    updateHeaderStats(payload);
    renderFilterButtons();
    renderSignals();
    hideUpdateToast();
  } catch (err) {
    if (!isBackgroundPoll) {
      console.error('Failed to load data.json:', err);
      container.innerHTML = `
        <div class="p-8 text-center terminal-card rounded-lg border border-rose-500/30 text-rose-300">
          <p class="font-mono text-lg font-bold">⚠️ Intelligence feed unavailable</p>
          <p class="text-sm text-slate-400 mt-2">Run <code>python3 internal/scripts/ingest.py</code> to generate <code>public/data.json</code>.</p>
        </div>
      `;
    }
  }
}

// ─── Header stats ──────────────────────────────────────────────────────────────

function updateHeaderStats(payload) {
  const totalCount = allSignals.length;
  const urgentCount = allSignals.filter(s => s.elevated_intelligence?.is_urgent_shift).length;
  const avgVelocity = totalCount > 0
    ? (allSignals.reduce((acc, s) => acc + (s.metrics?.velocity_score || 0), 0) / totalCount).toFixed(1)
    : '0.0';

  // Use nullish coalescing so a real 0 isn't masked, and missing data shows
  // an honest placeholder rather than a hardcoded fabricated number.
  const sludgeCount = payload?.sludge_filtered_count ?? null;
  const trackedCount = payload?.tracked_entities_count ?? null;

  document.getElementById('stat-total-signals').textContent = totalCount;
  document.getElementById('stat-urgent-shifts').textContent = urgentCount;
  document.getElementById('stat-avg-velocity').textContent = avgVelocity;
  document.getElementById('stat-sludge-dropped').textContent = sludgeCount !== null ? sludgeCount : '—';
  
  const trackedEl = document.getElementById('stat-tracked-entities');
  if (trackedEl) trackedEl.textContent = trackedCount !== null ? trackedCount : '—';

  if (payload?.generated_at) {
    const generatedDate = new Date(payload.generated_at);
    document.getElementById('last-updated-time').textContent = generatedDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', timeZone: 'UTC' }) + ' UTC';
    updateSyncIndicators(generatedDate);
  } else {
    document.getElementById('last-updated-time').textContent = '--:--';
  }
}

// Global sync schedule configuration
const SYNC_TIMES_UTC = ['00:00', '12:00'];

function updateSyncIndicators(lastSyncDate) {
  const container = document.getElementById('sync-schedule-indicators');
  if (!container) return;
  
  const now = new Date();
  const isTodayUTC = lastSyncDate.getUTCDate() === now.getUTCDate() && 
                     lastSyncDate.getUTCMonth() === now.getUTCMonth() && 
                     lastSyncDate.getUTCFullYear() === now.getUTCFullYear();
  
  const indicatorsHtml = SYNC_TIMES_UTC.map(timeStr => {
    const [hours, minutes] = timeStr.split(':').map(Number);
    const syncTime = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate(), hours, minutes, 0, 0));
    
    // Check if this specific sync time has been fulfilled today in UTC
    let isSynced = false;
    if (isTodayUTC && lastSyncDate >= syncTime) {
      isSynced = true;
    }
    
    const baseClass = "px-1.5 py-0.5 rounded text-[10px] font-bold";
    const colorClass = isSynced 
      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' 
      : 'bg-slate-800/50 text-slate-500 border border-slate-700/50';
    
    return `<div class="${baseClass} ${colorClass}" title="Scheduled: ${timeStr} UTC">${timeStr} UTC</div>`;
  }).join('');
  
  container.innerHTML = indicatorsHtml;
}

// ─── Toast notifications ───────────────────────────────────────────────────────

function showUpdateToast() {
  const toast = document.getElementById('new-signals-toast');
  if (toast) {
    toast.classList.remove('hidden');
    toast.classList.add('flex');
  }
}

function hideUpdateToast() {
  const toast = document.getElementById('new-signals-toast');
  if (toast) {
    toast.classList.add('hidden');
    toast.classList.remove('flex');
  }
}

function reloadFreshSignals() {
  hideUpdateToast();
  loadSignals(false);
}

// ─── Category filters ──────────────────────────────────────────────────────────

const CATEGORIES = [
  'All Signals',
  'Bitcoin',
  'Compute, Power & The Grid',
  'Agentic Rails & Settlement',
  'Macro Plumbing & Balance Sheets',
  'Autonomous Intelligence'
];

/**
 * Render category filter pills.
 *
 * L-3: Uses data-category attributes on each button instead of inline onclick
 * string interpolation. A single delegated listener on the container handles
 * all clicks — this avoids ampersand encoding bugs and keeps HTML clean.
 */
function renderFilterButtons() {
  const container = document.getElementById('category-filters');

  container.innerHTML = CATEGORIES.map(cat => {
    const count = cat === 'All Signals'
      ? allSignals.length
      : allSignals.filter(s => s.category === cat).length;
    const isActive = activeCategory === cat;
    
    return `
      <button 
        data-category="${cat}"
        class="px-3 py-1.5 rounded text-xs font-mono font-medium transition-all flex items-center gap-2 ${
          isActive 
            ? 'bg-amber-500 text-slate-950 font-bold shadow-md shadow-amber-500/20' 
            : 'bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700/60'
        }"
      >
        <span>${cat}</span>
        <span class="px-1.5 py-0.2 rounded-full text-[10px] ${isActive ? 'bg-slate-950/30 text-slate-950' : 'bg-slate-900 text-slate-400'}">${count}</span>
      </button>
    `;
  }).join('');
}

function setCategory(cat) {
  activeCategory = cat;
  renderFilterButtons();
  renderSignals();
}

function toggleUrgent() {
  onlyUrgent = !onlyUrgent;
  const btn = document.getElementById('btn-urgent-toggle');
  if (onlyUrgent) {
    btn.classList.add('bg-rose-600', 'text-white', 'border-rose-400');
    btn.classList.remove('bg-slate-800', 'text-slate-400');
  } else {
    btn.classList.remove('bg-rose-600', 'text-white', 'border-rose-400');
    btn.classList.add('bg-slate-800', 'text-slate-400');
  }
  renderSignals();
}

// ─── Card renderer ─────────────────────────────────────────────────────────────

/**
 * M-3: Dedicated card template function, extracted from renderSignals().
 *
 * Accepts a single signal item and its resolved CATEGORY_STYLES entry.
 * Returns an HTML string for one <article> card.
 * renderSignals() is now a pure orchestration function — filter, sort, join.
 */
function renderCard(item, style) {
  const isUrgent = item.elevated_intelligence?.is_urgent_shift;
  const sparkSvg = renderSparkline(item.metrics?.sparkline_points, 84, 22, style.sparkColor);
  const relTime = formatRelativeTime(item.timestamp);
  const entityInitials = (item.entity?.name || 'TE').split(' ').map(n => n[0]).join('').substring(0, 2);
  const lensContent = item.elevated_intelligence?.convergence_lens
    || item.elevated_intelligence?.alden_lens
    || 'Physical and monetary realities govern this transition.';
  const safeSourceUrl = (item.source_url && item.source_url !== '#')
    ? item.source_url
    : (item.entity?.handle ? `https://x.com/${item.entity.handle.replace('@', '')}` : '#');
  const isProfileLink = item.source_url_type === 'profile';

  const urgentBadge = isUrgent ? `
    <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-950/80 text-rose-400 border border-rose-600/50 uppercase tracking-wider flex items-center gap-1.5 animate-pulse">
      <span class="w-1.5 h-1.5 rounded-full bg-rose-400"></span>
      Urgent Shift
    </span>
  ` : '';

  const crossRefBlock = item.elevated_intelligence?.cross_reference ? `
    <div class="flex items-start gap-2 pt-2 border-t border-slate-800/80 min-w-0">
      <span class="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 uppercase tracking-wider flex-shrink-0 mt-0.5">
        Cross-Ref
      </span>
      <p class="text-xs text-slate-400 leading-relaxed break-words min-w-0">
        ${item.elevated_intelligence.cross_reference}
      </p>
    </div>
  ` : '';

  const sourceLink = isProfileLink ? `
    <a 
      href="${safeSourceUrl}" 
      target="_blank" 
      rel="noopener noreferrer" 
      title="No direct post link available — opens author profile"
      class="px-3 py-1.5 rounded bg-slate-900 hover:bg-slate-800 text-slate-500 hover:text-slate-300 font-mono text-xs flex items-center gap-1.5 border border-slate-800 transition-colors ml-auto italic"
    >
      <svg class="w-3 h-3 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
      </svg>
      <span>View Profile</span>
    </a>
  ` : `
    <a 
      href="${safeSourceUrl}" 
      target="_blank" 
      rel="noopener noreferrer" 
      class="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white font-mono text-xs flex items-center gap-1.5 border border-slate-700 transition-colors ml-auto"
    >
      <span>View Source</span>
      <svg class="w-3 h-3 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
      </svg>
    </a>
  `;

  return `
    <article class="terminal-card rounded-xl p-4 sm:p-5 border-l-4 ${style.accentBorder} flex flex-col justify-between gap-4 h-full w-full min-w-0 overflow-hidden box-border">
      <!-- Card Top Bar -->
      <div class="flex items-start justify-between gap-3 flex-wrap min-w-0">
        <div class="flex items-center gap-2.5 sm:gap-3 min-w-0 flex-1">
          <div class="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-mono font-bold text-amber-400 text-xs sm:text-sm overflow-hidden flex-shrink-0">
            <span title="${item.entity?.name}">${entityInitials}</span>
          </div>
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-1.5 min-w-0">
              <h3 class="font-semibold text-slate-100 text-xs sm:text-sm hover:text-amber-400 transition-colors truncate">
                ${item.entity?.name || 'Unknown Entity'}
              </h3>
              <span class="text-[11px] sm:text-xs font-mono text-slate-400 truncate">${item.entity?.handle || ''}</span>
            </div>
            <div class="flex items-center gap-2 text-[10px] sm:text-[11px] font-mono text-slate-400 mt-0.5">
              <span class="uppercase tracking-wider text-slate-400">${item.entity?.platform || 'FEED'}</span>
              <span>•</span>
              <span>${relTime}</span>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-1.5 flex-wrap justify-end max-w-full">
          ${urgentBadge}
          <span class="px-2 py-0.5 rounded text-[10px] sm:text-[11px] font-mono font-medium ${style.badgeBg} ${style.badgeText} border ${style.badgeBorder} break-words text-right">
            ${item.category}
          </span>
        </div>
      </div>

      <!-- Headline & Summary -->
      <div class="min-w-0">
        <h2 class="text-base sm:text-lg font-bold text-slate-100 tracking-tight leading-snug break-words">
          ${item.elevated_intelligence?.signal_headline || item.raw_summary}
        </h2>
        <p class="text-xs sm:text-sm text-slate-400 mt-2 leading-relaxed bg-slate-950/40 p-3 rounded-lg border border-slate-800/80 font-mono break-words">
          "${item.raw_summary}"
        </p>
      </div>

      <!-- Convergence Lens & Cross-Reference Box -->
      <div class="bg-slate-900/90 rounded-lg p-3.5 border border-slate-800 space-y-2.5 min-w-0">
        <div class="flex items-start gap-2 min-w-0">
          <span class="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20 uppercase tracking-wider flex-shrink-0 mt-0.5">
            Convergence Lens
          </span>
          <p class="text-xs sm:text-sm text-amber-100/90 leading-relaxed break-words min-w-0 flex-1">
            ${lensContent}
          </p>
        </div>
        ${crossRefBlock}
      </div>

      <!-- Card Footer -->
      <div class="flex items-center justify-between pt-2 border-t border-slate-800/60 flex-wrap gap-2 text-xs min-w-0">
        <div class="flex items-center gap-3 sm:gap-4 flex-wrap">
          <div class="flex items-center gap-1.5 font-mono">
            <span class="text-slate-400 text-[10px] sm:text-[11px]">VELOCITY:</span>
            <span class="font-bold text-amber-400 text-xs sm:text-sm">${item.metrics?.velocity_score ?? '—'}</span>
            <span class="text-slate-400 text-[10px]">/ 10</span>
          </div>

          <div class="flex items-center gap-2">
            ${sparkSvg}
            <span class="font-mono text-[10px] sm:text-[11px] text-slate-300 font-medium">${item.metrics?.momentum_label ?? '—'}</span>
          </div>
        </div>

        ${sourceLink}
      </div>
    </article>
  `;
}

// ─── Signal list renderer ──────────────────────────────────────────────────────

/**
 * Filter, sort, and render all matching signal cards.
 * Card HTML is produced by renderCard() — this function only orchestrates.
 */
function renderSignals() {
  const container = document.getElementById('signals-container');
  const countDisplay = document.getElementById('filtered-count');

  const filtered = allSignals.filter(item => {
    if (activeCategory !== 'All Signals' && item.category !== activeCategory) return false;
    if (onlyUrgent && !item.elevated_intelligence?.is_urgent_shift) return false;
    if (searchQuery.trim() !== '') {
      const q = searchQuery.toLowerCase();
      const name    = (item.entity?.name || '').toLowerCase();
      const handle  = (item.entity?.handle || '').toLowerCase();
      const headline = (item.elevated_intelligence?.signal_headline || '').toLowerCase();
      const lens    = (item.elevated_intelligence?.convergence_lens || item.elevated_intelligence?.alden_lens || '').toLowerCase();
      const raw     = (item.raw_summary || '').toLowerCase();
      const cross   = (item.elevated_intelligence?.cross_reference || '').toLowerCase();
      if (!name.includes(q) && !handle.includes(q) && !headline.includes(q) && !lens.includes(q) && !raw.includes(q) && !cross.includes(q)) {
        return false;
      }
    }
    return true;
  });

  filtered.sort((a, b) => (b.metrics?.velocity_score || 0) - (a.metrics?.velocity_score || 0));

  const displaySignals = filtered;

  if (countDisplay) {
    countDisplay.textContent = `Showing ${filtered.length} signal${filtered.length !== 1 ? 's' : ''}`;
  }

  if (displaySignals.length === 0) {
    container.innerHTML = `
      <div class="col-span-full py-16 text-center terminal-card rounded-xl border border-slate-800 p-8">
        <p class="font-mono text-base text-slate-400">No signals match the active filters or search query.</p>
        <button data-action="clear-filters" class="mt-4 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-amber-400 text-xs font-mono rounded border border-slate-700">
          Reset Filters
        </button>
      </div>
    `;
    return;
  }

  const defaultStyle = {
    badgeBg: 'bg-slate-800',
    badgeText: 'text-slate-300',
    badgeBorder: 'border-slate-700',
    accentBorder: 'border-l-slate-500',
    sparkColor: '#f59e0b'
  };

  container.innerHTML = displaySignals
    .map(item => renderCard(item, CATEGORY_STYLES[item.category] || defaultStyle))
    .join('');
}

// ─── Filter helpers ────────────────────────────────────────────────────────────

function clearFilters() {
  activeCategory = 'All Signals';
  searchQuery = '';
  onlyUrgent = false;
  const searchInput = document.getElementById('search-input');
  if (searchInput) searchInput.value = '';
  const urgentBtn = document.getElementById('btn-urgent-toggle');
  if (urgentBtn) {
    urgentBtn.classList.remove('bg-rose-600', 'text-white', 'border-rose-400');
    urgentBtn.classList.add('bg-slate-800', 'text-slate-400');
  }
  renderFilterButtons();
  renderSignals();
}

// ─── Bootstrap ─────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  // L-3: Event delegation for category filter buttons.
  // Buttons carry data-category attributes; a single listener on the container
  // handles all clicks. No inline onclick, no ampersand encoding risk.
  const filterContainer = document.getElementById('category-filters');
  if (filterContainer) {
    filterContainer.addEventListener('click', e => {
      const btn = e.target.closest('[data-category]');
      if (btn) setCategory(btn.dataset.category);
    });
  }

  // L-3: Event delegation for the "Reset Filters" button rendered inside the
  // empty-state message (which uses data-action="clear-filters").
  const signalsContainer = document.getElementById('signals-container');
  if (signalsContainer) {
    signalsContainer.addEventListener('click', e => {
      const btn = e.target.closest('[data-action="clear-filters"]');
      if (btn) clearFilters();
    });
  }

  const searchInput = document.getElementById('search-input');
  if (searchInput) {
    searchInput.addEventListener('input', e => {
      searchQuery = e.target.value;
      renderSignals();
    });
  }

  // Keyboard shortcuts
  document.addEventListener('keydown', e => {
    const activeEl = document.activeElement;
    const isTyping = activeEl && (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA');

    if (e.key === '/' && !isTyping) {
      e.preventDefault();
      if (searchInput) {
        searchInput.focus();
        searchInput.select();
      }
    } else if (e.key === 'Escape') {
      if (isTyping) {
        searchInput.blur();
      } else {
        clearFilters();
      }
    } else if (!isTyping) {
      if (['1', '2', '3', '4', '5', '6'].includes(e.key)) {
        const idx = parseInt(e.key, 10) - 1;
        if (CATEGORIES[idx]) setCategory(CATEGORIES[idx]);
      } else if (e.key.toLowerCase() === 'u') {
        toggleUrgent();
      }
    }
  });

  // L-4: Background soft polling timer started inside DOMContentLoaded.
  // Previously this ran at script parse time, before the DOM was ready,
  // risking a race condition on very fast connections where the first poll
  // could fire before loadSignals() had initialised lastGeneratedAt.
  setInterval(() => loadSignals(true), 60000);

  loadSignals(false);
});
