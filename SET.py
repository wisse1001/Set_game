from itertools import combinations
import itertools
import random
import pygame
import os


class Card:
    #Representeert een SET-kaart als een vector in Z_3^4

    def __init__(self, aantal: int, vorm: int, kleur: int, tint: int):
        self.aantal = aantal
        self.vorm = vorm
        self.kleur = kleur
        self.tint = tint

    @staticmethod
    def is_set(c1, c2, c3) -> bool:
        #Checken of drie kaarten een SET vormen
        for attr in ["aantal", "vorm", "kleur", "tint"]:
            values = {getattr(c1, attr), getattr(c2, attr), getattr(c3, attr)}
            if len(values) == 2:
                return False
        return True


def kaart_naar_bestand(card: Card) -> str:
    #Map een kaart object naar diens bestandnaam
    kleuren = ["green", "red", "purple"]
    vormen = ["diamond", "oval", "squiggle"]
    vulstijl = ["empty", "filled", "shaded"]
    aantallen = ["1", "2", "3"]

    return f"{kleuren[card.kleur]}{vormen[card.vorm]}{vulstijl[card.tint]}{aantallen[card.aantal]}.gif"


def maak_deck():
    #Maakt een deck van 81 kaarten
    waarden = [0, 1, 2]
    return [Card(*props) for props in itertools.product(waarden, repeat=4)]


def vind_een_set(kaarten):
    #Geeft een SET van de gegeven kaarten of None
    for c1, c2, c3 in combinations(kaarten, 3):
        if Card.is_set(c1, c2, c3):
            return (c1, c2, c3)
    return None


def vind_alle_sets(kaarten):
    #Geeft alle mogelijke SETs van de gegeven kaarten
    sets = []
    for c1, c2, c3 in combinations(kaarten, 3):
        if Card.is_set(c1, c2, c3):
            sets.append((c1, c2, c3))
    return sets


def verwijder_set(tafel, indexen, deck):
    #Vervangt kaarten op tafel met nieuwe kaarten uit het dek
    for i in sorted(indexen):
        if deck:
            tafel[i] = deck.pop(0)
        else:
            tafel[i] = None

    tafel[:] = [kaart for kaart in tafel if kaart is not None]


def kies_moeilijkheid(screen, font, WIDTH, HEIGHT):
    #Moeilijkheidsgraad kiezen
    knoppen = [
        ("Beginner (30s)", 30),
        ("Gemiddeld (20s)", 20),
        ("Moeilijk (10s)", 10)
    ]

    button_width, button_height = 300, 60
    start_y = HEIGHT // 2 - 100
    clock = pygame.time.Clock()

    while True:
        screen.fill((0, 100, 0))
        title = font.render("Kies moeilijkheid", True, (255, 255, 255))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, start_y - 80))

        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for i, (_, tijd) in enumerate(knoppen):
                    x = WIDTH // 2 - button_width // 2
                    y = start_y + i * (button_height + 20)
                    rect = pygame.Rect(x, y, button_width, button_height)
                    if rect.collidepoint(event.pos):
                        return tijd

        for i, (tekst, _) in enumerate(knoppen):
            x = WIDTH // 2 - button_width // 2
            y = start_y + i * (button_height + 20)
            rect = pygame.Rect(x, y, button_width, button_height)

            kleur = (0, 150, 0) if rect.collidepoint(mouse_pos) else (0, 120, 0)
            pygame.draw.rect(screen, kleur, rect)
            pygame.draw.rect(screen, (255, 255, 255), rect, 2)

            label = font.render(tekst, True, (255, 255, 255))
            screen.blit(label, (
                x + button_width // 2 - label.get_width() // 2,
                y + button_height // 2 - label.get_height() // 2
            ))

        pygame.display.flip()
        clock.tick(60)


