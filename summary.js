const htmlPlayLoc = "handviewer.html";
const htmlBidLoc = "bidding.html";
const htmlSummLoc = "summary.html";
const htmlLoc = htmlBidLoc;

const groupData = {};
const groupTextData = {};
const urlParams = new URLSearchParams(window.location.search);
const mode = urlParams.get('mode'); // 'tester' if from BookletTester, otherwise null
document.getElementById('nextButton').onclick = function() {
    if (mode === 'tester') {
        showNextHandSummaryOnly();
    } else {
        nextHand();
    }
};
var fastVersion = false;
var fireFox = 0;
var linURL;
var mainDivShowing = false;
var availableHeight = 10;
var availableWidth = 10;
var totalWidth = 10;
var totalHeight = 10;
var scrollBarWidth;
var margin = 0;
var suitHeight = 10;
var handHeight = 50;
var handWidth = 50;
var nameHeight = 10;
var displayType = '';
var handShowing = new Array(4);
var numHandsShowing = 4;
var seatKibitzed = -1;
var wasKibitzed = -1;
var seatKibitzedSet = false;
var showPlayedCards = true;
var hideChat = false;
var chatFontSize = 1;
var suits = new Array('Club', 'Diamond', 'Heart', 'Spade');
var suitHTMLs = new Array(
  "<font color='000000'>&clubs;</font>",
  "<font color='CB0000'>&diams;</font>",
  "<font color='CB0000'>&hearts;</font>",
  "<font color='000000'>&spades;</font>",
  "<font color='000000'>NT</font>"
);
//var suitHTMLs=new Array("<font color='000000'><tt>&clubs;</tt></font>","<font color='CB0000'><tt>&diams;</tt></font>","<font color='CB0000'><tt>&hearts;</tt></font>","<font color='000000'><tt>&spades;</tt></font>","<font color='000000'>NT</font>");
//var suitHTMLs=new Array("<font color='000000'><tt>&#9827;</tt></font>","<font color='CB0000'><tt>&#9830;</tt></font>","<font color='CB0000'><tt>&#9829;</tt></font>","<font color='000000'><tt>&#9824;</tt></font>","<font color='000000'>NT</font>");
var suitForums = new Array('[CL]', '[DI]', '[HE]', '[SP]', 'NT');
var suitchars = 'CDHSN';
var callchars = 'PDR?';
var calls = ['P', 'X', 'XX', '?'];
var cardchars = '23456789TJQKA';
var seats = new Array('South', 'West', 'North', 'East');
var xpos = new Array(90, 10, 90, 170);
var ypos = new Array(170, 90, 10, 90);
var blockDiv;
var statusDiv;
var menuDiv;
var menuTable;
var navMenuDiv;
var navMenuTable;
var hasAnnotations = false;
var introAnnotation = null;
var annotDiv;
var auctionHeadingDiv;
var auctionHeading;
var auctionHeadingCells = new Array(5);
var auctionTableDiv;
var auctionTable;
var mouseOverName = -1;
var handDivs = new Array(4);
var nameBars = new Array(4);
var nameInitials = new Array(4);
var nameTexts = new Array(4);
var suitRows = new Array(4);
var suitSymbols = new Array(4);
var suitHoldings = new Array(4);
var cardDivs = new Array(4);
var cardDivsCreated = false;
var gibDivs = new Array(4);
var gibDivsShowing = false;
var gibThinking = false;
var vulDivs = new Array(4);
var vulInnerDiv;
var trickDivs = new Array(4);
var tricksDiv;
var tricksDivLeft;
var tricksDivRight;
var scoreDiv;
var otherTableDiv;
var nsTeamDiv;
var ewTeamDiv;
var nsScoreDiv;
var ewScoreDiv;
var announceDiv;
var announceDivCentered = false;
var announceTimer;
var alertDiv;
var alertedCall = -1;
var deck = new Array(4);
var howManyCards = new Array(4);
var howManyCardsDealt = new Array(4);
var howManySuit = new Array(4);
var howManySuitDealt = new Array(4);
var howManyXs = new Array(4);
var boardNum = 0;
var groupNum =0 ;
var currentId ;
var dealer = -1;
var nsVul;
var ewVul;
var whosTurn;
var levelBid = new Array();
var strainBid = new Array();
var seatBid = new Array();
var passes = -1;
var lastLevelBid;
var lastStrainBid;
var lastBidder;
var contractLevel;
var doubled;
var trump;
var declarer;
var dummy;
var playSequence = new Array(52);
var playSeqPoint;
var playSeqMax;
var wasPlaySequence = new Array(52);
var wasPlaySeqPoint;
var wasPlaySeqMax;
var wasTricksClaimed;
var trick;
var inTrick;
var bidSeqPoint;
var bidSeqMax;
var bidSequence = new Array();
var callExplanation = new Array();
var callAnnotation = new Array();
var callAnnotType = new Array();
var rankPlayed = new Array(13);
var suitPlayed = new Array(13);
var seatPlayed = new Array(13);
var trickWinner = new Array(13);
var cardAnnotation = new Array(13);
var cardAnnotType = new Array(13);
var nsTricks = 0;
var ewTricks = 0;
var tricksClaimed;
var claimShowing;
var trickTimer;
var settings;
var fontSize = 12;
var buttonFontSize = 12;
var buttonHeight = 20;
var connected = false;
var connectTimer;
var keepAliveTimer;
var heartBeatTimer;
var inBlast = false;
var queueID;
var tableID;
var myTableID;
var contextID = '';
var lessonID;
var lessonBoardNumber;
var mySeat = -1;
var playingClient = false;
var vugraphClient = false;
var vugraphSession;
var vugraphScoreReceived = false;
var scoreNS;
var scoreEW;
var teamNS;
var teamEW;
var scoreFormat;
var otherTableResult;
var highlightColor = '#FFCE00';
var team1Color = '#99CCCC';
var team2Color = '#CBCBCB';
var borderStyle = '1px solid black';
var isVugraphMatch;
var vugraphEvent;
var vugraphSegment;
var vugraphScoring;
var vugraphFirstBoard;
var vugraphLastBoard;
var vugraphFirstRealBoard;
var vugraphLastRealBoard;
var vugraphNumBoards;
var vugraphTeam1;
var vugraphTeam2;
var vugraphCarryover1;
var vugraphCarryover2;
var vugraphSegment1;
var vugraphSegment2;
var vugraphResults;
var vugraphDeclarer;
var vugraphRawScores;
var vugraphIMPs;
var vugraphMatchpoints;
var vugraphPlayers;
var vugraphPlayerNames;
var vugraphPairsSeatDivs = new Array(4);
var roomShowing = 0;
var boardShowing;
var scoreBoardDiv;
var scoreBoardTableDiv;
var scoreBoardTable;
var scoreBoardHeadingDiv;
var scoreBoardDivShowing = false;
var scoreBoardTitleDiv;
var scoreBoardTitleLine1Div;
var scoreBoardTitleLine2Div;
var scoreBoardTitleLine3Div;
var scoreBoardScoreTable;
var scoreBoardLogo;
var picturesOfCards = false;
var autoPlayNextCard = false;
var cardAnimationTimer;
var cardAnimationTime = 2000;
var cardAnimationStepTime = 20;
var cardAnimationStepsRemaining;
var cardAnimationPosX;
var cardAnimationPosY;
var cardAnimationStepDX;
var cardAnimationStepDY;
var cardImageDrifting = null;
var cardImageDiv = new Array(4);
var cardBackDiv = new Array(4);
var cardImageHeight = 0;
var cardImageWidth = 0;
var cardImageXOverlap = 0;
var trickCardImage = new Array(4);

var commentsEdit;
var commentsHeading;
var cardHighlighted = new Array(4);
var userDealt = new Array(4);
var editorWidthOffset = 0;
var editorType;
var isEditor = false;
var getSequence = false;
var getDeal = false;
var getDealer = false;
var keyboardSuit = -1;
var editorDiv;
var editorDivHeight = 0;
var editorHVLButton;
var editorNewButton;
var trickEndTimer = null;
var dealEndState = false;
var dealsInLesson = 4;
var firstBlast = false;
var getLessonContractPhase = 0;
var gameOverState = false;
var lessonStrain;
var leaderBoardDiv = null;
var leaderBoardTable;
var newGameButton = null;
var currentBid = 'xyz';
var expectedBid = ''; 
let validBidEntered = false; 
let selectedNumber = null;
var lastBid='';

var editorMenuDiv = document.getElementById('editorMenuDiv');
var biddingCheck = document.getElementById('bidding');
var dealerTD = document.getElementById('dealerTD');
var vulTD = document.getElementById('vulTD');
var hands = [
  document.getElementById('south'),
  document.getElementById('west'),
  document.getElementById('north'),
  document.getElementById('east'),
];
var dealers = [
  document.getElementById('sdeals'),
  document.getElementById('wdeals'),
  document.getElementById('ndeals'),
  document.getElementById('edeals'),
];
var vuls = [
  document.getElementById('none'),
  document.getElementById('both'),
  document.getElementById('ns'),
  document.getElementById('ew'),
];
var createButton = document.getElementById('createButton');
var editorMenuShowing = false;
var firstResize = true;
var grpDeal ;

var cardByCard = true;
var exploreLine = false;

var myHandler = {
  rcvMessage: function (message) {
    processV2Message(message);
  },
};

if (typeof window.innerHeight == 'number') {
  fireFox = 1;
  window.onresize = function () {
    respondToBodyResize();
  };
} else {
  document.body.onresize = function () {
    setTimeout('respondToBodyResize()', 10);
  };
}
var wantsFast = gup('f').toLowerCase();
if (wantsFast == 'y') {
  fastVersion = true;
  removeButton('gibButton');
}

var tbt = gup('tbt').toLowerCase();

if (tbt == 'y') {
  cardByCard = false;
}


tableID = gup('tableID');
if (tableID != '') {
  vugraphClient = true;
} else {
  lessonID = gup('lessonID');
  if (lessonID != '') {
    playingClient = true;
    vugraphClient = true;
    firstBlast = true;
  }
}

window.addEventListener('resize', function() {
  // Recalculate positions and sizes as needed
  respondToResize();
  // Redraw the box
  drawHandsBox();
});


if (gup('hc').toUpperCase() == 'Y') hideChat = true;

editorType = gup('editor').toUpperCase();
isEditor = editorType != '';
if (editorType != 'Y' && editorType != 'F') {
  displayType = editorType;
}
if (editorType) {
  editorMenuShowing = true;
}

setDisplayType(displayType);
createHandTables();
// clearDeck(false);

if (vugraphClient) {
  createCardDivs();
  vugraphSession = 'vg' + Math.random() * 100000;
  initVugraphSession();
  removeButton('newButton');
  removeButton('nextButton');
  removeButton('rewindButton');
  removeButton('undoButton');
  removeButton('shuffleButton');
  if (playingClient) {
    removeButton('gibButton');
    mySeat = 0;
    showPlayedCards = false;
    resetLessonScores();
    setPlayerName('S', 'Declarer');
    setPlayerName('W', 'LHO');
    setPlayerName('N', 'Dummy');
    setPlayerName('E', 'RHO');
  } else {
    removeButton('helpButton');
  }
} else if (isEditor) {
  createCardDivs();
  removeButton('optionsButton');
 
  var vulParam = gup('v');
  if (vulParam) {
    setVul(vulParam);
  }
  if (picturesOfCards) {
    togglePictures();
  }
  showEditorMenu(true);
} else {
  removeButton('newButton');
  removeButton('helpButton');
  linURL = gup('linurl');

  if (linURL != '') {
    loadFromURL('vugproxy.php?linurl=' + linURL);
  } else {
    linURL = gup('myhand');
    if (linURL != '') {
      loadFromURL('https://www.bridgebase.com/tools/mh.php?id=' + linURL);
    } else {
      linURL = gup('linlocal');
      if (linURL != '') {
        loadFromURL(linURL);
      } else {
        linURL = safeDecode(gup('lin'));
        if (linURL != '') processLinFile(linURL);
        else loadParams();
        grpDeal = currentId;
        if (picturesOfCards && displayType != '') {
          togglePictures();
        }
      }
    }
  }
}

function showAll(visible) {
  var div = document.getElementById('theDiv');
  var buttonDiv = document.getElementById('buttonDiv');

  mainDivShowing = visible;
  scoreBoardDivShowing = !visible;

  if (visible) {
    if (scoreBoardDiv) {
      scoreBoardDiv.style.visibility = 'hidden';
      div.style.background = '#006600';
    }
   
    statusDiv.style.visibility = 'hidden';
    blockDiv.style.visibility = 'hidden';
    buttonDiv.style.visibility = 'visible';

    if (editorDiv) {
      editorDiv.style.visibility = 'visible';
    }
  } else {
    statusDiv.style.visibility = 'visible';
    blockDiv.style.visibility = 'visible';
    buttonDiv.style.visibility = 'hidden';
    annotDiv.style.visibility = 'hidden';
 
    clearTrickCards(0, 3);
    if (editorDiv && isEditor) {
      editorDiv.style.visibility = 'hidden';
    }
  }
  showCardImages(visible);
  respondToResize();
}

function showNextHandSummaryOnly() {
  if (typeof clearAuction === "function") clearAuction()  
  if (!currentId) {
        console.error("currentId is not set");
        return;
    }
    const match = currentId.match(/Group(\d+)Deal(\d+)/);
    if (!match) {
        console.error("Invalid currentId format", currentId);
        return;
    }
    const groupNumber = match[1];
    let dealNumber = parseInt(match[2], 10);

    dealNumber += 1;
    const newId = `Group${groupNumber}Deal${dealNumber}`;

    if (!groupData[groupNumber]) {
        if (typeof loadGroupData === "function") loadGroupData();
    }

    if (groupData[groupNumber]) {
        const linkData = groupData[groupNumber].find(item => item.id === newId);
        if (linkData) {
            // Extract LIN string from the deal's query parameter
            const linParam = new URLSearchParams(linkData.query).get("lin");
            if (linParam) {
                processLinFile(linParam, true);
            } else {
                console.warn("LIN string not found in query for", newId);
            }
            currentId = newId;
            if (typeof updateTextContainer === "function") updateTextContainer();
            if (typeof respondToResize === "function") respondToResize();
            if (typeof drawHandsBox === "function") drawHandsBox();
        } else {
            console.warn("No further hand found for", newId);
        }
    } else {
        console.error("Group data not found for group", groupNumber);
    }
}







function showEditorMenu(visible) {
  editorMenuShowing = visible;
  if (editorMenuShowing) {
    showAll(false);
    editorMenuDiv.style.visibility = 'visible';
    statusDiv.innerHTML = 'Select the type of bridge diagram you want to create';
    manageStatusDiv();
  } else {
    if (editorMenuDiv) {
      editorMenuDiv.style.visibility = 'hidden';
    }
    showAll(true);
  }
  manageEditorAnnouncement();
  editorMenuBiddingChanged(false);
}

function respondToBodyResize(param) {
  //if (!fastVersion) {

  respondToResize();
  // }
}

