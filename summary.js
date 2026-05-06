// =============================================================
// summary.js  –  stripped down for the summary screen only.
//
// Responsibilities:
//   1. Parse the LIN string (from URL param) and display the hand.
//   2. Show the auction in the auction table.
//   3. Display deal commentary from the deals*.js data files.
//   4. Navigate via "Replay" and "Next Hand" buttons.
//
// Everything related to vugraph, the editor, playing client /
// lessons, card images / animations, GIB, undo/rewind, context
// menus, chat, score-board, cookies, and XML/AJAX loading has
// been removed.
// =============================================================

// ─────────────────────────────────────────────────────────────
// Page targets
// ─────────────────────────────────────────────────────────────
const htmlPlayLoc = 'handviewer.html';
const htmlBidLoc = 'bidding.html';
const htmlLoc = htmlBidLoc;

// ─────────────────────────────────────────────────────────────
// Group / deal data (populated from external group*.js files)
// ─────────────────────────────────────────────────────────────
const groupData = {};
const groupTextData = {};

// ─────────────────────────────────────────────────────────────
// URL params
// ─────────────────────────────────────────────────────────────
const urlParams = new URLSearchParams(window.location.search);
const mode = urlParams.get('mode'); // 'tester' = from BookletTester

// Wire up the Next Hand button
document.getElementById('nextButton').onclick = function () {
  if (mode === 'tester') showNextHandSummaryOnly();
  else nextHand();
};

// ─────────────────────────────────────────────────────────────
// Display state
// ─────────────────────────────────────────────────────────────
var fireFox = (typeof window.innerHeight === 'number') ? 1 : 0;

// On the summary screen we always use the fast (innerHTML) path –
// no individual card divs, no card images.
var fastVersion = true;
var picturesOfCards = false;
var showPlayedCards = true;
var cardByCard = true;

var mainDivShowing = false;
var firstResize = true;

var availableHeight = 10, availableWidth = 10;
var totalWidth = 10, totalHeight = 10;
var scrollBarWidth;
var margin = 0;
var suitHeight = 10, handHeight = 50, handWidth = 50, nameHeight = 10;
var fontSize = 12, buttonFontSize = 12, buttonHeight = 20;
var displayType = '';
var editorWidthOffset = 0;
var highlightColor = '#FFCE00';

// ─────────────────────────────────────────────────────────────
// Suit / card constants
// ─────────────────────────────────────────────────────────────
var suits = ['Club', 'Diamond', 'Heart', 'Spade'];
var suitHTMLs = [
  "<font color='000000'>&clubs;</font>",
  "<font color='CB0000'>&diams;</font>",
  "<font color='CB0000'>&hearts;</font>",
  "<font color='000000'>&spades;</font>",
  "<font color='000000'>NT</font>"
];
var suitForums = ['[CL]', '[DI]', '[HE]', '[SP]', 'NT'];
var suitchars = 'CDHSN';
var callchars = 'PDR?';
var calls = ['P', 'X', 'XX', '?'];
var cardchars = '23456789TJQKA';
var seats = ['South', 'West', 'North', 'East'];

// Hand positions [S, W, N, E]
var xpos = [90, 10, 90, 170];
var ypos = [170, 90, 10, 90];

// ─────────────────────────────────────────────────────────────
// DOM element references (created in createHandTables)
// ─────────────────────────────────────────────────────────────
var blockDiv, statusDiv, announceDiv, annotDiv, menuDiv, menuTable;

var handDivs = new Array(4);
var nameBars = new Array(4);
var nameInitials = new Array(4);
var nameTexts = new Array(4);
var suitRows = new Array(4);
var suitSymbols = new Array(4);
var suitHoldings = new Array(4);
var cardDivs = new Array(4);
var cardDivsCreated = false;

var vulDivs = new Array(4);
var vulInnerDiv;

var auctionHeadingDiv;
var auctionHeading;
var auctionHeadingCells = new Array(5);
var auctionTableDiv;
var auctionTable;
var alertDiv;
var alertedCall = -1;

var trickDivs = new Array(4);
var tricksDiv, tricksDivLeft, tricksDivRight;
var scoreDiv, otherTableDiv, nsTeamDiv, ewTeamDiv, nsScoreDiv, ewScoreDiv;

// ─────────────────────────────────────────────────────────────
// Hand display state
// ─────────────────────────────────────────────────────────────
var handShowing = new Array(4);
var numHandsShowing = 4;
var mouseOverName = -1;

// ─────────────────────────────────────────────────────────────
// Card / deck state
// ─────────────────────────────────────────────────────────────
var deck = new Array(4);
var howManyCards = new Array(4);
var howManyCardsDealt = new Array(4);
var howManySuit = new Array(4);
var howManySuitDealt = new Array(4);
var howManyXs = new Array(4);

var cardHighlighted = new Array(4);
var userDealt = new Array(4);

// ─────────────────────────────────────────────────────────────
// Board / deal state
// ─────────────────────────────────────────────────────────────
var boardNum = 0, groupNum = 0;
var currentId;
var dealer = -1, nsVul = false, ewVul = false;
var whosTurn;

// ─────────────────────────────────────────────────────────────
// Bidding state
// ─────────────────────────────────────────────────────────────
var levelBid = [], strainBid = [], seatBid = [];
var passes = -1, lastLevelBid, lastStrainBid, lastBidder;
var contractLevel, doubled, trump, declarer, dummy;
var bidSeqPoint, bidSeqMax;
var bidSequence = [];
var callExplanation = [];
var callAnnotation = [];
var callAnnotType = [];

// ─────────────────────────────────────────────────────────────
// Play state
// ─────────────────────────────────────────────────────────────
var playSequence = new Array(52);
var playSeqPoint, playSeqMax;
var rankPlayed = new Array(13);
var suitPlayed = new Array(13);
var seatPlayed = new Array(13);
var trickWinner = new Array(13);
var cardAnnotation = new Array(13);
var cardAnnotType = new Array(13);
var trick, inTrick;
var nsTricks = 0, ewTricks = 0;
var tricksClaimed;
var claimShowing = false;
var trickTimer;

// ─────────────────────────────────────────────────────────────
// Annotation state (annotDiv is null on summary screen but
// processLinFile still calls addAnnotation, so we track state)
// ─────────────────────────────────────────────────────────────
var hasAnnotations = false;
var introAnnotation = null;

// ─────────────────────────────────────────────────────────────
// Window resize wiring
// ─────────────────────────────────────────────────────────────
if (fireFox) {
  window.onresize = function () { respondToBodyResize(); };
} else {
  document.body.onresize = function () {
    setTimeout('respondToBodyResize()', 10);
  };
}

window.addEventListener('resize', function () {
  respondToResize();
  drawHandsBox();
});

// ─────────────────────────────────────────────────────────────
// Startup – runs immediately (script is deferred, so DOM is ready)
// ─────────────────────────────────────────────────────────────
setDisplayType(displayType);
createHandTables();

// Load the hand from the lin= URL param (or fall back to individual params)
var linURL = gup('lin');
if (linURL !== '') {
  processLinFile(safeDecode(linURL));
} else {
  loadParams();
}

// ─────────────────────────────────────────────────────────────
// Layout / display helpers
// ─────────────────────────────────────────────────────────────
function showAll(visible) {
  var div = document.getElementById('theDiv');
  var buttonDiv = document.getElementById('buttonDiv');

  mainDivShowing = visible;

  if (visible) {
    statusDiv.style.visibility = 'hidden';
    blockDiv.style.visibility = 'hidden';
    buttonDiv.style.visibility = 'visible';
  } else {
    statusDiv.style.visibility = 'visible';
    blockDiv.style.visibility = 'visible';
    buttonDiv.style.visibility = 'hidden';
    if (annotDiv) annotDiv.style.visibility = 'hidden';
    clearTrickCards(0, 3);
  }

  // Show/hide name bars (no card images on this screen)
  for (var seat = 0; seat < 4; seat++) {
    nameBars[seat].style.visibility = visible ? 'visible' : 'hidden';
  }

  respondToResize();
}

// ─────────────────────────────────────────────────────────────
function respondToBodyResize() {
  respondToResize();
}

// Mobile breakpoint (px)
var MOBILE_BREAKPOINT = 768;

function isMobileLayout() {
  // Always use window.innerWidth – works on real devices and narrow desktop windows
  return window.innerWidth < MOBILE_BREAKPOINT;
}

function respondToResize() {
  var div = document.getElementById('theDiv');

  // Always use window dimensions for consistency
  availableWidth = window.innerWidth;
  availableHeight = window.innerHeight;

  if (firstResize) {
    firstResize = false;
    blockDiv.style.visibility = 'visible';
    blockDiv.style.width = availableWidth + 'px';
    blockDiv.style.height = availableHeight + 'px';
    return;
  }

  if (mainDivShowing) blockDiv.style.visibility = 'hidden';

  // Toggle body class so CSS can assist with max-width etc.
  if (isMobileLayout()) {
    document.body.classList.add('mobile-layout');
    respondToResizeMobile(div);
  } else {
    document.body.classList.remove('mobile-layout');
    respondToResizeDesktop(div);
  }

  // Common teardown
  tricksDiv.style.fontSize = (3 * fontSize) / 4 + 'px';
  tricksDiv.style.paddingLeft = margin + 'px';
  tricksDiv.style.paddingRight = margin + 'px';
  announceDiv.style.paddingRight = margin + 'px';
  announceDiv.style.paddingLeft = margin + 'px';
  manageTricksDiv();

  scoreDiv.style.fontSize = (3 * fontSize) / 4 + 'px';
  scoreDiv.style.paddingLeft = margin + 'px';
  scoreDiv.style.paddingRight = margin + 'px';
  tricksDiv.style.display = 'none';

  manageInfoDiv();
  positionHandsContainer();
  drawHandsBox();
  updateTextContainer();
}

