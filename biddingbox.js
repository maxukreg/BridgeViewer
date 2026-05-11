/**
 * biddingbox.js  — Plug-in bidding box using the same PNG assets as the
 *                  RealBridge script (bidbox/png/ folder).
 *
 * Drop this file next to your HTML, then call:
 *
 *   BiddingBox.init({ seatIndex, dealer, vulnerability, onBid });
 *   BiddingBox.setTurn(seatIndex);   // shows box when it equals seatIndex
 *   BiddingBox.pushBid(bidObj);      // record any bid (including opponents')
 *   BiddingBox.reset(dealer, vuln);  // new board
 *   BiddingBox.getAuction();         // returns auction array
 *
 * PNG filenames used (must be in bidbox/png/ relative to the HTML page):
 *   1CBB.png  1DBB.png  1HBB.png  1SBB.png  1NTBB.png
 *   2CBB.png  ...  7NTBB.png    (35 bid buttons)
 *   XBB.png   XXBB.png  PASSBB.png  (or PASSEBB.png for alternate layout)
 *   ALERTBB.png  STOPBB.png
 */

(function (global) {
  'use strict';

  /* ─── Constants ──────────────────────────────────────────────────── */
  const STRAINS  = ['C', 'D', 'H', 'S', 'NT'];
  const LEVELS   = [1, 2, 3, 4, 5, 6, 7];
  const SEATS    = ['N', 'E', 'S', 'W'];
  const SEAT_NAMES = ['North', 'East', 'South', 'West'];

  // Suit colours matching RealBridge: C=black D=orange H=red S=blue NT=grey
  const STRAIN_COLORS = {
    C: '#1a1a1a', D: '#e06000', H: '#cc0000', S: '#0033aa', NT: '#444444'
  };
  const AUCTION_BG = {
    PASS: '#007700', X: '#880000', XX: '#0000aa'
  };

  /* ─── State ───────────────────────────────────────────────────────── */
  let _cfg = {
    seatIndex:     2,       // which seat is the human player
    dealer:        0,
    vulnerability: 'none',  // 'none'|'ns'|'ew'|'both'
    onBid:         null
  };
  let _auction     = [];   // { seat, call, level, strain, alert, explanation }
  let _currentTurn = -1;   // whose turn it is right now
  let _container   = null; // #bbcontainer  (the main box element)
  let _auctionBox  = null; // auction diagram element
  let _imgs        = [];   // flat list: indices 0-34 = bids, 35=X, 36=XX, 37=PASS, 38=ALERT
  let _alertOn     = false;
  let _pendingLevel = -1;  // first click stores level; second click (strain) fires bid
  let _visible     = false;
  let _alertBtnImg = null;
  let _stopCard    = null;
  let _alertBox    = null; // the bbalertbox / explanation input
  let _pendingBid  = null; // bid waiting for explanation before firing

  /* ─── Helpers ─────────────────────────────────────────────────────── */

  function imgIdx(level, strainIdx) {
    return (level - 1) * 5 + strainIdx;
  }

  // Returns the highest bid so far as { level, strainIdx } or null
  function highestBid() {
    for (let i = _auction.length - 1; i >= 0; i--) {
      const c = _auction[i];
      if (c.level && c.strain) {
        return { level: c.level, strainIdx: STRAINS.indexOf(c.strain) };
      }
    }
    return null;
  }

  // Is doubling legal right now?
  function canDouble() {
    // Find the last non-pass call
    const calls = _auction.filter(c => c.call !== 'PASS');
    if (!calls.length) return false;
    const last = calls[calls.length - 1];
    if (last.call === 'X' || last.call === 'XX') return false;
    // Must be an opponent's bid
    const lastSeat = last.seat;
    const diff = ((_currentTurn - lastSeat) + 4) % 4;
    return diff === 1 || diff === 3; // opponent (odd offset)
  }

  function canRedouble() {
    const calls = _auction.filter(c => c.call !== 'PASS');
    if (!calls.length) return false;
    const last = calls[calls.length - 1];
    if (last.call !== 'X') return false;
    const diff = ((_currentTurn - last.seat) + 4) % 4;
    return diff === 1 || diff === 3;
  }

  // Three consecutive passes after at least one bid = auction over
  function isAuctionOver() {
    if (_auction.length < 4) return false;
    const last3 = _auction.slice(-3);
    if (last3.every(c => c.call === 'PASS')) return true;
    // All 4 pass = passed out
    if (_auction.length === 4 && _auction.every(c => c.call === 'PASS')) return true;
    return false;
  }

  function strainSymbol(s) {
    const map = { C: '♣', D: '♦', H: '♥', S: '♠', NT: 'NT' };
    return map[s] || s;
  }

  function vulnForSeat(seat) {
    const v = _cfg.vulnerability;
    if (v === 'both') return true;
    if (v === 'ns'   && (seat === 0 || seat === 2)) return true;
    if (v === 'ew'   && (seat === 1 || seat === 3)) return true;
    return false;
  }

  /* ─── DOM: Build the container ───────────────────────────────────── */

  function buildContainer() {
    // Remove any previous instance
    const old = document.getElementById('bb-plugin-container');
    if (old) old.parentNode.removeChild(old);

    const wrap = document.createElement('div');
    wrap.id = 'bb-plugin-container';
    Object.assign(wrap.style, {
      position:   'fixed',
      bottom:     '12px',
      right:      '12px',
      zIndex:     '9999',
      display:    'flex',
      flexDirection: 'column',
      alignItems: 'flex-end',
      gap:        '6px',
      pointerEvents: 'none',
      userSelect: 'none'
    });
    document.body.appendChild(wrap);
    return wrap;
  }

  /* ─── DOM: Auction diagram ────────────────────────────────────────── */

  function buildAuctionDiagram(parent) {
    const box = document.createElement('div');
    box.id = 'bb-auction-diagram';
    Object.assign(box.style, {
      background:   'rgba(0,0,20,0.88)',
      border:       '1px solid #336',
      borderRadius: '6px',
      padding:      '6px 8px',
      pointerEvents:'auto',
      minWidth:     '220px',
      maxHeight:    '220px',
      overflowY:    'auto',
      fontFamily:   'Roboto, Arial, sans-serif',
      fontSize:     '13px',
      color:        '#eee',
      lineHeight:   '1.5'
    });

    // Header row: seat names with dealer marker and vuln colour
    const hdr = document.createElement('div');
    hdr.style.cssText = 'display:grid;grid-template-columns:repeat(4,1fr);text-align:center;font-weight:bold;margin-bottom:4px;';
    for (let s = 0; s < 4; s++) {
      const cell = document.createElement('div');
      const isVuln = vulnForSeat(s);
      cell.style.cssText = `
        color:${isVuln ? '#ff6666' : '#99cc99'};
        background:${isVuln ? 'rgba(120,0,0,0.3)' : 'rgba(0,80,0,0.2)'};
        border-radius:3px;padding:1px 3px;
      `;
      cell.textContent = SEATS[s] + (s === _cfg.dealer ? '★' : '');
      hdr.appendChild(cell);
    }
    box.appendChild(hdr);

    // Bid rows will be added by refreshAuctionDiagram()
    const rows = document.createElement('div');
    rows.id = 'bb-auction-rows';
    rows.style.cssText = 'display:grid;grid-template-columns:repeat(4,1fr);gap:2px 0;text-align:center;';
    box.appendChild(rows);

    parent.appendChild(box);
    return box;
  }

  function refreshAuctionDiagram() {
    const rows = document.getElementById('bb-auction-rows');
    if (!rows) return;
    rows.innerHTML = '';

    // Fill empty cells for dealer offset
    for (let i = 0; i < _cfg.dealer; i++) {
      const blank = document.createElement('div');
      rows.appendChild(blank);
    }

    _auction.forEach(bid => {
      const cell = document.createElement('div');
      cell.style.cssText = 'padding:1px 2px;border-radius:3px;font-size:12px;';

      if (bid.call === 'PASS') {
        cell.textContent = 'Pass';
        cell.style.color = '#88dd88';
      } else if (bid.call === 'X') {
        cell.textContent = 'X';
        cell.style.color = '#ff6666'; cell.style.fontWeight = 'bold';
      } else if (bid.call === 'XX') {
        cell.textContent = 'XX';
        cell.style.color = '#6699ff'; cell.style.fontWeight = 'bold';
      } else if (bid.level && bid.strain) {
        const col = STRAIN_COLORS[bid.strain] || '#ccc';
        // Use bright versions for readability on dark bg
        const brightMap = { '#1a1a1a': '#cccccc', '#e06000': '#ff9900', '#cc0000': '#ff5555', '#0033aa': '#5599ff', '#444444': '#aaaaaa' };
        cell.style.color = brightMap[col] || col;
        cell.style.fontWeight = 'bold';
        cell.innerHTML = `${bid.level}<span style="color:${brightMap[col] || col}">${strainSymbol(bid.strain)}</span>`;
      }

      if (bid.alert) {
        const al = document.createElement('sup');
        al.textContent = '!';
        al.style.cssText = 'color:#ffcc00;font-size:9px;margin-left:1px;';
        cell.appendChild(al);
      }
      rows.appendChild(cell);
    });
  }

  /* ─── DOM: Build the bidding box (PNG buttons) ─────────────────────── */

  function buildBiddingBox(parent) {
    const box = document.createElement('div');
    box.id = 'bbcontainer';
    Object.assign(box.style, {
      background:    'rgba(20,40,20,0.96)',
      border:        '2px solid #3a5a3a',
      borderRadius:  '8px',
      padding:       '6px',
      pointerEvents: 'auto',
      opacity:       '0',
      transition:    'opacity 200ms ease',
      display:       'flex',
      flexDirection: 'column',
      gap:           '2px'
    });

    // ── Row 0: PASS | X | XX | ALERT ────────────────────────────────
    const topRow = document.createElement('div');
    topRow.style.cssText = 'display:flex;gap:3px;margin-bottom:3px;';

    const passImg  = makeImg('bidbox/png/PASSBB.png',  35 + 2, 'PASS');   // index 37
    const xImg     = makeImg('bidbox/png/XBB.png',     35,     'X');      // index 35
    const xxImg    = makeImg('bidbox/png/XXBB.png',    36,     'XX');     // index 36
    const alertImg = makeImg('bidbox/png/ALERTBB.png', 38,     'ALERT');  // index 38

    _imgs[37] = passImg;
    _imgs[35] = xImg;
    _imgs[36] = xxImg;
    _alertBtnImg = alertImg;

    [passImg, xImg, xxImg, alertImg].forEach(img => topRow.appendChild(img));
    box.appendChild(topRow);

    // ── Level rows: 7 rows × 5 strains ──────────────────────────────
    for (let lvl = 7; lvl >= 1; lvl--) {
      const row = document.createElement('div');
      row.style.cssText = 'display:flex;gap:2px;';
      for (let si = 0; si < 5; si++) {
        const strain = STRAINS[si];
        const idx    = imgIdx(lvl, si);
        const src    = `bidbox/png/${lvl}${strain === 'NT' ? 'NT' : strain}BB.png`;
        const img    = makeImg(src, idx, `${lvl}${strain}`);
        _imgs[idx]   = img;
        row.appendChild(img);
      }
      box.appendChild(row);
    }

    // ── STOP card (hidden until needed) ─────────────────────────────
    _stopCard = document.createElement('img');
    _stopCard.src = 'bidbox/png/STOPBB.png';
    _stopCard.draggable = false;
    Object.assign(_stopCard.style, {
      height:   '28px',
      display:  'none',
      cursor:   'default',
      alignSelf:'flex-start',
      marginTop:'2px'
    });
    box.appendChild(_stopCard);

    parent.appendChild(box);
    _container = box;
    return box;
  }

  function makeImg(src, idx, call) {
    const img = document.createElement('img');
    img.src       = src;
    img.draggable = false;
    Object.assign(img.style, {
      height:  '28px',
      width:   'auto',
      cursor:  'pointer',
      opacity: '0.35',
      display: 'block',
      transition: 'opacity 120ms, transform 100ms',
      objectFit: 'contain'
    });

    img.addEventListener('mouseenter', function () {
      if (parseFloat(this.style.opacity) > 0.5) {
        this.style.transform = 'scale(1.12)';
      }
    });
    img.addEventListener('mouseleave', function () {
      this.style.transform = 'scale(1.0)';
    });

    img.addEventListener('click', function () {
      if (parseFloat(this.style.opacity) < 0.6) return; // disabled
      handleBidClick(idx, call);
    });

    return img;
  }

  /* ─── DOM: Alert/Explanation input ───────────────────────────────── */

  function buildAlertBox(parent) {
    const box = document.createElement('div');
    box.id = 'bb-alertbox';
    Object.assign(box.style, {
      background:    'rgba(40,10,10,0.95)',
      border:        '1px solid #aa4444',
      borderRadius:  '6px',
      padding:       '6px 8px',
      pointerEvents: 'auto',
      display:       'none',
      flexDirection: 'column',
      gap:           '4px',
      minWidth:      '220px'
    });

    const label = document.createElement('div');
    label.textContent = '⚠ ALERT — enter explanation (optional):';
    label.style.cssText = 'font-size:11px;color:#ffcc88;font-family:Roboto,Arial,sans-serif;';

    const input = document.createElement('input');
    input.id = 'bb-alert-input';
    input.type = 'text';
    input.placeholder = 'e.g. 5+ clubs, 12-14 HCP';
    Object.assign(input.style, {
      background:   '#1a0a0a',
      border:       '1px solid #885555',
      borderRadius: '4px',
      color:        '#ffddbb',
      fontFamily:   'Roboto,Arial,sans-serif',
      fontSize:     '12px',
      padding:      '4px 6px',
      width:        '100%',
      boxSizing:    'border-box'
    });

    const btnRow = document.createElement('div');
    btnRow.style.cssText = 'display:flex;gap:6px;justify-content:flex-end;';

    const okBtn = document.createElement('button');
    okBtn.textContent = 'Confirm bid';
    Object.assign(okBtn.style, {
      background:   '#cc0000',
      color:        '#fff',
      border:       'none',
      borderRadius: '4px',
      padding:      '3px 10px',
      fontSize:     '12px',
      cursor:       'pointer',
      fontFamily:   'Roboto,Arial,sans-serif'
    });
    okBtn.addEventListener('click', function () {
      confirmPendingBid(input.value.trim());
    });

    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = 'Cancel';
    Object.assign(cancelBtn.style, {
      background:   '#333',
      color:        '#aaa',
      border:       'none',
      borderRadius: '4px',
      padding:      '3px 10px',
      fontSize:     '12px',
      cursor:       'pointer',
      fontFamily:   'Roboto,Arial,sans-serif'
    });
    cancelBtn.addEventListener('click', function () {
      _pendingBid = null;
      _alertOn    = false;
      hideAlertBox();
      updateButtonStates();
      refreshAlertBtnHighlight();
    });

    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') confirmPendingBid(input.value.trim());
      if (e.key === 'Escape') cancelBtn.click();
    });

    btnRow.appendChild(cancelBtn);
    btnRow.appendChild(okBtn);
    box.appendChild(label);
    box.appendChild(input);
    box.appendChild(btnRow);

    _alertBox = box;
    parent.appendChild(box);
    return box;
  }

  function showAlertBox() {
    if (!_alertBox) return;
    _alertBox.style.display = 'flex';
    const inp = document.getElementById('bb-alert-input');
    if (inp) { inp.value = ''; setTimeout(() => inp.focus(), 50); }
  }
  function hideAlertBox() {
    if (!_alertBox) return;
    _alertBox.style.display = 'none';
  }

  /* ─── Bid click logic ─────────────────────────────────────────────── */

  function handleBidClick(idx, call) {
    if (_currentTurn !== _cfg.seatIndex) return;

    // ALERT toggle
    if (idx === 38) {
      _alertOn = !_alertOn;
      refreshAlertBtnHighlight();
      return;
    }

    // PASS
    if (idx === 37) {
      fireBid({ seat: _cfg.seatIndex, call: 'PASS', text: 'Pass' });
      return;
    }
    // Double
    if (idx === 35) {
      fireBid({ seat: _cfg.seatIndex, call: 'X', text: 'Double' });
      return;
    }
    // Redouble
    if (idx === 36) {
      fireBid({ seat: _cfg.seatIndex, call: 'XX', text: 'Redouble' });
      return;
    }

    // Level/strain bid (0-34)
    const level   = Math.floor(idx / 5) + 1;
    const strainI = idx % 5;
    const strain  = STRAINS[strainI];

    // Validate legality
    const hi = highestBid();
    if (hi) {
      if (level < hi.level) return;
      if (level === hi.level && strainI <= hi.strainIdx) return;
    }

    const bidObj = {
      seat:   _cfg.seatIndex,
      call:   `${level}${strain}`,
      level:  level,
      strain: strain,
      text:   `${level}${strainSymbol(strain)}`,
      alert:  _alertOn
    };

    if (_alertOn) {
      _pendingBid = bidObj;
      showAlertBox();
    } else {
      fireBid(bidObj);
    }
  }

  function confirmPendingBid(explanation) {
    if (!_pendingBid) return;
    _pendingBid.explanation = explanation || '';
    fireBid(_pendingBid);
    _pendingBid = null;
    _alertOn = false;
    hideAlertBox();
    refreshAlertBtnHighlight();
  }

  function fireBid(bidObj) {
    _auction.push(bidObj);
    refreshAuctionDiagram();
    updateButtonStates();

    // Show STOP card if bid skips a level
    const prev = highestBidBefore(bidObj);
    if (_stopCard && bidObj.level && prev && bidObj.level > prev.level + 1) {
      _stopCard.style.display = 'block';
      setTimeout(() => { if (_stopCard) _stopCard.style.display = 'none'; }, 2000);
    }

    if (typeof _cfg.onBid === 'function') _cfg.onBid(bidObj);

    if (isAuctionOver()) {
      hideBox(200);
    }
  }

  function highestBidBefore(thisOne) {
    const idx = _auction.indexOf(thisOne);
    for (let i = idx - 1; i >= 0; i--) {
      if (_auction[i].level) return _auction[i];
    }
    return null;
  }

  /* ─── Button enable/disable logic ────────────────────────────────── */

  function updateButtonStates() {
    if (!_container) return;
    const hi = highestBid();

    // Level/strain buttons
    for (let lvl = 1; lvl <= 7; lvl++) {
      for (let si = 0; si < 5; si++) {
        const idx = imgIdx(lvl, si);
        const img = _imgs[idx];
        if (!img) continue;
        let legal = true;
        if (hi) {
          if (lvl < hi.level) legal = false;
          else if (lvl === hi.level && si <= hi.strainIdx) legal = false;
        }
        img.style.opacity = legal ? '1' : '0.18';
        img.style.cursor  = legal ? 'pointer' : 'default';
      }
    }

    // PASS always legal
    if (_imgs[37]) { _imgs[37].style.opacity = '1'; _imgs[37].style.cursor = 'pointer'; }
    // X / XX
    if (_imgs[35]) { _imgs[35].style.opacity = canDouble()   ? '1' : '0.18'; _imgs[35].style.cursor = canDouble()   ? 'pointer' : 'default'; }
    if (_imgs[36]) { _imgs[36].style.opacity = canRedouble() ? '1' : '0.18'; _imgs[36].style.cursor = canRedouble() ? 'pointer' : 'default'; }
    // ALERT always available while box is shown
    if (_alertBtnImg) { _alertBtnImg.style.opacity = '1'; _alertBtnImg.style.cursor = 'pointer'; }
  }

  function refreshAlertBtnHighlight() {
    if (!_alertBtnImg) return;
    _alertBtnImg.style.filter = _alertOn
      ? 'drop-shadow(0 0 6px #ffcc00) brightness(1.4)'
      : '';
  }

  /* ─── Show / hide the bidding box ────────────────────────────────── */

  function showBox(durationMs) {
    if (!_container) return;
    _visible = true;
    _container.style.pointerEvents = 'auto';
    _container.animate
      ? _container.animate([{ opacity: 0 }, { opacity: 1 }], { duration: durationMs || 200, fill: 'forwards' }).onfinish = () => { _container.style.opacity = '1'; }
      : (_container.style.opacity = '1');
    updateButtonStates();
    refreshAlertBtnHighlight();
  }

  function hideBox(durationMs) {
    if (!_container) return;
    _visible = false;
    _container.style.pointerEvents = 'none';
    _pendingBid = null;
    _alertOn    = false;
    hideAlertBox();
    const done = () => { _container.style.opacity = '0'; };
    _container.animate
      ? _container.animate([{ opacity: 1 }, { opacity: 0 }], { duration: durationMs || 200, fill: 'forwards' }).onfinish = done
      : done();
  }

  /* ─── Keyboard shortcuts ──────────────────────────────────────────── */

  function handleKey(e) {
    if (_currentTurn !== _cfg.seatIndex || !_visible) return;
    if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) return;

    const key = e.key.toUpperCase();
    if (key === 'P')     { handleBidClick(37, 'PASS'); return; }
    if (key === 'D')     { handleBidClick(35, 'X');    return; }
    if (key === 'R')     { handleBidClick(36, 'XX');   return; }
    if (key === 'A')     { handleBidClick(38, 'ALERT');return; }

    // Number = set level, then await strain key
    const num = parseInt(key);
    if (num >= 1 && num <= 7) { _pendingLevel = num; return; }

    if (_pendingLevel >= 1) {
      const strainMap = { C: 0, D: 1, H: 2, S: 3, N: 4 };
      if (key in strainMap) {
        const idx = imgIdx(_pendingLevel, strainMap[key]);
        handleBidClick(idx, `${_pendingLevel}${STRAINS[strainMap[key]]}`);
        _pendingLevel = -1;
      }
    }
  }

  /* ─── Public API ──────────────────────────────────────────────────── */

  const BiddingBox = {

    /**
     * init(options)
     *   options.seatIndex     {number}   0=N 1=E 2=S 3=W — the human's seat
     *   options.dealer        {number}   0-3
     *   options.vulnerability {string}   'none'|'ns'|'ew'|'both'
     *   options.onBid         {function} called with bid object when human bids
     */
    init(options) {
      _cfg = Object.assign({
        seatIndex:     2,
        dealer:        0,
        vulnerability: 'none',
        onBid:         null
      }, options);

      _auction      = [];
      _currentTurn  = -1;
      _alertOn      = false;
      _pendingLevel = -1;
      _pendingBid   = null;
      _imgs         = [];

      // Build DOM
      const wrap = buildContainer();
      buildAuctionDiagram(wrap);
      buildAlertBox(wrap);
      buildBiddingBox(wrap);

      // Keyboard listener (remove any prior one)
      document.removeEventListener('keydown', handleKey);
      document.addEventListener('keydown', handleKey);
    },

    /**
     * setTurn(seatIndex)
     * Call this to advance the auction to the given seat.
     * If seatIndex === the player's seat, the bidding box appears.
     */
    setTurn(seat) {
      _currentTurn = seat;
      if (seat === _cfg.seatIndex) {
        if (!isAuctionOver()) showBox(200);
      } else {
        hideBox(150);
      }
    },

    /**
     * pushBid(bidObj)
     * Record a bid made by any player (typically an opponent's bid arriving
     * from your server/game engine). bidObj: { seat, call, level?, strain?, alert? }
     * Does NOT trigger onBid — that fires only for the human player.
     */
    pushBid(bidObj) {
      _auction.push(bidObj);
      refreshAuctionDiagram();
    },

    /** Reset for a new board. */
    reset(dealer, vulnerability) {
      if (dealer        !== undefined) _cfg.dealer        = dealer;
      if (vulnerability !== undefined) _cfg.vulnerability = vulnerability;
      _auction      = [];
      _currentTurn  = -1;
      _alertOn      = false;
      _pendingLevel = -1;
      _pendingBid   = null;
      hideBox(0);
      hideAlertBox();
      refreshAuctionDiagram();

      // Rebuild the diagram header (vuln colours may have changed)
      const diag = document.getElementById('bb-auction-diagram');
      if (diag) {
        const wrap = document.getElementById('bb-plugin-container');
        if (wrap) {
          diag.parentNode.removeChild(diag);
          const newDiag = buildAuctionDiagram(wrap);
          // Reorder: auction diagram first, then alert box, then bid box
          wrap.insertBefore(newDiag, wrap.firstChild);
        }
      }
    },

    /** Returns a copy of the full auction array. */
    getAuction() {
      return _auction.slice();
    },

    /** Show / hide programmatically (e.g. for testing). */
    show()  { showBox(200);  },
    hide()  { hideBox(200);  }
  };

  global.BiddingBox = BiddingBox;

}(typeof window !== 'undefined' ? window : this));