function respondToResize() {
  var div = document.getElementById('theDiv');

  var wasTotalWidth = totalWidth;
  var wasTotalHeight = totalHeight;

  if (showAnnotations()) {
    atBottom = annotDiv.scrollTop + annotDiv.clientHeight + 10 >= annotDiv.scrollHeight;
  }

  


  var handRows = getHandRows();
  var handCols = getHandCols();

  if (isEditor) {
    handCols++;
  }

  if (typeof window.innerHeight == 'number') {
    availableHeight = window.innerHeight;
    availableWidth = window.innerWidth;
  } else {
    availableHeight = document.body.clientHeight;
    availableWidth = document.body.clientWidth;
  }

  if (firstResize) {
    firstResize = false;
    blockDiv.style.visibility = 'visible';
    blockDiv.style.width = availableWidth;
    blockDiv.style.height = availableHeight;
    return;
  }

  if (mainDivShowing) {
    blockDiv.style.visibility = 'hidden';
  }

  var maxWidthRatio;
  var maxHeightRatio;

  if (showAnnotations()) {
    maxWidthRatio = 6 / 5;
    maxHeightRatio = 5 / 4;
  } else {
    maxWidthRatio = 4 / 3;
    maxHeightRatio = 1;
  }
    totalHeight = availableHeight;
    totalWidth = availableWidth;

  if (totalWidth < 10) totalWidth = 10;
  if (totalHeight < 10) totalHeight = 10;

  blockDiv.style.width = totalWidth;
  blockDiv.style.height = availableHeight;
  var buttonDivHeight;
  var annotDivHeight;

 
    buttonDivHeight = Math.max(30, 0.07 * totalHeight);
    totalHeight -= buttonDivHeight;
 
  margin = Math.max(2, totalHeight / 35);

  if (showAnnotations()) {
    annotDivHeight = 0.2 * totalHeight;
    totalHeight *= 0.8;
  } else {
    annotDivHeight = 0;
  }

  totalHeight = Math.max(1, totalHeight);

  if (auctionOnly() && !isEditor) {
    handHeight = Math.max(1, totalHeight - 2 * margin);
    handWidth = Math.max(1, totalWidth - 2 * margin);
    suitHeight = handHeight / 5;
  } else {
    var margins = handCols + 1;
    if (isEditor) {
      margins++;
      if (numHandsShowing == 4) {
        handCols += 0.5;
      }
    }
    handWidth = Math.max(1, (totalWidth - margins * margin - fireFox * handCols * 2) / handCols);
    handHeight = Math.max(
      1,
      (totalHeight - (handRows + 1) * margin - fireFox * handCols * 2) / handRows
    );
    suitHeight = handHeight / 5;
  }

  if (picturesOfCards && playingClient && !showAuction()) {
    handWidth *= 4 / 3;
    handHeight *= 4 / 3;
    suitHeight *= 4 / 3;
  }
  //hands scaled here
  handWidth /= 3;
  handHeight /= 1.9;
  suitHeight /= 1.9;
  resizeButtons();
  cardImageWidth = handWidth / 4;
  cardImageHeight = handHeight / 4;

  cardImageHeight = 1.3 * cardImageWidth;
  cardImageXOverlap = cardImageWidth / 4;

  

  
  nameHeight = Math.floor(handHeight / 5);


    div.style.width = totalWidth;
    div.style.height = totalHeight;

  fontSize = handHeight / 6.5;


   

  var buttonDiv = document.getElementById('buttonDiv');

  

  buttonDiv.style.height = (buttonDivHeight/2) - 2 * fireFox;
  buttonDiv.style.width = totalWidth - (4 - isEditor) * fireFox - editorWidthOffset;

  if (showButtonBar()) {
    buttonDiv.style.top = totalHeight + annotDivHeight;
    buttonDiv.style.visibility = 'visible';
    if (editorWidthOffset) {
      buttonDiv.style.left = editorWidthOffset + 2 * fireFox;
    } else {
      buttonDiv.style.left = 0;
    }

    buttonHeight = Math.max(24, buttonDivHeight - 2 * margin);
    buttonFontSize = buttonHeight / 2;
    var pixels = margin;
    var gibButton = document.getElementById('gibButton');
    

    

    
    menuTable.style.fontSize = buttonFontSize;
    if (navMenuTable) {
      navMenuTable.style.fontSize = buttonFontSize;
    }
  } else {
    buttonDiv.style.top = 0;
    buttonDiv.style.visibility = 'hidden';
    menuTable.style.fontSize = (3 * fontSize) / 4;
  }

  for (seat = 0; seat < 4; seat++) {
    var table = handDivs[seat];

    if (!handShowing[seat]) {
      if (table.parentNode == div) {
        table.style.visibility = 'hidden';
      }
      if (nameBars[seat].parentNode == div) {
        nameBars[seat].style.visibility = 'hidden';
      }
      continue;
    }

    if (!picturesOfCards) {
      table.style.visibility = 'visible';
    }
    nameBars[seat].style.visibility = 'visible';

    table.style.width = getHandWidth(seat);
    table.style.height = handHeight;
    table.style.fontSize = fontSize;

    nameTexts[seat].style.left = nameInitials[seat].clientWidth;
    nameTexts[seat].style.top = 0;
    nameTexts[seat].style.paddingLeft = margin;

    for (suit = 0; suit < 4; suit++) {
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
//rework here
    // ypos is top
    // xpos is left
// South (seat 0)
xpos[0] = (totalWidth - (totalWidth/1.25));
ypos[0] = 2 * handHeight + (margin * 2.5) ;



// North (seat 2)
xpos[2] = xpos[0];
ypos[2] = margin;

// West (seat 1)
// xpos[1] = margin;
ypos[1] = ypos[2]+handHeight+margin;
xpos[1] = xpos[0] - handWidth - margin;

// East (seat 3)
xpos[3] = xpos[1]+(handWidth*2)+ (margin * 2);
ypos[3] = ypos[1];

    nameBars[seat].style.fontSize = fontSize;
    nameBars[seat].style.left = xpos[seat] ;
    table.style.left = xpos[seat];
    if (picturesOfCards) {
      nameBars[seat].style.top = getPicturesNameBarTop(seat);
    } else {
      nameBars[seat].style.top = ypos[seat];
    }
    table.style.top = ypos[seat];
    nameBars[seat].style.height = nameHeight;
    nameBars[seat].style.width = getHandWidth(seat);
    nameTexts[seat].style.left = nameInitials[seat].clientWidth;
    nameTexts[seat].style.width = getHandWidth(seat) - nameInitials[seat].clientWidth;
  }
  
  

  if (numHandsShowing == 4) {
    var trickAreaLeft = xpos[1] + handDivs[1].clientWidth;
    var trickAreaTop = ypos[2] + handDivs[2].clientHeight;
    var trickAreaRight = xpos[3];
    var trickAreaBottom = ypos[0];
    var trickCardWidth = Math.max(1, (4 * (handWidth - 6 * margin)) / 10);
    var trickCardHeight = Math.max(1, (trickAreaBottom - trickAreaTop - 8 * margin) / 3);

    for (seat = 0; seat < 4; seat++) {
      var trickCard = trickDivs[seat];
      trickCard.style.fontSize = (5 * fontSize) / 4;
      trickCard.style.width = trickCardWidth;
      trickCard.style.height = trickCardHeight;
      trickCard.style.lineHeight = trickCardHeight + 'px';
      if (seat == 1 || seat == 3) {
        trickCard.style.top = (totalHeight - trickCard.clientHeight) / 2 + div.offsetTop;
        if (seat == 1) trickCard.style.left = trickAreaLeft + 2 * margin;
        else trickCard.style.left = trickAreaRight - 2 * margin - trickCardWidth;
      } else {
        trickCard.style.left =
          editorWidthOffset + (totalWidth - editorWidthOffset - trickCardWidth) / 2;
        if (seat == 0) trickCard.style.top = trickAreaBottom - 2 * margin - trickCard.clientHeight;
        else trickCard.style.top = trickAreaTop + 2 * margin;
      }
      div.appendChild(trickCard);
    }
  } else {
    for (seat = 0; seat < 4; seat++) {
      if (trickDivs[seat].parentNode == div) div.removeChild(trickDivs[seat]);
    }
  }

  if (showAuction()) {
    if (auctionHeadingDiv.parentNode != div) div.appendChild(auctionHeadingDiv);
    if (auctionTableDiv.parentNode != div) div.appendChild(auctionTableDiv);
    div.appendChild(alertDiv);
    auctionHeading.style.fontSize = fontSize;
    auctionHeadingDiv.style.width = handWidth;

    auctionHeading.style.height = suitHeight;
    auctionHeading.style.width = handWidth;

    auctionTableDiv.style.fontSize = fontSize;
    auctionTableDiv.style.width = handWidth;

    var auctionDivHeight = 4 * suitHeight;
    auctionTableDiv.style.height = auctionDivHeight + 'px';

    auctionTable.style.fontSize = fontSize*0.88;
    auctionTable.style.width = handWidth;

    var auctionLeft;
    if (
      numHandsShowing == 2 &&
      ((handShowing[0] && handShowing[3]) || (handShowing[1] && handShowing[2]))
    )
      auctionLeft = editorWidthOffset + margin;
    else if (numHandsShowing == 2 && handShowing[1] && handShowing[3])
      auctionLeft =
        editorWidthOffset + (totalWidth - editorWidthOffset - auctionHeadingDiv.clientWidth) / 2;
    // else auctionLeft = totalWidth - margin - auctionHeadingDiv.clientWidth - 2;
    else auctionLeft = xpos[3];

    var auctionTop;
    if (numHandsShowing == 2 && handShowing[0] && handShowing[2])
      auctionTop = (totalHeight - 5 * suitHeight) / 2;
    else auctionTop = margin;
    auctionTop += div.offsetTop;

    auctionHeadingDiv.style.top = auctionTop;
    auctionHeadingDiv.style.left = auctionLeft;

    auctionTableDiv.style.top = auctionTop + auctionHeading.clientHeight;
    auctionTableDiv.style.left = auctionLeft;
    manageAuctionScrollBar();
    manageAuctionScrollBar();

    alertDiv.style.fontSize = (3 * fontSize) / 4;
    alertDiv.style.height = (3 * suitHeight) / 4;
    manageAlertDiv();
  } else {
    if (auctionHeadingDiv.parentNode == div) div.removeChild(auctionHeadingDiv);
    if (auctionTableDiv.parentNode == div) div.removeChild(auctionTableDiv);
  }

  

  if (cardDivsCreated && (picturesOfCards || getDeal)) {
    var suit;
    var card;
    var seat;

    for (suit = 0; suit < 4; suit++) {
      for (card = 0; card < 13; card++) {
        cardImageDiv[suit][card].style.height = cardImageHeight;
        cardImageDiv[suit][card].style.width = cardImageWidth;
        resizeCardDiv(cardImageDiv[suit][card]);
        cardBackDiv[suit][card].style.width = cardImageWidth;
        cardBackDiv[suit][card].style.height = cardImageHeight;
      }
    }

    moveCardImages(0, 3);

    for (seat = 0; seat < 4; seat++) {
      moveTrickCardImage(seat);
    }
  }

  tricksDiv.style.fontSize = (3 * fontSize) / 4;
  tricksDiv.style.paddingLeft = margin;
  tricksDiv.style.paddingRight = margin;
  announceDiv.style.paddingRight = margin;
  announceDiv.style.paddingLeft = margin;
  manageTricksDiv();

  scoreDiv.style.fontSize = (3 * fontSize) / 4;
  scoreDiv.style.paddingLeft = margin;
  scoreDiv.style.paddingRight = margin;
  tricksDiv.style.display = 'none';
  //manageAnnounceDiv();
  manageInfoDiv();
 // populateScrollableContainer() 
  positionHandsContainer();


  // Draw the box around the hands
  const canvas = document.createElement('canvas');
  canvas.width = totalWidth;
  canvas.height = totalHeight;
  document.body.appendChild(canvas);
  
  drawHandsBox();
  updateTextContainer();

  
}

function populateScrollableContainer() {
  var container = document.getElementById('scrollable-container');
  if (container) {
    var div = document.getElementById('theDiv');
    if (!div) return;

    var leftmostHand = Math.min(xpos[0], xpos[1], xpos[2], xpos[3]);
    
    container.style.left = '0px';
    container.style.top = '0px';
    container.style.height = div.clientHeight + 'px';
    container.style.width = (leftmostHand - margin) + 'px';
    container.innerHTML = '<h3>Scrollable Content</h3><p>Your content here...</p>';
    // Add more content as needed
  }
}
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
function hideButtons(buttonIds) {
  buttonIds.forEach(buttonId => {
      const button = document.getElementById(buttonId);
      if (button) {
          button.style.display = 'none';
          button.onclick = null;
      }
  });
}
function blankOutAuctionTable() {
  while (auctionTable.rows.length > 0) {
      auctionTable.deleteRow(0);
  }
  // Optionally, recreate the initial row structure if needed
  createAuctionRow();
}

function manageAuctionScrollBar() {
  var cellPercent;
  var rightPercent;

  if (auctionTable.clientHeight > auctionTableDiv.clientHeight && auctionTable.clientWidth != 0) {
    auctionTableDiv.style.overflowY = 'scroll';
    cellPercent =
      Math.max(
        1,
        (100.0 * ((auctionTable.clientWidth - scrollBarWidth) / 4)) / auctionTable.clientWidth
      ) + '%';
    rightPercent = 100.0 * (scrollBarWidth / auctionTable.clientWidth) + '%';
  } else {
    auctionTableDiv.style.overflowY = 'hidden';
    cellPercent = '25%';
    rightPercent = '0%';
  }

  var row;
  var col;

  for (row = 0; row < auctionTable.rows.length; row++) {
    for (col = 0; col < 4; col++) auctionTable.rows[row].cells[col].style.width = cellPercent;
    auctionTable.rows[row].cells[4].style.width = rightPercent;
  }
  for (col = 0; col < 4; col++) auctionHeading.rows[0].cells[col].style.width = cellPercent;
  auctionHeading.rows[0].cells[4].style.width = rightPercent;
}

function manageTricksDiv() {
  if (!showTricksDiv()) {
    var div = document.getElementById('theDiv');
    if (tricksDiv.parentNode == div) div.removeChild(tricksDiv);
    return;
  }

  if (!endPosition() && (passes < 3 || declarer < 0)) {
    tricksDiv.style.visibility = 'hidden';
    return;
  }

  var html;

  if (lessonID && lessonID > '1') {
    html = '<center>';
    if (trump >= 0 && trump <= 3) {
      html += 'Trump: ' + suitHTMLs[trump];
    } else {
      html = 'Notrump';
    }
    if (lessonID == '3') {
      html += '&nbsp;&nbsp;Goal: ' + lastLevelBid;
    }
    html += '</center>';
  } else if (endPosition() && declarer < 0) {
    if (trump >= 0 && trump <= 3) html = 'Trump: ' + suitHTMLs[trump] + '<br>';
    else html = 'Notrump<br>';
  } else {
    html =
      "<font color='000000'>" +
      contractLevel +
      '</font>' +
      suitHTMLs[trump] +
      "<font color='000000'>";
    if (doubled == 2) html += 'x';
    if (doubled == 4) html += 'xx';
    html += ' ' + seats[declarer].charAt(0) + ' ';
  }

  tricksDivLeft.innerHTML = html;
  html = 'NS: ' + nsTricks + ' EW: ' + ewTricks;

  if (!lessonID) {
    tricksDivRight.innerHTML = html;
  }
  tricksDivLeft.style.height = fontSize - margin / 2;
  tricksDiv.style.left = 0;

  if (picturesOfCards) {
    tricksDiv.style.width = Math.max(
      0,
      totalWidth - 2 * margin - 2 * margin * fireFox - (xpos[0] + getHandWidth(0))
    );
  } else {
    tricksDiv.style.width = Math.max(0, handWidth - 2 * margin * fireFox);
  }
  tricksDiv.style.height = tricksDivLeft.clientHeight + 2;
  tricksDiv.style.top = totalHeight - tricksDiv.clientHeight - margin - 2;

  tricksDivLeft.style.left = margin;
  tricksDivRight.style.right = 5;

  if (picturesOfCards) {
    tricksDiv.style.left = xpos[0] + getHandWidth(0) + margin;
  } else {
    tricksDiv.style.left = totalWidth - handWidth - margin - 2 * fireFox;
  }
  if (lessonID) {
    tricksDivLeft.style.width = tricksDiv.clientWidth - 2 * margin;
  }
  tricksDiv.style.visibility = 'visible';
}



function manageInfoDiv() {
  var div = document.getElementById('theDiv');
  if (!showInfoDiv()) {
    for (seat = 0; seat < 4; seat++) {
      if (vulDivs[seat].parentNode == div) div.removeChild(vulDivs[seat]);
    }
    if (vulInnerDiv.parentNode == div) {
      div.removeChild(vulInnerDiv);
    }

    return;
  }

  for (seat = 0; seat < 4; seat++) {
    if (showVul() && vulDivs[seat].parentNode != div) {
      div.appendChild(vulDivs[seat]);
    }
    if (!showVul() && vulDivs[seat].parentNode == div) {
      div.removeChild(vulDivs[seat]);
    }
    if (dealer >= 0) vulDivs[seat].style.visibility = 'visible';
    else vulDivs[seat].style.visibility = 'hidden';
    if (seat == dealer) vulDivs[seat].innerHTML = '<b>D</b>';
    else vulDivs[seat].innerHTML = '';
  }

  if (vulInnerDiv.parentNode != div) {
    div.appendChild(vulInnerDiv);
  }

  if (lessonID) {
    vulInnerDiv.innerHTML =
      '<div><center>&nbsp;Level&nbsp;' +
      lessonID +
      '&nbsp;<br>&nbsp;Deal&nbsp;' +
      Math.max(1, boardNum) +
      '&nbsp;</center></div>';
  } else if (boardNum > 0) vulInnerDiv.innerHTML = boardNum;
  /*else
       vulInnerDiv.innerHTML="";*/

  if (dealer < 0 && !playingClient) vulInnerDiv.style.visibility = 'hidden';
  else vulInnerDiv.style.visibility = 'visible';

  var suitHeight = handHeight / 5;
  var vulMargin = 2;
  var vulSize = Math.floor((2 * suitHeight) / 3);
  var vulBorder = 2;
  var minWidth = (5 * fontSize) / 2;
  if (lessonID) {
    vulInnerDiv.style.fontSize = fontSize;
  } else {
    vulInnerDiv.style.fontSize = (7 * fontSize) / 4;
  }
  vulInnerDiv.style.height = minWidth + 'px';

  if (lessonID) {
  } else if (fireFox) {
    vulInnerDiv.style.minWidth = minWidth;
  } else {
    vulInnerDiv.style.width = minWidth;
  }
  if (!lessonID) {
    vulInnerDiv.style.lineHeight = Math.max(1, minWidth - 2 * vulMargin) + 'px';
  }
  if (showVul()) {
    vulInnerDiv.style.top = margin + vulMargin + vulSize;
    vulInnerDiv.style.left = xpos[0]-handWidth;  //margin + vulMargin + vulSize + editorWidthOffset;
  } else {
    vulInnerDiv.style.top = margin;
    vulInnerDiv.style.left = margin + editorWidthOffset;
  }

  for (seat = 0; seat < 4; seat++) {
    vulDivs[seat].style.fontSize = (2 * fontSize) / 3;
    if (seat % 2) {
      vulDivs[seat].style.top = margin + vulMargin + vulSize;
      vulDivs[seat].style.height = vulInnerDiv.clientHeight + 2 * vulBorder - !fireFox;
      vulDivs[seat].style.width = vulSize;
      vulDivs[seat].style.lineHeight = vulInnerDiv.clientHeight + 2 * vulBorder + 'px';

      if (seat == 1) vulDivs[seat].style.left = xpos[0]- handWidth -vulSize -vulMargin ;// margin + editorWidthOffset;
      else
        vulDivs[seat].style.left = xpos[0] - handWidth+ minWidth  + (margin*0.25) 
         ;
/*           margin +
          2 * vulMargin +
          vulSize +
          vulInnerDiv.clientWidth +
          2 * vulBorder +
          editorWidthOffset -
          !fireFox; */
    } else {
      vulDivs[seat].style.left = xpos[0]-handWidth; // margin + vulMargin + vulSize + editorWidthOffset;
      vulDivs[seat].style.width = vulInnerDiv.clientWidth + 2 * vulBorder - !fireFox;
      vulDivs[seat].style.height = vulSize;
      vulDivs[seat].style.lineHeight = vulSize + 'px';

      if (seat == 2) vulDivs[seat].style.top = margin;
      else
        vulDivs[seat].style.top =
          margin + 2 * vulMargin + vulSize + vulInnerDiv.clientHeight + 2 * vulBorder - !fireFox;
    }
  }
}

function manageHandBackground(seatMin, seatMax) {
  for (seat = seatMin; seat <= seatMax; seat++) {
    if (seat == dummy) handDivs[seat].style.background = '#989898';
    else handDivs[seat].style.background = '#CBCBCB';
  }
}

function manageVul() {
  for (seat = 0; seat < 4; seat++) {
    if ((seat % 2 == 1 && ewVul) || (seat % 2 == 0 && nsVul)) {
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
  for (seat = 0; seat < 4; seat++) {
    if (!handShowing[seat]) {
      continue;
    }
    if (mouseOverName == seat) {
      nameBars[seat].style.backgroundColor = '#99CCCC';
    } else if (
      seat == whosTurn &&
      (showMovie() || endPosition() || isEditor) &&
      (showAuction() || passes == 3 || getDeal)
    ) {
      nameBars[seat].style.backgroundColor = '#FFFFFF';
    } else if (picturesOfCards) {
      nameBars[seat].style.backgroundColor = '#CBCBCB';
    } else {
      nameBars[seat].style.backgroundColor = '#FFFFFF';
    }
  }

 
}

function getCardChar(card) {
  if (card == 8) return '10';
  else return cardchars.charAt(card);
}

function getSuitOrder(suitOrder) {
  var suits;
  if (picturesOfCards) {
    suits = [3, 2, 0, 1];
  } else {
    suits = [0, 1, 2, 3];
  }
  return suits[suitOrder];
}

function getSuitColor(suit) {
  if (suit == 1 || suit == 2) return '#CB0000';
  else return '#000000';
}

function createHandTables() {
  disableSelection(document.getElementById('buttonDiv'));
  scrollBarWidth = getScrollBarWidth();

  var theParent = document.getElementById('theDiv');



  for (seat = 0; seat < 4; seat++) {
    var hand = document.createElement('div');
    disableSelection(hand);

    hand.className = 'handDivStyle';
    handDivs[seat] = hand;
    theParent.appendChild(hand);

    nameBars[seat] = document.createElement('div');
    disableSelection(nameBars[seat]);
    nameBars[seat].className = 'nameRowDivStyle';
    nameBars[seat].style.position = 'absolute';
    nameBars[seat].style.border = '1px solid white';
    nameBars[seat].style.whiteSpace = 'nowrap';
    var nameInitial = document.createElement('div');
    nameInitial.className = 'nameInitialDivStyle';
    var nameText = document.createElement('div');
    nameText.className = 'nameTextDivStyle';

    nameBars[seat].seat = seat;
    nameBars[seat].onclick = function () {
      nameBarClicked(this);
    };
   
    
    nameInitials[seat] = nameInitial;
    nameTexts[seat] = nameText;
    nameInitial.innerHTML = seats[seat].charAt(0);

    nameBars[seat].appendChild(nameInitial);
    nameBars[seat].appendChild(nameText);
    theParent.appendChild(nameBars[seat]);

    suitRows[seat] = new Array(4);
    suitSymbols[seat] = new Array(4);
    suitHoldings[seat] = new Array(4);
    cardDivs[seat] = new Array(4);

    for (suit = 0; suit < 4; suit++) {
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

    trickDivs[seat] = document.createElement('div');
    disableSelection(trickDivs[seat]);
    trickDivs[seat].className = 'trickCardStyle';
    theParent.appendChild(trickDivs[seat]);

    vulDivs[seat] = document.createElement('div');
    disableSelection(vulDivs[seat]);
    vulDivs[seat].className = 'vulDivStyle';
    theParent.appendChild(vulDivs[seat]);
  }

  vulInnerDiv = document.createElement('div');
  disableSelection(vulInnerDiv);
  vulInnerDiv.className = 'vulInnerDivStyle';
  vulInnerDiv.onmouseover = function () {
    if (isEditor) {
      vulInnerDiv.style.backgroundColor = highlightColor;
    }
  };
  vulInnerDiv.onmouseout = function () {
    if (isEditor) {
      vulInnerDiv.style.backgroundColor = '#99CCCC';
    }
  };
  vulInnerDiv.onclick = function () {
    vulDivClicked();
  };
  theParent.appendChild(vulInnerDiv);

  auctionHeadingDiv = document.createElement('div');
  disableSelection(auctionHeadingDiv);
  auctionHeadingDiv.className = 'auctionTableDivStyle';

  auctionHeading = document.createElement('table');
  auctionHeading.cellSpacing = 0;
  auctionHeading.cellPadding = 0;
  var headingRow = auctionHeading.insertRow(0);
  seat = 1;
  for (i = 0; i < 4; i++) {
    auctionHeadingCells[seat] = headingRow.insertCell(i);
    auctionHeadingCells[seat].align = 'center';
    auctionHeadingCells[seat].style.width = '25%';
    auctionHeadingCells[seat].innerHTML = seats[seat].charAt(0);
    seat++;
    if (seat == 4) seat = 0;
  }
  var extraCell = headingRow.insertCell(4);
  extraCell.style.width = '0%';

  theParent.appendChild(auctionHeadingDiv);
  auctionHeadingDiv.appendChild(auctionHeading);

  auctionTableDiv = document.createElement('div');
  disableSelection(auctionTableDiv);
  auctionTableDiv.className = 'auctionTableDivStyle';
  auctionTableDiv.onscroll = function () {
    alertedCall = -1;
    manageAlertDiv();
  };
  theParent.appendChild(auctionTableDiv);

  auctionTable = document.createElement('table');
  auctionTable.cellSpacing = 0;
  auctionTable.cellPadding = 0;
  auctionTableDiv.appendChild(auctionTable);

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

  scoreDiv = document.createElement('div');
  disableSelection(scoreDiv);
  scoreDiv.className = 'auctionTableDivStyle';
  otherTableDiv = document.createElement('div');
  disableSelection(otherTableDiv);
  otherTableDiv.className = 'teamDivStyle';
  scoreDiv.appendChild(otherTableDiv);
  nsTeamDiv = document.createElement('div');
  disableSelection(nsTeamDiv);
  nsTeamDiv.className = 'teamDivStyle';
  scoreDiv.appendChild(nsTeamDiv);
  ewTeamDiv = document.createElement('div');
  disableSelection(ewTeamDiv);
  ewTeamDiv.className = 'teamDivStyle';
  scoreDiv.appendChild(ewTeamDiv);
  nsScoreDiv = document.createElement('div');
  disableSelection(nsScoreDiv);
  nsScoreDiv.className = 'scoreDivStyle';
  scoreDiv.appendChild(nsScoreDiv);
  ewScoreDiv = document.createElement('div');
  disableSelection(ewScoreDiv);
  ewScoreDiv.className = 'scoreDivStyle';
  scoreDiv.appendChild(ewScoreDiv);
  theParent.appendChild(scoreDiv);

  announceDiv = document.createElement('div');
  disableSelection(announceDiv);
  announceDiv.className = 'announceDivStyle';
  announceDiv.style.visibility = 'hidden';
  theParent.appendChild(announceDiv);

  annotDiv = document.getElementById('annotDiv');

  alertDiv = document.createElement('div');
  disableSelection(alertDiv);
  alertDiv.className = 'alertDivStyle';
  theParent.appendChild(alertDiv);

  menuDiv = document.createElement('div');
  disableSelection(menuDiv);
  menuDiv.className = 'menuDivStyle';
  menuTable = document.createElement('table');
  menuDiv.appendChild(menuTable);

  if (!fastVersion && !isEditor) {
    addMenuCommand('pictures');
  }

  if (!playingClient) {
    addMenuCommand('played');
    addMenuCommand('cardbycard');
  }

  if (vugraphClient && !playingClient) {
    addMenuCommand('hidechat');
    manageChatFontSizeMenuCommands();
  }
  
  
  document.body.appendChild(menuDiv);

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

function createCardDivs() {
  if (cardDivsCreated) return;

  cardDivsCreated = true;

  if (fastVersion) return;

  for (seat = 0; seat < 4; seat++) {
    for (suit = 0; suit < 4; suit++) {
      for (card = 0; card < 13; card++) {
        cardDivs[seat][suit][card] = document.createElement('div');
        cardDivs[seat][suit][card].className = 'cardDivStyle';
        cardDivs[seat][suit][card].suit = suit;
        cardDivs[seat][suit][card].card = -1;
        
        suitHoldings[seat][suit].appendChild(cardDivs[seat][suit][card]);
      }
    }
  }

  

  createCardImageDivs();
  
}

function createAuctionRow() {
  var rowIndex;
  if (!auctionTable.rows) rowIndex = 0;
  else rowIndex = auctionTable.rows.length;

  var newRow = auctionTable.insertRow(rowIndex);
  var newCell;
  for (i = 0; i < 5; i++) {
    newCell = newRow.insertCell(i);
    newCell.align = 'center';
    if (i < 4) newCell.style.width = '25%';
    else newCell.style.width = '0%';
  }
}

function clearAuction() {
  var i;
  for (i = auctionTable.rows.length - 1; i >= 0; i--) {
    auctionTable.deleteRow(i);
  }
  createAuctionRow();
  manageAuctionScrollBar();
}

function clearDeck() {
  for (w = 0; w < 4; w++) {
    howManyCards[w] = 0;
    howManyCardsDealt[w] = 0;
    howManySuit[w] = new Array(4);
    howManySuitDealt[w] = new Array(4);
    howManyXs[w] = new Array(4);
    for (s = 0; s < 4; s++) {
      howManySuit[w][s] = 0;
      howManySuitDealt[w][s] = 0;
      howManyXs[w][s] = 0;
    }
  }

  for (s = 0; s < 4; s++) {
    deck[s] = new Array(13);
    userDealt[s] = new Array(13);
    cardHighlighted[s] = new Array(13);
    for (c = 0; c < 13; c++) {
      userDealt[s][c] = false;
      cardHighlighted[s][c] = false;
      deck[s][c] = -10;
    }
  }

  for (t = 0; t < 13; t++) {
    suitPlayed[t] = new Array(4);
    rankPlayed[t] = new Array(4);
    seatPlayed[t] = new Array(4);
    cardAnnotation[t] = [null, null, null, null];
    cardAnnotType[t] = [null, null, null, null];

    trickWinner[t] = -1;

    for (it = 0; it < 4; it++) {
      suitPlayed[t][it] = -1;
      rankPlayed[t][it] = -1;
      seatPlayed[t][it] = -1;
    }
  }

  populateHands(0, 3, 0, 3);
  clearAuction();
  hilightSuitSymbol(false);
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
  if (!isVugraphMatch) {
    otherTableResult = '';
  }
  claimShowing = false;
  clearTrickCards(0, 3);
  auctionTableDiv.style.visibility = 'hidden';
  auctionHeadingDiv.style.visibility = 'hidden';
  callExplanation[0] = '';

  manageWhosTurn();
  manageHandBackground(0, 3);
  manageVul();
  manageTricksDiv();
  manageAlertDiv();
  
  
  // managePlayButton();
  disableButton('play', false);
  disableButton('next', true);
  disableButton('undo', true);
  disableButton('rewind', true);

  if (isVugraphMatch || vugraphClient) {
    introAnnotation = null;
  } else if (annotDiv) {
    annotDiv.innerHTML = '';
  }

  if (commentsEdit) {
    commentsEdit.value = '';
  }
}

function dealCardToPlayer(suit, card, seat) {
  var who = deck[suit][card];

  if (who == -10) {
    deck[suit][card] = seat;
    howManyCards[seat]++;
    howManyCardsDealt[seat]++;
    howManySuit[seat][suit]++;
    howManySuitDealt[seat][suit]++;
  }
}

function removeButton(buttonID) {
  var buttonTD = document.getElementById('buttonDiv');
  var button = document.getElementById(buttonID);

  if (button && button.parentNode == buttonTD) {
    buttonTD.removeChild(button);
  }
}

function disableButton(which, disable) {
  var button;
  if (which == 'new') button = document.getElementById('newButton');
  else if (which == 'shuffle') button = document.getElementById('shuffleButton');
  else if (which == 'next') button = document.getElementById('nextButton');
  else if (which == 'undo') button = document.getElementById('undoButton');
  else if (which == 'rewind') button = document.getElementById('rewindButton');
  else if (which == 'gib') button = document.getElementById('gibButton');
  else if (which == 'options') button = document.getElementById('optionsButton');
  else if (which == 'play') button = document.getElementById('playButton');
  if (button) button.disabled = disable;
}

function isButtonEnabled(which) {
  var button;
  if (which == 'next') button = document.getElementById('nextButton');
  else if (which == 'undo') button = document.getElementById('undoButton');
  else if (which == 'rewind') button = document.getElementById('rewindButton');
  else if (which == 'gib') button = document.getElementById('gibButton');
  else if (which == 'options') button = document.getElementById('optionsButton');
  else if (which == 'play') button = document.getElementById('playButton');
  if (button) return !button.disabled;
  return false;
}

function nextCard(animate, fromCardClick) {
  if (playSeqPoint <= playSeqMax) {
    if (!playCard(playSequence[playSeqPoint], animate)) {
      playSeqMax = playSeqPoint - 1;
    } else {
      playSeqPoint++;
    }
    if (playSeqPoint > playSeqMax) {
      if (trick == 12 && seat == 4) {
        // Do not disable the next button
      } else {
      disableButton('next', true);
      }
      if (tricksClaimed >= 0) {
        showTrickResult();
      }
    }
    disableButton('undo', false);

    if (!exploreLine) disableButton('rewind', false);

    if (trick == 12 && seat == 4) {
      disableButton('rewind', true);}
    

    autoPlayNextCard = false;

    if (
      !fromCardClick &&
      areEventsGrouped() &&
      // !advanceCardByCard() &&
      animate &&
      (!cardAnnotation[trick][inTrick] || hideChat)
    ) {
      if ((inTrick < 3) && ((whosTurn==1) || (whosTurn==3))) {
        autoPlayNextCard = true;
        if (!picturesOfCards) {
          trickTimer = setTimeout('nextCard(true)', 500);
        }
      } else if (!picturesOfCards) {
        killTimer();
      }
    } else if (trickTimer) {
      clearTimeout(trickTimer);
      trickTimer = null;
    }
  }
}



function resizeCards(seat, suit) {
  if (fastVersion || !cardDivsCreated) {
    return;
  }

  var pixels = 0;
  var fs = 1.2 * fontSize;
  var maxWidth = 0.82 * handWidth;
  for (i = 0; i < 13; i++) {
    if (cardDivs[seat][suit][i].innerHTML == '') {
      cardDivs[seat][suit][i].style.left = 0;
    } else {
      cardDivs[seat][suit][i].style.left = pixels;
      cardDivs[seat][suit][i].style.fontSize = fs;
      pixels += cardDivs[seat][suit][i].clientWidth + 1;

      if (pixels > maxWidth && fs > 8) {
        fs--;
        i = -1;
        pixels = 0;
      }
    }
  }
}

function populateHands(seatMin, seatMax, suitMin, suitMax) {
  if (!cardDivsCreated) {
    return;
  }

  var div = document.getElementById('theDiv');
  var seat;
  var suit;
  var card;
  var suitOrder;

  if (picturesOfCards) {
    suitMin = 0;
    suitMax = 3;
  }

  for (seat = seatMin; seat <= seatMax; seat++) {
    var totalCards = 0;
    for (suitOrder = suitMin; suitOrder <= suitMax; suitOrder++) {
      var which = 0;
      var holding = '';
      suit = getSuitOrder(suitOrder);

      if (fastVersion) {
        suitHoldings[seat][suit].innerHTML = '';
      }

      for (card = 12; card >= 0; card--) {
        var played = false;
        if (deck[suit][card] == seat - 4) played = true;
        if (picturesOfCards) {
          if (played) {
            if (cardImageDiv[suit][card].parentNode == div) {
              div.removeChild(cardImageDiv[suit][card]);
              cardImageDiv[suit][card].needsResizing = true;
            }
          } else if (deck[suit][card] == seat) {
            if (isHandShowing(seat)) {
              div.insertBefore(cardImageDiv[suit][card], nameBars[seat]);
              maybeResizeCardImage(cardImageDiv[suit][card]);
            } else {
              if (cardImageDiv[suit][card].parentNode == div) {
                div.removeChild(cardImageDiv[suit][card]);
                cardImageDiv[suit][card].needsResizing = true;
              }
              div.insertBefore(cardBackDiv[seat][totalCards], nameBars[seat]);
              totalCards++;
            }
          }

        } else if (deck[suit][card] == seat || (showPlayedCards && played)) {
          holding = '';
          if (played) holding += "<font color='808080'>";
          else holding += "<font color='000000'>";
          holding += getCardChar(card);
          holding += '</font>';

          if (fastVersion) {
            suitHoldings[seat][suit].innerHTML += holding;
          } else {
            cardDivs[seat][suit][which].innerHTML = holding;
            cardDivs[seat][suit][which].card = card;
          }

          which++;
        }
      }

      if (!picturesOfCards) {
        for (x = 0; x < howManyXs[seat][suit]; x++) {
          if (fastVersion) {
            suitHoldings[seat][suit].innerHTML += 'x';
          } else {
            cardDivs[seat][suit][which].innerHTML = 'x';
            cardDivs[seat][suit][which].card = -1;
            which++;
          }
        }

        if (!fastVersion) {
          for (i = which; i < 13; i++) {
            cardDivs[seat][suit][i].innerHTML = ' ';
            cardDivs[seat][suit][i].card = -10;
          }

          resizeCards(seat, suit);
        }
      }

      for (card = totalCards; card < 13; card++) {
        if (cardBackDiv[seat] && cardBackDiv[seat][card].parentNode == div) {
          div.removeChild(cardBackDiv[seat][card]);
        }
      }
    }
    if (picturesOfCards || getDeal) {
      moveCardImages(seat, seat);
    }
  }
}

function getHandWidth(seat) {
  if (picturesOfCards && playingClient && seat % 2 && !isHandShowing(seat)) {
    return (2 * handWidth) / 3;
  }
  return handWidth;
}

function getCardXOverlap(seat) {
  if (picturesOfCards && playingClient && seat % 2) {
    return (getHandWidth(seat) - cardImageWidth) / 12;
  }
  return cardImageXOverlap;
}

function moveCardImages(seatMin, seatMax) {
  if (getDeal) {
    moveEditorCardImages();

    if (!picturesOfCards) {
      return;
    }
  }

  var seat;
  var suit;
  var card;
  var suitOrder;

  for (seat = seatMin; seat <= seatMax; seat++) {
    var overlap = getCardXOverlap(seat);
    var theHandWidth = getHandWidth(seat);

    var cardImageX =
      xpos[seat] + (theHandWidth - ((howManyCards[seat] - 1) * overlap + cardImageWidth)) / 2;
    var cardTop = getPicturesNameBarTop(seat) + nameHeight - cardImageHeight;

    var totalCards = 0;
    for (suitOrder = 0; suitOrder <= 3; suitOrder++) {
      suit = getSuitOrder(suitOrder);
      for (card = 13; card >= 0; card--) {
        if (deck[suit][card] == seat) {
          if (isHandShowing(seat)) {
            cardImageDiv[suit][card].style.top = cardTop;
            cardImageDiv[suit][card].style.left = cardImageX;
          } else {
            cardBackDiv[seat][totalCards].style.top = cardTop;
            cardBackDiv[seat][totalCards].style.left = cardImageX;
          }
          totalCards++;
          cardImageX += overlap;
        }
      }
    }
  }
}

function removeMenuCommand(command, nav) {
  var table = getMenuTable(nav);

  for (var row = 0; row < table.rows.length; row++) {
    var item = table.rows[row].cells[0];
    if (!command || item.id == command) {
      table.deleteRow(row);
      row--;
      if (command) {
        return;
      }
    }
  }
}

function addMenuCommand(command, nav) {
  var table = getMenuTable(nav);

  for (var row = 0; row < table.rows.length; row++) {
    var item = table.rows[row].cells[0];
    if (item.id == command) {
      return;
    }
  }

  var items = table.rows.length;
  var menuTableRow = table.insertRow(items);
  var menuTableCell = menuTableRow.insertCell(0);
  menuTableCell.id = command;
  menuTableCell.onmouseover = function () {
    this.style.backgroundColor = '#99CCCC';
  };
  menuTableCell.onmouseout = function () {
    this.style.backgroundColor = '#E2E1B5';
  };
  menuTableCell.onclick = function () {
    issueMenuCommand(this, nav);
  };
  menuTableCell.style.whiteSpace = 'nowrap';
  menuTableCell.style.paddingLeft = 2;
  menuTableCell.style.paddingRight = 2;
}



function manageChatFontSizeMenuCommands() {
  removeMenuCommand('smallerchat');
  removeMenuCommand('biggerchat');

  if ((vugraphClient || isVugraphMatch) && !hideChat && !playingClient) {
    if (chatFontSize < 4) {
      addMenuCommand('biggerchat');
    }
    if (chatFontSize > 0) {
      addMenuCommand('smallerchat');
    }
  }
  
}

function setAnnotChatFontSize() {
  var sizes = [0.6, 0.7, 0.8, 1, 1.2];
  annotDiv.style.fontSize = sizes[chatFontSize] * fontSize;
}



function toggleShowPlayed() {
  showPlayedCards = !showPlayedCards;
  populateHands(0, 3, 0, 3);
  manageGIBDivs();
  
  setCookie('showPlayedCards', showPlayedCards, 365);
}

function toggleHideChat() {
  hideChat = !hideChat;
  manageChatFontSizeMenuCommands();
  respondToResize();
  setCookie('hideChat', hideChat, 365);
}

function toggleCardByCard() {
  cardByCard = !cardByCard;
  setCookie('cardByCard', cardByCard, 365);
  
}

function changeChatFontSize(bigger) {
  if (bigger) {
    chatFontSize++;
  } else {
    chatFontSize--;
  }
  manageChatFontSizeMenuCommands();
  setAnnotChatFontSize();
  setCookie('chatFontSize', chatFontSize, 365);
}

function issueMenuCommand(command) {
  
  
  if (command.id == 'pictures') {
    togglePictures();
  } else if (command.id == 'played') {
    toggleShowPlayed();
  } else if (command.id == 'hidechat') {
    toggleHideChat();
  } else if (command.id == 'cardbycard') {
    toggleCardByCard();
  } else if (command.id == 'biggerchat') {
    changeChatFontSize(true);
  } else if (command.id == 'smallerchat') {
    changeChatFontSize(false);
  } else if (command.id == 'scoreboard') {
    showScoreBoard();
  } else if (command.id == 'nextboard') {
    showVugraphBoard(roomShowing, boardShowing + 1);
  } else if (command.id == 'prevboard') {
    showVugraphBoard(roomShowing, boardShowing - 1);
  } else if (command.id == 'otherroom') {
    showVugraphBoard(1 - roomShowing, boardShowing);
  }
}

function getMenuTable(nav) {
  if (nav) {
    if (navMenuTable) {
      return navMenuTable;
    }
  }
  if (menuTable) {
    return menuTable;
  }
  return null;
}

function getMenuDiv(nav) {
  if (nav) {
    if (navMenuDiv) {
      return navMenuDiv;
    }
  }
  if (menuDiv) {
    return menuDiv;
  }
  return null;
}



function fillInFourthHand() {
  var num13 = 0;
  var not13 = -1;

  for (seat = 0; seat < 4; seat++) {
    if (howManyCardsDealt[seat] == 13) num13++;
    else not13 = seat;
  }

  if (num13 == 3 && not13 >= 0) {
    for (suit = 0; suit < 4; suit++) {
      for (card = 0; card < 13; card++) {
        if (deck[suit][card] == -10) dealCardToPlayer(suit, card, not13);
      }
    }
    return true;
  }
  return false;
}

function getTrickCardImageTop(seat) {
  var midY = (totalHeight - cardImageHeight) / 2;
  if (seat == 0) {
    return midY + 0.35 * cardImageHeight;
  } else if (seat == 2) {
    return midY - 0.35 * cardImageHeight;
  } else if (seat == 1) {
    return midY + 0.1 * cardImageHeight;
  } else {
    return midY - 0.1 * cardImageHeight;
  }
}

function getTrickCardImageLeft(seat) {
  var midX = editorWidthOffset + (totalWidth - editorWidthOffset - cardImageWidth) / 2;

  if (seat == 1) {
    return midX - 0.45 * cardImageWidth;
  } else if (seat == 3) {
    return midX + 0.45 * cardImageWidth;
  } else {
    return midX;
  }
}

function moveTrickCardImage(seat) {
  if (trickCardImage[seat]) {
    trickCardImage[seat].style.top = getTrickCardImageTop(seat);
    trickCardImage[seat].style.left = getTrickCardImageLeft(seat);
  }
}

function clearTrickCards(seatMin, seatMax) {
  var div = document.getElementById('theDiv');

  for (seat = seatMin; seat <= seatMax; seat++) {
    trickDivs[seat].style.visibility = 'hidden';
    if (trickCardImage[seat] && trickCardImage[seat].parentNode == div) {
      div.removeChild(trickCardImage[seat]);
      trickCardImage[seat].needsResizing = true;
    }
    trickCardImage[seat] = null;
  }
}

function showAllTrickCards() {
  if (trick < 0) {
    return;
  }
  var it;
  for (it = 0; it <= inTrick; it++) {
    showTrickCard(seatPlayed[trick][it], suitPlayed[trick][it], rankPlayed[trick][it]);
  }
}

function showTrickCard(seat, suit, rank) {
  if (suit < 0 || rank < 0) {
    return;
  }

  if (picturesOfCards) {
    var div = document.getElementById('theDiv');
    if (cardImageDiv[suit][rank].parentNode != div) {
      div.appendChild(cardImageDiv[suit][rank]);
      maybeResizeCardImage(cardImageDiv[suit][rank]);
    }

    trickCardImage[seat] = cardImageDiv[suit][rank];
    moveTrickCardImage(seat);
  } else {
    var rankShow = getCardChar(rank);

    trickDivs[seat].innerHTML = suitHTMLs[suit] + "<font color='000000'>" + rankShow + '</font>';
    trickDivs[seat].style.visibility = 'visible';
  }
}

function getPartner(seat) {
  if (seat >= 0 && seat <= 4) {
    var pardSeat = seat + 2;
    if (pardSeat > 3) {
      pardSeat -= 4;
    }
    return pardSeat;
  }
  return -1;
}

function getBidSeqPoint(r, ir) {
  var where = 4 * (r - 1) + (ir - 1);
  var fromWest = dealer - 1;
  if (fromWest < 0) fromWest = 3;
  where -= fromWest;
  return where;
}

function isVul(seat, board) {
  var i = board % 16;

  if (
    (seat == 0 || seat == 2) &&
    (i == 2 || i == 4 || i == 5 || i == 7 || i == 10 || i == 12 || i == 13 || i == 15)
  )
    return true;
  if (
    (seat == 1 || seat == 3) &&
    (i == 3 || i == 4 || i == 6 || i == 7 || i == 10 || i == 9 || i == 13 || i == 0)
  )
    return true;

  return false;
}

function interpretSuitChar(suit) {
  var s;

  for (s = 0; s < 5; s++) {
    if (suit.toUpperCase() == suitchars.charAt(s)) return s;
  }
  return -1;
}

function interpretSeatString(direction) {
  if (!direction || !direction.length) return -1;

  for (seat = 0; seat < 4; seat++) {
    if (direction.charAt(0).toUpperCase() == seats[seat].charAt(0).toUpperCase()) {
      return seat;
    }
  }
  return -1;
}

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

function setDeclarer() {
  var bsp = 0;
  while (bsp <= bidSeqPoint) {
    if (levelBid[bsp] > 0 && strainBid[bsp] == trump && seatBid[bsp] % 2 == lastBidder % 2) {
      declarer = seatBid[bsp];
      break;
    }

    bsp++;
  }
}

function explainCall(explain, bsp) {
  callExplanation[bsp] = explain;

  var row = bspToAuctionRow(bsp);
  var col = bspToAuctionCol(bsp);

  if (explain && explain != '') {
    auctionTable.rows[row].cells[col].style.background = highlightColor;
    auctionTable.rows[row].cells[col].onclick = function () {
      auctionCellClicked(bsp);
    };
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
  if (callExplanation[bsp] && alertedCall != bsp) {
    alertedCall = bsp;
  } else {
    alertedCall = -1;
  }

  manageAlertDiv();
}

function allowDouble() {
  if (doubled || lastBidder < 0) return false;
  if (whosTurn % 2 == lastBidder % 2) return false;

  return true;
}

function allowRedouble() {
  if (doubled != 2 || lastBidder < 0) return false;
  if (whosTurn % 2 != lastBidder % 2) return false;
  return true;
}

function makeCall(call) {
  if (call.length < 1 || passes == 3 || dealer == -1) return false;

  if (call.toUpperCase() == 'X') call = 'D';
  if (call.toUpperCase() == 'XX') call = 'R';

  var level = -1;
  var strain = -1;

  if (call.length == 1) {
    strain = callchars.indexOf(call.charAt(0).toUpperCase());
    if (strain >= 0) {
      level = 0;
    }
  }

  if (call.length == 2) {
    level = parseInt(call.charAt(0));
    strain = suitchars.indexOf(call.charAt(1).toUpperCase());
  }

  if (level < 0 || strain < 0) return false;
  if (level == 0 && strain == 1 && !allowDouble()) {
    return false;
  }
  if (level == 0 && strain == 2 && !allowRedouble()) {
    return false;
  }
  if (level > 0) {
    if (10 * level + strain <= 10 * lastLevelBid + lastStrainBid) return false;
  }

  bidSeqPoint++;
  if (bidSeqPoint > bidSeqMax) bidSeqMax = bidSeqPoint;
  if (callAnnotation[bidSeqPoint] != null) {
    if (callAnnotType[bidSeqPoint]) {
      annotDiv.innerHTML += callAnnotation[bidSeqPoint];
    } else {
      annotDiv.innerHTML = callAnnotation[bidSeqPoint];
    }
  }
  bidSequence[bidSeqPoint] = call;
  levelBid[bidSeqPoint] = level;
  strainBid[bidSeqPoint] = strain;
  seatBid[bidSeqPoint] = whosTurn;
  whosTurn++;
  if (whosTurn == 4) whosTurn = 0;

  var row = bspToAuctionRow(bidSeqPoint);
  var col = bspToAuctionCol(bidSeqPoint);

  if (auctionTable.rows.length < row + 1) createAuctionRow();

  if (level == 0) auctionTable.rows[row].cells[col].innerHTML = calls[strain];
  else
    auctionTable.rows[row].cells[col].innerHTML =
      "<font color='000000'>" + level + '</font>' + suitHTMLs[strain];

  explainCall('', bidSeqPoint);
  auctionTable.rows[row].cells[col].style.visibility = 'visible';
  if (level == 0 && strain == 0) {
    passes++;

    if (passes == 3) {
      trump = lastStrainBid;
      contractLevel = lastLevelBid;
      setDeclarer();
      whosTurn = declarer + 1;
      if (whosTurn == 4) {
        whosTurn = 0;
      }
      setKeyboardSuit();
      if (contractLevel > 0) {
        
      } else {
        showTrickResult();
      }
    }
    manageTricksDiv();
    //manageAnnounceDiv();
  } else if (level == 0) {
    doubled = strain * 2;
    passes = 0;
  } else {
    lastLevelBid = levelBid[bidSeqPoint];
    lastStrainBid = strainBid[bidSeqPoint];
    lastBidder = seatBid[bidSeqPoint];
    doubled = 0;
    passes = 0;
  }
  
    // Check if auction should end (after cell is displayed)
  if (passes == 3 && contractLevel == -1) {
      trump = lastStrainBid;
      contractLevel = lastLevelBid;
      setDeclarer();
      whosTurn = declarer + 1;
      if (whosTurn == 4) {
        whosTurn = 0;
      }
      setKeyboardSuit();
      if (contractLevel > 0) {
        
      } else {
        showTrickResult();
      }
      manageTricksDiv();
  }


  manageBiddingQuestionMark();
  manageWhosTurn();
  manageAuctionScrollBar();
  auctionTableDiv.scrollTop = auctionTableDiv.scrollHeight;
  disableButton('undo', false);
  disableButton('rewind', false);
  disableButton(
    'next',
    (passes == 3 && playSeqMax == -1) || (passes < 3 && bidSeqPoint == bidSeqMax)
  );

  return true;
}
// Check if auction should end (after cell is displayed)
if (passes == 3 && contractLevel == -1) {
    trump = lastStrainBid;
    contractLevel = lastLevelBid;
    setDeclarer();
    whosTurn = declarer + 1;
    if (whosTurn == 4) {
      whosTurn = 0;
    }
    setKeyboardSuit();
    if (contractLevel > 0) {
      
    } else {
      showTrickResult();
    }
    manageTricksDiv();
}

function manageBiddingQuestionMark() {
  if (passes < 3 && (vugraphClient || getSequence || isVugraphMatch)) {
    var row = bspToAuctionRow(bidSeqPoint + 1);
    var col = bspToAuctionCol(bidSeqPoint + 1);

    if (auctionTable.rows.length < row + 1) createAuctionRow();

    auctionTable.rows[row].cells[col].innerHTML = '?';
  }
}



function killTimer() {
  endCardAnimation();

  if (autoPlayNextCard) {
    autoPlayNextCard = false;
    if (trickTimer) {
      clearTimeout(trickTimer);
      trickTimer = null;
    }

    while (inTrick < 3 && playSeqPoint <= playSeqMax) {
      nextCard(false);
      if (cardAnnotation[trick][inTrick] && !hideChat) break;
    }
  }
}

function play() {
  
  // const element = document.getElementById(currentId);
  // if (element) {
  //     console.log(`Element with ID '${currentId}' exists. Navigating to the link.`);
  //     // Navigate to the link if it exists
  //     window.location.href = element.href;
  // } else {
  //     console.log(`Element with ID '${newId}' does not exist.`);
  // }
  const queryString = getQueryString();
  const fullUrl = `${htmlPlayLoc}?${queryString}`;
  window.location.href = fullUrl;

}

function getQueryString() {
  const url = window.location.href;
  const queryString = url.split('?')[1];
  return queryString || '';
}






function advanceCardByCard() {
  return cardByCard;
}

function areEventsGrouped() {
  return !vugraphClient && !getSequence;
}
function next() {
 
  var retVal;



    
   if (bidSeqPoint < bidSeqMax) {
    while (bidSeqPoint < bidSeqMax && passes < 3) {
      var explain = callExplanation[bidSeqPoint + 1];
      retVal = makeCall(bidSequence[bidSeqPoint + 1]);
      if (retVal) {
        explainCall(explain, bidSeqPoint);
        if (callAnnotation[bidSeqPoint] && showMovie() && !hideChat) {
          retVal = false;
          break;
        }
      } else {
        disableButton('next', true);
        break;
      }

      if (!areEventsGrouped()) break;
    }
  }
  // if(((whosTurn==0) || (whosTurn==2))) {
  //   if (inTrick == 3){clearTrickCards(0, 3);}
  //   showTransientAnnouncement('Select a card', 1000);
  // }
  // return retVal;
}
function getNextDealIdAndNavigate(currentId) {
  // Extract the group number and deal number from the current ID
  const match = currentId.match(/Group(\d+)Deal(\d+)/);
  if (!match) {
      console.error('Invalid ID format');
      return;
  }

  const groupNumber = match[1];
  let dealNumber = parseInt(match[2], 10);

  // Increment the deal number
  dealNumber += 1;

  // Construct the new ID
  const newId = `Group${groupNumber}Deal${dealNumber}`;

  // Check if an element with the new ID exists in the document
  const element = document.getElementById(newId);
  if (element) {
      console.log(`Element with ID '${newId}' exists. Navigating to the link.`);
      // Navigate to the link if it exists
      window.location.href = element.href;
  } else {
      console.log(`Element with ID '${newId}' does not exist.`);
  }
}

function replay(){
  const element = document.getElementById(currentId);
  window.location.href = element.href;
}

function undo() {
  killTimer();
  if (trick == 12 && seat == 4) {
    replay()
    ;}
  
    if (trick >= 0) {
    do {
      undoCard();

      if (
        !areEventsGrouped() ||
        advanceCardByCard() ||
        (trick >= 0 && cardAnnotation[trick][inTrick] && !hideChat)
      ) {
        break;
      }
    } while (inTrick != 3);
  } else {
    do {
      undoCall();
      if (!areEventsGrouped() || (bidSeqPoint >= 0 && callAnnotation[bidSeqPoint] && !hideChat)) {
        break;
      }
    } while (bidSeqPoint >= 0);
  }

  computeAnnotation();
}

function rewind() {
  killTimer();

  while (trick >= 0 || (undoIntoAuction() && bidSeqPoint >= 0)) {
    undo();
  }
  computeAnnotation();
}

function deal(dealString) {
  if (!dealString || dealString.length == 0) return false;

  clearDeck();

  var seat = 0;
  var suit = -1;
  var card = -1;
  var p = 1;

  while (p < dealString.length) {
    var ch = dealString.charAt(p).toUpperCase();

    if (ch == ',') {
      seat++;
      if (seat > 3) return false;
      suit = -1;
      card = -1;
    }

    var st = suitchars.indexOf(ch);

    if (st >= 0) suit = st;

    if (ch == 'X') {
      if (suit < 0) return false;
      if (howManyCardsDealt[seat] < 13) {
        howManyXs[seat][suit]++;
        howManyCards[seat]++;
        howManyCardsDealt[seat]++;
        howManySuit[seat][suit]++;
        howManySuitDealt[seat][suit]++;
      }
    } else {
      if (ch == '1') {
        card = 8;
      } else {
        card = cardchars.indexOf(ch);
      }

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

  if (vChar == 'N' || vChar == 'B') nsVul = true;
  else nsVul = false;
  if (vChar == 'E' || vChar == 'B') ewVul = true;
  else ewVul = false;

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
    manageBiddingQuestionMark();
    return true;
  }

  return false;
}

function setPlayerName(direction, name) {
  var seat = interpretSeatString(direction);
  if (seat >= 0) {
    if (!name || !name.length) {
      name = seats[seat];
    }
    if (name.charAt(0) == '~') {
      name = 'Robot';
    }
    nameTexts[seat].innerHTML = name;
  }
  return false;
}

function clearPlayerNames() {
  for (seat = 0; seat < 4; seat++) {
    setPlayerName(seats[seat], seats[seats]);
  }
}

function setBoardNumber(num) {
  boardNum = parseInt(num);
  manageInfoDiv();
}

function setGroupNumber(num) {
  groupNum= parseInt(num);
}

function setCurrentId(){
  currentId = 'Group'+groupNum.toString()+'Deal'+boardNum.toString() ;
}


function processPlayerNames(param, vugraph) {
  var startPoint = -1;
  var endPoint;
  var seat;
  var room;

  for (room = 0; room < 2; room++) {
    for (seat = 0; seat < 4; seat++) {
      endPoint = param.indexOf(',', startPoint + 1);

      if (endPoint < 0) {
        endPoint = param.length;
      }

      if (endPoint < 0) {
        break;
      }

      if (vugraph) {
        vugraphPlayerNames[room][seat] = decodePlayerName(
          param.substring(startPoint + 1, endPoint)
        );
      } else if (room == roomShowing) {
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

function computeAnnotation() {
  if (vugraphClient) {
    return;
  }

  var annot;
  if (introAnnotation != null) {
    annot = introAnnotation;
  } else {
    annot = '';
  }

  var bsp = 0;

  while (bsp <= bidSeqPoint) {
    if (callAnnotation[bsp] != null) {
      if (callAnnotType[bsp]) {
        annot += callAnnotation[bsp];
      } else {
        annot = callAnnotation[bsp];
      }
    }

    bsp++;
  }

  if (trick >= 0) {
    var t = 0;
    var it = 0;

    while (4 * t + it <= 4 * trick + inTrick) {
      if (cardAnnotation[t][it] != null) {
        if (cardAnnotType[t][it]) {
          annot += cardAnnotation[t][it];
        } else {
          annot = cardAnnotation[t][it];
        }
      }
      it++;
      if (it == 4) {
        it = 0;
        t++;
      }
    }
  }

  annotDiv.innerHTML = annot;
}

function insertLinkHTML(orig) {
  var copy = '';
  var link;
  var linkURL;
  var found = false;
  var start = 0;
  var end = 0;
  var space = false;

  if (
    (orig.length > 4 && orig.substr(0, 4) == 'www.') ||
    (orig.length > 7 && orig.substr(0, 7) == 'http://') ||
    (orig.length > 8 && orig.substr(0, 8) == 'https://')
  ) {
    found = true;
  }

  do {
    if (found) {
      copy += orig.substring(end, start);
      end = orig.indexOf(' ', start + 1);

      if (end == -1) {
        if (space) {
          copy += ' ';
          link = orig.substr(start + 1);
        } else {
          link = orig.substr(start);
        }
      } else {
        if (space) {
          copy += ' ';
          link = orig.substring(start + 1, end);
        } else {
          link = orig.substring(start, end);
        }
      }
      if (link.charAt(0) == 'w') {
        linkURL = 'http://' + link;
      } else {
        linkURL = link;
      }
      copy += '<a href="' + linkURL + '" target="_blank">' + link + '</a>';
      if (end == -1) {
        break;
      }
    }
    found = false;
    start = orig.indexOf(' www.', end);
    if (start > 0) {
      found = true;
    } else {
      start = orig.indexOf(' http://', end);
      if (start > 0) {
        found = true;
      } else {
        start = orig.indexOf(' https://', end);
        if (start > 0) {
          found = true;
        }
      }
    }
    space = true;
  } while (found);

  if (end != -1) {
    copy += orig.substring(end);
  }

  return copy;
}

function insertSuitHTML(msg, forums) {
  for (var suit = 0; suit < 4; suit++) {
    var pattern = new RegExp('!' + suits[suit].charAt(0), 'gi');
    if (forums) {
      msg = msg.replace(pattern, suitForums[suit]);
    } else {
      msg = msg.replace(pattern, suitHTMLs[suit]);
    }
    if (isVugraphMatch) {
      pattern = new RegExp('@' + suits[suit].charAt(0), 'gi');
      msg = msg.replace(pattern, suitHTMLs[suit]);
    }
  }

  return msg;
}

function addAnnotation(msg, append) {
  msg = insertSuitHTML(msg);
  msg = insertLinkHTML(msg);

  if (isVugraphMatch) {
    var colon = msg.indexOf(':');
    if (colon > 0 && colon <= 10) {
      msg =
        "<b><font color='#000080'>" +
        msg.substring(0, colon) +
        '</font></b>' +
        msg.substring(colon);
    }
  }

  if (playSeqPoint > 0) {
    var t = Math.floor((playSeqPoint - 1) / 4);
    var it = (playSeqPoint - 1) % 4;

    if (!cardAnnotation[t][it]) {
      cardAnnotation[t][it] = msg;
      cardAnnotType[t][it] = append;
    } else {
      cardAnnotation[t][it] += '<br>' + msg;
    }
  } else if (bidSeqPoint >= 0) {
    if (!callAnnotation[bidSeqPoint]) {
      callAnnotation[bidSeqPoint] = msg;
      callAnnotType[bidSeqPoint] = append;
    } else {
      callAnnotation[bidSeqPoint] += '<br>' + msg;
    }
  } else {
    if (!introAnnotation) {
      introAnnotation = msg;
    } else {
      introAnnotation += '<br>' + msg;
    }
  }
  hasAnnotations = true;
}

function getPicturesNameBarTop(seat) {
  if (numHandsShowing == 2) {
    if (seat == 2) {
      return margin + cardImageHeight - nameHeight;
    } else if (seat == 0) {
      return 2 * margin + 2 * cardImageHeight - nameHeight;
    } else if (seat == 1) {
      if (handShowing[3] || handShowing[0]) {
        // ew or sw
        if (showAuction() && handShowing[3]) {
          return 2 * margin + 5 * suitHeight + cardImageHeight - nameHeight;
        } else {
          return margin + cardImageHeight - nameHeight;
        }
      } // nw
      else {
        if (showAuction()) {
          return 2 * margin + 5 * suitHeight + cardImageHeight - nameHeight;
        } else {
          return 2 * margin + 2 * cardImageHeight - nameHeight;
        }
      }
    } else {
      if (handShowing[1] || handShowing[0]) {
        // ew or se
        if (showAuction() && handShowing[1]) {
          return 2 * margin + 5 * suitHeight + cardImageHeight - nameHeight;
        } else {
          return margin + cardImageHeight - nameHeight;
        }
      } // ne
      else {
        if (showAuction()) {
          return 2 * margin + 5 * suitHeight + cardImageHeight - nameHeight;
        } else {
          return 2 * margin + 2 * cardImageHeight - nameHeight;
        }
      }
    }
  } else if (numHandsShowing == 1) {
    if (showAuction()) {
      return 2 * margin + 5 * suitHeight + cardImageHeight - nameHeight;
    } else {
      return margin + cardImageHeight - nameHeight;
    }
  } else if (seat == 2) {
    return margin + cardImageHeight - nameHeight;
  } else if (seat == 0) {
    return totalHeight - margin - nameHeight - 2 * fireFox;
  } else {
    return (totalHeight - cardImageHeight) / 2 + cardImageHeight - nameHeight;
  }
}

function getHandRows() {
  if (numHandsShowing == 1 && showAuction()) return 2;

  if (numHandsShowing < 2) return 1;

  if (numHandsShowing == 2) {
    if (handShowing[1] && handShowing[3] && !showAuction()) return 1;
    return 2;
  }

  return 3;
}

function getHandCols() {
  if (numHandsShowing < 2) return 1;

  if (numHandsShowing == 2) {
    if (handShowing[0] && handShowing[2] && !showAuction()) return 1;
    return 2;
  }

  return 3;
}

function showHand(seat) {
  if (showMovie() || endPosition()) {
    return true;
  }

  for (i = 0; i < displayType.length; i++) {
    if (displayType.charAt(i) == seats[seat].charAt(0).toUpperCase()) {
      return true;
    }
  }

  return false;
}

function showMovie() {
  return displayType == '';
}

function auctionOnly() {
  return displayType == 'A';
}

function endPosition() {
  return displayType.charAt(0).toUpperCase() == 'P';
}

function showAuction() {
  if (editorMenuShowing) {
    return false;
  }
  if (playingClient) {
    if (lessonID <= '3') {
      return false;
    }
  }

  return (displayType == '' && !getDeal) || auctionOnly() || displayType.indexOf('A') != -1;
}

function showInfoDiv() {
  return showMovie() && !getDeal && !getDealer && !editorMenuShowing;
}

function showTricksDiv() {
  if (playingClient) {
    if (lessonID == '1') {
      return false;
    }
  }

  return showMovie() || endPosition();
}

function showScoreDiv() {
  return vugraphClient || (isVugraphMatch && vugraphScoring == 'I');
}

function showButtonBar() {
  return (
    !inBlast &&
    mainDivShowing &&
    ((isEditor && showAuction()) || showMovie() || (endPosition() && playSeqMax >= 0))
  );
}

function showAnnotations() {
  return (
    !inBlast && mainDivShowing && !hideChat && (hasAnnotations || (vugraphClient && !playingClient))
  );
}

function setDisplayType(param) {
  displayType = param.toUpperCase();

  numHandsShowing = 0;
  for (seat = 0; seat < 4; seat++) {
    handShowing[seat] = showHand(seat);
    if (handShowing[seat]) numHandsShowing++;
  }
  if (numHandsShowing == 3) {
    setDisplayType('NSEW');
  }
}

function processBidding(bidding) {
  var i = 0;

  while (i < bidding.length) {
    var c = bidding.charAt(i).toUpperCase();
    var len = 0;

    if (c == '-') {
      i++;
      continue;
    }
    if (c == 'P' || c == 'D' || c == 'R' || c == '?') {
      len = 1;
    } else if (c == 'X') {
      len = 1;

      if (i < bidding.length - 1 && bidding.charAt(i + 1).toUpperCase() == 'X') {
        len++;
      }
    } else if (c >= '1' && c <= '7') {
      len = 2;
    }
    if (len == 0) {
      break;
    }
    callAnnotation[bidSeqPoint + 1] = null;
    callExplanation[bidSeqPoint + 1] = '';
    bidSequence[bidSeqPoint + 1] = bidding.substring(i, i + len);
    bidSeqMax = bidSeqPoint + 1;
    bidSeqPoint++;
    if (i + 1 < bidding.length - 1 && bidding.charAt(i + len) == '!') {
      len++;
    }
    i += len;
  }
}

function processLinCommand(command, param) {
  switch (command) {
    case 'DT':
      setDisplayType(param);
      break;
    case 'SV':
      setVul(param);
      break;
    case 'MD':
      deal(param);
      setDealer(seats[parseInt(param.charAt(0)) - 1]);
      break;
    case 'SK':
      // setKibitzed(param, true);
      break;
    case 'MB':
      processBidding(param);
      break;
    case 'PC':
      playSequence[playSeqPoint] = param;
      playSeqMax = playSeqPoint;
      playSeqPoint++;
      break;
    case 'AN':
      callExplanation[bidSeqPoint] = param;
      break;
    case 'AH':
      setBoardNumber(parseInt(param.substring(5)));
      setCurrentId();
      break;
    case 'RH':
      setGroupNumber(parseInt(param.substring(5)));
      break;
    case 'PN':
      processPlayerNames(param, false);
      break;
    case 'MC':
      tricksClaimed = parseInt(param);
      break;
    case 'NT':
      addAnnotation(param, false);
      break;
    case 'AT':
      addAnnotation(param, true);
      break;
  }
}

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
    var param = lin.substring(openPipeIndex + 1, closePipeIndex, 1);

    if (command == 'VG') {
      processVugraphLinFile(lin, param, closePipeIndex + 1);
      return;
    }

    processLinCommand(command, param);
    startIndex = closePipeIndex + 1;
  }

  if (!isVugraphMatch) {
    removeButton('shuffleButton');
  }

  playSeqPoint = 0;
  bidSeqPoint = -1;

  if (getSequence) {
    if (bidSeqMax > 0) {
      // disableButton('next', false);
    }
  } else if (introAnnotation != null) {
    annotDiv.innerHTML = introAnnotation;
    if (bidSeqMax >= 0) {
      // disableButton('next', false);
    }
    if (!showMovie()) {
      next();
    }
  } else if (!endPosition()) {
    next();
  }
  if (endPosition()) {
    if (displayType.length > 1) {
      var level = parseInt(displayType.charAt(1));
      if (level > 0 && level < 8 && displayType.length == 4) {
        contractLevel = level;
        trump = suitchars.indexOf(displayType.charAt(2).toUpperCase());
        declarer = interpretSeatString(displayType.charAt(3));
        whosTurn = declarer + 1;
        if (whosTurn > 3) {
          whosTurn = 0;
        }
      } else {
        whosTurn = interpretSeatString(displayType.charAt(1));

        if (displayType.length > 2) {
          trump = suitchars.indexOf(displayType.charAt(2).toUpperCase());
        } else {
          trump = 4;
        }
      }
    } else {
      whosTurn = 0;
    }

    manageWhosTurn();

    if (playSeqMax >= 0) {
      // disableButton('next', false);
    }
  }
  disableButton('undo', true);
  disableButton('rewind', true);

  if (isVugraphMatch) {
    
  } else if (numHandsShowing < 4) {
    fastVersion = true;
    picturesOfCards = false;
    
    removeMenuCommand('pictures');
    removeButton('gibButton');
  }

  createCardDivs();
  populateHands(0, 3, 0, 3);
  showAll(true);
}

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

  var hands = new Array(pSouth, pWest, pNorth, pEast);
  var dealer = interpretSeatString(pDealer) + 1;
  if (dealer <= 0) dealer = 3;
  var nt = '';
  if (pIntro.length) nt = 'nt|' + pIntro + '|';
  var sk = 'sk|' + pKibitz + '|';
  var md = 'md|' + dealer + pSouth + ',' + pWest + ',' + pNorth + ',' + pEast + '|';
  var pn =
    'pn|' +
    encodePlayerName(pSouthName) +
    ',' +
    encodePlayerName(pWestName) +
    ',' +
    encodePlayerName(pNorthName) +
    ',' +
    encodePlayerName(pEastName) +
    '|';

  var wantsPictures = gup('pc', source).toLowerCase();

  if (!fastVersion && wantsPictures == 'y') {
    picturesOfCards = true;
  } else if (fastVersion || wantsPictures == 'n') {
    picturesOfCards = false;
  }
  

  var dt = 'dt|';

  for (seat = 0; seat < 4; seat++) {
    if (hands[seat].length) dt += seats[seat].charAt(0);
  }
  if (pAuction.length && pAuction.charAt(0) == '-') {
    dt = 'dt|P' + pAuction.substring(1);
    pAuction = '';
  } else if ((dt.length >= 6 && pAuction.length) || pPlay.length > 0) {
    dt = 'dt|';
  } else if (pAuction.length) {
    dt += 'A';
  }
  dt += '|';

  var sv = 'sv|' + pVul + '|';
  var ah = '';
  var board = parseInt(pBoard);
  if (board > 0) ah = 'ah|Board ' + board + '|';

  var bidding = '';
  var startPoint = 0;
  var endPoint;

  while (startPoint < pAuction.length) {
    var ch = pAuction.charAt(startPoint);
    if (ch == '(') {
      endPoint = pAuction.indexOf(')', startPoint + 1);
      if (endPoint >= 0) {
        bidding += 'an|' + pAuction.substring(startPoint + 1, endPoint) + '|';
        startPoint = endPoint + 1;
        continue;
      }
      break;
    }
    if (ch == '{') {
      endPoint = pAuction.indexOf('}', startPoint + 1);
      if (endPoint >= 0) {
        if (pAuction.charAt(startPoint + 1) == '+')
          bidding += 'at|' + pAuction.substring(startPoint + 2, endPoint) + '|';
        else bidding += 'nt|' + pAuction.substring(startPoint + 1, endPoint) + '|';
        startPoint = endPoint + 1;
        continue;
      }
      break;
    }
    var level = parseInt(ch);
    if (level > 0) endPoint = startPoint + 2;
    else endPoint = startPoint + 1;
    if (endPoint < pAuction.length && pAuction.charAt(endPoint) == '!') endPoint++;

    bidding += 'mb|' + pAuction.substring(startPoint, endPoint) + '|';
    startPoint = endPoint;
  }

  var play = '';
  var mc = '';

  if (pPlay.length) {
    startPoint = 0;
    while (startPoint < pPlay.length) {
      ch = pPlay.charAt(startPoint);
      if (ch == '{') {
        endPoint = pPlay.indexOf('}', startPoint + 1);
        if (endPoint >= 0) {
          if (pPlay.charAt(startPoint + 1) == '+')
            play += 'at|' + pPlay.substring(startPoint + 2, endPoint) + '|';
          else play += 'nt|' + pPlay.substring(startPoint + 1, endPoint) + '|';
          startPoint = endPoint + 1;
          continue;
        }
        break;
      }
      play += 'pc|' + pPlay.substring(startPoint, startPoint + 2) + '|';
      startPoint += 2;
    }
    if (pClaim.length) mc = 'mc|' + pClaim + '|';
  }

  var lin = dt + nt + md + sk + pn + sv + ah + bidding + play + mc;
  processLinFile(lin, true);
}



function fatalError(message) {
  statusDiv.innerHTML = message;
  showAll(false);
}

var xmlDoc;



function managePlayButton() {
  var disable = false;

  if (seatKibitzed != -1) disable = true;

  // disableButton('play', disable);
}

function processXMLData(data) {
  x = data.getElementsByTagName('vhv');
  if (!connected && x.length > 0) {
    connectToAMQ(x[0].getAttribute('q'));
  } else {
    x = data.getElementsByTagName('sc_bm');
    if (x.length > 0) {
      if (!gibThinking) {
        return;
      }
     
      var requestID = x[0].getAttribute('request_id');

      if (parseInt(requestID) == 100 * trick + inTrick && (!vugraphClient || connected)) {
        gibDataReceived(x[0].childNodes);
      }
    } else {
      x = data.getElementsByTagName('lin');

      if (x.length) {
        var chunks = x[0].getElementsByTagName('chunk');
        if (!chunks.length) {
          if (x[0].normalize) {
            x[0].normalize();
          }
          processLinFile(x[0].childNodes[0].nodeValue);
          return;
        } else {
          var linText = '';
          var node;

          for (node = 0; node < chunks.length; node++) {
            if (chunks[node].normalize) {
              chunks[node].normalize();
            }
            linText += chunks[node].childNodes[0].nodeValue;
          }
          processLinFile(linText);
          return;
        }
      }

      fatalError('Error parsing file');
    }
  }
}

function processReqChange() {
  if (xmlDoc.readyState == 4) {
    if (xmlDoc.status == 200) {
      processXMLData(xmlDoc.responseXML);
    } else {
      if (mainDivShowing) {
        showTransientAnnouncement('Service not available', 5);
      } else {
        fatalError('File not found');
      }
    }
  }
}

function loadXMLDoc(dname) {
  try {
    xmlDoc = new XMLHttpRequest();
    xmlDoc.onreadystatechange = processReqChange;
    xmlDoc.open('GET', dname, true);
    xmlDoc.send('');
    return;
  } catch (e) {
    try {
      //Internet Explorer
      xmlDoc = new ActiveXObject('Microsoft.XMLDOM');
    } catch (e) {
      try {
        //Firefox, Mozilla, Opera, etc.
        xmlDoc = document.implementation.createDocument('', '', null);
      } catch (e) {
        alert('ERROR ' + e.message);
      }
    }
  }

  try {
    xmlDoc.async = false;
    xmlDoc.load(dname);
    processXMLData(xmlDoc);
    return;
  } catch (e) {
    alert('ERROR ' + e.message);
  }
  return null;
}

function gup(name, source) {
  name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');

  var regexS = '[\\?&]' + name + '=([^&#]*)';
  var regex = new RegExp(regexS);
  var results;

  if (source) {
    results = regex.exec(source);
  } else {
    results = regex.exec(window.location.href);
  }
  if (results == null) return '';
  else return results[1];
}

function getScrollBarWidth() {
  var inner = document.createElement('p');
  inner.style.width = '100%';
  inner.style.height = '200px';

  var outer = document.createElement('div');
  outer.style.position = 'absolute';
  outer.style.top = '0px';
  outer.style.left = '0px';
  outer.style.visibility = 'hidden';
  outer.style.width = '200px';
  outer.style.height = '150px';
  outer.style.overflow = 'hidden';
  outer.appendChild(inner);

  document.body.appendChild(outer);
  var w1 = inner.offsetWidth;
  outer.style.overflow = 'scroll';
  var w2 = inner.offsetWidth;
  if (w1 == w2) w2 = outer.clientWidth;

  document.body.removeChild(outer);

  return w1 - w2;
}

function getX(obj) {
  var curleft = 0;

  if (obj.offsetParent) {
    while (1) {
      curleft += obj.offsetLeft;
      if (!obj.offsetParent) {
        break;
      }

      obj = obj.offsetParent;
    }
  } else if (obj.x) {
    curleft += obj.x;
  }

  return curleft;
}

function getY(obj) {
  var curtop = 0;

  if (obj.offsetParent) {
    while (1) {
      curtop += obj.offsetTop - obj.scrollTop;
      if (!obj.offsetParent) {
        break;
      }
      obj = obj.offsetParent;
    }
  } else if (obj.y) {
    curtop += obj.y;
  }

  return curtop;
}

function disableSelection(target) {
  if (typeof target.onselectstart != 'undefined') {
    //IE route
    target.onselectstart = function () {
      return false;
    };
  } else if (typeof target.style.MozUserSelect != 'undefined') {
    //Firefox route
    target.style.MozUserSelect = 'none';
  } //All other route (ie: Opera)
  else {
    target.onmousedown = function () {
      return false;
    };
  }

  target.style.cursor = 'default';
}

function loadFromURL(url) {
  statusDiv.innerHTML = 'Loading. Please wait...';
  showAll(false);
  loadXMLDoc(url);
}


function resizeCardDiv(cardDiv) {
  if (cardDiv) {
    cardDiv.image.style.width = cardDiv.clientWidth;
    cardDiv.image.style.height = cardDiv.clientHeight;
    var fontSize = cardDiv.clientHeight / 4;
    cardDiv.topLeftTopDiv.style.fontSize = fontSize;
    cardDiv.botLeftBotDiv.style.fontSize = fontSize + 2;
    cardDiv.topLeftBotDiv.style.fontSize = fontSize + 2;
    cardDiv.botLeftTopDiv.style.fontSize = fontSize;
    cardDiv.middleDiv.style.fontSize = 2 * fontSize;
    var margin = fontSize / 8;
    if (cardDiv.card == 8) {
      cardDiv.topLeftTopDiv.style.left = 0;
    } else {
      cardDiv.topLeftTopDiv.style.left = margin;
    }
    cardDiv.topLeftTopDiv.style.top = margin;
    cardDiv.topLeftBotDiv.style.left = margin;
    cardDiv.topLeftBotDiv.style.top = fontSize;
    cardDiv.botLeftBotDiv.style.left =
      cardDiv.clientWidth - margin - cardDiv.botLeftBotDiv.clientWidth;
    cardDiv.botLeftTopDiv.style.left =
      cardDiv.clientWidth - margin - cardDiv.botLeftTopDiv.clientWidth;
    cardDiv.botLeftBotDiv.style.top =
      cardDiv.clientHeight - margin - cardDiv.botLeftBotDiv.clientHeight;
    cardDiv.botLeftTopDiv.style.top =
      cardDiv.clientHeight - fontSize - cardDiv.botLeftTopDiv.clientHeight;
    cardDiv.middleDiv.style.left = (cardDiv.clientWidth - cardDiv.middleDiv.clientWidth) / 2;
    cardDiv.middleDiv.style.top = (cardDiv.clientHeight - cardDiv.middleDiv.clientHeight) / 2;
  }
}

function maybeResizeCardImage(cardDiv) {
  if (cardDiv && cardDiv.needsResizing) {
    resizeCardDiv(cardDiv);
    cardDiv.needsResizing = false;
  }
}

function setCardImageDivCard(cardDiv, suit, card) {
  if (cardDiv) {
    cardDiv.suit = suit;
    cardDiv.card = card;
    cardDiv.topLeftTopDiv.innerHTML = getCardChar(card);
    cardDiv.botLeftBotDiv.innerHTML = getCardChar(card);
    cardDiv.topLeftBotDiv.innerHTML = suitHTMLs[suit];
    cardDiv.botLeftTopDiv.innerHTML = suitHTMLs[suit];
    cardDiv.middleDiv.innerHTML = suitHTMLs[suit];
    cardDiv.topLeftTopDiv.style.color = getSuitColor(suit);
    cardDiv.botLeftBotDiv.style.color = getSuitColor(suit);
  }
}

function hilightSuitSymbol(hilight) {
  if (whosTurn >= 0 && keyboardSuit >= 0) {
    if (hilight && getDeal) {
      suitSymbols[whosTurn][keyboardSuit].style.background = highlightColor;
    } else {
      suitSymbols[whosTurn][keyboardSuit].style.background = '';
    }
  }
}

function setKeyboardSuit() {
  hilightSuitSymbol(false);
  keyboardSuit = -1;
  if (contractLevel != -1 && whosTurn != -1) {
    var onlySuit = -1;
    var suit;
    for (suit = 0; suit < 4; suit++) {
      if (howManySuit[whosTurn][suit]) {
        if (onlySuit == -1) {
          onlySuit = suit;
        } else {
          onlySuit = -2;
        }
      }
    }

    if (onlySuit >= 0) {
      keyboardSuit = onlySuit;
    } else if (inTrick != 3 && howManySuit[whosTurn][suitPlayed[trick][0]]) {
      keyboardSuit = suitPlayed[trick][0];
    }
  }
  hilightSuitSymbol(true);
}

function charForCardSelection(theChar) {
  var suit;
  for (suit = 0; suit < 4; suit++) {
    if (theChar == suitchars.charAt(suit)) {
      var legal = false;
      if (getDeal) {
        legal = true;
      } else if (whosTurn >= 0 && trick < 13) {
        if (trick < 0) {
          legal = true;
        } else if (howManySuit[whosTurn][suit]) {
          var leadSuit = suitPlayed[trick][0];
          if (inTrick == 3 || howManySuit[whosTurn][leadSuit] == 0 || suit == leadSuit) {
            legal = true;
          }
        }
      }

      if (legal) {
        hilightSuitSymbol(false);
        keyboardSuit = suit;
        hilightSuitSymbol(true);
      }
      return;
    }
  }
  var card;
  if (keyboardSuit >= 0) {
    for (card = 0; card < 13; card++) {
      if (theChar == cardchars.charAt(card)) {
        var cardDiv = new Object();
        cardDiv.suit = keyboardSuit;
        cardDiv.card = card;
        mouseClickCardImage(cardDiv);
        break;
      }
    }
  }
}

function createCardBackDiv() {
  var div = document.createElement('div');
  disableSelection(div);
  div.style.position = 'absolute';
  div.image = document.createElement('img');
  div.image.src = 'cardback.gif';
  div.image.style.width = '100%';
  div.image.style.height = '100%';
  div.appendChild(div.image);
  return div;
}

function createCardImageDiv(suit, card) {
  var div = document.createElement('div');
  disableSelection(div);
  div.style.position = 'absolute';
  div.style.width = '100';
  div.style.height = '100';
  div.needsResizing = true;
  div.image = new Image();
  div.image.style.position = 'absolute';
  div.image.style.top = 0;
  div.image.style.left = 0;
  div.image.src = 'cardbg.gif';
  div.appendChild(div.image);
  div.onmouseover = function () {
    mouseOverCardImage(this);
  };
  div.onmouseout = function () {
    mouseOutCardImage(this);
  };
  div.onclick = function () {
    mouseClickCardImage(this);
  };
  div.onmousedown = function (event) {
    mouseDownCardImage(event);
  };
  div.topLeftTopDiv = document.createElement('div');
  div.topLeftTopDiv.style.position = 'absolute';
  div.appendChild(div.topLeftTopDiv);
  div.topLeftBotDiv = document.createElement('div');
  div.topLeftBotDiv.style.position = 'absolute';
  div.appendChild(div.topLeftBotDiv);
  div.botLeftTopDiv = document.createElement('div');
  div.botLeftTopDiv.style.position = 'absolute';
  div.appendChild(div.botLeftTopDiv);
  div.botLeftBotDiv = document.createElement('div');
  div.botLeftBotDiv.style.position = 'absolute';
  div.appendChild(div.botLeftBotDiv);
  div.middleDiv = document.createElement('div');
  div.middleDiv.style.position = 'absolute';
  div.appendChild(div.middleDiv);
  setCardImageDivCard(div, suit, card);
  return div;
}

function startCardAnimation(seat, suit, rank) {
  if (cardImageDiv[suit][rank]) {
    if (!isHandShowing(seat)) {
      var whichCard = Math.floor(howManyCards[seat] / 2);
      var theDiv = document.getElementById('theDiv');
      theDiv.insertBefore(cardImageDiv[suit][rank], nameBars[seat]);
      cardImageDiv[suit][rank].needsResizing = true;
      maybeResizeCardImage(cardImageDiv[suit][rank]);
      cardImageDiv[suit][rank].style.left = cardBackDiv[seat][whichCard].style.left;
      cardImageDiv[suit][rank].style.top = cardBackDiv[seat][whichCard].style.top;
      theDiv.removeChild(cardBackDiv[seat][whichCard]);
    }
    highlightCard(suit, rank, false);
    cardImageDrifting = cardImageDiv[suit][rank];
    cardImageDrifting.parentNode.insertBefore(cardImageDrifting, null);
    var destinationX = getTrickCardImageLeft(seat);
    var destinationY = getTrickCardImageTop(seat);
    cardAnimationPosX = parseInt(cardImageDrifting.style.left);
    cardAnimationPosY = parseInt(cardImageDrifting.style.top);
    var distanceX = destinationX - cardAnimationPosX;
    var distanceY = destinationY - cardAnimationPosY;
    var totalDistance = Math.sqrt(Math.pow(distanceX, 2) + Math.pow(distanceY, 2));
    var animationDuration = cardAnimationTime * (totalDistance / totalWidth);
    cardAnimationStepsRemaining = Math.floor(animationDuration / cardAnimationStepTime) - 1;
    cardAnimationStepDX = distanceX / cardAnimationStepsRemaining;
    cardAnimationStepDY = distanceY / cardAnimationStepsRemaining;
    moveCard();
  }
}

function endCardAnimation() {
  if (cardImageDrifting) {
    if (cardAnimationTimer) {
      clearTimeout(cardAnimationTimer);
      cardAnimationTimer = null;
    }

    cardAnimationStepsRemaining = 0;
    cardImageDrifting = null;

    if (claimShowing) {
      wasKibitzed = seatKibitzed;
      // setKibitzed('');
    } else {
      populateHands(0, 3, 0, 3);
      showAllTrickCards();
    }
    respondToResize();
  }
}

function moveCard() {
  if (cardImageDrifting) {
    if (cardAnimationStepsRemaining) {
      cardAnimationPosX += cardAnimationStepDX;
      cardAnimationPosY += cardAnimationStepDY;
      cardImageDrifting.style.left = parseInt(cardAnimationPosX);
      cardImageDrifting.style.top = parseInt(cardAnimationPosY);
      cardAnimationStepsRemaining--;
      cardAnimationTimer = setTimeout(moveCard, cardAnimationStepTime);
    } else {
      endCardAnimation();
      if (autoPlayNextCard) {
        autoPlayNextCard = false;
        nextCard(true);
      } else {
        maybePlayCard();
      }
    }
  }
}

function readyForNextDeal() {
  if (dealEndState) {
    dealEndState = false;
    removeTransientAnnouncement();
    if (lessonBoardNumber == dealsInLesson) {
      showAll(false);
      statusDiv.innerHTML = 'Game&nbsp;Over&nbsp;-&nbsp;Score:&nbsp;' + scoreEW;
      gameOverState = true;
      manageStatusDiv();
      manageLeaderBoard();
    } else {
      shuffle();
    }
  }
}

function trickEndTimerTick() {
  if (trickEndTimer) {
    clearTimeout(trickEndTimer);
    trickEndTimer = null;

    if (trick == 12) {
      dealEndState = true;
      showTransientAnnouncement('Click&nbsp;to<br>&nbsp;Continue', -1);
      while (bidSeqPoint >= 0) {
        undo();
      }
      setKibitzed(' ');
      whosTurn = -1;
      manageWhosTurn();
      showTrickResult();
      respondToResize();
    } else {
      maybePlayCard();
    }
  }
}

function maybePlayCard() {
  if (vugraphClient) {
    var target = 4 * trick + inTrick + 1;

    if (playSeqMax >= target && (!playingClient || (!cardImageDrifting && !trickEndTimer))) {
      playSeqPoint = target;
      next();
    }
  }
}

function createCardImageDivs() {
  var suit;
  var card;

  for (suit = 0; suit < 4; suit++) {
    cardImageDiv[suit] = new Array(13);
    cardBackDiv[suit] = new Array(13);

    for (card = 12; card >= 0; card--) {
      cardImageDiv[suit][card] = createCardImageDiv(suit, card);
      cardBackDiv[suit][card] = createCardBackDiv();
    }
  }
}

function showCardImages(visible) {
  var suit;
  var card;

  for (suit = 0; suit < 4; suit++) {
    for (card = 12; card >= 0; card--) {
      if ((!getDeal && !picturesOfCards) || !visible) {
        if (cardImageDiv[suit] && cardImageDiv[suit][card] && cardImageDiv[suit][card].parentNode) {
          cardImageDiv[suit][card].parentNode.removeChild(cardImageDiv[suit][card]);
          cardImageDiv[suit][card].needsResizing = true;
        }
      }
    }
  }
  var seat;
  for (seat = 0; seat < 4; seat++) {
    if (visible) {
      nameBars[seat].style.visibility = 'visible';
    } else {
      nameBars[seat].style.visibility = 'hidden';
    }
  }
}




function resizeButtons() {
  // Define the width and height factors
  var widthFactor = 0.116;
  var heightFactor = 0.17;

  // Calculate the new dimensions
  var newWidth = handWidth * widthFactor;
  var newHeight = handHeight * heightFactor;

  // Select all buttons with the class 'number'
  var buttons = document.querySelectorAll('.number');
  var suitButtons = document.querySelectorAll('.suit');
  var ntButton = document.querySelector('button[data-value="NT"]');
  // Apply the new dimensions to each button
  buttons.forEach(function(button) {
      button.style.marginRight = margin/2000  + 'px';
      button.style.width = newWidth + 'px';
      button.style.height = suitHeight + 'px';
      button.style.fontSize = suitHeight*0.8 + 'px'; // Adjust font size based on height
  });
  suitButtons.forEach(function(button) {
    button.style.marginRight = margin/2000  + 'px';
    button.style.width = newWidth*1.4 + 'px';
    button.style.height = suitHeight + 'px';
    button.style.fontSize = suitHeight*1.15 + 'px'; // Adjust font size based on height
});
  // ntButton.style.fontSize = suitHeight* 0.7 + 'px';
}


function getTheDealer() {
  getSequence = false;
  getDeal = false;
  getDealer = true;
  whosTurn = -1;
  manageWhosTurn();
}



function showVul() {
  if (playingClient) {
    return false;
  }
  return true;
}

function documentLoaded() {
  if (isEditor) {
    initEditorMenu();
    manageStatusDiv();
  }
  setTimeout('respondToResize()', 10);
}

function safeDecode(param) {
  try {
    return decodeURIComponent(param);
  } catch (e) {
    if (e instanceof URIError) {
      return unescape(param);
    } else {
      return param;
    }
  }
}


function hideAnnounceDiv() {
  announceDiv.style.display='none';
}

function getSuitLetter(suit) {
  switch (suit) {
      case '♥':
          return 'H';
      case '♦':
          return 'D';
      case '♠':
          return 'S';
      case '♣':
          return 'C';
      case 'NT':
          return 'N';
      default:
          return suit;
  }
}

function isNumericBid(bid) {
  return /^\d+\w$/.test(bid);
}

// Function to format the text
function formatText(text) {
  const lines = text.split('\n');
  let formattedText = '';
  lines.forEach(line => {
    const trimmedLine = line.trim();
    if (trimmedLine.startsWith('###')) {
      formattedText += `<h3>${trimmedLine.substring(3).trim()}</h3>`;
    } else if (trimmedLine !== '') {
      formattedText += `<p>${trimmedLine}</p>`;
    }
  });
  console.log("Raw text:", text);
  console.log("Formatted text:", formattedText)
  return formattedText;
}

// Function to update the text container
function updateTextContainer() {
  const textContainer = document.getElementById('textContainer');
  const match = currentId.match(/Group(\d+)Deal(\d+)/);
  if (!match) {
    console.error('Invalid ID format');
    return;
  }

  const groupNum = match[1];
  const boardNum = match[2];

  // Construct the deal-specific property name
  const dealPropertyName = `Group${groupNum}Deal${boardNum}`;
  loadGroupTextData();
  // Directly access the Group38dealText object
  if (groupTextData[groupNum] && groupTextData[groupNum].hasOwnProperty(dealPropertyName)) {

    const rawText = groupTextData[groupNum][dealPropertyName];
    const formattedText = formatText(rawText);
  
    // Set the inner HTML of the text container to the formatted text
    textContainer.innerHTML = formattedText;
    
  } else {
    console.error(`Deal text not found for ${dealPropertyName}`);
    textContainer.innerHTML = 'Deal text not available.';
  }
}

function drawHandsBox() {
  const canvas = document.getElementById('boxCanvas');
  const ctx = canvas.getContext('2d');
  
  // Set canvas size to match window
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  


  // Calculate box coordinates
  let left = Math.min(xpos[0], xpos[1], xpos[2], xpos[3]);
  const top = Math.min(ypos[0], ypos[1], ypos[2], ypos[3]);
  let right = Math.max(xpos[0] + handWidth, xpos[1] + handWidth, xpos[2] + handWidth, xpos[3] + handWidth);
  const bottom = Math.max(ypos[0] + handHeight, ypos[1] + handHeight, ypos[2] + handHeight, ypos[3] + handHeight);

  // Add padding to make the box lower
  const padding = 15;
  const topPadding = 25; // Extra padding for the top to lower the box
  const rightShift = 20; // Shift the entire box to the right

  // Adjust both left and right positions
  left += rightShift;
  right += rightShift;

  // Draw the box
    // Clear the entire canvas
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);

  

  ctx.strokeStyle = '#ffce00'; // Yellow color to match the existing border
  ctx.lineWidth = 4;
  ctx.strokeRect(
      left - padding, 
      top - padding + topPadding, 
      right - left + (padding * 2), 
      bottom - top + (padding * 2)
  );
}

function nextHand() {
    // Extract the group number and deal number from the current ID
    const match = currentId.match(/Group(\d+)Deal(\d+)/);
    if (!match) {
        console.error("Invalid ID format");
        return;
    }
    
    const groupNumber = match[1];
    let dealNumber = parseInt(match[2], 10);
    
    // Increment the deal number
    dealNumber += 1;
    
    // Construct the new ID
    const newId = `Group${groupNumber}Deal${dealNumber}`;
    
    // Load the group data if not already loaded
    if (!groupData[groupNumber]) {
        loadGroupData();
    }
    
    // Look up the deal in the loaded data
    if (groupData[groupNumber]) {
        const linkData = groupData[groupNumber].find(item => item.id === newId);
        if (linkData) {
            const fullUrl = `${htmlLoc}?${linkData.query}`;
            window.location.href = fullUrl;
        } else {
            console.error("Link data not found for ID:", newId);
        }
    } else {
        console.error("Data for Group", groupNumber, "not found");
    }
}

function loadGroupData() {
  // Assuming group data variables are already loaded from separate files
  if (typeof group11Data !== 'undefined') groupData['11'] = group11Data;
  if (typeof group12Data !== 'undefined') groupData['12'] = group12Data;
  if (typeof group17Data !== 'undefined') groupData['17'] = group17Data;
  if (typeof group18Data !== 'undefined') groupData['18'] = group18Data;
  if (typeof group19Data !== 'undefined') groupData['19'] = group19Data;
  if (typeof group20Data !== 'undefined') groupData['20'] = group20Data;
  if (typeof group21Data !== 'undefined') groupData['21'] = group21Data;
  if (typeof group22Data !== 'undefined') groupData['22'] = group22Data;
  if (typeof group23Data !== 'undefined') groupData['23'] = group23Data;
  if (typeof group24Data !== 'undefined') groupData['24'] = group24Data;
  if (typeof group25Data !== 'undefined') groupData['25'] = group25Data;
  if (typeof group26Data !== 'undefined') groupData['26'] = group26Data;
  if (typeof group27Data !== 'undefined') groupData['27'] = group27Data;
  if (typeof group28Data !== 'undefined') groupData['28'] = group28Data;
  if (typeof group29Data !== 'undefined') groupData['29'] = group29Data;
  if (typeof group30Data !== 'undefined') groupData['30'] = group30Data;
  if (typeof group31Data !== 'undefined') groupData['31'] = group31Data;
  if (typeof group32Data !== 'undefined') groupData['32'] = group32Data;
  if (typeof group33Data !== 'undefined') groupData['33'] = group33Data;
  if (typeof group34Data !== 'undefined') groupData['34'] = group34Data;
  if (typeof group35Data !== 'undefined') groupData['35'] = group35Data;
  if (typeof group36Data !== 'undefined') groupData['36'] = group36Data;
  if (typeof group37Data !== 'undefined') groupData['37'] = group37Data;
  if (typeof group38Data !== 'undefined') groupData['38'] = group38Data;
  // Add more groups as needed
  
}

function loadGroupTextData() {
  // Directly assign the dealText object to the appropriate group
  console.log("loadGroupTextData() called. currentId is:", currentId); // Log currentId

    // Ensure currentId is defined before trying to match
    if (typeof currentId !== 'string' || !currentId) {
        console.error("loadGroupTextData: currentId is not defined or not a string.");
        return;
    }

    const match = currentId.match(/Group(\d+)/);
    if (match) {
        const currentGroupNumFromFile = match[1]; // e.g., "12", "37"

        // Construct the expected global variable name based on the current group
        const expectedGlobalVarName = `group${currentGroupNumFromFile}DealText`; // e.g., "group12DealText", "group37DealText"
        console.log(`loadGroupTextData: Expecting global variable named: ${expectedGlobalVarName}`);

        // Check if this global variable exists (meaning the corresponding JS file was loaded and defined it)
        if (typeof window[expectedGlobalVarName] !== 'undefined') {
            // Assign the specific group's deal text object to our working object
            groupTextData[currentGroupNumFromFile] = window[expectedGlobalVarName];
            console.log(`loadGroupTextData: SUCCESS - Loaded ${expectedGlobalVarName} into groupTextData for group ${currentGroupNumFromFile}.`);
        } else {
            console.error(`loadGroupTextData: ERROR - Global variable ${expectedGlobalVarName} is UNDEFINED. Was deals${currentGroupNumFromFile}.js loaded and does it define this constant?`);
            // Ensure groupTextData[currentGroupNumFromFile] is at least an empty object
            // to prevent errors if other code tries to access it without checking.
            if (!groupTextData[currentGroupNumFromFile]) {
                groupTextData[currentGroupNumFromFile] = {};
            }
        }
    } else {
        console.error("loadGroupTextData: Could not determine current group from currentId:", currentId);
    }

}
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOMContentLoaded event fired.");

    function initializePageDataAndDisplay() {
        console.log("initializePageDataAndDisplay: Starting actual initialization.");
        console.log("initializePageDataAndDisplay: currentId at this point:", currentId);

        if (typeof currentId !== 'string' || !currentId) {
            console.error("initializePageDataAndDisplay: currentId is not set. Cannot proceed to load text data.");
            // Display a message to the user or set a default if appropriate
            const textContainer = document.getElementById('textContainer');
            if(textContainer) textContainer.innerHTML = 'Please select a deal.';
            return;
        }

        // Load text data for the currentId's group
        loadGroupTextData();

        // Update the text container with the commentary
        if (typeof updateTextContainer === 'function') {
            console.log("initializePageDataAndDisplay: Calling updateTextContainer().");
            updateTextContainer();
        } else {
            console.warn("initializePageDataAndDisplay: updateTextContainer function not found.");
        }

        // Any other UI updates that depend on the initial deal
        if (typeof respondToResize === 'function') respondToResize();
        if (typeof drawHandsBox === 'function') drawHandsBox();
    }

    function waitForDataAndInitialize() {
        console.log("waitForDataAndInitialize: Checking for necessary data and currentId...");
        console.log("waitForDataAndInitialize: currentId is currently:", currentId);

        let groupNumForReadyCheck = null;
        if (typeof currentId === 'string' && currentId) {
            const idMatch = currentId.match(/Group(\d+)/);
            if (idMatch) {
                groupNumForReadyCheck = idMatch[1];
            }
        }

        if (!groupNumForReadyCheck) {
            console.warn("waitForDataAndInitialize: currentId not yet set or invalid. Retrying in 100ms. (This is normal if documentLoaded sets currentId from URL).");
            setTimeout(waitForDataAndInitialize, 100); // Retry
            return;
        }

        const expectedReadyFlagName = `group${groupNumForReadyCheck}DealTextReady`;
        const expectedDataObjectName = `group${groupNumForReadyCheck}DealText`;

        console.log(`waitForDataAndInitialize: Checking for ready flag: window.${expectedReadyFlagName}`);

        if (typeof window[expectedReadyFlagName] === 'boolean' && window[expectedReadyFlagName] === true) {
            console.log(`waitForDataAndInitialize: SUCCESS - ${expectedReadyFlagName} IS true.`);
            
            if (typeof window[expectedDataObjectName] !== 'undefined') {
                console.log(`waitForDataAndInitialize: SUCCESS - window.${expectedDataObjectName} IS defined.`);
                initializePageDataAndDisplay(); // All clear, proceed with full initialization
            } else {
                console.error(`waitForDataAndInitialize: CRITICAL ERROR - ${expectedReadyFlagName} is true, but window.${expectedDataObjectName} is UNDEFINED!`);
                initializePageDataAndDisplay(); // Attempt to initialize anyway, errors will be logged
            }
        } else {
            // console.warn(`waitForDataAndInitialize: ${expectedReadyFlagName} is not yet true or not defined. Retrying in 100ms.`);
            setTimeout(waitForDataAndInitialize, 100); // Retry after a short delay
        }
    }

    // Call documentLoaded() first, as it's responsible for setting up initial state,
    // including potentially parsing URL parameters to set 'currentId'.
    if (typeof documentLoaded === 'function') {
        console.log("DOMContentLoaded: Calling documentLoaded() first...");
        documentLoaded(); // Let this run and potentially set currentId
        
        // After documentLoaded has run (and hopefully set currentId), start polling for the data to be ready.
        // Give a very brief moment for documentLoaded to complete its synchronous tasks.
        setTimeout(waitForDataAndInitialize, 50); 
    } else {
        console.error("DOMContentLoaded: CRITICAL - documentLoaded function not found! Cannot initialize properly.");
        // If documentLoaded is missing, but currentId might be set globally by other means,
        // you could try calling waitForDataAndInitialize directly, but it's risky.
        // setTimeout(waitForDataAndInitialize, 50);
    }
});