// ─────────────────────────────────────────────────────────────
// DESKTOP layout: hand compass left ~42%, text panel right
// ─────────────────────────────────────────────────────────────
function respondToResizeDesktop(div) {
  var handRows = getHandRows();
  var handCols = getHandCols();

  totalHeight = availableHeight;
  totalWidth = availableWidth;
  if (totalWidth < 10) totalWidth = 10;
  if (totalHeight < 10) totalHeight = 10;

  blockDiv.style.width = totalWidth + 'px';
  blockDiv.style.height = availableHeight + 'px';

  var buttonDivHeight = Math.max(40, 0.09 * totalHeight);
  totalHeight -= buttonDivHeight;
  margin = Math.max(2, totalHeight / 35);
  totalHeight = Math.max(1, totalHeight);

  var margins = handCols + 1;
  handWidth = Math.max(1, (totalWidth - margins * margin) / handCols);
  handHeight = Math.max(1, (totalHeight - (handRows + 1) * margin) / handRows);
  suitHeight = handHeight / 5;

  // Scale to the 42%-wide left column
  handWidth /= 3;
  handHeight /= 1.9;
  suitHeight /= 1.9;

  resizeButtons();
  nameHeight = Math.floor(handHeight / 5);
  fontSize = handHeight / 6.5;

  // Hands panel
  div.style.position = 'absolute';
  div.style.top = '0px';
  div.style.left = '0px';
  div.style.width = '42%';
  div.style.height = totalHeight + 'px';

  // Text panel: right of hands
  var tc = document.getElementById('textContainer');
  if (tc) {
    tc.style.position = 'absolute';
    tc.style.top = '0px';
    tc.style.left = '42%';
    tc.style.width = '';       // CSS right:0 handles this
    tc.style.height = (totalHeight + buttonDivHeight) * 0.966 + 'px';
    tc.style.overflowY = 'auto';
  }

  // Button bar: full width at bottom
  var buttonDiv = document.getElementById('buttonDiv');
  buttonDiv.style.position = 'absolute';
  buttonDiv.style.top = totalHeight + 'px';
  buttonDiv.style.left = '0px';
  buttonDiv.style.width = totalWidth + 'px';
  buttonDiv.style.height = (buttonDivHeight - 2 * fireFox) + 'px';
  buttonDiv.style.visibility = showButtonBar() ? 'visible' : 'hidden';

  if (showButtonBar()) {
    buttonHeight = Math.max(24, buttonDivHeight - 2 * margin);
    buttonFontSize = buttonHeight / 2;
    if (menuTable) menuTable.style.fontSize = buttonFontSize + 'px';
  } else {
    if (menuTable) menuTable.style.fontSize = (3 * fontSize) / 4 + 'px';
  }

  positionHandCompass(div);
  positionAuction(div);
}

// ─────────────────────────────────────────────────────────────
// MOBILE layout: hands on top ~46%, scrollable text below
// ─────────────────────────────────────────────────────────────
function respondToResizeMobile(div) {
  totalWidth = availableWidth;
  totalHeight = availableHeight;

  var buttonDivHeight = Math.max(50, Math.round(totalHeight * 0.10));
  var handAreaHeight = Math.round(totalHeight * 0.46);
  var textAreaHeight = totalHeight - handAreaHeight - buttonDivHeight;

  blockDiv.style.width = totalWidth + 'px';
  blockDiv.style.height = totalHeight + 'px';

  margin = Math.max(2, handAreaHeight / 40);

  // Divide into a 3×3 compass grid then scale down to leave room for
  // the name bar (≈ handHeight/5) above each hand and the auction table.
  var MOBILE_SCALE = 0.68;
  handWidth = Math.max(1, (totalWidth - 4 * margin) / 3) * MOBILE_SCALE;
  handHeight = Math.max(1, (handAreaHeight - 4 * margin) / 3) * MOBILE_SCALE;
  suitHeight = handHeight / 5;

  resizeButtons();
  nameHeight = Math.floor(handHeight / 5);
  fontSize = handHeight / 6.5;

  // Hands panel: full width, top of screen
  div.style.position = 'absolute';
  div.style.top = '0px';
  div.style.left = '0px';
  div.style.width = totalWidth + 'px';   // explicit px beats CSS 42%
  div.style.height = handAreaHeight + 'px';

  // Text panel: full width, directly below hands
  var tc = document.getElementById('textContainer');
  if (tc) {
    tc.style.position = 'absolute';
    tc.style.top = handAreaHeight + 'px';
    tc.style.left = '0px';
    tc.style.width = totalWidth + 'px';
    tc.style.height = textAreaHeight + 'px';
    tc.style.overflowY = 'auto';
  }

  // Button bar: full width, pinned at bottom
  var buttonDiv = document.getElementById('buttonDiv');
  buttonDiv.style.position = 'absolute';
  buttonDiv.style.top = (handAreaHeight + textAreaHeight) + 'px';
  buttonDiv.style.left = '0px';
  buttonDiv.style.width = totalWidth + 'px';
  buttonDiv.style.height = buttonDivHeight + 'px';
  buttonDiv.style.visibility = 'visible';

  buttonHeight = Math.max(24, buttonDivHeight - 2 * margin);
  buttonFontSize = buttonHeight / 2;
  if (menuTable) menuTable.style.fontSize = buttonFontSize + 'px';

  positionHandCompass(div);
  positionAuction(div);
}

// ─────────────────────────────────────────────────────────────
// Shared: position the four hand divs in a compass inside `div`
// ─────────────────────────────────────────────────────────────
function positionHandCompass(div) {
  for (var seat = 0; seat < 4; seat++) {
    var table = handDivs[seat];

    if (!handShowing[seat]) {
      if (table.parentNode === div) table.style.visibility = 'hidden';
      if (nameBars[seat].parentNode === div) nameBars[seat].style.visibility = 'hidden';
      continue;
    }

    table.style.visibility = 'visible';
    nameBars[seat].style.visibility = 'visible';

    table.style.width = getHandWidth(seat);
    table.style.height = handHeight;
    table.style.fontSize = fontSize;

    nameTexts[seat].style.left = nameInitials[seat].clientWidth;
    nameTexts[seat].style.top = 0;
    nameTexts[seat].style.paddingLeft = margin;

    for (var suit = 0; suit < 4; suit++) {
      suitRows[seat][suit].style.top = (4 - suit) * suitHeight;
      suitRows[seat][suit].style.height = suitHeight;
      suitSymbols[seat][suit].style.fontSize = 1.5 * fontSize;
      suitSymbols[seat][suit].style.lineHeight = 1.3 * fontSize + 'px';
      suitHoldings[seat][suit].style.fontSize = 1.2 * fontSize;
      suitHoldings[seat][suit].style.lineHeight = 1.4 * fontSize + 'px';
      suitHoldings[seat][suit].style.left = suitSymbols[seat][suit].clientWidth;
      suitHoldings[seat][suit].style.top = 0;
      resizeCards(seat, suit);
    }

    // Compass positions: N top-centre, S bottom-centre, W/E middle sides
    var panelWidth = isMobileLayout() ? totalWidth : totalWidth * 0.42;
    var xOffset = isMobileLayout() ? -margin * 2 : 0;
    var yOffset = isMobileLayout() ? margin * 3 : 0;
    var compassWidth = 3 * handWidth + 2 * margin;
    var compassLeft = (panelWidth - compassWidth) / 2 + xOffset;
    xpos[1] = compassLeft;                               // West
    xpos[0] = compassLeft + handWidth + margin;          // North / South (centre column)
    xpos[2] = xpos[0];
    xpos[3] = compassLeft + 2 * (handWidth + margin);   // East
    ypos[0] = 2 * handHeight + (margin * 2.5) + yOffset; // South
    ypos[2] = margin + yOffset;                          // North
    ypos[1] = ypos[2] + handHeight + margin;             // West (middle row)
    ypos[3] = ypos[1];                                   // East (middle row)

    nameBars[seat].style.fontSize = fontSize;
    nameBars[seat].style.left = xpos[seat];
    nameBars[seat].style.top = ypos[seat];
    nameBars[seat].style.height = nameHeight;
    nameBars[seat].style.width = getHandWidth(seat);
    table.style.left = xpos[seat];
    table.style.top = ypos[seat];
    nameTexts[seat].style.left = nameInitials[seat].clientWidth;
    nameTexts[seat].style.width = getHandWidth(seat) - nameInitials[seat].clientWidth;
  }
}

