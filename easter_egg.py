"""
=============================================================================
SISTEMA SEPAN - EASTER EGG RETRO ARCADE (PAC-MAN)
Arquivo: easter_egg.py
=============================================================================
Módulo autônomo que injeta o easter egg do clássico jogo Pac-Man com estética
retrô Arcade CRT dos anos 80 e regras 100% fiéis ao jogo original de 1980 (Toru Iwatani).

Regras Oficiais Implementadas:
1. Portão da Casa dos Fantasmas:
   - O Pac-Man NUNCA consegue entrar na casa dos fantasmas nem passar pela porta.
   - Fantasmas vivos saem da porta, mas não podem voltar por ela.
   - Fantasmas devorados (olhos) atravessam a porta livremente para renascer.
2. Comportamento e IA dos 4 Fantasmas:
   - Blinky (Vermelho - "Shadow"): Perseguição direta ao Pac-Man (Target = posição exata).
     Acelera conforme as pílulas acabam (Cruise Elroy 1 e 2).
   - Pinky (Rosa - "Speedy"): Emboscada (Target = 4 ladrilhos à frente da direção do Pac-Man).
   - Inky (Ciano - "Bashful"): Flanqueamento em pinça (Target = Blinky + 2 * (PacMan+2 - Blinky)).
   - Clyde (Laranja - "Pokey"): Covarde (Persegue se distância >= 8 ladrilhos; foge para o
     canto inferior esquerdo se distância < 8).
   - Redução de velocidade dos fantasmas dentro do túnel lateral.
3. Ciclos de Modo e Temporizadores:
   - Alternância precisa de Scatter (cantos) e Chase (perseguição) em ciclos de 7s / 20s.
   - Modo Assustado (Frightened): Fantasmas azuis com movimentação errática lenta (8s)
     e piscando em branco nos últimos 2s.
4. Pontuação e Frutas Bônus:
   - Pílulas normais (Dots): 10 pontos.
   - Power Pellets (Energizers): 50 pontos.
   - Fantasmas devorados consecutivos: 200 -> 400 -> 800 -> 1600 pontos.
   - Cereja Bônus (Cherry): Surge aos 70 e 170 dots comidos, valendo 100 pontos.
   - Placar e High Score salvos no localStorage.
=============================================================================
"""

import streamlit.components.v1 as components


