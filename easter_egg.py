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

import os
import streamlit as st
import streamlit.components.v1 as components

_EASTER_EGG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "components", "easter_egg")
_easter_egg_component = components.declare_component("sepan_easter_egg", path=_EASTER_EGG_DIR)


def inject_easter_egg():
    """
    Injeta o ouvinte global de eventos e o modal arcade do Pac-Man no DOM principal
    do Streamlit via componente nativo do Streamlit, garantindo persistência total,
    acesso same-origin e execução contínua em qualquer tela e após reruns.
    """
    try:
        _easter_egg_component(key="sepan_pacman_easter_egg")
    except Exception:
        pass