// ─────────────────────────────────────────────────────────────
// Shared: position/size the auction table inside `div`
// ─────────────────────────────────────────────────────────────
function positionAuction(div) {
  if (showAuction()) {
    if (auctionHeadingDiv.parentNode !== div) div.appendChild(auctionHeadingDiv);
    if (auctionTableDiv.parentNode !== div) div.appendChild(auctionTableDiv);
    div.appendChild(alertDiv);

    auctionHeading.style.fontSize = fontSize;
    auctionHeadingDiv.style.width = handWidth;
    auctionHeading.style.height = suitHeight;
    auctionHeading.style.width = handWidth;

    auctionTableDiv.style.fontSize = fontSize;
    auctionTableDiv.style.width = handWidth;

    var auctionDivHeight = 4 * suitHeight;
    auctionTableDiv.style.height = auctionDivHeight + 'px';

    auctionTable.style.fontSize = fontSize * 0.88;
    auctionTable.style.width = handWidth;

    var yOffset = isMobileLayout() ? margin * 3 : 0;
    var auctionLeft = xpos[3];
    var auctionTop = margin + yOffset + div.offsetTop;

    auctionHeadingDiv.style.top = auctionTop;
    auctionHeadingDiv.style.left = auctionLeft;

    auctionTableDiv.style.top = auctionTop + auctionHeading.clientHeight;
    auctionTableDiv.style.left = auctionLeft;

    manageAuctionScrollBar();

    alertDiv.style.fontSize = (3 * fontSize) / 4;
    alertDiv.style.height = (3 * suitHeight) / 4;
    manageAlertDiv();
  } else {
    if (auctionHeadingDiv.parentNode === div) div.removeChild(auctionHeadingDiv);
    if (auctionTableDiv.parentNode === div) div.removeChild(auctionTableDiv);
  }
}

// ─────────────────────────────────────────────────────────────
// Auction scroll bar
// ─────────────────────────────────────────────────────────────
function manageAuctionScrollBar() {
  var cellPercent, rightPercent;

  if (auctionTable.clientHeight > auctionTableDiv.clientHeight && auctionTable.clientWidth !== 0) {
    auctionTableDiv.style.overflowY = 'scroll';
    cellPercent = Math.max(1, (100 * ((auctionTable.clientWidth - scrollBarWidth) / 4)) / auctionTable.clientWidth) + '%';
    rightPercent = 100 * (scrollBarWidth / auctionTable.clientWidth) + '%';
  } else {
    auctionTableDiv.style.overflowY = 'hidden';
    cellPercent = '25%';
    rightPercent = '0%';
  }

  for (var row = 0; row < auctionTable.rows.length; row++) {
    for (var col = 0; col < 4; col++) auctionTable.rows[row].cells[col].style.width = cellPercent;
    auctionTable.rows[row].cells[4].style.width = rightPercent;
  }
  for (var col = 0; col < 4; col++) auctionHeading.rows[0].cells[col].style.width = cellPercent;
  auctionHeading.rows[0].cells[4].style.width = rightPercent;
}

// ─────────────────────────────────────────────────────────────
// Tricks div (hidden on summary screen but kept to avoid errors)
// ─────────────────────────────────────────────────────────────
function manageTricksDiv() {
  var div = document.getElementById('theDiv');
  if (!showTricksDiv()) {
    if (tricksDiv.parentNode === div) div.removeChild(tricksDiv);
    return;
  }

  if (!endPosition() && (passes < 3 || declarer < 0)) {
    tricksDiv.style.visibility = 'hidden';
    return;
  }

  var html = "<font color='000000'>" + contractLevel + '</font>' + suitHTMLs[trump] + "<font color='000000'>";
  if (doubled === 2) html += 'x';
  if (doubled === 4) html += 'xx';
  html += ' ' + seats[declarer].charAt(0) + ' ';

  tricksDivLeft.innerHTML = html;
  tricksDivRight.innerHTML = 'NS: ' + nsTricks + ' EW: ' + ewTricks;

  tricksDivLeft.style.height = fontSize - margin / 2;
  tricksDiv.style.left = totalWidth - handWidth - margin - 2 * fireFox;
  tricksDiv.style.width = Math.max(0, handWidth - 2 * margin * fireFox);
  tricksDiv.style.height = tricksDivLeft.clientHeight + 2;
  tricksDiv.style.top = totalHeight - tricksDiv.clientHeight - margin - 2;
  tricksDiv.style.visibility = 'visible';
}

// ─────────────────────────────────────────────────────────────
// Vulnerability / dealer indicator
// ─────────────────────────────────────────────────────────────
function manageInfoDiv() {
  var div = document.getElementById('theDiv');

  if (!showInfoDiv()) {
    for (var seat = 0; seat < 4; seat++) {
      if (vulDivs[seat].parentNode === div) div.removeChild(vulDivs[seat]);
    }
    if (vulInnerDiv.parentNode === div) div.removeChild(vulInnerDiv);
    return;
  }

  for (var seat = 0; seat < 4; seat++) {
    if (vulDivs[seat].parentNode !== div) div.appendChild(vulDivs[seat]);
    vulDivs[seat].style.visibility = (dealer >= 0) ? 'visible' : 'hidden';
    vulDivs[seat].innerHTML = (seat === dealer) ? '<b>D</b>' : '';
  }

  if (vulInnerDiv.parentNode !== div) div.appendChild(vulInnerDiv);
  vulInnerDiv.innerHTML = (boardNum > 0) ? boardNum : '';

  if (dealer < 0) vulInnerDiv.style.visibility = 'hidden';
  else vulInnerDiv.style.visibility = 'visible';

  var suitH = handHeight / 5;
  var vulMargin = 2;
  var vulSize = Math.floor((2 * suitH) / 3);
  var vulBorder = 2;
  var minWidth = (5 * fontSize) / 2;
  var yOffset = isMobileLayout() ? margin * 3 : 0;
  var vTop = margin + yOffset;

  vulInnerDiv.style.fontSize = (7 * fontSize) / 4;
  vulInnerDiv.style.height = minWidth + 'px';
  if (fireFox) vulInnerDiv.style.minWidth = minWidth;
  else vulInnerDiv.style.width = minWidth;
  vulInnerDiv.style.lineHeight = Math.max(1, minWidth - 2 * vulMargin) + 'px';
  vulInnerDiv.style.top = vTop + vulMargin + vulSize;
  vulInnerDiv.style.left = xpos[0] - handWidth;

  for (var seat = 0; seat < 4; seat++) {
    vulDivs[seat].style.fontSize = (2 * fontSize) / 3;
    if (seat % 2) {
      vulDivs[seat].style.top = vTop + vulMargin + vulSize;
      vulDivs[seat].style.height = vulInnerDiv.clientHeight + 2 * vulBorder - !fireFox;
      vulDivs[seat].style.width = vulSize;
      vulDivs[seat].style.lineHeight = vulInnerDiv.clientHeight + 2 * vulBorder + 'px';
      vulDivs[seat].style.left = (seat === 1)
        ? xpos[0] - handWidth - vulSize - vulMargin
        : xpos[0] - handWidth + minWidth + (margin * 0.25);
    } else {
      vulDivs[seat].style.left = xpos[0] - handWidth;
      vulDivs[seat].style.width = vulInnerDiv.clientWidth + 2 * vulBorder - !fireFox;
      vulDivs[seat].style.height = vulSize;
      vulDivs[seat].style.lineHeight = vulSize + 'px';
      vulDivs[seat].style.top = (seat === 2)
        ? vTop
        : vTop + 2 * vulMargin + vulSize + vulInnerDiv.clientHeight + 2 * vulBorder - !fireFox;
    }
  }
}

// ─────────────────────────────────────────────────────────────
function manageHandBackground(seatMin, seatMax) {
  for (var seat = seatMin; seat <= seatMax; seat++) {
    handDivs[seat].style.background = (seat === dummy) ? '#989898' : '#CBCBCB';
  }
}

function manageVul() {
  for (var seat = 0; seat < 4; seat++) {
    if ((seat % 2 === 1 && ewVul) || (seat % 2 === 0 && nsVul)) {
      auctionHeadingCells[seat].style.background = '#CB0000';
      auctionHeadingCells[seat].style.color = '#FFFFFF';
      vulDivs[seat].style.background = '#CB0000';
      vulDivs[seat].style.color = '#FFFFFF';
    } else {
      auctionHeadingCells[seat].style.background = '#FFFFFF';
      auctionHeadingCells[seat].style.color = '#000000';
      vulDivs[seat].style.background = '#FFFFFF';
      vulDivs[seat].style.color = '#000000';
    }
  }
  auctionHeading.rows[0].cells[4].style.background =
    auctionHeading.rows[0].cells[3].style.background;
  manageInfoDiv();
}

function manageWhosTurn() {
  for (var seat = 0; seat < 4; seat++) {
    if (!handShowing[seat]) continue;
    nameBars[seat].style.backgroundColor = '#FFFFFF';
  }
}

// ─────────────────────────────────────────────────────────────
// Card / suit helpers
// ─────────────────────────────────────────────────────────────
function getCardChar(card) {
  return (card === 8) ? '10' : cardchars.charAt(card);
}

function getSuitOrder(suitOrder) {
  return [0, 1, 2, 3][suitOrder];
}

function getSuitColor(suit) {
  return (suit === 1 || suit === 2) ? '#CB0000' : '#000000';
}