class SetGame:
    #Hoofdspelcontroller voor het SET-spel

    def __init__(self):
        pygame.init()

        self.cols = 4
        self.card_width = 100
        self.card_height = 150
        self.spacing_x = 20
        self.spacing_y = 20
        self.left_margin = 50
        self.top_margin = 50
        self.text_space = 200
        self.extra_width = 200

        self.deck = maak_deck()
        random.shuffle(self.deck)

        self.tafel = self.deck[:12]
        self.deck = self.deck[12:]

        self.rows_needed = ((len(self.tafel) - 1) // self.cols + 1)
        self.HEIGHT = self.top_margin + self.rows_needed * (self.card_height + self.spacing_y) + self.text_space
        self.WIDTH = self.left_margin + self.cols * (self.card_width + self.spacing_x) + self.left_margin + self.extra_width
        self.left_margin = (self.WIDTH - (self.cols * (self.card_width + self.spacing_x) - self.spacing_x)) // 2

        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Set Kaarten")

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 30)

        self.messages = []
        self.geselecteerd = []

        self.computer_score = 0
        self.jouw_score = 0

        self.highlight_active = False
        self.computer_highlight = []
        self.highlight_start = 0
        self.HIGHLIGHT_TIME = 3000

        self.kaart_afbeeldingen = self.laad_kaart_afbeeldingen()

        self.timeout = kies_moeilijkheid(self.screen, self.font, self.WIDTH, self.HEIGHT)
        self.start_time = pygame.time.get_ticks()

    def laad_kaart_afbeeldingen(self):
        #Laadt alle kaartafbeeldingen
        images = {}
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cards_path = os.path.join(script_dir, "kaartenset", "kaarten")

        for kaart in self.deck + self.tafel:
            filename = kaart_naar_bestand(kaart)
            path = os.path.join(cards_path, filename)
            if os.path.exists(path):
                img = pygame.image.load(path)
                img = pygame.transform.scale(img, (self.card_width, self.card_height))
                images[kaart] = img
            else:
                print(f"Bestand ontbreekt: {path}")

        self.cards_path = cards_path
        return images

    def render_kaarten(self):
        #Geeft alle kaarten weer op tafel
        for idx, kaart in enumerate(self.tafel):
            row = idx // self.cols
            col = idx % self.cols
            x = self.left_margin + col * (self.card_width + self.spacing_x)
            y = self.top_margin + row * (self.card_height + self.spacing_y)

            self.screen.blit(self.kaart_afbeeldingen[kaart], (x, y))

            if idx in self.geselecteerd:
                pygame.draw.rect(self.screen, (255, 255, 0),
                                 (x - 2, y - 2, self.card_width + 4, self.card_height + 4), 4)

            if self.highlight_active and idx in self.computer_highlight:
                pygame.draw.rect(self.screen, (255, 0, 0),
                                 (x - 2, y - 2, self.card_width + 4, self.card_height + 4), 4)

    def render_tekst(self):
        #Geeft tekst weer
        text_y = self.top_margin + ((len(self.tafel) - 1) // self.cols + 1) * (self.card_height + self.spacing_y) + 20
        for i, m in enumerate(self.messages[-2:]):
            text_surface = self.font.render(m, True, (255, 255, 255))
            self.screen.blit(text_surface, (self.left_margin, text_y + i * 40))

    def render_timer(self):
        #Geeft de timer weer
        now = pygame.time.get_ticks()
        resterend = max(0, self.timeout - (now - self.start_time) // 1000)
        timer_text = self.font.render(f"Tijd: {resterend}", True, (255, 255, 255))
        self.screen.blit(timer_text, (self.WIDTH - 140, 20))

    def render_scorebord(self):
        #Geeft het scorebord weer
        score_speler = self.font.render(f"Speler: {self.jouw_score}", True, (255, 255, 255))
        score_computer = self.font.render(f"Computer: {self.computer_score}", True, (255, 255, 255))

        x = self.WIDTH - 155
        y = 80

        self.screen.blit(score_speler, (x, y))
        self.screen.blit(score_computer, (x, y + 40))

    def computer_beurt(self):
        #Geeft de computer een beurt
        comp_set = vind_een_set(self.tafel)
        if comp_set:
            self.computer_score += 1
            self.messages.append("De computer vond een set!")
            self.computer_highlight = [self.tafel.index(c) for c in comp_set]
            self.highlight_active = True
            self.highlight_start = pygame.time.get_ticks()
        else:
            if len(self.tafel) >= 3:
                self.messages.append("Geen set op tafel! 3 nieuwe kaarten")
                for idx in range(3):
                    if self.deck:
                        self.tafel[idx] = self.deck.pop(0)

        self.start_time = pygame.time.get_ticks()

    def handle_click(self, pos):
        #Handelt het muisklikken
        mx, my = pos

        for idx, kaart in enumerate(self.tafel):
            row = idx // self.cols
            col = idx % self.cols
            x = self.left_margin + col * (self.card_width + self.spacing_x)
            y = self.top_margin + row * (self.card_height + self.spacing_y)
            rect = pygame.Rect(x, y, self.card_width, self.card_height)

            if rect.collidepoint(mx, my):
                if idx not in self.geselecteerd:
                    self.geselecteerd.append(idx)
                else:
                    self.geselecteerd.remove(idx)

        if len(self.geselecteerd) == 3:
            i, j, k = self.geselecteerd
            if Card.is_set(self.tafel[i], self.tafel[j], self.tafel[k]):
                self.jouw_score += 1
                self.messages.append("SET! Punt voor jou!")
                verwijder_set(self.tafel, [i, j, k], self.deck)
            else:
                self.messages.append("Helaas, geen set. De computer krijgt een beurt")
                self.computer_beurt()

            self.geselecteerd = []
            self.start_time = pygame.time.get_ticks()

    def update_timer_logic(self):
        #Handelt de tijdexpiratie
        now = pygame.time.get_ticks()
        if now - self.start_time > self.timeout * 1000:
            self.computer_beurt()

    def update_highlight_logic(self):
        #Haalt de highlight weg na een bepaalde tijd
        if self.highlight_active:
            if pygame.time.get_ticks() - self.highlight_start > self.HIGHLIGHT_TIME:
                verwijder_set(self.tafel, self.computer_highlight, self.deck)
                self.computer_highlight = []
                self.highlight_active = False
                self.start_time = pygame.time.get_ticks()

    def check_game_end(self):
        #Checkt of het spel is beëindigt
        if not self.deck and not vind_alle_sets(self.tafel):
            self.messages.append(
                f"Einde spel! Score: Speler {self.jouw_score} - Computer {self.computer_score}"
            )
            self.screen.fill((0, 128, 0))
            self.render_kaarten()
            self.render_tekst()
            pygame.display.flip()
            pygame.time.delay(5000)
            return True
        return False

    def run(self):
        #Hierin vindt het spel plaats
        running = True

        while running:
            self.clock.tick(60)

            self.update_highlight_logic()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)

            self.update_timer_logic()

            self.screen.fill((0, 128, 0))
            self.render_kaarten()
            self.render_tekst()
            self.render_timer()
            self.render_scorebord()
            pygame.display.flip()

            if self.check_game_end():
                running = False

        pygame.quit()


if __name__ == "__main__":
    game = SetGame()
    game.run()