def inject_easter_egg():
    """
    Injeta o ouvinte global de eventos e o modal arcade do Pac-Man no DOM principal
    do Streamlit. Funciona em todos os módulos e telas do sistema.
    """
    html_code = """
    <script>
    (function() {
        const topDoc = window.parent.document;
        const topWin = window.parent;

        if (!topDoc) return;

        // Evita injeção duplicada de listeners se o Streamlit fizer rerun
        if (topDoc.getElementById('sepan-pacman-injected-flag')) {
            return;
        }

        const flag = topDoc.createElement('div');
        flag.id = 'sepan-pacman-injected-flag';
        flag.style.display = 'none';
        topDoc.body.appendChild(flag);

        // =====================================================================
        // CARREGA FONTE RETRO 'Press Start 2P'
        // =====================================================================
        if (!topDoc.getElementById('sepan-retro-font')) {
            const fontLink = topDoc.createElement('link');
            fontLink.id = 'sepan-retro-font';
            fontLink.rel = 'stylesheet';
            fontLink.href = 'https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap';
            topDoc.head.appendChild(fontLink);
        }

        // =====================================================================
        // CRIAÇÃO DO MODAL ARCADE COM FILTRO CRT
        // =====================================================================
        const modalId = 'sepan-arcade-overlay';
        let overlay = topDoc.getElementById(modalId);
        if (!overlay) {
            overlay = topDoc.createElement('div');
            overlay.id = modalId;
            overlay.style.cssText = `
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                background: rgba(3, 4, 10, 0.94);
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                z-index: 9999999;
                justify-content: center;
                align-items: center;
                flex-direction: column;
                user-select: none;
                font-family: 'Press Start 2P', monospace, sans-serif;
                box-sizing: border-box;
                padding: 10px;
                opacity: 0;
                transition: opacity 0.25s ease-out;
            `;

            overlay.innerHTML = `
                <style>
                    #sepan-arcade-overlay * {
                        box-sizing: border-box;
                    }
                    .arcade-cabinet {
                        background: radial-gradient(circle at center, #1e2442 0%, #0a0c16 100%);
                        border: 6px solid #2d365c;
                        border-radius: 20px;
                        box-shadow: 0 0 45px rgba(0, 210, 255, 0.35), inset 0 0 30px rgba(0, 0, 0, 0.95);
                        padding: 14px 18px 18px 18px;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        position: relative;
                        max-width: 96vw;
                        max-height: 96vh;
                        animation: arcadeZoomIn 0.3s cubic-bezier(0.18, 0.89, 0.32, 1.28);
                    }
                    @keyframes arcadeZoomIn {
                        from { transform: scale(0.85); opacity: 0; }
                        to { transform: scale(1); opacity: 1; }
                    }
                    .arcade-marquee {
                        width: 100%;
                        background: linear-gradient(90deg, #ff0055, #ffb852, #00f0ff);
                        border-radius: 8px;
                        padding: 7px 12px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 10px;
                        box-shadow: 0 0 15px rgba(255, 184, 82, 0.5);
                    }
                    .marquee-title {
                        color: #000;
                        font-size: 11px;
                        font-weight: 900;
                        letter-spacing: 1px;
                        display: flex;
                        align-items: center;
                        gap: 8px;
                    }
                    .arcade-close-btn {
                        background: #111;
                        color: #ff3366;
                        border: 2px solid #ff3366;
                        border-radius: 6px;
                        font-family: 'Press Start 2P', monospace;
                        font-size: 10px;
                        padding: 4px 8px;
                        cursor: pointer;
                        transition: all 0.15s ease;
                    }
                    .arcade-close-btn:hover {
                        background: #ff3366;
                        color: #fff;
                        box-shadow: 0 0 10px #ff3366;
                    }
                    /* CRT Bezel e Filtro de Scanlines */
                    .crt-bezel {
                        position: relative;
                        background: #000;
                        border: 10px solid #141622;
                        border-radius: 16px;
                        box-shadow: inset 0 0 35px rgba(0, 0, 0, 0.95), 0 0 20px rgba(33, 33, 222, 0.4);
                        overflow: hidden;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                    }
                    .crt-scanlines {
                        position: absolute;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        pointer-events: none;
                        background: linear-gradient(
                            rgba(18, 16, 16, 0) 50%, 
                            rgba(0, 0, 0, 0.45) 50%
                        );
                        background-size: 100% 4px;
                        z-index: 10;
                    }
                    .crt-glow {
                        position: absolute;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        pointer-events: none;
                        background: radial-gradient(circle at center, rgba(255, 255, 255, 0.03) 0%, rgba(0, 0, 0, 0.5) 100%);
                        box-shadow: inset 0 0 40px rgba(0, 0, 0, 0.9);
                        z-index: 11;
                    }
                    #pacman-canvas {
                        display: block;
                        background-color: #000;
                        image-rendering: pixelated;
                    }
                    .arcade-footer-controls {
                        margin-top: 8px;
                        display: flex;
                        gap: 12px;
                        align-items: center;
                        justify-content: space-between;
                        width: 100%;
                        color: #8892b0;
                        font-size: 8px;
                        line-height: 1.4;
                    }
                    .ctrl-pill {
                        background: rgba(255, 255, 255, 0.08);
                        border: 1px solid rgba(255, 255, 255, 0.15);
                        border-radius: 4px;
                        padding: 2px 5px;
                        color: #64ffda;
                        font-family: monospace;
                        font-size: 9px;
                    }
                    .sound-toggle-btn {
                        background: #1e293b;
                        color: #fbbf24;
                        border: 1px solid #fbbf24;
                        border-radius: 4px;
                        padding: 4px 7px;
                        font-family: 'Press Start 2P', monospace;
                        font-size: 8px;
                        cursor: pointer;
                        transition: all 0.2s;
                    }
                    .sound-toggle-btn:hover {
                        background: #fbbf24;
                        color: #000;
                    }
                    /* Mobile D-Pad */
                    .mobile-dpad {
                        display: none;
                        margin-top: 8px;
                        grid-template-columns: repeat(3, 44px);
                        grid-template-rows: repeat(3, 38px);
                        gap: 4px;
                        justify-content: center;
                    }
                    .dpad-btn {
                        background: #252b48;
                        border: 2px solid #4a5580;
                        color: #fff;
                        border-radius: 6px;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        font-size: 14px;
                        cursor: pointer;
                        user-select: none;
                        touch-action: manipulation;
                    }
                    .dpad-btn:active {
                        background: #ffcc00;
                        color: #000;
                    }
                    @media (max-width: 600px) {
                        .mobile-dpad { display: grid; }
                        .arcade-footer-controls span.desktop-hint { display: none; }
                    }
                </style>

                <div class="arcade-cabinet">
                    <div class="arcade-marquee">
                        <div class="marquee-title">
                            <span>🕹️ PAC-MAN '80</span>
                        </div>
                        <div style="display: flex; gap: 8px;">
                            <button id="pacman-sound-btn" class="sound-toggle-btn" title="Alternar Efeitos Sonoros">SOM: ON</button>
                            <button id="pacman-close-btn" class="arcade-close-btn" title="Fechar (ESC)">✕ SAIR</button>
                        </div>
                    </div>

                    <div class="crt-bezel">
                        <div class="crt-scanlines"></div>
                        <div class="crt-glow"></div>
                        <canvas id="pacman-canvas" width="380" height="470"></canvas>
                    </div>

                    <div class="arcade-footer-controls">
                        <span class="desktop-hint">CONTROLES: <span class="ctrl-pill">▲ ▼ ◄ ►</span> ou <span class="ctrl-pill">W A S D</span> | PAUSAR: <span class="ctrl-pill">ESPAÇO</span></span>
                        <span>EASTER EGG SEPAN</span>
                    </div>

                    <div class="mobile-dpad">
                        <div></div>
                        <div class="dpad-btn" id="dpad-up">▲</div>
                        <div></div>
                        <div class="dpad-btn" id="dpad-left">◄</div>
                        <div class="dpad-btn" id="dpad-center" style="font-size:8px; background:#1b2038;">PAUSE</div>
                        <div class="dpad-btn" id="dpad-right">►</div>
                        <div></div>
                        <div class="dpad-btn" id="dpad-down">▼</div>
                        <div></div>
                    </div>
                </div>
            `;
            topDoc.body.appendChild(overlay);
        }

        // =====================================================================
        // SINTETIZADOR DE ÁUDIO RETRO (Web Audio API Chiptune)
        // =====================================================================
        let audioCtx = null;
        let soundEnabled = true;

        function getAudioContext() {
            if (!audioCtx) {
                const AudioContextClass = topWin.AudioContext || topWin.webkitAudioContext;
                if (AudioContextClass) {
                    audioCtx = new AudioContextClass();
                }
            }
            if (audioCtx && audioCtx.state === 'suspended') {
                audioCtx.resume();
            }
            return audioCtx;
        }

        function playTone(freq, duration, type = 'square', gainVal = 0.08) {
            if (!soundEnabled) return;
            try {
                const ctx = getAudioContext();
                if (!ctx) return;
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = type;
                osc.frequency.setValueAtTime(freq, ctx.currentTime);
                gain.gain.setValueAtTime(gainVal, ctx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start();
                osc.stop(ctx.currentTime + duration);
            } catch(e) {}
        }

        function playWaka(step) {
            if (!soundEnabled) return;
            const freq = step % 2 === 0 ? 440 : 580;
            playTone(freq, 0.06, 'triangle', 0.08);
        }

        function playCoinChime() {
            if (!soundEnabled) return;
            try {
                const ctx = getAudioContext();
                if (!ctx) return;
                const now = ctx.currentTime;
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = 'square';
                osc.frequency.setValueAtTime(987.77, now); // B5
                osc.frequency.setValueAtTime(1318.51, now + 0.1); // E6
                gain.gain.setValueAtTime(0.12, now);
                gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start(now);
                osc.stop(now + 0.35);
            } catch(e) {}
        }

        function playGhostEaten() {
            if (!soundEnabled) return;
            try {
                const ctx = getAudioContext();
                if (!ctx) return;
                const now = ctx.currentTime;
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = 'sawtooth';
                osc.frequency.setValueAtTime(350, now);
                osc.frequency.exponentialRampToValueAtTime(1200, now + 0.28);
                gain.gain.setValueAtTime(0.12, now);
                gain.gain.exponentialRampToValueAtTime(0.001, now + 0.28);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start(now);
                osc.stop(now + 0.28);
            } catch(e) {}
        }

        function playFruitSound() {
            if (!soundEnabled) return;
            try {
                const ctx = getAudioContext();
                if (!ctx) return;
                const now = ctx.currentTime;
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = 'triangle';
                osc.frequency.setValueAtTime(523.25, now);
                osc.frequency.setValueAtTime(659.25, now + 0.08);
                osc.frequency.setValueAtTime(783.99, now + 0.16);
                gain.gain.setValueAtTime(0.15, now);
                gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start(now);
                osc.stop(now + 0.35);
            } catch(e) {}
        }

        function playDeathSound() {
            if (!soundEnabled) return;
            try {
                const ctx = getAudioContext();
                if (!ctx) return;
                const now = ctx.currentTime;
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = 'sawtooth';
                osc.frequency.setValueAtTime(750, now);
                osc.frequency.exponentialRampToValueAtTime(70, now + 0.7);
                gain.gain.setValueAtTime(0.15, now);
                gain.gain.exponentialRampToValueAtTime(0.001, now + 0.7);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start(now);
                osc.stop(now + 0.7);
            } catch(e) {}
        }

        // =====================================================================
        // MOTOR DO JOGO PAC-MAN (HTML5 CANVAS 2D)
        // =====================================================================
        const canvas = topDoc.getElementById('pacman-canvas');
        const ctx = canvas ? canvas.getContext('2d') : null;
        let animationFrameId = null;

        // Mapa do Labirinto Clássico (19 colunas x 22 linhas)
        // 1: Parede Azul | 2: Pílula (10 pts) | 3: Power Pellet (50 pts) | 0: Caminho Vazio | 4: Porta da Casa | 5: Casa dos Fantasmas
        const INITIAL_MAP = [
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,3,2,2,2,2,2,2,2,1,2,2,2,2,2,2,2,3,1],
            [1,2,1,1,2,1,1,1,2,1,2,1,1,1,2,1,1,2,1],
            [1,2,1,1,2,1,1,1,2,1,2,1,1,1,2,1,1,2,1],
            [1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1],
            [1,2,1,1,2,1,2,1,1,1,1,1,2,1,2,1,1,2,1],
            [1,2,2,2,2,1,2,2,2,1,2,2,2,1,2,2,2,2,1],
            [1,1,1,1,2,1,1,1,0,1,0,1,1,1,2,1,1,1,1],
            [0,0,0,1,2,1,0,0,0,0,0,0,0,1,2,1,0,0,0],
            [1,1,1,1,2,1,0,1,1,4,1,1,0,1,2,1,1,1,1],
            [0,0,0,0,2,0,0,1,5,5,5,1,0,0,2,0,0,0,0],
            [1,1,1,1,2,1,0,1,1,1,1,1,0,1,2,1,1,1,1],
            [0,0,0,1,2,1,0,0,0,0,0,0,0,1,2,1,0,0,0],
            [1,1,1,1,2,1,0,1,1,1,1,1,0,1,2,1,1,1,1],
            [1,2,2,2,2,2,2,2,2,1,2,2,2,2,2,2,2,2,1],
            [1,2,1,1,2,1,1,1,2,1,2,1,1,1,2,1,1,2,1],
            [1,3,2,1,2,2,2,2,2,0,2,2,2,2,2,1,2,3,1],
            [1,1,2,1,2,1,2,1,1,1,1,1,2,1,2,1,2,1,1],
            [1,2,2,2,2,1,2,2,2,1,2,2,2,1,2,2,2,2,1],
            [1,2,1,1,1,1,1,1,2,1,2,1,1,1,1,1,1,2,1],
            [1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
        ];

        const TILE_SIZE = 20;
        const MAP_COLS = 19;
        const MAP_ROWS = 22;
        const HEADER_OFFSET = 30;

        let map = [];
        let score = 0;
        let highScore = parseInt(topWin.localStorage.getItem('sepan_pacman_hi') || '0', 10);
        let lives = 3;
        let gameState = 'START'; // 'START', 'PLAYING', 'PAUSED', 'DEATH', 'GAMEOVER', 'VICTORY'
        let totalDots = 0;
        let dotsEaten = 0;
        let wakaCounter = 0;
        let frightenedTimer = 0;
        let ghostScoreMultiplier = 200;
        let floatingScores = [];

        // Fruta Bônus (Cereja: 100 pontos)
        let fruit = {
            active: false,
            col: 9,
            row: 12,
            timer: 0,
            spawned70: false,
            spawned170: false
        };

        // Modo Global dos Fantasmas: Scatter (Dispersão) vs Chase (Perseguição)
        let modeTimer = 0;
        let currentGlobalMode = 'SCATTER'; // 'SCATTER' ou 'CHASE'

        // Pac-Man Player
        const pacman = {
            x: 9 * TILE_SIZE + 10,
            y: 16 * TILE_SIZE + 10 + HEADER_OFFSET,
            dirX: 0,
            dirY: 0,
            nextDirX: 0,
            nextDirY: 0,
            speed: 2.0,
            radius: 8.5,
            mouthAngle: 0.2,
            mouthSpeed: 0.03,
            mouthMax: 0.45,
            rotation: 0,
            reset: function() {
                this.x = 9 * TILE_SIZE + 10;
                this.y = 16 * TILE_SIZE + 10 + HEADER_OFFSET;
                this.dirX = 0;
                this.dirY = 0;
                this.nextDirX = 0;
                this.nextDirY = 0;
                this.mouthAngle = 0.2;
                this.rotation = 0;
            }
        };

        // 4 Fantasmas Clássicos com Personalidades e Algoritmos Originais de 1980
        const ghosts = [
            {
                name: 'Blinky',
                color: '#ff0000',
                spawnTile: { col: 9, row: 8 },
                x: 9 * TILE_SIZE + 10,
                y: 8 * TILE_SIZE + 10 + HEADER_OFFSET,
                dirX: -1, dirY: 0,
                baseSpeed: 2.0,
                speed: 2.0,
                state: 'CHASE', // 'CHASE', 'SCATTER', 'FRIGHTENED', 'EATEN'
                inHouse: false,
                exitTimer: 0,
                scatterCorner: { col: 18, row: 0 } // Canto Superior Direito
            },
            {
                name: 'Pinky',
                color: '#ffb8ff',
                spawnTile: { col: 9, row: 10 },
                x: 9 * TILE_SIZE + 10,
                y: 10 * TILE_SIZE + 10 + HEADER_OFFSET,
                dirX: 0, dirY: -1,
                baseSpeed: 1.8,
                speed: 1.8,
                state: 'SCATTER',
                inHouse: true,
                exitTimer: 90, // ~1.5 segundos
                scatterCorner: { col: 0, row: 0 } // Canto Superior Esquerdo
            },
            {
                name: 'Inky',
                color: '#00ffff',
                spawnTile: { col: 8, row: 10 },
                x: 8 * TILE_SIZE + 10,
                y: 10 * TILE_SIZE + 10 + HEADER_OFFSET,
                dirX: 0, dirY: -1,
                baseSpeed: 1.8,
                speed: 1.8,
                state: 'SCATTER',
                inHouse: true,
                exitTimer: 240, // ~4 segundos
                scatterCorner: { col: 18, row: 21 } // Canto Inferior Direito
            },
            {
                name: 'Clyde',
                color: '#ffb852',
                spawnTile: { col: 10, row: 10 },
                x: 10 * TILE_SIZE + 10,
                y: 10 * TILE_SIZE + 10 + HEADER_OFFSET,
                dirX: 0, dirY: -1,
                baseSpeed: 1.8,
                speed: 1.8,
                state: 'SCATTER',
                inHouse: true,
                exitTimer: 420, // ~7 segundos
                scatterCorner: { col: 0, row: 21 } // Canto Inferior Esquerdo
            }
        ];

        function resetGame(fullReset = true) {
            if (fullReset) {
                map = INITIAL_MAP.map(row => [...row]);
                score = 0;
                lives = 3;
                totalDots = 0;
                dotsEaten = 0;
                fruit.active = false;
                fruit.timer = 0;
                fruit.spawned70 = false;
                fruit.spawned170 = false;
                for (let r = 0; r < MAP_ROWS; r++) {
                    for (let c = 0; c < MAP_COLS; c++) {
                        if (map[r][c] === 2 || map[r][c] === 3) totalDots++;
                    }
                }
            }
            pacman.reset();
            frightenedTimer = 0;
            ghostScoreMultiplier = 200;
            floatingScores = [];
            modeTimer = 0;
            currentGlobalMode = 'SCATTER';

            ghosts.forEach((g) => {
                g.x = g.spawnTile.col * TILE_SIZE + 10;
                g.y = g.spawnTile.row * TILE_SIZE + 10 + HEADER_OFFSET;
                g.dirX = (g.name === 'Blinky') ? -1 : 0;
                g.dirY = (g.name === 'Blinky') ? 0 : -1;
                g.state = 'SCATTER';
                g.inHouse = (g.name !== 'Blinky');
                if (g.name === 'Pinky') g.exitTimer = 90;
                else if (g.name === 'Inky') g.exitTimer = 240;
                else if (g.name === 'Clyde') g.exitTimer = 420;
                else g.exitTimer = 0;
            });
        }

        // =====================================================================
        // VERIFICAÇÕES DE COLISÃO RÍGIDAS
        // =====================================================================

        // Pac-Man: NUNCA entra na porta da casa (4), nem na casa dos fantasmas (5), nem em paredes (1)
        function isPacmanWall(col, row) {
            if (col < 0 || col >= MAP_COLS) return false; // Túnel lateral livre
            if (row < 0 || row >= MAP_ROWS) return true;
            const tile = map[row][col];
            return tile === 1 || tile === 4 || tile === 5;
        }

        // Fantasmas: Paredes (1) sempre bloqueiam
        function isGhostWall(col, row) {
            if (col < 0 || col >= MAP_COLS) return false;
            if (row < 0 || row >= MAP_ROWS) return true;
            return map[row][col] === 1;
        }

        // =====================================================================
        // ALGORITMO ORIGINAL DE TARGETING DOS FANTASMAS (TORU IWATANI - 1980)
        // =====================================================================
        function getGhostTargetTile(ghost) {
            const pacCol = Math.floor((pacman.x - 10 + TILE_SIZE / 2) / TILE_SIZE);
            const pacRow = Math.floor((pacman.y - 10 - HEADER_OFFSET + TILE_SIZE / 2) / TILE_SIZE);

            // 1. Modo Olhos (Eaten): Mira na entrada da casa para renascer
            if (ghost.state === 'EATEN') {
                return { col: 9, row: 8 };
            }

            // 2. Modo Assustado (Frightened): Alvo pseudoaleatório
            if (ghost.state === 'FRIGHTENED') {
                return {
                    col: Math.floor(Math.random() * MAP_COLS),
                    row: Math.floor(Math.random() * MAP_ROWS)
                };
            }

            // 3. Modo Scatter (Dispersão nos 4 cantos)
            if (currentGlobalMode === 'SCATTER' && ghost.state !== 'CHASE') {
                return ghost.scatterCorner;
            }

            // 4. Modo Chase (Perseguição Ativa) - Personalidades Únicas:

            // BLINKY (Vermelho - "Shadow" / Perseguidor Direto)
            // Mira exatamente na posição atual do Pac-Man
            if (ghost.name === 'Blinky') {
                return { col: pacCol, row: pacRow };
            }

            // PINKY (Rosa - "Speedy" / Emboscadora)
            // Mira 4 ladrilhos à frente da direção em que o Pac-Man está andando
            if (ghost.name === 'Pinky') {
                let targetCol = pacCol + pacman.dirX * 4;
                let targetRow = pacRow + pacman.dirY * 4;
                if (pacman.dirY === -1) {
                    targetCol -= 4; // Bug clássico de offset do arcade original
                }
                return { col: targetCol, row: targetRow };
            }

            // INKY (Ciano - "Bashful" / Flanqueador com Vetor do Blinky)
            // Vetor: pega o ponto 2 ladrilhos à frente do Pac-Man, calcula vetor a partir do Blinky e duplica
            if (ghost.name === 'Inky') {
                const blinky = ghosts[0];
                const blinkyCol = Math.floor((blinky.x - 10 + TILE_SIZE / 2) / TILE_SIZE);
                const blinkyRow = Math.floor((blinky.y - 10 - HEADER_OFFSET + TILE_SIZE / 2) / TILE_SIZE);

                let aheadCol = pacCol + pacman.dirX * 2;
                let aheadRow = pacRow + pacman.dirY * 2;
                if (pacman.dirY === -1) {
                    aheadCol -= 2;
                }

                const vecCol = aheadCol - blinkyCol;
                const vecRow = aheadRow - blinkyRow;

                return {
                    col: blinkyCol + vecCol * 2,
                    row: blinkyRow + vecRow * 2
                };
            }

            // CLYDE (Laranja - "Pokey" / Covarde)
            // Se distância >= 8 ladrilhos: Persegue Pac-Man diretamente (como Blinky)
            // Se distância < 8 ladrilhos: Foge para o seu canto inferior esquerdo
            if (ghost.name === 'Clyde') {
                const clydeCol = Math.floor((ghost.x - 10 + TILE_SIZE / 2) / TILE_SIZE);
                const clydeRow = Math.floor((ghost.y - 10 - HEADER_OFFSET + TILE_SIZE / 2) / TILE_SIZE);
                const distTiles = Math.hypot(clydeCol - pacCol, clydeRow - pacRow);

                if (distTiles >= 8) {
                    return { col: pacCol, row: pacRow };
                } else {
                    return ghost.scatterCorner; // { col: 0, row: 21 }
                }
            }

            return { col: pacCol, row: pacRow };
        }

        // =====================================================================
        // CONTROLES DE ENTRADA DO PAC-MAN
        // =====================================================================
        function setPacmanDirection(dx, dy) {
            if (gameState === 'START' || gameState === 'GAMEOVER' || gameState === 'VICTORY') {
                resetGame(gameState === 'GAMEOVER' || gameState === 'VICTORY');
                gameState = 'PLAYING';
                playCoinChime();
            } else if (gameState === 'PAUSED') {
                gameState = 'PLAYING';
            }
            pacman.nextDirX = dx;
            pacman.nextDirY = dy;
        }

        function togglePause() {
            if (gameState === 'PLAYING') {
                gameState = 'PAUSED';
            } else if (gameState === 'PAUSED') {
                gameState = 'PLAYING';
            }
        }

        function handleArcadeKey(e) {
            if (!overlay || overlay.style.display !== 'flex') return;

            const code = e.code || e.key;
            if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space'].includes(e.code)) {
                e.preventDefault();
            }

            if (code === 'Escape') {
                closeArcadeModal();
                return;
            }

            if (code === 'KeyP' || code === 'Space') {
                togglePause();
                return;
            }

            if (code === 'ArrowUp' || code === 'KeyW') setPacmanDirection(0, -1);
            else if (code === 'ArrowDown' || code === 'KeyS') setPacmanDirection(0, 1);
            else if (code === 'ArrowLeft' || code === 'KeyA') setPacmanDirection(-1, 0);
            else if (code === 'ArrowRight' || code === 'KeyD') setPacmanDirection(1, 0);
            else if (code === 'Enter') {
                if (gameState !== 'PLAYING') {
                    resetGame(gameState === 'GAMEOVER' || gameState === 'VICTORY');
                    gameState = 'PLAYING';
                    playCoinChime();
                }
            }
        }

        // =====================================================================
        // LOOP PRINCIPAL DE ATUALIZAÇÃO E FÍSICA A 60 FPS
        // =====================================================================
        function update() {
            if (gameState !== 'PLAYING') return;

            // 1. Atualização dos Ciclos Globais Scatter / Chase
            modeTimer++;
            if (modeTimer < 420) {
                currentGlobalMode = 'SCATTER'; // 7s Scatter inicial
            } else if (modeTimer < 1620) {
                currentGlobalMode = 'CHASE';   // 20s Chase
            } else if (modeTimer < 2040) {
                currentGlobalMode = 'SCATTER'; // 7s Scatter
            } else if (modeTimer < 3240) {
                currentGlobalMode = 'CHASE';   // 20s Chase
            } else if (modeTimer < 3540) {
                currentGlobalMode = 'SCATTER'; // 5s Scatter
            } else {
                currentGlobalMode = 'CHASE';   // Chase permanente
            }

            // 2. Atualização e Movimentação do Pac-Man
            const pGridCol = Math.floor((pacman.x - 10 + TILE_SIZE / 2) / TILE_SIZE);
            const pGridRow = Math.floor((pacman.y - 10 - HEADER_OFFSET + TILE_SIZE / 2) / TILE_SIZE);
            const pCenterX = pGridCol * TILE_SIZE + 10;
            const pCenterY = pGridRow * TILE_SIZE + 10 + HEADER_OFFSET;

            // Reversão imediata em 180° sem esperar interseção
            const isReverse = (pacman.nextDirX === -pacman.dirX && pacman.nextDirY === -pacman.dirY);
            if (isReverse && (pacman.nextDirX !== 0 || pacman.nextDirY !== 0)) {
                pacman.dirX = pacman.nextDirX;
                pacman.dirY = pacman.nextDirY;
                pacman.nextDirX = 0;
                pacman.nextDirY = 0;
            }

            const prevPacX = pacman.x;
            const prevPacY = pacman.y;

            // Avanço do Pac-Man
            pacman.x += pacman.dirX * pacman.speed;
            pacman.y += pacman.dirY * pacman.speed;

            // Checagem se cruzou o centro do ladrilho atual
            const crossedPacCenter = (
                (pacman.dirX === 1 && prevPacX < pCenterX && pacman.x >= pCenterX) ||
                (pacman.dirX === -1 && prevPacX > pCenterX && pacman.x <= pCenterX) ||
                (pacman.dirY === 1 && prevPacY < pCenterY && pacman.y >= pCenterY) ||
                (pacman.dirY === -1 && prevPacY > pCenterY && pacman.y <= pCenterY) ||
                (pacman.dirX === 0 && pacman.dirY === 0)
            );

            if (crossedPacCenter) {
                // Tenta virar na direção enfileirada (nextDir)
                if (pacman.nextDirX !== 0 || pacman.nextDirY !== 0) {
                    const nextCol = pGridCol + pacman.nextDirX;
                    const nextRow = pGridRow + pacman.nextDirY;
                    if (!isPacmanWall(nextCol, nextRow)) {
                        pacman.x = pCenterX;
                        pacman.y = pCenterY;
                        pacman.dirX = pacman.nextDirX;
                        pacman.dirY = pacman.nextDirY;
                        pacman.nextDirX = 0;
                        pacman.nextDirY = 0;
                    }
                }
                // Se a direção atual colidir com parede à frente, para no centro
                if (isPacmanWall(pGridCol + pacman.dirX, pGridRow + pacman.dirY)) {
                    pacman.x = pCenterX;
                    pacman.y = pCenterY;
                    pacman.dirX = 0;
                    pacman.dirY = 0;
                }
            }

            // Animação da boca quando se movimenta
            if (pacman.dirX !== 0 || pacman.dirY !== 0) {
                pacman.mouthAngle += pacman.mouthSpeed;
                if (pacman.mouthAngle > pacman.mouthMax || pacman.mouthAngle < 0.04) {
                    pacman.mouthSpeed = -pacman.mouthSpeed;
                }

                if (pacman.dirX === 1) pacman.rotation = 0;
                else if (pacman.dirX === -1) pacman.rotation = Math.PI;
                else if (pacman.dirY === 1) pacman.rotation = Math.PI / 2;
                else if (pacman.dirY === -1) pacman.rotation = -Math.PI / 2;
            }

            // Túnel lateral de teletransporte
            if (pacman.x < -10) pacman.x = MAP_COLS * TILE_SIZE + 5;
            if (pacman.x > MAP_COLS * TILE_SIZE + 10) pacman.x = -5;

            // Comer Pílulas, Power Pellets e Frutas
            const curTileCol = Math.floor((pacman.x - 10 + TILE_SIZE / 2) / TILE_SIZE);
            const curTileRow = Math.floor((pacman.y - 10 - HEADER_OFFSET + TILE_SIZE / 2) / TILE_SIZE);

            if (curTileCol >= 0 && curTileCol < MAP_COLS && curTileRow >= 0 && curTileRow < MAP_ROWS) {
                const currentTile = map[curTileRow][curTileCol];
                if (currentTile === 2) {
                    map[curTileRow][curTileCol] = 0;
                    score += 10;
                    dotsEaten++;
                    wakaCounter++;
                    playWaka(wakaCounter);
                } else if (currentTile === 3) {
                    map[curTileRow][curTileCol] = 0;
                    score += 50;
                    dotsEaten++;
                    frightenedTimer = 480; // ~8 segundos
                    ghostScoreMultiplier = 200;
                    ghosts.forEach(g => {
                        if (g.state !== 'EATEN') {
                            g.state = 'FRIGHTENED';
                            // Inverte direção ao entrar em Frightened
                            g.dirX = -g.dirX;
                            g.dirY = -g.dirY;
                        }
                    });
                    playTone(850, 0.22, 'square', 0.1);
                }
            }

            // Geração de Fruta Bônus (Cereja: aos 70 e 170 dots)
            if (!fruit.spawned70 && dotsEaten >= 70) {
                fruit.spawned70 = true;
                fruit.active = true;
                fruit.timer = 600; // 10 segundos na tela
            } else if (!fruit.spawned170 && dotsEaten >= 170) {
                fruit.spawned170 = true;
                fruit.active = true;
                fruit.timer = 600;
            }

            if (fruit.active) {
                fruit.timer--;
                if (fruit.timer <= 0) fruit.active = false;

                // Checa se Pac-Man comeu a Cereja
                const distToFruit = Math.hypot(pacman.x - (fruit.col * TILE_SIZE + 10), pacman.y - (fruit.row * TILE_SIZE + 10 + HEADER_OFFSET));
                if (distToFruit < 12) {
                    fruit.active = false;
                    score += 100;
                    playFruitSound();
                    floatingScores.push({
                        text: '+100',
                        x: fruit.col * TILE_SIZE + 10,
                        y: fruit.row * TILE_SIZE + 10 + HEADER_OFFSET,
                        timer: 50
                    });
                }
            }

            if (score > highScore) {
                highScore = score;
                topWin.localStorage.setItem('sepan_pacman_hi', highScore.toString());
            }

            // Vitória
            if (dotsEaten >= totalDots && totalDots > 0) {
                gameState = 'VICTORY';
                playTone(1000, 0.5, 'sine', 0.2);
                return;
            }

            // Temporizador de Frightened
            if (frightenedTimer > 0) {
                frightenedTimer--;
                if (frightenedTimer === 0) {
                    ghosts.forEach(g => {
                        if (g.state === 'FRIGHTENED') g.state = currentGlobalMode;
                    });
                }
            }

            // 3. Atualização dos 4 Fantasmas
            ghosts.forEach((ghost) => {
                // A) Mecânica de Saída da Casa dos Fantasmas
                if (ghost.inHouse) {
                    if (ghost.exitTimer > 0) {
                        ghost.exitTimer--;
                        // Flutua suavemente no ninho enquanto espera
                        ghost.y = (ghost.spawnTile.row * TILE_SIZE + 10 + HEADER_OFFSET) + Math.sin(Date.now() / 150) * 3;
                        return;
                    }

                    // 1. Move horizontalmente até a coluna central da porta (coluna 9)
                    const targetExitX = 9 * TILE_SIZE + 10;
                    if (Math.abs(ghost.x - targetExitX) > 1.2) {
                        ghost.x += (ghost.x < targetExitX ? 1.2 : -1.2);
                        return;
                    }
                    ghost.x = targetExitX;

                    // 2. Move para cima atravessando a porta (linha 8)
                    const targetExitY = 8 * TILE_SIZE + 10 + HEADER_OFFSET;
                    if (ghost.y > targetExitY) {
                        ghost.y -= 1.5;
                        ghost.dirX = 0;
                        ghost.dirY = -1;
                        return;
                    }

                    // 3. Saiu com sucesso da casa
                    ghost.y = targetExitY;
                    ghost.inHouse = false;
                    ghost.dirX = -1;
                    ghost.dirY = 0;
                    ghost.state = (frightenedTimer > 0) ? 'FRIGHTENED' : currentGlobalMode;
                    return;
                }

                // B) Velocidade adaptativa (Cruise Elroy para o Blinky + Túnel + Frightened + Eaten)
                let ghostSpeed = ghost.baseSpeed;
                if (ghost.name === 'Blinky') {
                    const remaining = totalDots - dotsEaten;
                    if (remaining <= 15) ghostSpeed = 2.3; // Cruise Elroy 2
                    else if (remaining <= 30) ghostSpeed = 2.15; // Cruise Elroy 1
                }
                if (ghost.state === 'FRIGHTENED') ghostSpeed = 1.2;
                else if (ghost.state === 'EATEN') ghostSpeed = 3.6; // Olhos voltam voando

                const gCol = Math.floor((ghost.x - 10 + TILE_SIZE / 2) / TILE_SIZE);
                const gRow = Math.floor((ghost.y - 10 - HEADER_OFFSET + TILE_SIZE / 2) / TILE_SIZE);

                // Desaceleração no túnel lateral (linha 10)
                if (gRow === 10 && (gCol <= 3 || gCol >= 15) && ghost.state !== 'EATEN') {
                    ghostSpeed = 0.9;
                }

                ghost.speed = ghostSpeed;

                // C) Movimento e Decisão nas Interseções
                const gCenterX = gCol * TILE_SIZE + 10;
                const gCenterY = gRow * TILE_SIZE + 10 + HEADER_OFFSET;

                const prevGX = ghost.x;
                const prevGY = ghost.y;

                ghost.x += ghost.dirX * ghost.speed;
                ghost.y += ghost.dirY * ghost.speed;

                const crossedGCenter = (
                    (ghost.dirX === 1 && prevGX < gCenterX && ghost.x >= gCenterX) ||
                    (ghost.dirX === -1 && prevGX > gCenterX && ghost.x <= gCenterX) ||
                    (ghost.dirY === 1 && prevGY < gCenterY && ghost.y >= gCenterY) ||
                    (ghost.dirY === -1 && prevGY > gCenterY && ghost.y <= gCenterY) ||
                    (ghost.dirX === 0 && ghost.dirY === 0)
                );

                if (crossedGCenter) {
                    ghost.x = gCenterX;
                    ghost.y = gCenterY;

                    // Se for modo EATEN e chegou na entrada da casa (col 9, row 8 ou 9), desce pelo portão
                    if (ghost.state === 'EATEN' && gCol === 9 && (gRow === 8 || gRow === 9)) {
                        ghost.dirX = 0;
                        ghost.dirY = 1;
                        return;
                    }

                    // Se o fantasma no modo EATEN chegou dentro da casa (row >= 10), RENASCE IMEDIATAMENTE!
                    if (ghost.state === 'EATEN' && gRow >= 10 && (gCol >= 8 && gCol <= 10)) {
                        ghost.state = (frightenedTimer > 0) ? 'FRIGHTENED' : currentGlobalMode;
                        ghost.inHouse = true;
                        ghost.exitTimer = 0; // Respawn instantâneo original do arcade
                        ghost.dirX = 0;
                        ghost.dirY = -1;
                        return;
                    }

                    // Determina o alvo conforme a personalidade única
                    const target = getGhostTargetTile(ghost);

                    // Ordem de prioridade oficial do arcade: CIMA > ESQUERDA > BAIXO > DIREITA
                    const candidates = [
                        { dx: 0, dy: -1 }, // Cima
                        { dx: -1, dy: 0 }, // Esquerda
                        { dx: 0, dy: 1 },  // Baixo
                        { dx: 1, dy: 0 }   // Direita
                    ];

                    let bestDir = null;
                    let bestDistSq = Infinity;

                    candidates.forEach(cand => {
                        // Não pode dar meia-volta imediata a menos que seja modo Frightened ou beco
                        if (cand.dx === -ghost.dirX && cand.dy === -ghost.dirY && ghost.state !== 'FRIGHTENED') {
                            return;
                        }

                        const nCol = gCol + cand.dx;
                        const nRow = gRow + cand.dy;

                        // Checa colisão com paredes externas
                        if (isGhostWall(nCol, nRow)) return;

                        // Porta da casa (4): somente fantasmas mortos (EATEN) podem entrar
                        if (map[nRow] && map[nRow][nCol] === 4 && ghost.state !== 'EATEN') {
                            return;
                        }

                        // Distância Euclidiana ao quadrado até o alvo
                        const distSq = (nCol - target.col) * (nCol - target.col) + (nRow - target.row) * (nRow - target.row);
                        if (distSq < bestDistSq) {
                            bestDistSq = distSq;
                            bestDir = cand;
                        }
                    });

                    // Se todas as direções para frente forem bloqueadas (beco), inverte
                    if (!bestDir) {
                        bestDir = { dx: -ghost.dirX, dy: -ghost.dirY };
                    }

                    ghost.dirX = bestDir.dx;
                    ghost.dirY = bestDir.dy;
                }

                // Túnel lateral para fantasmas
                if (ghost.x < -10) ghost.x = MAP_COLS * TILE_SIZE + 5;
                if (ghost.x > MAP_COLS * TILE_SIZE + 10) ghost.x = -5;

                // D) Checagem de Colisão com o Pac-Man
                const distToPac = Math.hypot(ghost.x - pacman.x, ghost.y - pacman.y);
                if (distToPac < 12) {
                    if (ghost.state === 'FRIGHTENED') {
                        ghost.state = 'EATEN';
                        score += ghostScoreMultiplier;
                        playGhostEaten();
                        floatingScores.push({
                            text: '+' + ghostScoreMultiplier,
                            x: ghost.x,
                            y: ghost.y,
                            timer: 45
                        });
                        ghostScoreMultiplier *= 2;
                    } else if (ghost.state !== 'EATEN') {
                        // Pac-Man é pego por um fantasma ativo
                        lives--;
                        playDeathSound();
                        if (lives <= 0) {
                            gameState = 'GAMEOVER';
                        } else {
                            gameState = 'PAUSED';
                            setTimeout(() => {
                                resetGame(false);
                                gameState = 'PLAYING';
                            }, 1200);
                        }
                    }
                }
            });

            // Textos flutuantes de pontuação
            floatingScores.forEach(fs => fs.timer--);
            floatingScores = floatingScores.filter(fs => fs.timer > 0);
        }

        // =====================================================================
        // RENDERIZAÇÃO GRÁFICA NO CANVAS
        // =====================================================================
        function draw() {
            if (!ctx) return;

            // Fundo Preto do Arcade
            ctx.fillStyle = '#000';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // 1. HUD Superior (1UP, Score, High Score)
            ctx.font = '9px "Press Start 2P", monospace';
            ctx.fillStyle = '#fff';
            ctx.textAlign = 'left';
            ctx.fillText('1UP', 20, 16);
            ctx.fillStyle = '#ffff00';
            ctx.fillText(score.toString().padStart(5, '0'), 20, 28);

            ctx.fillStyle = '#fff';
            ctx.textAlign = 'right';
            ctx.fillText('HIGH SCORE', 360, 16);
            ctx.fillStyle = '#00ffff';
            ctx.fillText(highScore.toString().padStart(5, '0'), 360, 28);

            // 2. Labirinto
            for (let r = 0; r < MAP_ROWS; r++) {
                for (let c = 0; c < MAP_COLS; c++) {
                    const tile = map[r][c];
                    const px = c * TILE_SIZE;
                    const py = r * TILE_SIZE + HEADER_OFFSET;

                    if (tile === 1) {
                        // Paredes em azul neon arcade
                        ctx.fillStyle = '#2121de';
                        ctx.fillRect(px + 1, py + 1, TILE_SIZE - 2, TILE_SIZE - 2);
                        ctx.strokeStyle = '#4242ff';
                        ctx.lineWidth = 1;
                        ctx.strokeRect(px + 2, py + 2, TILE_SIZE - 4, TILE_SIZE - 4);
                    } else if (tile === 2) {
                        // Pílula comum (10 pts)
                        ctx.fillStyle = '#ffb8ae';
                        ctx.beginPath();
                        ctx.arc(px + 10, py + 10, 2.5, 0, Math.PI * 2);
                        ctx.fill();
                    } else if (tile === 3) {
                        // Power Pellet piscante (50 pts)
                        if (Math.floor(Date.now() / 200) % 2 === 0) {
                            ctx.fillStyle = '#ffb8ae';
                            ctx.beginPath();
                            ctx.arc(px + 10, py + 10, 6, 0, Math.PI * 2);
                            ctx.fill();
                        }
                    } else if (tile === 4) {
                        // Porta do ninho dos fantasmas (Rosa claro arcade)
                        ctx.fillStyle = '#ffb8ff';
                        ctx.fillRect(px, py + 8, TILE_SIZE, 4);
                    }
                }
            }

            // Fruta Bônus (Cereja Clássica: 100 pts)
            if (fruit.active) {
                const fx = fruit.col * TILE_SIZE + 10;
                const fy = fruit.row * TILE_SIZE + 10 + HEADER_OFFSET;

                // Duas cerejas vermelhas
                ctx.fillStyle = '#ff0033';
                ctx.beginPath();
                ctx.arc(fx - 3, fy + 2, 4, 0, Math.PI * 2);
                ctx.arc(fx + 3, fy + 3, 4, 0, Math.PI * 2);
                ctx.fill();

                // Cabinho verde
                ctx.strokeStyle = '#00ff66';
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                ctx.moveTo(fx - 3, fy);
                ctx.quadraticCurveTo(fx, fy - 5, fx + 2, fy - 6);
                ctx.moveTo(fx + 3, fy);
                ctx.quadraticCurveTo(fx + 2, fy - 4, fx + 2, fy - 6);
                ctx.stroke();
            }

            // 3. Pac-Man
            ctx.save();
            ctx.translate(pacman.x, pacman.y);
            ctx.rotate(pacman.rotation);
            ctx.fillStyle = '#ffff00';
            ctx.beginPath();
            ctx.arc(0, 0, pacman.radius, pacman.mouthAngle * Math.PI, (2 - pacman.mouthAngle) * Math.PI);
            ctx.lineTo(0, 0);
            ctx.closePath();
            ctx.fill();
            ctx.restore();

            // 4. Fantasmas
            ghosts.forEach(ghost => {
                ctx.save();
                ctx.translate(ghost.x, ghost.y);

                let bodyColor = ghost.color;
                if (ghost.state === 'FRIGHTENED') {
                    // Pisca branco nos últimos 2 segundos
                    if (frightenedTimer < 120 && Math.floor(frightenedTimer / 15) % 2 === 0) {
                        bodyColor = '#ffffff';
                    } else {
                        bodyColor = '#1d27ff';
                    }
                }

                if (ghost.state !== 'EATEN') {
                    // Corpo do Fantasma
                    ctx.fillStyle = bodyColor;
                    ctx.beginPath();
                    ctx.arc(0, -2, 8, Math.PI, 0, false);
                    ctx.lineTo(8, 6);
                    // Tentáculos ondulados na base
                    ctx.lineTo(5, 4);
                    ctx.lineTo(2, 6);
                    ctx.lineTo(-1, 4);
                    ctx.lineTo(-4, 6);
                    ctx.lineTo(-8, 4);
                    ctx.lineTo(-8, -2);
                    ctx.closePath();
                    ctx.fill();
                }

                // Olhos
                if (ghost.state === 'FRIGHTENED') {
                    ctx.fillStyle = '#ffb8ae';
                    ctx.beginPath();
                    ctx.arc(-3, -2, 1.5, 0, Math.PI * 2);
                    ctx.arc(3, -2, 1.5, 0, Math.PI * 2);
                    ctx.fill();
                } else {
                    // Olhos brancos que olham na direção do movimento
                    ctx.fillStyle = '#ffffff';
                    ctx.beginPath();
                    ctx.arc(-3.5 + ghost.dirX * 1.5, -3 + ghost.dirY * 1.5, 3, 0, Math.PI * 2);
                    ctx.arc(3.5 + ghost.dirX * 1.5, -3 + ghost.dirY * 1.5, 3, 0, Math.PI * 2);
                    ctx.fill();

                    // Pupilas azuis
                    ctx.fillStyle = '#0000ff';
                    ctx.beginPath();
                    ctx.arc(-3.5 + ghost.dirX * 2.5, -3 + ghost.dirY * 2.5, 1.5, 0, Math.PI * 2);
                    ctx.arc(3.5 + ghost.dirX * 2.5, -3 + ghost.dirY * 2.5, 1.5, 0, Math.PI * 2);
                    ctx.fill();
                }

                ctx.restore();
            });

            // 5. Pontuações Flutuantes (+200, +400, +100 Cereja, etc.)
            floatingScores.forEach(fs => {
                ctx.font = '8px "Press Start 2P", monospace';
                ctx.fillStyle = fs.text === '+100' ? '#ff3366' : '#00ffff';
                ctx.textAlign = 'center';
                ctx.fillText(fs.text, fs.x, fs.y);
            });

            // 6. Rodapé do Canvas (Vidas Restantes e Indicador de Cereja)
            for (let i = 0; i < lives; i++) {
                const lx = 20 + i * 22;
                const ly = canvas.height - 10;
                ctx.fillStyle = '#ffff00';
                ctx.beginPath();
                ctx.arc(lx, ly, 7, 0.2 * Math.PI, 1.8 * Math.PI);
                ctx.lineTo(lx, ly);
                ctx.closePath();
                ctx.fill();
            }

            // Ícone da cereja no canto inferior direito
            ctx.fillStyle = '#ff0033';
            ctx.beginPath();
            ctx.arc(canvas.width - 24, canvas.height - 8, 3.5, 0, Math.PI * 2);
            ctx.arc(canvas.width - 18, canvas.height - 7, 3.5, 0, Math.PI * 2);
            ctx.fill();

            // 7. Telas de Estado (START, PAUSED, GAMEOVER, VICTORY)
            if (gameState === 'START') {
                ctx.fillStyle = 'rgba(0, 0, 0, 0.75)';
                ctx.fillRect(0, 160, canvas.width, 160);
                ctx.font = '13px "Press Start 2P", monospace';
                ctx.fillStyle = '#ffff00';
                ctx.textAlign = 'center';
                ctx.fillText('READY!', canvas.width / 2, 215);

                ctx.font = '8px "Press Start 2P", monospace';
                ctx.fillStyle = '#fff';
                ctx.fillText('PRESSIONE SETA OU ESPAÇO', canvas.width / 2, 255);
                ctx.fillStyle = '#64ffda';
                ctx.fillText('PARA JOGAR', canvas.width / 2, 275);
            } else if (gameState === 'PAUSED') {
                ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
                ctx.fillRect(0, 200, canvas.width, 80);
                ctx.font = '12px "Press Start 2P", monospace';
                ctx.fillStyle = '#ffcc00';
                ctx.textAlign = 'center';
                ctx.fillText('PAUSADO', canvas.width / 2, 245);
            } else if (gameState === 'GAMEOVER') {
                ctx.fillStyle = 'rgba(0, 0, 0, 0.85)';
                ctx.fillRect(0, 180, canvas.width, 120);
                ctx.font = '14px "Press Start 2P", monospace';
                ctx.fillStyle = '#ff0033';
                ctx.textAlign = 'center';
                ctx.fillText('GAME OVER', canvas.width / 2, 230);
                ctx.font = '8px "Press Start 2P", monospace';
                ctx.fillStyle = '#fff';
                ctx.fillText('PRESSIONE ESPAÇO / TOQUE', canvas.width / 2, 265);
            } else if (gameState === 'VICTORY') {
                ctx.fillStyle = 'rgba(0, 0, 0, 0.85)';
                ctx.fillRect(0, 180, canvas.width, 120);
                ctx.font = '13px "Press Start 2P", monospace';
                ctx.fillStyle = '#00ff66';
                ctx.textAlign = 'center';
                ctx.fillText('VOCÊ VENCEU! ★', canvas.width / 2, 230);
                ctx.font = '8px "Press Start 2P", monospace';
                ctx.fillStyle = '#fff';
                ctx.fillText('PRESSIONE ESPAÇO / NOVO JOGO', canvas.width / 2, 265);
            }
        }

        function gameLoop() {
            update();
            draw();
            animationFrameId = requestAnimationFrame(gameLoop);
        }

        // =====================================================================
        // CONTROLE DO MODAL DO EASTER EGG
        // =====================================================================
        function openArcadeModal() {
            if (!overlay) return;
            overlay.style.display = 'flex';
            setTimeout(() => {
                overlay.style.opacity = '1';
            }, 10);

            resetGame(true);
            gameState = 'START';
            playCoinChime();

            if (!animationFrameId) {
                gameLoop();
            }
        }

        function closeArcadeModal() {
            if (!overlay) return;
            overlay.style.opacity = '0';
            setTimeout(() => {
                overlay.style.display = 'none';
                if (animationFrameId) {
                    cancelAnimationFrame(animationFrameId);
                    animationFrameId = null;
                }
            }, 250);
        }

        // Ligações dos botões da interface
        const closeBtn = topDoc.getElementById('pacman-close-btn');
        if (closeBtn) closeBtn.onclick = closeArcadeModal;

        const soundBtn = topDoc.getElementById('pacman-sound-btn');
        if (soundBtn) {
            soundBtn.onclick = function() {
                soundEnabled = !soundEnabled;
                soundBtn.textContent = soundEnabled ? 'SOM: ON' : 'SOM: OFF';
                soundBtn.style.color = soundEnabled ? '#fbbf24' : '#888';
                soundBtn.style.borderColor = soundEnabled ? '#fbbf24' : '#888';
                if (soundEnabled) playCoinChime();
            };
        }

        // Controles de Toque / D-Pad
        const dUp = topDoc.getElementById('dpad-up');
        const dDown = topDoc.getElementById('dpad-down');
        const dLeft = topDoc.getElementById('dpad-left');
        const dRight = topDoc.getElementById('dpad-right');
        const dCenter = topDoc.getElementById('dpad-center');

        if (dUp) dUp.onclick = () => setPacmanDirection(0, -1);
        if (dDown) dDown.onclick = () => setPacmanDirection(0, 1);
        if (dLeft) dLeft.onclick = () => setPacmanDirection(-1, 0);
        if (dRight) dRight.onclick = () => setPacmanDirection(1, 0);
        if (dCenter) dCenter.onclick = () => togglePause();

        // =====================================================================
        // DETECTOR DO CÓDIGO KONAMI E ATALHOS SECRETOS
        // ↑ ↑ ↓ ↓ ← → ← → B A
        // =====================================================================
        const KONAMI_SEQUENCE = [
            'ArrowUp', 'ArrowUp',
            'ArrowDown', 'ArrowDown',
            'ArrowLeft', 'ArrowRight',
            'ArrowLeft', 'ArrowRight',
            'b', 'a'
        ];
        let konamiIndex = 0;

        function checkKonamiCode(e) {
            // Se o modal estiver aberto, repassa os comandos para o jogo
            if (overlay && overlay.style.display === 'flex') {
                handleArcadeKey(e);
                return;
            }

            const key = e.key.toLowerCase();
            const expected = KONAMI_SEQUENCE[konamiIndex].toLowerCase();

            const isMatch = (key === expected) || 
                            (expected === 'b' && (e.code === 'KeyB' || key === 'b')) ||
                            (expected === 'a' && (e.code === 'KeyA' || key === 'a'));

            if (isMatch) {
                konamiIndex++;
                if (konamiIndex === KONAMI_SEQUENCE.length) {
                    konamiIndex = 0;
                    openArcadeModal();
                }
            } else {
                if (key === KONAMI_SEQUENCE[0].toLowerCase() || e.code === 'ArrowUp') {
                    konamiIndex = 1;
                } else {
                    konamiIndex = 0;
                }
            }
        }

        // Adiciona ouvinte global de teclado no documento principal
        topDoc.addEventListener('keydown', checkKonamiCode, true);
        window.addEventListener('keydown', checkKonamiCode, true);

    })();
    </script>
    """
    components.html(html_code, height=0, width=0)