function isHandShowing(seat) {
  return handShowing[seat];
}

// ─────────────────────────────────────────────────────────────
// Build the DOM structure for the hand display
// ─────────────────────────────────────────────────────────────
function createHandTables() {
  scrollBarWidth = getScrollBarWidth();
  var theParent = document.getElementById('theDiv');

  disableSelection(document.getElementById('buttonDiv'));

  for (var seat = 0; seat < 4; seat++) {
    var hand = document.createElement('div');
    disableSelection(hand);
    hand.className = 'handDivStyle';
    handDivs[seat] = hand;
    theParent.appendChild(hand);

    var nameBar = document.createElement('div');
    disableSelection(nameBar);
    nameBar.className = 'nameRowDivStyle';
    nameBar.style.position = 'absolute';
    nameBar.style.border = '1px solid white';
    nameBar.style.whiteSpace = 'nowrap';

    var nameInitial = document.createElement('div');
    nameInitial.className = 'nameInitialDivStyle';
    var nameText = document.createElement('div');
    nameText.className = 'nameTextDivStyle';

    nameInitial.innerHTML = seats[seat].charAt(0);
    nameBar.appendChild(nameInitial);
    nameBar.appendChild(nameText);
    theParent.appendChild(nameBar);

    nameBars[seat] = nameBar;
    nameInitials[seat] = nameInitial;
    nameTexts[seat] = nameText;

    suitRows[seat] = new Array(4);
    suitSymbols[seat] = new Array(4);
    suitHoldings[seat] = new Array(4);
    cardDivs[seat] = new Array(4);

    for (var suit = 0; suit < 4; suit++) {
      suitRows[seat][suit] = document.createElement('div');
      suitRows[seat][suit].className = 'suitRowDivStyle';
      suitSymbols[seat][suit] = document.createElement('div');
      suitSymbols[seat][suit].className = 'suitSymbolDivStyle';
      suitHoldings[seat][suit] = document.createElement('div');
      suitHoldings[seat][suit].className = 'suitHoldingDivStyle';
      suitSymbols[seat][suit].innerHTML = suitHTMLs[suit];

      suitRows[seat][suit].appendChild(suitSymbols[seat][suit]);
      suitRows[seat][suit].appendChild(suitHoldings[seat][suit]);
      hand.appendChild(suitRows[seat][suit]);

      cardDivs[seat][suit] = new Array(13);
    }

    var trickCard = document.createElement('div');
    disableSelection(trickCard);
    trickCard.className = 'trickCardStyle';
    theParent.appendChild(trickCard);
    trickDivs[seat] = trickCard;

    var vulDiv = document.createElement('div');
    disableSelection(vulDiv);
    vulDiv.className = 'vulDivStyle';
    theParent.appendChild(vulDiv);
    vulDivs[seat] = vulDiv;
  }

  vulInnerDiv = document.createElement('div');
  disableSelection(vulInnerDiv);
  vulInnerDiv.className = 'vulInnerDivStyle';
  theParent.appendChild(vulInnerDiv);

  // Auction heading
  auctionHeadingDiv = document.createElement('div');
  disableSelection(auctionHeadingDiv);
  auctionHeadingDiv.className = 'auctionTableDivStyle';

  auctionHeading = document.createElement('table');
  auctionHeading.cellSpacing = 0;
  auctionHeading.cellPadding = 0;

  var headingRow = auctionHeading.insertRow(0);
  var s = 1;
  for (var i = 0; i < 4; i++) {
    auctionHeadingCells[s] = headingRow.insertCell(i);
    auctionHeadingCells[s].align = 'center';
    auctionHeadingCells[s].style.width = '25%';
    auctionHeadingCells[s].innerHTML = seats[s].charAt(0);
    s++;
    if (s === 4) s = 0;
  }
  headingRow.insertCell(4).style.width = '0%';

  theParent.appendChild(auctionHeadingDiv);
  auctionHeadingDiv.appendChild(auctionHeading);

  // Auction body
  auctionTableDiv = document.createElement('div');
  disableSelection(auctionTableDiv);
  auctionTableDiv.className = 'auctionTableDivStyle';
  auctionTableDiv.onscroll = function () { alertedCall = -1; manageAlertDiv(); };
  theParent.appendChild(auctionTableDiv);

  auctionTable = document.createElement('table');
  auctionTable.cellSpacing = 0;
  auctionTable.cellPadding = 0;
  auctionTableDiv.appendChild(auctionTable);

  // Tricks
  tricksDiv = document.createElement('div');
  disableSelection(tricksDiv);
  tricksDiv.className = 'auctionTableDivStyle';
  theParent.appendChild(tricksDiv);
  tricksDivLeft = document.createElement('div');
  disableSelection(tricksDivLeft);
  tricksDivLeft.className = 'vulDivStyle';
  tricksDiv.appendChild(tricksDivLeft);
  tricksDivRight = document.createElement('div');
  disableSelection(tricksDivRight);
  tricksDivRight.className = 'vulDivStyle';
  tricksDiv.appendChild(tricksDivRight);

  // Score (not visible on summary screen but referenced)
  scoreDiv = document.createElement('div');
  disableSelection(scoreDiv);
  scoreDiv.className = 'auctionTableDivStyle';
  otherTableDiv = document.createElement('div');
  otherTableDiv.className = 'teamDivStyle';
  scoreDiv.appendChild(otherTableDiv);
  nsTeamDiv = document.createElement('div');
  nsTeamDiv.className = 'teamDivStyle';
  scoreDiv.appendChild(nsTeamDiv);
  ewTeamDiv = document.createElement('div');
  ewTeamDiv.className = 'teamDivStyle';
  scoreDiv.appendChild(ewTeamDiv);
  nsScoreDiv = document.createElement('div');
  nsScoreDiv.className = 'scoreDivStyle';
  scoreDiv.appendChild(nsScoreDiv);
  ewScoreDiv = document.createElement('div');
  ewScoreDiv.className = 'scoreDivStyle';
  scoreDiv.appendChild(ewScoreDiv);
  theParent.appendChild(scoreDiv);

  // Announce (not used on summary screen)
  announceDiv = document.createElement('div');
  disableSelection(announceDiv);
  announceDiv.className = 'announceDivStyle';
  announceDiv.style.visibility = 'hidden';
  theParent.appendChild(announceDiv);

  // annotDiv is not present in summary.html – leave as null
  annotDiv = document.getElementById('annotDiv');

  // Alert tooltip for auction explanations
  alertDiv = document.createElement('div');
  disableSelection(alertDiv);
  alertDiv.className = 'alertDivStyle';
  theParent.appendChild(alertDiv);

  // Minimal menu table (referenced in respondToResize)
  menuDiv = document.createElement('div');
  menuDiv.className = 'menuDivStyle';
  menuTable = document.createElement('table');
  menuDiv.appendChild(menuTable);
  document.body.appendChild(menuDiv);

  // Loading overlay
  blockDiv = document.createElement('div');
  disableSelection(blockDiv);
  blockDiv.className = 'blockDivStyle';
  blockDiv.style.backgroundColor = '#FFFFFF';
  theParent.appendChild(blockDiv);

  statusDiv = document.createElement('div');
  disableSelection(statusDiv);
  statusDiv.className = 'statusDivStyle';
  blockDiv.appendChild(statusDiv);
}

// ─────────────────────────────────────────────────────────────
// Card divs – on the summary screen fastVersion is always true
// so we just set the flag and skip creating individual card divs.
// populateHands() uses innerHTML directly in fast mode.
// ─────────────────────────────────────────────────────────────
function createCardDivs() {
  if (cardDivsCreated) return;
  cardDivsCreated = true;
  // fastVersion = true, so no individual divs needed
}

// ─────────────────────────────────────────────────────────────
// Auction table rows
// ─────────────────────────────────────────────────────────────
function createAuctionRow() {
  var rowIndex = auctionTable.rows ? auctionTable.rows.length : 0;
  var newRow = auctionTable.insertRow(rowIndex);
  for (var i = 0; i < 5; i++) {
    var cell = newRow.insertCell(i);
    cell.align = 'center';
    cell.style.width = (i < 4) ? '25%' : '0%';
  }
}

function clearAuction() {
  for (var i = auctionTable.rows.length - 1; i >= 0; i--) {
    auctionTable.deleteRow(i);
  }
  createAuctionRow();
  manageAuctionScrollBar();
}

