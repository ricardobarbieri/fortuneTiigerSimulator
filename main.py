import pygame
import random
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict

# Inicializa o Pygame
pygame.init()

# Configurações da janela
WIDTH, HEIGHT = 1200, 850
GRID_SIZE = 3
CELL_SIZE = 160
GRID_OFFSET_X = (WIDTH - GRID_SIZE * CELL_SIZE - 350) // 2
GRID_OFFSET_Y = 120
BUTTON_WIDTH, BUTTON_HEIGHT = 180, 80
BUTTON_SPACING = 25
PANEL_WIDTH = 320
FONT = pygame.font.SysFont("helvetica", 32, bold=True)
INFO_FONT = pygame.font.SysFont("helvetica", 26)
LABEL_FONT = pygame.font.SysFont("helvetica", 22)

# Símbolos
SYMBOLS = {
    "tigre": {"color": (255, 215, 0), "gradient": (255, 255, 100), "payout": 25, "prob": 0.03},
    "jade": {"color": (0, 200, 0), "gradient": (100, 255, 100), "payout": 10, "prob": 0.07},
    "saco": {"color": (255, 165, 0), "gradient": (255, 200, 100), "payout": 5, "prob": 0.10},
    "moeda": {"color": (255, 255, 0), "gradient": (255, 255, 150), "payout": 2, "prob": 0.15},
    "sino": {"color": (192, 192, 192), "gradient": (220, 220, 220), "payout": 1, "prob": 0.20},
    "laranja": {"color": (255, 100, 0), "gradient": (255, 150, 100), "payout": 0.5, "prob": 0.20},
    "fogo": {"color": (200, 0, 0), "gradient": (255, 100, 100), "payout": 0.3, "prob": 0.25},
}

# Classe do jogo
class FortuneTiger:
    def __init__(self):
        self.reels = np.array([["fogo" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)])
        self.bet = 1.00
        self.balance = 1000.00
        self.total_bet = 0.00
        self.total_win = 0.00
        self.spin_history = []
        self.balance_history = [self.balance]
        self.bonus_active = False
        self.animating = False
        self.anim_frame = 0
        self.anim_reels = [[] for _ in range(GRID_SIZE)]
        self.particles = []
        self.bonus_progress = 0.0
        self.shake_frame = 0
        self.last_win = 0.0
        self.balance_display = self.balance
        self.win_display = 0.0

    def spin(self):
        if self.animating:
            return 0
        self.animating = True
        self.anim_frame = 0
        symbols = list(SYMBOLS.keys())
        probs = [SYMBOLS[s]["prob"] for s in symbols]

        for i in range(GRID_SIZE):
            self.anim_reels[i] = [random.choices(symbols, probs)[0] for _ in range(25)]

        self.reels = np.array([[random.choices(symbols, probs)[0] for _ in range(GRID_SIZE)]
                              for _ in range(GRID_SIZE)])

        if self.bonus_active:
            chosen_symbol = random.choice([s for s in symbols if s != "tigre"])
            self.reels = np.array([[random.choice([chosen_symbol, "tigre", chosen_symbol])
                                   for _ in range(GRID_SIZE)]
                                  for _ in range(GRID_SIZE)])

        win = self.check_paylines()
        if self.bonus_active and np.any(self.reels != "tigre"):
            win *= 10

        if win > 2500 * self.bet:
            win = 2500 * self.bet

        self.total_bet += self.bet
        self.balance -= self.bet
        self.total_win += win
        self.balance += win
        self.spin_history.append(win)
        self.balance_history.append(self.balance)
        self.last_win = win
        self.bonus_active = False
        self.bonus_progress = min(self.bonus_progress + random.uniform(0.05, 0.15), 1.0)
        if self.bonus_progress >= 1.0:
            self.bonus_progress = 0.0

        if win > 0:
            self.shake_frame = 30
            for _ in range(int(win * 15)):
                self.particles.append({
                    "pos": [GRID_OFFSET_X + random.randint(0, GRID_SIZE * CELL_SIZE),
                            GRID_OFFSET_Y + random.randint(0, GRID_SIZE * CELL_SIZE)],
                    "vel": [random.uniform(-4, 4), random.uniform(-4, 4)],
                    "life": 100,
                    "color": (random.randint(200, 255), random.randint(150, 255), random.randint(0, 50))
                })

        return win

    def check_paylines(self):
        paylines = [
            [(0, 0), (0, 1), (0, 2)],
            [(1, 0), (1, 1), (1, 2)],
            [(2, 0), (2, 1), (2, 2)],
            [(0, 0), (1, 1), (2, 2)],
            [(0, 2), (1, 1), (2, 0)]
        ]
        total_win = 0

        for line in paylines:
            symbols_in_line = [self.reels[i][j] for i, j in line]
            if symbols_in_line[0] == symbols_in_line[1] == symbols_in_line[2]:
                total_win += SYMBOLS[symbols_in_line[0]]["payout"] * self.bet
            elif "tigre" in symbols_in_line:
                non_wild = [s for s in symbols_in_line if s != "tigre"]
                if len(set(non_wild)) == 1 and non_wild:
                    total_win += SYMBOLS[non_wild[0]]["payout"] * self.bet

        return total_win

    def trigger_bonus(self):
        self.bonus_active = random.random() < 0.01 or self.bonus_progress >= 1.0

    def update_particles(self):
        for p in self.particles[:]:
            p["pos"][0] += p["vel"][0]
            p["pos"][1] += p["vel"][1]
            p["life"] -= 1
            if p["life"] <= 0:
                self.particles.remove(p)

    def update_display(self):
        # Animação suave para saldo e ganhos
        if abs(self.balance_display - self.balance) > 0.01:
            self.balance_display += (self.balance - self.balance_display) * 0.1
        if abs(self.win_display - self.last_win) > 0.01:
            self.win_display += (self.last_win - self.win_display) * 0.1

