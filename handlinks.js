// Define the base URL - using your existing configuration
        const htmlPlayLoc = 'handviewer.html';
        const htmlBidLoc = 'bidding.html';
        const htmlLoc = htmlBidLoc;

        // Group configuration - defines the structure of each group
        const groupConfig = {
            '11': { name: 'Squeeze Plays - Part 1', dealStart: 1, dealEnd: 32 },
            '12': { name: 'Squeeze Plays - Part 2', dealStart: 33, dealEnd: 64 },
            '17': { name: 'Play Technique - Part 1', dealStart: 1, dealEnd: 32 },
            '18': { name: 'Play Technique - Part 2', dealStart: 33, dealEnd: 64 },
            '19': { name: 'Finesses - Part 1', dealStart: 1, dealEnd: 32 },
            '20': { name: 'Finesses - Part 2', dealStart: 33, dealEnd: 64 },
            '21': { name: 'Entries - Part 1', dealStart: 1, dealEnd: 32 },
            '22': { name: 'Entries - Part 2', dealStart: 33, dealEnd: 64 },
            '23': { name: 'Help from the enemy - Part 1', dealStart: 1, dealEnd: 32 },
            '24': { name: 'Help from the enemy - Part 2', dealStart: 33, dealEnd: 64 },
            '25': { name: 'Trump Management - Part 1', dealStart: 1, dealEnd: 32 },
            '26': { name: 'Trump Management - Part 2', dealStart: 33, dealEnd: 64 },
            '27': { name: 'Slam Bidding - Part 1', dealStart: 1, dealEnd: 32 },
            '28': { name: 'Slam Bidding - Part 2', dealStart: 33, dealEnd: 64 },
            '29': { name: 'NoTrump Play - Part 1', dealStart: 1, dealEnd: 32 },
            '30': { name: 'NoTrump Play - Part 2', dealStart: 33, dealEnd: 64 },
            '31': { name: 'Trump Play - Part 1', dealStart: 1, dealEnd: 32 },
            '32': { name: 'Trump Play - Part 2', dealStart: 33, dealEnd: 64 },
            '33': { name: 'Match Point Tourn - Part 1', dealStart: 1, dealEnd: 32 },
            '34': { name: 'Match Point Tourn Play  - Part 2', dealStart: 33, dealEnd: 64 },
            '35': { name: 'Safety Plays - Part 1', dealStart: 1, dealEnd: 32 },
            '36': { name: 'Safety Plays - Part 2', dealStart: 33, dealEnd: 64 },
            '37': { name: 'End Plays - Part 1', dealStart: 1, dealEnd: 32 },
            '38': { name: 'End Plays - Part 2', dealStart: 33, dealEnd: 64 }
        };

        // Object to store all group data - will be populated by your existing JS files
        const groupData = {};
        const loadedDealsTextFiles = new Set();
        const dealsTextCache = {};

        function loadDealsTextFile(groupNumber) {
            if (dealsTextCache[groupNumber]) {
                return Promise.resolve(dealsTextCache[groupNumber]);
            }

            if (loadedDealsTextFiles.has(groupNumber)) {
                return Promise.resolve(window[`group${groupNumber}DealText`] || window[`group${groupNumber}DealTextData`] || null);
            }

            return new Promise((resolve, reject) => {
                const script = document.createElement('script');
                script.src = `deals${groupNumber}.js`;
                script.onload = () => {
                    loadedDealsTextFiles.add(groupNumber);
                    const data = window[`group${groupNumber}DealText`] || window[`group${groupNumber}DealTextData`] || null;
                    if (data) {
                        dealsTextCache[groupNumber] = data;
                        resolve(data);
                    } else {
                        reject(new Error(`No deal text data found in deals${groupNumber}.js`));
                    }
                };
                script.onerror = () => reject(new Error(`Unable to load deals${groupNumber}.js`));
                document.head.appendChild(script);
            });
        }

        function getIntroductionText(groupNumber, dealTextData) {
            if (!dealTextData) return '';
            const introKey = `Group${groupNumber}Deal0`;
            return dealTextData[introKey] || '';
        }

        function isHandDiagramLine(line) {
            const trimmed = line.trim();
        
            if (!trimmed) return false;
        
            if (/^(NORTH|SOUTH|EAST|WEST)$/.test(trimmed)) return true;
            if (/^[♠♥♦♣]/.test(trimmed)) return true;
            if (/^(Only three cards are left in each hand\.|Diamonds are trumps, but nobody has any diamonds, so the last few tricks might just as well be at notrump\.)$/i.test(trimmed)) return true;
        
            return false;
        }
        
        function splitIntoBlocks(text) {
            const lines = text.split('\n');
            const blocks = [];
            let paragraphLines = [];
            let i = 0;
        
            function flushParagraph() {
                if (!paragraphLines.length) return;
        
                const paragraphText = paragraphLines.join(' ').replace(/\s+/g, ' ').trim();
                if (paragraphText) {
                    blocks.push({ type: 'paragraph', text: paragraphText });
                }
                paragraphLines = [];
            }
        
            function isSeatLine(line) {
                return /^\s*(NORTH|SOUTH|EAST|WEST)\s*$/.test(line.trim()) ||
                       /^\s*WEST\s+EAST\s*$/.test(line.trim());
            }
        
            function isSuitLine(line) {
                return /^\s*[♠♥♦♣]/.test(line.trim());
            }
        
            function isHandishLine(line) {
                const trimmed = line.trim();
                if (trimmed === '') return true;
                return isSeatLine(line) || isSuitLine(line);
            }
        
            while (i < lines.length) {
                const line = lines[i];
                const trimmed = line.trim();
        
                if (trimmed === '') {
                    flushParagraph();
                    i++;
                    continue;
                }
        
                if (trimmed === 'NORTH') {
                    flushParagraph();
        
                    const handLines = [];
                    let seenSouth = false;
        
                    while (i < lines.length) {
                        const currentLine = lines[i];
                        const currentTrimmed = currentLine.trim();
        
                        if (currentTrimmed === 'SOUTH') {
                            seenSouth = true;
                        }
        
                        if (isHandishLine(currentLine)) {
                            handLines.push(currentLine);
                            i++;
                            continue;
                        }
        
                        if (seenSouth) {
                            break;
                        }
        
                        handLines.push(currentLine);
                        i++;
                    }
        
                    const handText = handLines.join('\n').replace(/\n{3,}/g, '\n\n').trimEnd();
                    if (handText) {
                        blocks.push({ type: 'hand', text: handText });
                    }
                    continue;
                }
        
                paragraphLines.push(trimmed);
                i++;
            }
        
            flushParagraph();
            return blocks;
        }
        
        
        
        function parseHandDiagram(blockText) {
            const lines = blockText.split('\n').map(line => line.trimEnd());
        
            const hands = {
                NORTH: [],
                WEST: [],
                EAST: [],
                SOUTH: []
            };
        
            let current = null;
        
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i].trim();
        
                if (!line) continue;
        
                if (line === 'NORTH' || line === 'SOUTH') {
                    current = line;
                    continue;
                }
        
                if (line === 'WEST EAST' || /^WEST\s+EAST$/.test(line)) {
                    current = 'WEST_EAST';
                    continue;
                }
        
                if (current === 'NORTH' || current === 'SOUTH') {
                    if (/^[♠♥♦♣]/.test(line)) {
                        hands[current].push(line);
                    }
                    continue;
                }
        
                if (current === 'WEST_EAST') {
                    if (/^[♠♥♦♣]/.test(line)) {
                        const match = line.match(/^([♠♥♦♣]\s*[^♠♥♦♣]+?)\s{2,}([♠♥♦♣].*)$/);
                        if (match) {
                            hands.WEST.push(match[1].trim());
                            hands.EAST.push(match[2].trim());
                        } else {
                            const suit = line.charAt(0);
                            const rest = line.slice(1).trim();
                            const split = rest.split(/\s{2,}/);
                            if (split.length >= 2) {
                                hands.WEST.push(`${suit} ${split[0].trim()}`);
                                hands.EAST.push(`${suit} ${split.slice(1).join(' ').trim()}`);
                            }
                        }
                    }
                }
            }
        
            return hands;
        }
        
        function renderHandDiagram(blockText) {
            const hands = parseHandDiagram(blockText);
        
            const wrapper = document.createElement('div');
            wrapper.className = 'hand-diagram-grid';
        
            const north = document.createElement('div');
            north.className = 'hand-seat hand-seat-north';
            north.innerHTML = `<div class="seat-label">NORTH</div>${hands.NORTH.map(line => `<div>${line}</div>`).join('')}`;
        
            const west = document.createElement('div');
            west.className = 'hand-seat hand-seat-west';
            west.innerHTML = `<div class="seat-label">WEST</div>${hands.WEST.map(line => `<div>${line}</div>`).join('')}`;
        
            const east = document.createElement('div');
            east.className = 'hand-seat hand-seat-east';
            east.innerHTML = `<div class="seat-label">EAST</div>${hands.EAST.map(line => `<div>${line}</div>`).join('')}`;
        
            const south = document.createElement('div');
            south.className = 'hand-seat hand-seat-south';
            south.innerHTML = `<div class="seat-label">SOUTH</div>${hands.SOUTH.map(line => `<div>${line}</div>`).join('')}`;
        
            wrapper.appendChild(north);
            wrapper.appendChild(west);
            wrapper.appendChild(east);
            wrapper.appendChild(south);
        
            return wrapper;
        }
        
        function formatIntroductionText(rawText) {
            if (!rawText) return [];
        
            const normalised = rawText
                .replace(/\s+TITLE\s+/g, '\n\nTITLE ')
                .replace(/TITLE\s+Intro\.\.\./g, 'TITLE Introduction')
                .replace(/TITLE\s+The Play\.\.\./g, 'TITLE The Play')
                .replace(/TITLE\s+The Bidding\.\.\./g, 'TITLE The Bidding')
                .replace(/\s+NORTH\b/g, '\nNORTH')
                .replace(/\s+WEST\s+EAST\b/g, '\nWEST EAST')
                .replace(/\s+SOUTH\b/g, '\nSOUTH')
                .replace(/\n{3,}/g, '\n\n')
                .trim();
        
            const parts = normalised.split(/\n\n(?=TITLE )/g).filter(Boolean);
        
            return parts.map(part => {
                let heading = '';
                let body = part.trim();
        
                if (body.startsWith('TITLE ')) {
                    const lines = body.split('\n');
                    heading = lines.shift().replace(/^TITLE\s+/, '').trim();
                    body = lines.join('\n').trim();
                }
        
                const lines = body.split('\n');
                const blocks = [];
                let para = [];
                let i = 0;
        
                function flushPara() {
                    if (!para.length) return;
                    const text = para.join(' ').replace(/\s+/g, ' ').trim();
                    if (text) blocks.push({ type: 'paragraph', text });
                    para = [];
                }
        
                function isSuitLine(t) {
                    return /^[♠♥♦♣]/.test(t);
                }
        
                while (i < lines.length) {
                    const t = lines[i].trim();
        
                    if (!t) {
                        flushPara();
                        i++;
                        continue;
                    }
        
                    if (t === 'NORTH') {
                        flushPara();
                        const handLines = [];
                        while (i < lines.length) {
                            const current = lines[i].trimEnd();
                            const trimmed = current.trim();
        
                            if (
                                trimmed === '' ||
                                trimmed === 'NORTH' ||
                                trimmed === 'SOUTH' ||
                                /^WEST\s+EAST$/.test(trimmed) ||
                                isSuitLine(trimmed)
                            ) {
                                handLines.push(current);
                                i++;
                                continue;
                            }
                            break;
                        }
        
                        blocks.push({
                            type: 'diagram',
                            text: handLines.join('\n').trim()
                        });
                        continue;
                    }
        
                    para.push(t);
                    i++;
                }
        
                flushPara();
                return { heading, blocks };
            });
        }
        
        function showIntroOverlay(title, sections) {
            const overlay = document.getElementById('intro-overlay');
            const modalTitle = document.getElementById('intro-modal-title');
            const modalBody = document.getElementById('intro-modal-body');
        
            modalTitle.textContent = title;
            modalBody.innerHTML = '';
        
            if (!sections || !sections.length) {
                const emptyState = document.createElement('div');
                emptyState.className = 'intro-status';
                emptyState.textContent = 'No introduction text was found for this group.';
                modalBody.appendChild(emptyState);
            } else {
                const wrapper = document.createElement('div');
                wrapper.className = 'intro-content';
        
                sections.forEach(section => {
                    if (section.heading) {
                        const heading = document.createElement('div');
                        heading.className = 'intro-heading';
                        heading.textContent = section.heading;
                        wrapper.appendChild(heading);
                    }
        
                    (section.blocks || []).forEach(block => {
                        if (block.type === 'diagram') {
                            wrapper.appendChild(renderHandDiagram(block.text));
                        } else {
                            const paragraph = document.createElement('p');
                            paragraph.className = 'intro-paragraph';
                            paragraph.textContent = block.text;
                            wrapper.appendChild(paragraph);
                        }
                    });
                });
        
                modalBody.appendChild(wrapper);
            }
        
            overlay.classList.remove('hidden');
            overlay.setAttribute('aria-hidden', 'false');
        }

        function closeIntroOverlay() {
            const overlay = document.getElementById('intro-overlay');
            overlay.classList.add('hidden');
            overlay.setAttribute('aria-hidden', 'true');
        }

        async function handleIntroductionClick() {
            const groupNumber = document.getElementById('group-select').value;
            if (!groupNumber) return;

            const config = groupConfig[groupNumber];
            const introButton = document.getElementById('intro-button');
            introButton.disabled = true;
            introButton.textContent = 'Loading...';

            try {
                const dealTextData = await loadDealsTextFile(groupNumber);
                const introSections = formatIntroductionText(getIntroductionText(groupNumber, dealTextData));
                showIntroOverlay(`${config.name} - Introduction`, introSections);
            } catch (error) {
                showIntroOverlay(`${config ? config.name : 'Group'} - Introduction`, error.message);
            } finally {
                introButton.disabled = false;
                introButton.textContent = 'Introduction';
            }
        }

        // Function to load group data from your existing JS files
        function loadGroupData() {
            // Load data from your existing group JS files
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
            
            console.log('Loaded group data:', Object.keys(groupData));
        }

        // Function to handle link clicks - preserves your existing functionality
        function handleLinkClick(event) {
            event.preventDefault();
            const linkId = event.target.id;
            const groupMatch = linkId.toLowerCase().match(/group(\d+)/);
            
            if (groupMatch) {
                const groupNumber = groupMatch[1];
                
                if (groupData[groupNumber]) {
                    const linkData = groupData[groupNumber].find(item => item.id === linkId);
                    
                    if (linkData) {
                        const fullUrl = `${htmlLoc}?${linkData.query}`;
                        console.log('Navigating to:', fullUrl);
                        window.location.href = fullUrl;
                    } else {
                        console.error('Link data not found for ID:', linkId);
                    }
                } else {
                    console.error(`Data for Group ${groupNumber} not found`);
                }
            } else {
                console.error('Invalid link ID format:', linkId);
            }
        }

        // Function to generate hand links for the selected group
        function generateHandLinks(groupNumber) {
            const config = groupConfig[groupNumber];
            const data = groupData[groupNumber];
            const linkGrid = document.getElementById('link-grid');
            
            if (!config || !data) {
                console.error(`Configuration or data not found for group ${groupNumber}`);
                return;
            }

            // Clear existing links
            linkGrid.innerHTML = '';

            // Generate links based on the deal range for this group
            for (let dealNum = config.dealStart; dealNum <= config.dealEnd; dealNum++) {
                const linkId = `Group${groupNumber}Deal${dealNum}`;
                const linkData = data.find(item => item.id === linkId);
                
                if (linkData) {
                    const link = document.createElement('a');
                    link.className = 'link';
                    link.id = linkId;
                    link.href = '#';
                    link.textContent = `Deal ${dealNum}`;
                    link.addEventListener('click', handleLinkClick);
                    linkGrid.appendChild(link);
                } else {
                    console.warn(`No data found for ${linkId}`);
                }
            }
            
            console.log(`Generated ${linkGrid.children.length} links for group ${groupNumber}`);
        }

        // Function to handle group selection from dropdown
        function handleGroupSelection() {
            const select = document.getElementById('group-select');
            const noSelection = document.getElementById('no-selection');
            const handsDisplay = document.getElementById('hands-display');
            const sectionTitle = document.getElementById('section-title');
            const introButton = document.getElementById('intro-button');

            const selectedGroup = select.value;

            if (selectedGroup === '') {
                noSelection.classList.remove('hidden');
                handsDisplay.classList.add('hidden');
                introButton.disabled = true;
            } else {
                noSelection.classList.add('hidden');
                handsDisplay.classList.remove('hidden');

                const config = groupConfig[selectedGroup];
                sectionTitle.textContent = config.name;
                introButton.disabled = false;

                generateHandLinks(selectedGroup);
            }
        }

        // Function to dynamically populate dropdown (for future extensibility)
        function populateDropdown() {
            const select = document.getElementById('group-select');
            
            // Clear existing options except the first one
            while (select.children.length > 1) {
                select.removeChild(select.lastChild);
            }
            
            // Add options based on available data and configuration
            Object.keys(groupConfig).forEach(groupNumber => {
                if (groupData[groupNumber]) {
                    const option = document.createElement('option');
                    option.value = groupNumber;
                    option.textContent = groupConfig[groupNumber].name;
                    select.appendChild(option);
                }
            });
        }

        // Initialize everything when the page loads
        document.addEventListener('DOMContentLoaded', function() {
            console.log('Page loaded, initializing...');
            
            // Load group data from your JS files
            loadGroupData();
            
            // Populate dropdown (currently static, but ready for dynamic loading)
            // populateDropdown(); // Uncomment this if you want dynamic dropdown population
            
            // Add event listener to dropdown
            const select = document.getElementById('group-select');
            const introButton = document.getElementById('intro-button');
            const introClose = document.getElementById('intro-close');
            const introOverlay = document.getElementById('intro-overlay');

            select.addEventListener('change', handleGroupSelection);
            introButton.addEventListener('click', handleIntroductionClick);
            introClose.addEventListener('click', closeIntroOverlay);
            introOverlay.addEventListener('click', (event) => {
                if (event.target === introOverlay) {
                    closeIntroOverlay();
                }
            });
            document.addEventListener('keydown', (event) => {
                if (event.key === 'Escape') {
                    closeIntroOverlay();
                }
            });
            
            // Initialize display state (no group selected)
            handleGroupSelection();
            
            console.log('Initialization complete');
        });

        // Optional: Function to add new groups dynamically (for future use)
        function addNewGroup(groupNumber, groupName, dealStart, dealEnd, groupDataArray) {
            // Add to configuration
            groupConfig[groupNumber] = {
                name: groupName,
                dealStart: dealStart,
                dealEnd: dealEnd
            };
            
            // Add data
            groupData[groupNumber] = groupDataArray;
            
            // Update dropdown
            populateDropdown();
            
            console.log(`Added new group: ${groupNumber} - ${groupName}`);
        }