// ─────────────────────────────────────────────────────────────
// Deck state reset
// ─────────────────────────────────────────────────────────────
function clearDeck() {
  for (var w = 0; w < 4; w++) {
    howManyCards[w] = 0;
    howManyCardsDealt[w] = 0;
    howManySuit[w] = new Array(4);
    howManySuitDealt[w] = new Array(4);
    howManyXs[w] = new Array(4);
    cardHighlighted[w] = new Array(13);
    userDealt[w] = new Array(13);
    for (var s = 0; s < 4; s++) {
      howManySuit[w][s] = 0;
      howManySuitDealt[w][s] = 0;
      howManyXs[w][s] = 0;
    }
    for (var c = 0; c < 13; c++) {
      cardHighlighted[w][c] = false;
      userDealt[w][c] = false;
    }
  }

  for (var s = 0; s < 4; s++) {
    deck[s] = new Array(13);
    for (var c = 0; c < 13; c++) deck[s][c] = -10;
  }

  for (var t = 0; t < 13; t++) {
    suitPlayed[t] = new Array(4);
    rankPlayed[t] = new Array(4);
    seatPlayed[t] = new Array(4);
    cardAnnotation[t] = [null, null, null, null];
    cardAnnotType[t] = [null, null, null, null];
    trickWinner[t] = -1;
    for (var it = 0; it < 4; it++) {
      suitPlayed[t][it] = rankPlayed[t][it] = seatPlayed[t][it] = -1;
    }
  }

  populateHands(0, 3, 0, 3);
  clearAuction();
  boardNum = 0;
  dealer = -1;
  nsVul = false;
  ewVul = false;
  trick = -1;
  inTrick = 3;
  playSeqPoint = 0;
  playSeqMax = -1;
  bidSeqPoint = -1;
  bidSeqMax = -1;
  lastBidder = -1;
  contractLevel = -1;
  nsTricks = 0;
  ewTricks = 0;
  tricksClaimed = -1;
  alertedCall = -1;
  lastLevelBid = -1;
  lastStrainBid = -1;
  doubled = 0;
  passes = -1;
  trump = -1;
  dummy = -1;
  declarer = -1;
  whosTurn = -1;
  claimShowing = false;
  hasAnnotations = false;
  introAnnotation = null;
  callExplanation[0] = '';

  clearTrickCards(0, 3);
  auctionTableDiv.style.visibility = 'hidden';
  auctionHeadingDiv.style.visibility = 'hidden';

  manageWhosTurn();
  manageHandBackground(0, 3);
  manageVul();
  manageTricksDiv();
  manageAlertDiv();

  disableButton('play', false);
  disableButton('next', true);
}

// ─────────────────────────────────────────────────────────────
// Deal a card to a seat
// ─────────────────────────────────────────────────────────────
function dealCardToPlayer(suit, card, seat) {
  if (deck[suit][card] === -10) {
    deck[suit][card] = seat;
    howManyCards[seat]++;
    howManyCardsDealt[seat]++;
    howManySuit[seat][suit]++;
    howManySuitDealt[seat][suit]++;
  }
}

// ─────────────────────────────────────────────────────────────
// Button helpers
// ─────────────────────────────────────────────────────────────
function removeButton(buttonID) {
  var buttonTD = document.getElementById('buttonDiv');
  var button = document.getElementById(buttonID);
  if (button && button.parentNode === buttonTD) buttonTD.removeChild(button);
}

function disableButton(which, disable) {
  var ids = {
    new: 'newButton', shuffle: 'shuffleButton', next: 'nextButton',
    undo: 'undoButton', rewind: 'rewindButton', play: 'playButton'
  };
  var button = document.getElementById(ids[which]);
  if (button) button.disabled = disable;
}

// ─────────────────────────────────────────────────────────────
// Card resizing (no-op in fast mode)
// ─────────────────────────────────────────────────────────────
function resizeCards(seat, suit) {
  // fastVersion = true, individual card divs do not exist
}

// ─────────────────────────────────────────────────────────────
// Populate the hand display with card text
// ─────────────────────────────────────────────────────────────
function populateHands(seatMin, seatMax, suitMin, suitMax) {
  if (!cardDivsCreated) return;

  for (var seat = seatMin; seat <= seatMax; seat++) {
    for (var suitOrder = suitMin; suitOrder <= suitMax; suitOrder++) {
      var suit = getSuitOrder(suitOrder);
      var holding = '';

      for (var card = 12; card >= 0; card--) {
        var played = (deck[suit][card] === seat - 4);
        if (deck[suit][card] === seat || (showPlayedCards && played)) {
          if (played) holding += "<font color='808080'>";
          else holding += "<font color='000000'>";
          holding += getCardChar(card) + '</font>';
        }
      }

      for (var x = 0; x < howManyXs[seat][suit]; x++) holding += 'x';

      suitHoldings[seat][suit].innerHTML = holding;
    }
  }
}

function getHandWidth(seat) {
  return handWidth;
}

// ─────────────────────────────────────────────────────────────
// Trick cards (centre of compass)
// ─────────────────────────────────────────────────────────────
function clearTrickCards(seatMin, seatMax) {
  for (var seat = seatMin; seat <= seatMax; seat++) {
    trickDivs[seat].style.visibility = 'hidden';
  }
}

function showAllTrickCards() {
  if (trick < 0) return;
  for (var it = 0; it <= inTrick; it++) {
    showTrickCard(seatPlayed[trick][it], suitPlayed[trick][it], rankPlayed[trick][it]);
  }
}

function showTrickCard(seat, suit, rank) {
  if (suit < 0 || rank < 0) return;
  var rankShow = getCardChar(rank);
  trickDivs[seat].innerHTML = suitHTMLs[suit] + "<font color='000000'>" + rankShow + '</font>';
  trickDivs[seat].style.visibility = 'visible';
}

// ─────────────────────────────────────────────────────────────
// Alert / explanation tooltip for auction bids
// ─────────────────────────────────────────────────────────────
function bspToAuctionRow(bsp) {
  var fromWest = dealer - 1;
  if (fromWest < 0) fromWest = 3;
  return Math.floor((bsp + fromWest) / 4);
}

function bspToAuctionCol(bsp) {
  var fromWest = dealer - 1;
  if (fromWest < 0) fromWest = 3;
  return (bsp + fromWest) % 4;
}

function explainCall(explain, bsp) {
  callExplanation[bsp] = explain;
  var row = bspToAuctionRow(bsp);
  var col = bspToAuctionCol(bsp);
  if (explain && explain !== '') {
    auctionTable.rows[row].cells[col].style.background = highlightColor;
    auctionTable.rows[row].cells[col].onclick = (function (b) {
      return function () { auctionCellClicked(b); };
    }(bsp));
  } else {
    auctionTable.rows[row].cells[col].style.background = '#99CCCC';
  }
}

function manageAlertDiv() {
  if (alertedCall >= 0) {
    var row = bspToAuctionRow(alertedCall);
    var col = bspToAuctionCol(alertedCall);
    var cell = auctionTable.rows[row].cells[col];
    alertDiv.innerHTML = insertSuitHTML(callExplanation[alertedCall]);
    alertDiv.style.left = Math.max(
      margin + (1 - fireFox),
      getX(cell) + cell.clientWidth - alertDiv.clientWidth + 2 * fireFox
    );
    alertDiv.style.top = Math.max(
      getY(auctionHeadingDiv) + auctionHeadingDiv.clientHeight - alertDiv.clientHeight + 1,
      getY(cell) - alertDiv.clientHeight + 1
    );
    alertDiv.style.visibility = 'visible';
  } else {
    alertDiv.style.visibility = 'hidden';
  }
}

function auctionCellClicked(bsp) {
  alertedCall = (callExplanation[bsp] && alertedCall !== bsp) ? bsp : -1;
  manageAlertDiv();
}

// ─────────────────────────────────────────────────────────────
// Bidding logic
// ─────────────────────────────────────────────────────────────
function allowDouble() {
  if (doubled || lastBidder < 0) return false;
  return (whosTurn % 2 !== lastBidder % 2);
}

function allowRedouble() {
  if (doubled !== 2 || lastBidder < 0) return false;
  return (whosTurn % 2 === lastBidder % 2);
}

function setDeclarer() {
  for (var bsp = 0; bsp <= bidSeqPoint; bsp++) {
    if (levelBid[bsp] > 0 && strainBid[bsp] === trump && seatBid[bsp] % 2 === lastBidder % 2) {
      declarer = seatBid[bsp];
      break;
    }
  }
}

function manageBiddingQuestionMark() {
  // Not needed on summary screen
}

function makeCall(call) {
  if (call.length < 1 || passes === 3 || dealer === -1) return false;

  if (call.toUpperCase() === 'X') call = 'D';
  if (call.toUpperCase() === 'XX') call = 'R';

  var level = -1, strain = -1;

  if (call.length === 1) {
    strain = callchars.indexOf(call.charAt(0).toUpperCase());
    if (strain >= 0) level = 0;
  }
  if (call.length === 2) {
    level = parseInt(call.charAt(0));
    strain = suitchars.indexOf(call.charAt(1).toUpperCase());
  }

  if (level < 0 || strain < 0) return false;
  if (level === 0 && strain === 1 && !allowDouble()) return false;
  if (level === 0 && strain === 2 && !allowRedouble()) return false;
  if (level > 0 && 10 * level + strain <= 10 * lastLevelBid + lastStrainBid) return false;

  bidSeqPoint++;
  if (bidSeqPoint > bidSeqMax) bidSeqMax = bidSeqPoint;

  bidSequence[bidSeqPoint] = call;
  levelBid[bidSeqPoint] = level;
  strainBid[bidSeqPoint] = strain;
  seatBid[bidSeqPoint] = whosTurn;
  whosTurn++;
  if (whosTurn === 4) whosTurn = 0;

  var row = bspToAuctionRow(bidSeqPoint);
  var col = bspToAuctionCol(bidSeqPoint);

  if (auctionTable.rows.length < row + 1) createAuctionRow();

  auctionTable.rows[row].cells[col].innerHTML = (level === 0)
    ? calls[strain]
    : "<font color='000000'>" + level + '</font>' + suitHTMLs[strain];

  explainCall('', bidSeqPoint);
  auctionTable.rows[row].cells[col].style.visibility = 'visible';

  if (level === 0 && strain === 0) {
    passes++;
    if (passes === 3) {
      trump = lastStrainBid;
      contractLevel = lastLevelBid;
      setDeclarer();
      whosTurn = declarer + 1;
      if (whosTurn === 4) whosTurn = 0;
    }
  } else if (level === 0) {
    doubled = strain * 2;
    passes = 0;
  } else {
    lastLevelBid = levelBid[bidSeqPoint];
    lastStrainBid = strainBid[bidSeqPoint];
    lastBidder = seatBid[bidSeqPoint];
    doubled = 0;
    passes = 0;
  }

  manageWhosTurn();
  manageAuctionScrollBar();
  auctionTableDiv.scrollTop = auctionTableDiv.scrollHeight;

  return true;
}