# Desenha gradiente
def draw_gradient_rect(screen, rect, color1, color2, border_radius=0):
    x, y, w, h = rect
    surface = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(h):
        ratio = i / h
        color = tuple(int(c1 + (c2 - c1) * ratio) for c1, c2 in zip(color1, color2))
        pygame.draw.line(surface, color, (0, i), (w, i))
    screen.blit(surface, (x, y))
    if border_radius:
        pygame.draw.rect(screen, (255, 255, 255, 120), rect, 3, border_radius=border_radius)

# Desenha a grade
def draw_grid(screen, game):
    grid_rect = (GRID_OFFSET_X - 25, GRID_OFFSET_Y - 25,
                 GRID_SIZE * CELL_SIZE + 50, GRID_SIZE * CELL_SIZE + 50)
    draw_gradient_rect(screen, grid_rect, (60, 60, 120), (20, 20, 60), border_radius=20)

    offset_x = offset_y = 0
    if game.shake_frame > 0:
        offset_x = random.randint(-6, 6)
        offset_y = random.randint(-6, 6)
        game.shake_frame -= 1

    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if game.animating:
                frame = min(game.anim_frame // (7 * (j + 1)), 24)
                symbol = game.anim_reels[j][frame] if frame < len(game.anim_reels[j]) else game.reels[i][j]
            else:
                symbol = game.reels[i][j]

            rect = (GRID_OFFSET_X + j * CELL_SIZE + offset_x,
                    GRID_OFFSET_Y + i * CELL_SIZE + offset_y,
                    CELL_SIZE, CELL_SIZE)
            draw_gradient_rect(screen, rect, SYMBOLS[symbol]["color"],
                              SYMBOLS[symbol]["gradient"], border_radius=12)
            
            pygame.draw.circle(screen, (255, 255, 255, 60),
                              (rect[0] + CELL_SIZE // 2, rect[1] + CELL_SIZE // 2),
                              CELL_SIZE // 2, 1)
            
            text = FONT.render(symbol[:4], True, (255, 255, 255))
            text_rect = text.get_rect(center=(rect[0] + CELL_SIZE // 2, rect[1] + CELL_SIZE // 2))
            screen.blit(text, text_rect)

    if game.bonus_active:
        glow = (255, 255, 0, 160) if game.anim_frame % 15 < 7 else (255, 200, 0, 160)
        pygame.draw.rect(screen, glow,
                         (GRID_OFFSET_X - 30 + offset_x, GRID_OFFSET_Y - 30 + offset_y,
                          GRID_SIZE * CELL_SIZE + 60, GRID_SIZE * CELL_SIZE + 60),
                         6, border_radius=25)
        
        notify = FONT.render("Bônus Ativado!", True, (255, 255, 0))
        screen.blit(notify, (GRID_OFFSET_X + (GRID_SIZE * CELL_SIZE - notify.get_width()) // 2,
                            GRID_OFFSET_Y - 80))

# Desenha partículas
def draw_particles(screen, game):
    for p in game.particles:
        size = max(1, p["life"] // 8)
        pygame.draw.circle(screen, p["color"], 
                          (int(p["pos"][0]), int(p["pos"][1])), size)

# Desenha botão
def draw_button(screen, rect, text, color, hover, label, clicked):
    scale = 1.1 if clicked else 1.0
    scaled_rect = rect.inflate(rect.width * (scale - 1), rect.height * (scale - 1))
    
    if hover:
        bright_color = tuple(min(c + 40, 255) for c in color)
        draw_gradient_rect(screen, scaled_rect, color, bright_color, border_radius=15)
        pygame.draw.rect(screen, (255, 255, 255, 180), scaled_rect, 4, border_radius=15)
    else:
        draw_gradient_rect(screen, scaled_rect, color, 
                          tuple(min(c + 20, 255) for c in color), border_radius=15)

    text_surf = FONT.render(text, True, (255, 255, 255))
    text_rect = text_surf.get_rect(center=scaled_rect.center)
    screen.blit(text_surf, text_rect)

    label_surf = LABEL_FONT.render(label, True, (220, 220, 255))
    label_rect = label_surf.get_rect(midtop=(scaled_rect.centerx, scaled_rect.bottom + 8))
    screen.blit(label_surf, label_rect)

# Desenha a interface
def draw_ui(screen, game, mouse_pos, clicked_button):
    panel_rect = (WIDTH - PANEL_WIDTH - 30, 30, PANEL_WIDTH, HEIGHT - 60)
    draw_gradient_rect(screen, panel_rect, (40, 40, 100), (15, 15, 60), border_radius=20)

    buttons = [
        {"rect": pygame.Rect(WIDTH - PANEL_WIDTH + 60, HEIGHT - 120 - 3 * (BUTTON_HEIGHT + BUTTON_SPACING),
                            BUTTON_WIDTH, BUTTON_HEIGHT),
         "text": "Girar", "color": (0, 160, 0), "label": "Iniciar um giro"},
        {"rect": pygame.Rect(WIDTH - PANEL_WIDTH + 60, HEIGHT - 120 - 2 * (BUTTON_HEIGHT + BUTTON_SPACING),
                            BUTTON_WIDTH // 2, BUTTON_HEIGHT // 2),
         "text": "+", "color": (0, 120, 220), "label": "Aumentar aposta"},
        {"rect": pygame.Rect(WIDTH - PANEL_WIDTH + 60 + BUTTON_WIDTH // 2 + 15,
                            HEIGHT - 120 - 2 * (BUTTON_HEIGHT + BUTTON_SPACING),
                            BUTTON_WIDTH // 2, BUTTON_HEIGHT // 2),
         "text": "-", "color": (220, 0, 0), "label": "Diminuir aposta"},
        {"rect": pygame.Rect(WIDTH - PANEL_WIDTH + 60, HEIGHT - 120 - (BUTTON_HEIGHT + BUTTON_SPACING),
                            BUTTON_WIDTH, BUTTON_HEIGHT),
         "text": "Estatísticas", "color": (160, 0, 160), "label": "Ver gráficos"}
    ]

    hover_states = []
    for i, button in enumerate(buttons):
        hover = button["rect"].collidepoint(mouse_pos)
        clicked = clicked_button == i
        draw_button(screen, button["rect"], button["text"], button["color"], 
                   hover, button["label"], clicked)
        hover_states.append(hover)

    game.update_display()
    info_texts = [
        f"Saldo: R${game.balance_display:.2f}",
        f"Aposta: R${game.bet:.2f}",
        f"Último Ganho: R${game.win_display:.2f}",
        f"RTP: {100 * game.total_win / game.total_bet:.2f}%" if game.total_bet > 0 else "RTP: 0%",
        "Teclas: 'S' (Girar), 'P' (Gráficos)"
    ]
    for i, text in enumerate(info_texts):
        text_surf = INFO_FONT.render(text, True, (220, 220, 255))
        screen.blit(text_surf, (WIDTH - PANEL_WIDTH + 50, 50 + i * 60))

    progress_rect = (WIDTH - PANEL_WIDTH + 50, 50 + len(info_texts) * 60 + 30, 220, 25)
    pygame.draw.rect(screen, (60, 60, 60), progress_rect, border_radius=8)
    fill_width = 220 * game.bonus_progress
    draw_gradient_rect(screen, (progress_rect[0], progress_rect[1], fill_width, 25),
                      (255, 200, 0), (255, 255, 100), border_radius=8)
    progress_text = INFO_FONT.render("Progresso Bônus", True, (255, 255, 255))
    screen.blit(progress_text, (progress_rect[0], progress_rect[1] - 40))

    return buttons, hover_states

# Plota estatísticas
def plot_stats(game):
    plt.style.use('dark_background')
    plt.figure(figsize=(15, 12))

    plt.subplot(2, 2, 1)
    sns.histplot(game.spin_history, bins=50, kde=True, color="cyan")
    plt.title("Distribuição dos Ganhos", fontsize=16, color="white")
    plt.xlabel("Ganho (R$)", fontsize=14, color="white")
    plt.ylabel("Frequência", fontsize=14, color="white")
    plt.tick_params(colors="white")

    plt.subplot(2, 2, 2)
    plt.plot(game.balance_history, color="lime")
    plt.title("Saldo ao Longo dos Giros", fontsize=16, color="white")
    plt.xlabel("Giro", fontsize=14, color="white")
    plt.ylabel("Saldo (R$)", fontsize=14, color="white")
    plt.tick_params(colors="white")

    plt.subplot(2, 2, 3)
    block_size = 100
    variances = [np.var(game.spin_history[i:i + block_size])
                 for i in range(0, len(game.spin_history), block_size)]
    plt.plot(range(0, len(game.spin_history), block_size)[:len(variances)], variances, color="red")
    plt.title("Variância por Bloco", fontsize=16, color="white")
    plt.xlabel("Giro", fontsize=14, color="white")
    plt.ylabel("Variância", fontsize=14, color="white")
    plt.tick_params(colors="white")

    plt.subplot(2, 2, 4)
    rtp = [sum(game.spin_history[:i+1]) / (i + 1) / game.bet * 100
           for i in range(len(game.spin_history))] if game.spin_history else [0]
    plt.plot(rtp, color="yellow")
    plt.axhline(96.81, color="white", linestyle="--", label="RTP Teórico (96.81%)")
    plt.title("RTP Acumulado", fontsize=16, color="white")
    plt.xlabel("Giro", fontsize=14, color="white")
    plt.ylabel("RTP (%)", fontsize=14, color="white")
    plt.legend(facecolor="black", edgecolor="white", labelcolor="white")
    plt.tick_params(colors="white")

    plt.tight_layout()
    plt.show()

# Loop principal
def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Fortune Tiger - Simulador Gamificado")
    clock = pygame.time.Clock()
    game = FortuneTiger()
    running = True
    clicked_button = None

    background = pygame.Surface((WIDTH, HEIGHT))
    draw_gradient_rect(background, (0, 0, WIDTH, HEIGHT), (130, 30, 30), (30, 30, 60))

    while running:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for i, button in enumerate(buttons):
                    if button["rect"].collidepoint(event.pos):
                        clicked_button = i
                        if i == 0:
                            game.trigger_bonus()
                            game.spin()
                        elif i == 1:
                            game.bet = min(game.bet + 0.50, 10.00)
                        elif i == 2:
                            game.bet = max(game.bet - 0.50, 0.50)
                        elif i == 3:
                            plot_stats(game)
            elif event.type == pygame.MOUSEBUTTONUP:
                clicked_button = None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    game.trigger_bonus()
                    game.spin()
                elif event.key == pygame.K_p:
                    plot_stats(game)

        if game.animating:
            game.anim_frame += 1
            if game.anim_frame >= 70:
                game.animating = False
        game.update_particles()

        screen.blit(background, (0, 0))
        draw_grid(screen, game)
        buttons, hover_states = draw_ui(screen, game, mouse_pos, clicked_button)
        draw_particles(screen, game)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()