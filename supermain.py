import pygame
import sqlite3
import sys
import math
from random import randint
import time

pygame.init()

WIDTH, HEIGHT = 800, 600
FONT_SIZE = 30
BACKGROUND_IMAGE = 'images/fon.png'
warrior_image = pygame.image.load("images/warrior.png")

WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

font = pygame.font.Font(None, FONT_SIZE)

def create_database():
    conn = sqlite3.connect('leaderboard.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leaderboard (
            username TEXT PRIMARY KEY,
            max_survival_time INTEGER,
            waves_passed INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def register_user(username, password):
    conn = sqlite3.connect('leaderboard.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def check_user(username, password):
    conn = sqlite3.connect('leaderboard.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user is not None

def get_leaderboard():
    conn = sqlite3.connect('leaderboard.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, max_survival_time, waves_passed FROM leaderboard ORDER BY max_survival_time DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows


def add_leaderboard_entry(username, survival_time, waves_passed):
    conn = sqlite3.connect('leaderboard.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM leaderboard WHERE username = ?", (username,))
    existing_entry = cursor.fetchone()

    if existing_entry:
        prev_max_time, prev_waves = existing_entry[1], existing_entry[2]

        if survival_time > prev_max_time or (survival_time == prev_max_time and waves_passed > prev_waves):
            cursor.execute("UPDATE leaderboard SET max_survival_time = ?, waves_passed = ? WHERE username = ?",
                           (survival_time, waves_passed, username))
    else:
        cursor.execute("INSERT INTO leaderboard (username, max_survival_time, waves_passed) VALUES (?, ?, ?)",
                       (username, survival_time, waves_passed))

    conn.commit()
    conn.close()

def draw_text(surface, text, x, y, color=WHITE):
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, (x, y))

class Button:
    def __init__(self, text, x, y, width, height, action=None):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.action = action

    def draw(self, surface):
        draw_text(surface, self.text, self.rect.x + 10, self.rect.y + 10)

    def is_clicked(self, pos):
        if self.rect.collidepoint(pos):
            if self.action:
                self.action()

class App:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Аутентификация")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = 'login'
        self.username = ''
        self.password = ''
        self.message = ''
        self.leaderboard_data = []
        create_database()

        self.login_button = Button("Войти", WIDTH // 2 - 100, 250, 200, 50, self.login)
        self.register_button = Button("Зарегистрироваться", WIDTH // 2 - 100, 300, 200, 50, self.register)
        self.start_game_button = Button("Начать игру", WIDTH // 2 - 100, 150, 200, 50, self.start_game)
        self.skins_button = Button("Скины", WIDTH // 2 - 100, 200, 200, 50, self.show_skins)
        self.leaderboard_button = Button("Лидеры", WIDTH // 2 - 100, 250, 200, 50, self.show_leaderboard)
        self.about_button = Button("О программе", WIDTH // 2 - 100, 300, 200, 50, self.show_about)
        self.back_button = Button("Назад", WIDTH // 2 - 100, 350, 200, 50, self.go_back)
        self.warrior_button = Button("standard", WIDTH // 2 - 100, 150, 200, 50, self.change_skin_to_grey)
        self.red_warrior_button = Button("red", WIDTH // 2 - 100, 200, 200, 50, self.change_skin_to_red)
        self.green_warrior_button = Button("green", WIDTH // 2 - 100, 250, 200, 50, self.change_skin_to_green)
        self.blue_warrior_button = Button("blue", WIDTH // 2 - 100, 300, 200, 50, self.change_skin_to_blue)

        self.username_input_active = True

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(60)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.state == 'login':
                        self.login_button.is_clicked(event.pos)
                        self.register_button.is_clicked(event.pos)
                    elif self.state == 'register':
                        self.register_button.is_clicked(event.pos)
                        self.back_button.is_clicked(event.pos)
                    elif self.state == 'main':
                        self.start_game_button.is_clicked(event.pos)
                        self.skins_button.is_clicked(event.pos)
                        self.leaderboard_button.is_clicked(event.pos)
                        self.about_button.is_clicked(event.pos)
                    elif self.state == "skins":
                        self.warrior_button.is_clicked(event.pos)
                        self.red_warrior_button.is_clicked(event.pos)
                        self.green_warrior_button.is_clicked(event.pos)
                        self.blue_warrior_button.is_clicked(event.pos)
                        self.back_button.is_clicked(event.pos)
                    elif self.state in ['about', 'leaderboard']:
                        self.back_button.is_clicked(event.pos)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state in ['register', 'about', 'skins', 'leaderboard']:
                        self.go_back()
                    else:
                        self.running = False
                if self.state in ['login', 'register']:
                    if event.key == pygame.K_BACKSPACE:
                        if self.username_input_active:
                            self.username = self.username[:-1]
                        else:
                            self.password = self.password[:-1]
                    else:
                        if self.username_input_active:
                            self.username += event.unicode
                        else:
                            self.password += event.unicode
                if event.key == pygame.K_TAB:
                    self.username_input_active = not self.username_input_active
                if event.key == pygame.K_m and self.state == 'game':
                    self.state = 'main'

    def login(self):
        if check_user(self.username, self.password):
            self.message = "Вход выполнен успешно!"
            self.state = 'main'
        else:
            self.message = "Ошибка: неверный логин или пароль."

    def register(self):
        if register_user(self.username, self.password):
            self.message = "Регистрация прошла успешно!"
            self.state = 'login'
            self.username = ''
            self.password = ''
        else:
            self.message = "Ошибка: пользователь с таким именем уже существует."

    def go_back(self):
        if self.state in ['leaderboard', 'about', 'skins']:
            self.state = 'main'
        elif self.state == 'register':
            self.state = 'login'
            self.username = ''
            self.password = ''
            self.message = ''
        elif self.state == 'leaderboard':
            self.leaderboard_data = []

    def show_about(self):
        self.state = 'about'

    def show_skins(self):
        self.state = 'skins'

    def show_leaderboard(self):
        self.leaderboard_data = get_leaderboard()
        self.state = 'leaderboard'

    def start_game(self):
        self.state = 'game'
        main(self.username)

    def update(self):
        pass

    def change_skin_to_grey(self):
        global warrior_image
        warrior_image = pygame.image.load("images/warrior.png")

    def change_skin_to_red(self):
        global warrior_image
        warrior_image = pygame.image.load("images/red_warrior.png")

    def change_skin_to_green(self):
        global warrior_image
        warrior_image = pygame.image.load("images/green_warrior.png")

    def change_skin_to_blue(self):
        global warrior_image
        warrior_image = pygame.image.load("images/blue_warrior.png")

    def render(self):
        self.screen.blit(pygame.image.load(BACKGROUND_IMAGE), (0, 0))
        if self.state == 'login':
            draw_text(self.screen, "Login", WIDTH // 2 - 50, 50)
            draw_text(self.screen, "Username: " + self.username, WIDTH // 2 - 100, 150)
            draw_text(self.screen, "Password: " + "*" * len(self.password), WIDTH // 2 - 100, 200)
            self.login_button.draw(self.screen)
            self.register_button.draw(self.screen)
        elif self.state == 'register':
            draw_text(self.screen, "Register", WIDTH // 2 - 50, 50)
            draw_text(self.screen, "Username: " + self.username, WIDTH // 2 - 100, 150)
            draw_text(self.screen, "Password: " + "*" * len(self.password), WIDTH // 2 - 100, 200)
            self.register_button.draw(self.screen)
            self.back_button.draw(self.screen)
        elif self.state == 'main':
            draw_text(self.screen, "Main Menu", WIDTH // 2 - 50, 50)
            self.start_game_button.draw(self.screen)
            self.skins_button.draw(self.screen)
            self.leaderboard_button.draw(self.screen)
            self.about_button.draw(self.screen)
            draw_text(self.screen, "Press Esc to Exit", WIDTH // 2 - 50, 450)
        elif self.state == 'about':
            draw_text(self.screen, "О программе", WIDTH // 2 - 50, 50)
            draw_text(self.screen, "Управление:", 10, 80)
            draw_text(self.screen, "WASD/мышка - движение, пробел - стрельба, F - рестарт,", 10, 110)
            draw_text(self.screen, "ESC - выход, M - главное меню", 10, 130)
            draw_text(self.screen, "Авторы:", 10, 160)
            draw_text(self.screen, "Максим Л. Андрей Ж.", 10, 190)
            self.back_button.draw(self.screen)
        elif self.state == 'skins':
            draw_text(self.screen, "Скины", WIDTH // 2 - 50, 50)
            draw_text(self.screen, "Выбери свой скин:", WIDTH // 2 - 100, 100)
            self.warrior_button.draw(self.screen)
            self.red_warrior_button.draw(self.screen)
            self.green_warrior_button.draw(self.screen)
            self.blue_warrior_button.draw(self.screen)
            self.back_button.draw(self.screen)
        elif self.state == 'leaderboard':
            draw_text(self.screen, "Таблица лидеров", WIDTH // 2 - 50, 50)
            if not self.leaderboard_data:
                draw_text(self.screen, "Пока нет записей", WIDTH // 2 - 100, 100)
            else:
                for index, (username, max_time, waves) in enumerate(self.leaderboard_data):
                    draw_text(self.screen, f"{index + 1}. {username} - Время: {max_time}s, Волны: {waves}", WIDTH // 2 - 100, 100 + index * 30)

            self.back_button.draw(self.screen)

        draw_text(self.screen, self.message, WIDTH // 2 - 100, HEIGHT - 50, RED)

        pygame.display.flip()

def main(username):
    global warrior_image

    width, height = 1000, 450
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("PyWars_v1.0")

    background_color = (0, 0, 0)

    main_bullet_image = pygame.image.load("images/bullet.jpg")
    enemy_bullet_image = pygame.image.load("images/bullet2.jpg")
    shotgun_image = pygame.image.load("images/shotgun.png")
    game_over_image = pygame.image.load("images/game_over.jpg")
    boom_image = pygame.image.load("images/boom.jpg")
    coin_image = pygame.image.load("images/coin.png")
    game_over_sound = pygame.mixer.Sound("sounds/wha-wha-wha.mp3")
    shoot_sound = pygame.mixer.Sound("sounds/shoot.mp3")
    get_coin_sound = pygame.mixer.Sound("sounds/get_coin.mp3")
    fon_image = pygame.image.load("images/fon_game.png")

    class Player:
        def __init__(self):
            self.image = warrior_image.copy()
            self.rect = self.image.get_rect(center=(50, 250))
            self.speed = 10
            self.current_bullets = 0
            self.max_bullets = 8
            self.survival_time = 0
            self.wave_count = 0

        def move_towards(self, target):
            if target is not None:
                dx = target[0] - self.rect.centerx
                dy = target[1] - self.rect.centery
                distance = math.sqrt(dx ** 2 + dy ** 2)
                if distance > 0:
                    dx /= distance
                    dy /= distance
                    self.rect.x += dx * self.speed
                    self.rect.y += dy * self.speed
                    if math.sqrt((self.rect.centerx - target[0]) ** 2 + (self.rect.centery - target[1]) ** 2) < self.speed:
                        self.rect.center = target

    class Bullet:
        def __init__(self, image, center):
            self.image = image
            self.rect = self.image.get_rect(center=center)

        def update(self, speed):
            self.rect.centerx += speed

    class Shotgun:
        def __init__(self, position):
            self.image = shotgun_image
            self.position = position
            self.state = 1
            self.last_shot_time = 0
            self.timer = randint(2000, 5000)

        def shoot(self, current_time):
            if self.state == 1 and current_time - self.last_shot_time >= self.timer:
                self.last_shot_time = current_time
                self.timer = randint(1000, 2000)
                return Bullet(enemy_bullet_image, (self.position[0], self.position[1] + 1))
            return None

    class Coin:
        def __init__(self):
            self.image = coin_image
            self.rect = None
            self.timer = 0
            self.duration = 5000

        def spawn(self):
            self.rect = self.image.get_rect(center=(randint(0, 500), randint(0, 450)))
            self.timer = pygame.time.get_ticks()

        def is_active(self):
            return self.rect is not None and (pygame.time.get_ticks() - self.timer < self.duration)

        def collect(self):
            self.rect = None

    class HUD:
        def __init__(self):
            self.font = pygame.font.Font(None, 36)

        def draw(self, survival_time, wave_count, coins_collected, current_bullets, max_bullets):
            timer_surface = self.font.render(f"Время жизни: {survival_time}s", True, (255, 255, 255))
            wave_surface = self.font.render(f"Волна: {wave_count}", True, (255, 255, 255))
            bullet_count_surface = self.font.render(f"Пули: {current_bullets}/{max_bullets}", True, (255, 255, 255))
            coins_surface = self.font.render(f"Монеты: {coins_collected}", True, (255, 255, 255))
            screen.blit(timer_surface, (10, 10))
            screen.blit(wave_surface, (10, 50))
            screen.blit(bullet_count_surface, (10, 90))
            screen.blit(coins_surface, (10, 130))

    def game_loop(username):
        global end, wave_count, reset_timer, enemy_bullet_speed, coins_collected

        clock = pygame.time.Clock()
        MYEVENTTYPE = pygame.USEREVENT + 1
        MYEVENTTYPE2 = pygame.USEREVENT + 2
        pygame.time.set_timer(MYEVENTTYPE, 1)
        pygame.time.set_timer(MYEVENTTYPE2, 1)

        player = Player()
        shotguns = [Shotgun((width - 100, 10 + i * 60)) for i in range(7)]
        coins_collected = 0
        coin = Coin()
        end = False
        wave_count = 0
        reset_timer = 0
        enemy_bullet_speed = 7

        list_main_bullets = []
        list_enemy_bullets = []

        game_over_rect = game_over_image.get_rect(center=(-500, 250))
        target = None
        hud = HUD()

        while True:
            current_time = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN and not end:
                    target = event.pos

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and player.current_bullets < player.max_bullets:
                        bullet = Bullet(main_bullet_image, (player.rect.centerx + 30, player.rect.centery + 10))
                        list_main_bullets.append(bullet)
                        player.current_bullets += 1
                        shoot_sound.play()
                    if event.key == pygame.K_w or event.key == pygame.K_UP:
                        if player.rect.centery - 40 > 0:
                            target = (player.rect.centerx, player.rect.centery - 40)
                    if event.key == pygame.K_s or event.key == pygame.K_DOWN:
                        if player.rect.centery + 40 < 450:
                            target = (player.rect.centerx, player.rect.centery + 40)
                    if event.key == pygame.K_a or event.key == pygame.K_LEFT:
                        if player.rect.centerx - 40 > 0:
                            target = (player.rect.centerx - 40, player.rect.centery)
                    if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                        if player.rect.centerx + 40 < 800:
                            target = (player.rect.centerx + 40, player.rect.centery)
                    if event.key == pygame.K_f:
                        main(username)
                    if event.key == pygame.K_m:
                        return

                if event.type == MYEVENTTYPE and not end:
                    for shotgun in shotguns:
                        bullet = shotgun.shoot(current_time)
                        if bullet:
                            list_enemy_bullets.append(bullet)

                    for bullet in list_main_bullets:
                        bullet.update(5)

                if event.type == MYEVENTTYPE2 and end:
                    if game_over_rect.centerx != 500:
                        game_over_rect.centerx += 1

            screen.blit(fon_image, (0, 0))

            if not end:
                player.move_towards(target)
                screen.blit(player.image, player.rect)

                for bullet in list_main_bullets:
                    bullet.update(5)
                    screen.blit(bullet.image, bullet.rect)

                for bullet in list_enemy_bullets:
                    bullet.update(-enemy_bullet_speed)
                    if bullet.rect.colliderect(player.rect):
                        end = True
                        game_over_sound.play()
                        player.image = boom_image
                    screen.blit(bullet.image, bullet.rect)

                for bullet in list_main_bullets[:]:
                    for enemy_bullet in list_enemy_bullets[:]:
                        if bullet.rect.colliderect(enemy_bullet.rect):
                            list_main_bullets.remove(bullet)
                            list_enemy_bullets.remove(enemy_bullet)
                            player.current_bullets -= 1
                            break

                for bullet in list_main_bullets[:]:
                    for shotgun in shotguns:
                        if shotgun.state == 1:
                            shotgun_rect = shotgun.image.get_rect(topleft=shotgun.position)
                            if bullet.rect.colliderect(shotgun_rect):
                                shotgun.state = 0
                                list_main_bullets.remove(bullet)
                                player.current_bullets -= 1
                                break

                for shotgun in shotguns:
                    shotgun_rect = shotgun.image.get_rect(topleft=shotgun.position)
                    if player.rect.colliderect(shotgun_rect):
                        end = True
                        game_over_sound.play()

                for shotgun in shotguns:
                    if shotgun.state == 1:
                        screen.blit(shotgun.image, shotgun.image.get_rect(topleft=shotgun.position))

                if all(shotgun.state == 0 for shotgun in shotguns):
                    reset_timer += 1
                    if reset_timer >= 7000 / 1000:
                        for shotgun in shotguns:
                            shotgun.state = 1
                        reset_timer = 0
                        wave_count += 1
                        player.current_bullets = 0
                        coin.spawn()
                        enemy_bullet_speed *= 1.2

                if coin.is_active():
                    screen.blit(coin.image, coin.rect)
                    if player.rect.colliderect(coin.rect):
                        coins_collected += 1
                        coin.collect()
                        get_coin_sound.play()

                survival_time = current_time // 1000
                hud.draw(survival_time, wave_count, coins_collected, player.current_bullets, player.max_bullets)

            else:
                add_leaderboard_entry(username, survival_time, wave_count)

                screen.blit(player.image, player.rect)
                screen.blit(game_over_image, game_over_rect)

            pygame.display.flip()
            clock.tick(60)

    game_loop(username)

if __name__ == "__main__":
    app = App()
    app.run()
    pygame.quit()
    sys.exit()