// ─────────────────────────────────────────────────────────────
// Navigation – Replay button
// ─────────────────────────────────────────────────────────────
function play() {
  window.location.href = htmlPlayLoc + '?' + getQueryString();
}

function getQueryString() {
  var url = window.location.href;
  return url.split('?')[1] || '';
}

// ─────────────────────────────────────────────────────────────
// Advance bidding to end position (called after loading LIN)
// ─────────────────────────────────────────────────────────────
function next() {
  while (bidSeqPoint < bidSeqMax && passes < 3) {
    var explain = callExplanation[bidSeqPoint + 1];
    var retVal = makeCall(bidSequence[bidSeqPoint + 1]);
    if (retVal) {
      explainCall(explain, bidSeqPoint);
    } else {
      break;
    }
  }
}

// ─────────────────────────────────────────────────────────────
// Navigation – Next Hand button
// ─────────────────────────────────────────────────────────────
function nextHand() {
  var match = currentId.match(/Group(\d+)Deal(\d+)/);
  if (!match) { console.error('Invalid ID format'); return; }

  var groupNumber = match[1];
  var dealNumber = parseInt(match[2], 10) + 1;
  var newId = 'Group' + groupNumber + 'Deal' + dealNumber;

  if (!groupData[groupNumber]) loadGroupData();

  if (groupData[groupNumber]) {
    var linkData = groupData[groupNumber].find(function (item) { return item.id === newId; });
    if (linkData) {
      window.location.href = htmlLoc + '?' + linkData.query;
    } else {
      console.error('Link data not found for ID:', newId);
    }
  } else {
    console.error('Data for Group', groupNumber, 'not found');
  }
}

function showNextHandSummaryOnly() {
  if (!currentId) { console.error('currentId is not set'); return; }

  var match = currentId.match(/Group(\d+)Deal(\d+)/);
  if (!match) { console.error('Invalid currentId format', currentId); return; }

  var groupNumber = match[1];
  var dealNumber = parseInt(match[2], 10) + 1;
  var newId = 'Group' + groupNumber + 'Deal' + dealNumber;

  if (!groupData[groupNumber]) loadGroupData();

  if (groupData[groupNumber]) {
    var linkData = groupData[groupNumber].find(function (item) { return item.id === newId; });
    if (linkData) {
      var linParam = new URLSearchParams(linkData.query).get('lin');
      if (linParam) {
        processLinFile(linParam, true);
      } else {
        console.warn('LIN string not found in query for', newId);
      }
      currentId = newId;
      updateTextContainer();
      respondToResize();
      drawHandsBox();
    } else {
      console.warn('No further hand found for', newId);
    }
  } else {
    console.error('Group data not found for group', groupNumber);
  }
}

// ─────────────────────────────────────────────────────────────
// Deal parsing
// ─────────────────────────────────────────────────────────────
function fillInFourthHand() {
  var num13 = 0, not13 = -1;
  for (var seat = 0; seat < 4; seat++) {
    if (howManyCardsDealt[seat] === 13) num13++;
    else not13 = seat;
  }
  if (num13 === 3 && not13 >= 0) {
    for (var suit = 0; suit < 4; suit++) {
      for (var card = 0; card < 13; card++) {
        if (deck[suit][card] === -10) dealCardToPlayer(suit, card, not13);
      }
    }
    return true;
  }
  return false;
}

function deal(dealString) {
  if (!dealString || dealString.length === 0) return false;

  clearDeck();

  var seat = 0, suit = -1, card = -1, p = 1;

  while (p < dealString.length) {
    var ch = dealString.charAt(p).toUpperCase();

    if (ch === ',') { seat++; if (seat > 3) return false; suit = -1; card = -1; }

    var st = suitchars.indexOf(ch);
    if (st >= 0) suit = st;

    if (ch === 'X') {
      if (suit < 0) return false;
      if (howManyCardsDealt[seat] < 13) {
        howManyXs[seat][suit]++;
        howManyCards[seat]++;
        howManyCardsDealt[seat]++;
        howManySuit[seat][suit]++;
        howManySuitDealt[seat][suit]++;
      }
    } else {
      card = (ch === '1') ? 8 : cardchars.indexOf(ch);
      if (card >= 0) {
        if (suit < 0) return false;
        dealCardToPlayer(suit, card, seat);
      }
    }
    p++;
  }

  fillInFourthHand();
  populateHands(0, 3, 0, 3);
  return true;
}

function setVul(vul) {
  if (!vul || !vul.length) return false;
  var vChar = vul.charAt(0).toUpperCase();
  nsVul = (vChar === 'N' || vChar === 'B');
  ewVul = (vChar === 'E' || vChar === 'B');
  manageVul();
  return true;
}

function setDealer(direction) {
  var seat = interpretSeatString(direction);
  if (seat >= 0) {
    dealer = seat;
    whosTurn = seat;
    manageWhosTurn();
    manageInfoDiv();
    auctionTableDiv.style.visibility = 'visible';
    auctionHeadingDiv.style.visibility = 'visible';
    return true;
  }
  return false;
}

function setPlayerName(direction, name) {
  var seat = interpretSeatString(direction);
  if (seat >= 0) {
    if (!name || !name.length) name = seats[seat];
    if (name.charAt(0) === '~') name = 'Robot';
    nameTexts[seat].innerHTML = name;
  }
  return false;
}

function clearPlayerNames() {
  for (var seat = 0; seat < 4; seat++) setPlayerName(seats[seat], seats[seat]);
}

function processPlayerNames(param) {
  var startPoint = -1, endPoint, seat, room;
  for (room = 0; room < 2; room++) {
    for (seat = 0; seat < 4; seat++) {
      endPoint = param.indexOf(',', startPoint + 1);
      if (endPoint < 0) endPoint = param.length;
      if (room === 0) {
        setPlayerName(seats[seat], decodePlayerName(param.substring(startPoint + 1, endPoint)));
      }
      startPoint = endPoint;
    }
  }
}

function encodePlayerName(str) {
  return str.replace(/,/g, '%COMMA%').replace(/\|/g, '%PIPE%');
}

function decodePlayerName(str) {
  return str.replace(/%COMMA%/g, ',').replace(/%PIPE%/g, '|');
}

function setBoardNumber(num) {
  boardNum = parseInt(num);
  manageInfoDiv();
}

function setGroupNumber(num) {
  groupNum = parseInt(num);
}

function setCurrentId() {
  currentId = 'Group' + groupNum.toString() + 'Deal' + boardNum.toString();
}

// ─────────────────────────────────────────────────────────────
// Interpretation helpers
// ─────────────────────────────────────────────────────────────
function interpretSuitChar(suit) {
  for (var s = 0; s < 5; s++) {
    if (suit.toUpperCase() === suitchars.charAt(s)) return s;
  }
  return -1;
}

function interpretSeatString(direction) {
  if (!direction || !direction.length) return -1;
  for (var seat = 0; seat < 4; seat++) {
    if (direction.charAt(0).toUpperCase() === seats[seat].charAt(0).toUpperCase()) return seat;
  }
  return -1;
}

function insertSuitHTML(msg) {
  for (var suit = 0; suit < 4; suit++) {
    var pattern = new RegExp('!' + suits[suit].charAt(0), 'gi');
    msg = msg.replace(pattern, suitHTMLs[suit]);
  }
  return msg;
}

// ─────────────────────────────────────────────────────────────
// Bidding sequence parsing (from LIN mb| tokens)
// ─────────────────────────────────────────────────────────────
function processBidding(bidding) {
  var i = 0;
  while (i < bidding.length) {
    var c = bidding.charAt(i).toUpperCase();
    var len = 0;

    if (c === '-') { i++; continue; }
    if (c === 'P' || c === 'D' || c === 'R' || c === '?') {
      len = 1;
    } else if (c === 'X') {
      len = (i < bidding.length - 1 && bidding.charAt(i + 1).toUpperCase() === 'X') ? 2 : 1;
    } else if (c >= '1' && c <= '7') {
      len = 2;
    }
    if (len === 0) break;

    callAnnotation[bidSeqPoint + 1] = null;
    callExplanation[bidSeqPoint + 1] = '';
    bidSequence[bidSeqPoint + 1] = bidding.substring(i, i + len);
    bidSeqMax = bidSeqPoint + 1;
    bidSeqPoint++;

    if (i + len < bidding.length && bidding.charAt(i + len) === '!') len++;
    i += len;
  }
}

// ─────────────────────────────────────────────────────────────
// LIN command processor
// ─────────────────────────────────────────────────────────────
function processLinCommand(command, param) {
  switch (command) {
    case 'DT': setDisplayType(param); break;
    case 'SV': setVul(param); break;
    case 'MD':
      deal(param);
      setDealer(seats[parseInt(param.charAt(0)) - 1]);
      break;
    case 'MB': processBidding(param); break;
    case 'PC':
      playSequence[playSeqPoint] = param;
      playSeqMax = playSeqPoint;
      playSeqPoint++;
      break;
    case 'AN': callExplanation[bidSeqPoint] = param; break;
    case 'AH':
      setBoardNumber(parseInt(param.substring(5)));
      setCurrentId();
      break;
    case 'RH': setGroupNumber(parseInt(param.substring(5))); break;
    case 'PN': processPlayerNames(param); break;
    case 'MC': tricksClaimed = parseInt(param); break;
    // NT/AT annotations are stored but not displayed on summary screen
    case 'NT': hasAnnotations = true; break;
    case 'AT': hasAnnotations = true; break;
  }
}

// ─────────────────────────────────────────────────────────────
// LIN file parser
// ─────────────────────────────────────────────────────────────
function processLinFile(lin) {
  clearDeck();
  clearPlayerNames();

  var startIndex = 0;
  while (startIndex < lin.length) {
    var openPipeIndex = lin.indexOf('|', startIndex);
    if (openPipeIndex < 2) break;
    var closePipeIndex = lin.indexOf('|', openPipeIndex + 1);
    if (closePipeIndex < 0) break;

    var command = lin.substring(openPipeIndex - 2, openPipeIndex).toUpperCase();
    var param = lin.substring(openPipeIndex + 1, closePipeIndex);

    processLinCommand(command, param);
    startIndex = closePipeIndex + 1;
  }

  playSeqPoint = 0;
  bidSeqPoint = -1;

  // Advance auction to end position
  if (!endPosition()) next();

  // In end-position mode set declarer / trump from displayType suffix
  if (endPosition() && displayType.length > 1) {
    var level = parseInt(displayType.charAt(1));
    if (level > 0 && level < 8 && displayType.length === 4) {
      contractLevel = level;
      trump = suitchars.indexOf(displayType.charAt(2).toUpperCase());
      declarer = interpretSeatString(displayType.charAt(3));
      whosTurn = declarer + 1;
      if (whosTurn > 3) whosTurn = 0;
    } else {
      whosTurn = interpretSeatString(displayType.charAt(1));
      trump = (displayType.length > 2) ? suitchars.indexOf(displayType.charAt(2).toUpperCase()) : 4;
    }
  }

  if (numHandsShowing < 4) {
    fastVersion = true;
    picturesOfCards = false;
  }

  createCardDivs();
  populateHands(0, 3, 0, 3);
  showAll(true);
}

// ─────────────────────────────────────────────────────────────
// Fallback: load from individual URL params (v, d, b, s, w, n, e, a, p …)
// ─────────────────────────────────────────────────────────────
function loadParams(source) {
  var pVul = gup('v', source);
  var pDealer = gup('d', source);
  var pBoard = gup('b', source);
  var pSouth = gup('s', source);
  var pWest = gup('w', source);
  var pNorth = gup('n', source);
  var pEast = gup('e', source);
  var pIntro = safeDecode(gup('i', source));
  var pSouthName = safeDecode(gup('sn', source));
  var pWestName = safeDecode(gup('wn', source));
  var pNorthName = safeDecode(gup('nn', source));
  var pEastName = safeDecode(gup('en', source));
  var pAuction = safeDecode(gup('a', source));
  var pClaim = gup('c', source);
  var pPlay = safeDecode(gup('p', source));
  var pKibitz = gup('k', source);

  var dealerNum = interpretSeatString(pDealer) + 1;
  if (dealerNum <= 0) dealerNum = 3;

  var nt = pIntro.length ? 'nt|' + pIntro + '|' : '';
  var sk = 'sk|' + pKibitz + '|';
  var md = 'md|' + dealerNum + pSouth + ',' + pWest + ',' + pNorth + ',' + pEast + '|';
  var pn = 'pn|' + encodePlayerName(pSouthName) + ',' + encodePlayerName(pWestName) + ','
    + encodePlayerName(pNorthName) + ',' + encodePlayerName(pEastName) + '|';

  var dt = 'dt|';
  var hands = [pSouth, pWest, pNorth, pEast];
  for (var seat = 0; seat < 4; seat++) {
    if (hands[seat].length) dt += seats[seat].charAt(0);
  }
  if (pAuction.length && pAuction.charAt(0) === '-') {
    dt = 'dt|P' + pAuction.substring(1);
    pAuction = '';
  } else if ((dt.length >= 6 && pAuction.length) || pPlay.length > 0) {
    dt = 'dt|';
  } else if (pAuction.length) {
    dt += 'A';
  }
  dt += '|';

  var sv = 'sv|' + pVul + '|';
  var board = parseInt(pBoard);
  var ah = (board > 0) ? 'ah|Board ' + board + '|' : '';

  var bidding = '';
  var startPoint = 0, endPoint;
  while (startPoint < pAuction.length) {
    var ch = pAuction.charAt(startPoint);
    if (ch === '(') {
      endPoint = pAuction.indexOf(')', startPoint + 1);
      if (endPoint >= 0) { bidding += 'an|' + pAuction.substring(startPoint + 1, endPoint) + '|'; startPoint = endPoint + 1; continue; }
      break;
    }
    if (ch === '{') {
      endPoint = pAuction.indexOf('}', startPoint + 1);
      if (endPoint >= 0) {
        bidding += (pAuction.charAt(startPoint + 1) === '+')
          ? 'at|' + pAuction.substring(startPoint + 2, endPoint) + '|'
          : 'nt|' + pAuction.substring(startPoint + 1, endPoint) + '|';
        startPoint = endPoint + 1; continue;
      }
      break;
    }
    var lvl = parseInt(ch);
    endPoint = startPoint + (lvl > 0 ? 2 : 1);
    if (endPoint < pAuction.length && pAuction.charAt(endPoint) === '!') endPoint++;
    bidding += 'mb|' + pAuction.substring(startPoint, endPoint) + '|';
    startPoint = endPoint;
  }

  var play = '', mc = '';
  if (pPlay.length) {
    startPoint = 0;
    while (startPoint < pPlay.length) {
      ch = pPlay.charAt(startPoint);
      if (ch === '{') {
        endPoint = pPlay.indexOf('}', startPoint + 1);
        if (endPoint >= 0) {
          play += (pPlay.charAt(startPoint + 1) === '+')
            ? 'at|' + pPlay.substring(startPoint + 2, endPoint) + '|'
            : 'nt|' + pPlay.substring(startPoint + 1, endPoint) + '|';
          startPoint = endPoint + 1; continue;
        }
        break;
      }
      play += 'pc|' + pPlay.substring(startPoint, startPoint + 2) + '|';
      startPoint += 2;
    }
    if (pClaim.length) mc = 'mc|' + pClaim + '|';
  }

  processLinFile(dt + nt + md + sk + pn + sv + ah + bidding + play + mc);
}

// ─────────────────────────────────────────────────────────────
// Utility: read a URL query parameter
// ─────────────────────────────────────────────────────────────
function gup(name, source) {
  name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
  var regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
  var results = source ? regex.exec(source) : regex.exec(window.location.href);
  return (results == null) ? '' : results[1];
}

function safeDecode(param) {
  try {
    return decodeURIComponent(param);
  } catch (e) {
    return (e instanceof URIError) ? unescape(param) : param;
  }
}

// ─────────────────────────────────────────────────────────────
// Utility: DOM position helpers
// ─────────────────────────────────────────────────────────────
function getX(obj) {
  var curleft = 0;
  if (obj.offsetParent) {
    while (true) { curleft += obj.offsetLeft; if (!obj.offsetParent) break; obj = obj.offsetParent; }
  } else if (obj.x) { curleft += obj.x; }
  return curleft;
}

function getY(obj) {
  var curtop = 0;
  if (obj.offsetParent) {
    while (true) { curtop += obj.offsetTop - obj.scrollTop; if (!obj.offsetParent) break; obj = obj.offsetParent; }
  } else if (obj.y) { curtop += obj.y; }
  return curtop;
}

function getScrollBarWidth() {
  var inner = document.createElement('p');
  inner.style.width = '100%';
  inner.style.height = '200px';
  var outer = document.createElement('div');
  outer.style.cssText = 'position:absolute;top:0;left:0;visibility:hidden;width:200px;height:150px;overflow:hidden';
  outer.appendChild(inner);
  document.body.appendChild(outer);
  var w1 = inner.offsetWidth;
  outer.style.overflow = 'scroll';
  var w2 = inner.offsetWidth;
  if (w1 === w2) w2 = outer.clientWidth;
  document.body.removeChild(outer);
  return w1 - w2;
}

function disableSelection(target) {
  if (typeof target.onselectstart !== 'undefined') {
    target.onselectstart = function () { return false; };
  } else if (typeof target.style.MozUserSelect !== 'undefined') {
    target.style.MozUserSelect = 'none';
  } else {
    target.onmousedown = function () { return false; };
  }
  target.style.cursor = 'default';
}

// ─────────────────────────────────────────────────────────────
// Display-type helpers
// ─────────────────────────────────────────────────────────────
function getHandRows() {
  if (numHandsShowing < 2) return 1;
  if (numHandsShowing === 2) {
    if (handShowing[1] && handShowing[3] && !showAuction()) return 1;
    return 2;
  }
  return 3;
}

function getHandCols() {
  if (numHandsShowing < 2) return 1;
  if (numHandsShowing === 2) {
    if (handShowing[0] && handShowing[2] && !showAuction()) return 1;
    return 2;
  }
  return 3;
}

function showHand(seat) {
  if (showMovie() || endPosition()) return true;
  for (var i = 0; i < displayType.length; i++) {
    if (displayType.charAt(i) === seats[seat].charAt(0).toUpperCase()) return true;
  }
  return false;
}

function showMovie() { return displayType === ''; }
function auctionOnly() { return displayType === 'A'; }
function endPosition() { return displayType.charAt(0).toUpperCase() === 'P'; }

function showAuction() {
  return (displayType === '') || auctionOnly() || (displayType.indexOf('A') !== -1);
}

function showInfoDiv() { return showMovie(); }
function showTricksDiv() { return showMovie() || endPosition(); }
function showVul() { return true; }

function showButtonBar() {
  return mainDivShowing && (showMovie() || (endPosition() && playSeqMax >= 0));
}

function showAnnotations() { return false; } // no annotDiv on summary screen

function setDisplayType(param) {
  displayType = param.toUpperCase();
  numHandsShowing = 0;
  for (var seat = 0; seat < 4; seat++) {
    handShowing[seat] = showHand(seat);
    if (handShowing[seat]) numHandsShowing++;
  }
  if (numHandsShowing === 3) setDisplayType('NSEW');
}

// ─────────────────────────────────────────────────────────────
// Hands container border (yellow box drawn on canvas)
// ─────────────────────────────────────────────────────────────
function positionHandsContainer() {
  var container = document.getElementById('hands-container');
  if (!container) return;

  var minLeft = Math.min(xpos[0], xpos[1], xpos[2], xpos[3]);
  var minTop = Math.min(ypos[0], ypos[1], ypos[2], ypos[3]);
  var maxRight = Math.max(xpos[0] + handWidth, xpos[1] + handWidth, xpos[2] + handWidth, xpos[3] + handWidth);
  var maxBottom = Math.max(ypos[0] + handHeight, ypos[1] + handHeight, ypos[2] + handHeight, ypos[3] + handHeight);

  container.style.left = (minLeft - margin) + 'px';
  container.style.top = (minTop - margin / 2) + 'px';
  container.style.width = (maxRight - minLeft + 2 * margin) + 'px';
  container.style.height = (maxBottom - minTop + 2 * margin) + 'px';
}

function drawHandsBox() {
  var canvas = document.getElementById('boxCanvas');
  if (!canvas) return;
  var ctx = canvas.getContext('2d');

  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  var left = Math.min(xpos[0], xpos[1], xpos[2], xpos[3]);
  var top = Math.min(ypos[0], ypos[1], ypos[2], ypos[3]);
  var right = Math.max(xpos[0] + handWidth, xpos[1] + handWidth, xpos[2] + handWidth, xpos[3] + handWidth);
  var bottom = Math.max(ypos[0] + handHeight, ypos[1] + handHeight, ypos[2] + handHeight, ypos[3] + handHeight);

  var padding = 15;
  var topPadding = 25;
  var rightShift = isMobileLayout() ? 20 : 20;

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = '#ffce00';
  ctx.lineWidth = 4;
  ctx.strokeRect(
    left - padding + rightShift,
    top - padding + topPadding,
    right - left + padding * 2,
    bottom - top + padding * 2
  );
}

// ─────────────────────────────────────────────────────────────
// Button resize
// ─────────────────────────────────────────────────────────────
function resizeButtons() {
  var newWidth = handWidth * 0.116;
  var newHeight = handHeight * 0.17;

  document.querySelectorAll('.number').forEach(function (btn) {
    btn.style.marginRight = margin / 2000 + 'px';
    btn.style.width = newWidth + 'px';
    btn.style.height = suitHeight + 'px';
    btn.style.fontSize = suitHeight * 0.8 + 'px';
  });
  document.querySelectorAll('.suit').forEach(function (btn) {
    btn.style.marginRight = margin / 2000 + 'px';
    btn.style.width = newWidth * 1.4 + 'px';
    btn.style.height = suitHeight + 'px';
    btn.style.fontSize = suitHeight * 1.15 + 'px';
  });
}

// ─────────────────────────────────────────────────────────────
// documentLoaded – called from DOMContentLoaded
// ─────────────────────────────────────────────────────────────
function documentLoaded() {
  setTimeout('respondToResize()', 10);
}

// ─────────────────────────────────────────────────────────────
// Keyboard handler – stub (onkeydown wired in HTML)
// ─────────────────────────────────────────────────────────────
function handleKeyDown(event) {
  // No keyboard interaction needed on the summary screen
}

// ─────────────────────────────────────────────────────────────
// Error display
// ─────────────────────────────────────────────────────────────
function fatalError(message) {
  statusDiv.innerHTML = message;
  showAll(false);
}

// ─────────────────────────────────────────────────────────────
// Group navigation data
// ─────────────────────────────────────────────────────────────
function loadGroupData() {
  // Each group file defines a global like group11Data, group12Data, …
  var groups = [11, 12, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38];
  groups.forEach(function (g) {
    var varName = 'group' + g + 'Data';
    if (typeof window[varName] !== 'undefined') groupData[String(g)] = window[varName];
  });
}

// ─────────────────────────────────────────────────────────────
// Commentary text
// ─────────────────────────────────────────────────────────────
function loadGroupTextData() {
  if (typeof currentId !== 'string' || !currentId) {
    console.error('loadGroupTextData: currentId not set');
    return;
  }

  var match = currentId.match(/Group(\d+)/);
  if (!match) { console.error('loadGroupTextData: cannot determine group from', currentId); return; }

  var groupNum = match[1];
  var varName = 'group' + groupNum + 'DealText';

  if (typeof window[varName] !== 'undefined') {
    groupTextData[groupNum] = window[varName];
  } else {
    console.error('loadGroupTextData:', varName, 'is not defined');
    if (!groupTextData[groupNum]) groupTextData[groupNum] = {};
  }
}

function updateTextContainer() {
  var textContainer = document.getElementById('textContainer');
  if (!textContainer || !currentId) return;

  var match = currentId.match(/Group(\d+)Deal(\d+)/);
  if (!match) { console.error('updateTextContainer: invalid ID', currentId); return; }

  var groupNum = match[1];
  var boardNum = match[2];
  var dealPropName = 'Group' + groupNum + 'Deal' + boardNum;

  loadGroupTextData();

  if (groupTextData[groupNum] && groupTextData[groupNum].hasOwnProperty(dealPropName)) {
    var rawText = groupTextData[groupNum][dealPropName];

    var biddingMatch = rawText.match(/The Bidding([\s\S]*?)(?=The Play|$)/i);
    var playMatch = rawText.match(/The Play([\s\S]*)/i);

    function buildSection(title, sectionText) {
      var sentences = sectionText.replace(/\s+/g, ' ').trim()
        .split(/(?<=[.!?])\s+(?=[A-Z])/).filter(Boolean);
      var html = '<h3>' + title + '</h3>';
      for (var i = 0; i < sentences.length; i += 2) {
        var para = [sentences[i], sentences[i + 1]].filter(Boolean).join(' ').trim();
        if (para) html += '<p>' + para + '</p>';
      }
      return html;
    }

    var html = '';
    if (biddingMatch) html += buildSection('The Bidding', biddingMatch[1]);
    if (playMatch) html += buildSection('The Play', playMatch[1]);

    textContainer.innerHTML = html || rawText;
  } else {
    console.error('updateTextContainer: deal text not found for', dealPropName);
    textContainer.innerHTML = 'Deal text not available.';
  }
}

// ─────────────────────────────────────────────────────────────
// DOMContentLoaded – initialise page and wait for data files
// ─────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {

  function initializeDisplay() {
    if (typeof currentId !== 'string' || !currentId) {
      var el = document.getElementById('textContainer');
      if (el) el.innerHTML = 'Please select a deal.';
      return;
    }
    loadGroupTextData();
    updateTextContainer();
    respondToResize();
    drawHandsBox();
  }

  function waitForData() {
    var groupNum = null;
    if (typeof currentId === 'string' && currentId) {
      var m = currentId.match(/Group(\d+)/);
      if (m) groupNum = m[1];
    }

    if (!groupNum) {
      setTimeout(waitForData, 100);
      return;
    }

    var readyFlag = 'group' + groupNum + 'DealTextReady';
    if (typeof window[readyFlag] === 'boolean' && window[readyFlag] === true) {
      initializeDisplay();
    } else {
      setTimeout(waitForData, 100);
    }
  }

  if (typeof documentLoaded === 'function') {
    documentLoaded();
    setTimeout(waitForData, 50);
  }
});