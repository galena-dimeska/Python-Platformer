import pygame
import sys
from pygame.locals import *
from pygame import mixer
import pickle
from os import path

#initialize pygame and mixer
pygame.mixer.pre_init(44100, -16, 2, 512)
mixer.init()
pygame.init()
clock = pygame.time.Clock()

#constants and game settings
fps = 60
screen_width = 800
screen_height = 800
tile_size = 40
max_levels = 7

#colors
white = (255, 255, 255)
red = (200, 0, 0)
black = (0, 0, 0)

#game State Variables
game_over = 0  # 0: running, 1: level complete, -1: player died
main_menu = True
level = 1
score = 0
player_start_x = int(100 * 0.8)
player_start_y = screen_height - tile_size - int(80 * 0.8)

#setup pygame screen
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Platformer")

#fonts
font_score = pygame.font.Font("Font/monogram.ttf", 40)
font = pygame.font.Font("Font/monogram.ttf", 120)

#load Images
sun_path = "Graphics/sun.png"
sun_img = pygame.image.load(sun_path)
background_path = "Graphics/sky.png"
background_img = pygame.image.load(background_path)
restart_path = "Graphics/restart_btn.png"
restart_img = pygame.image.load(restart_path)
start_path = "Graphics/start.png"
start_img = pygame.image.load(start_path)
start_img = pygame.transform.scale(start_img, ( int(start_img.get_width() * 0.8), int(start_img.get_height() * 0.8)))
exit_path = "Graphics/exit_btn.png"
exit_img = pygame.image.load(exit_path)
exit_img = pygame.transform.scale(exit_img, (int(exit_img.get_width() * 0.8), int (exit_img.get_height() * 0.8)))

#load Sounds
coin_sound = pygame.mixer.Sound('Sounds/coin.wav')
jump_sound = pygame.mixer.Sound('Sounds/jump.wav')
game_over_sound = pygame.mixer.Sound('Sounds/game_over.wav')
level_clear_sound = pygame.mixer.Sound('Sounds/level_up.ogg')

for sound in [coin_sound, jump_sound, game_over_sound, level_clear_sound]:
    sound.set_volume(0.5)

pygame.mixer.music.load("Sounds/bubble_instrumental.ogg")
pygame.mixer.music.set_volume(0.2)
pygame.mixer.music.play(-1, 0.0, 5000)

#helper Functions
def draw_text(text, font, color, x, y):
    surface = font.render(text, True, color)
    screen.blit(surface, (x, y))

def reset_level(level):
    player.reset(player_start_x, player_start_y)
    lava_group.empty()
    enemy_group.empty()
    exit_group.empty()
    platform_group.empty()

    if path.exists(f'level{level}_data'):
        with open(f'level{level}_data', 'rb') as pickle_in:
            world_data = pickle.load(pickle_in)
    world = World(world_data)
    return world

#button Class
class Button():
    def __init__(self, image_path, position, scale=1.0):
        self.image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.smoothscale(self.image, (int(self.image.get_width() * scale), int(self.image.get_height() * scale)))
        self.rect = self.image.get_rect(topleft=position)
        self.pressed = False

    def draw(self):
        screen.blit(self.image, self.rect)

    def is_pressed(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        if self.rect.collidepoint(mouse_pos) and mouse_pressed and not self.pressed:
            self.pressed = True
            return True

        if not mouse_pressed:
            self.pressed = False
        return False

#world Class
class World():
    def __init__(self, data):
        self.tile_list = []

        dirt_img = pygame.image.load("Graphics/dirt.png")
        grass_img = pygame.image.load("Graphics/grass.png")

        row_count = 0
        for row in data:
            column_count = 0
            for tile in row:
                if tile == 1:
                    img = pygame.transform.scale(dirt_img, (tile_size, tile_size))
                    img_rect = img.get_rect(x=tile_size * column_count, y=tile_size * row_count)
                    self.tile_list.append((img, img_rect))
                elif tile == 2:
                    img = pygame.transform.scale(grass_img, (tile_size, tile_size))
                    img_rect = img.get_rect(x=tile_size * column_count, y=tile_size * row_count)
                    self.tile_list.append((img, img_rect))
                elif tile == 3:
                    blob = Enemy(column_count * tile_size + 2, row_count * tile_size + 15)
                    enemy_group.add(blob)
                elif tile == 4:
                    platform = Platform(column_count * tile_size, row_count * tile_size, 1, 0)
                    platform_group.add(platform)
                elif tile == 5:
                    platform = Platform(column_count * tile_size, row_count * tile_size, 0, 1)
                    platform_group.add(platform)
                elif tile == 6:
                    lava = Lava(column_count * tile_size, row_count * tile_size + (tile_size // 2))
                    lava_group.add(lava)
                elif tile == 7:
                    coin = Coin(column_count * tile_size + (tile_size // 2), row_count * tile_size + (tile_size // 2))
                    coin_group.add(coin)
                elif tile == 8:
                    exit = Exit(column_count * tile_size, row_count * tile_size - (tile_size // 2))
                    exit_group.add(exit)
                column_count += 1
            row_count += 1

    def draw(self):
        for tile in self.tile_list:
            screen.blit(tile[0], tile[1])


#player class
class Player():
	def __init__(self, x, y):
		self.reset(x, y)

	def get_player_images(self):
		img_right = []
		img_left = []
		img_dead = pygame.image.load("Graphics/ghost.png")
		for num in range (1,5):
			player_img_right = pygame.image.load(f"Graphics/guy{num}.png")
			
			player_img_right = pygame.transform.scale(player_img_right,(int(40*0.8),int(80*0.8)))
			img_right.append(player_img_right)
			
			player_img_left = pygame.transform.flip(player_img_right, True, False)
			#flip(image, x axis, y axis)
			img_left.append(player_img_left)

		return img_right, img_left, img_dead


	def update(self, game_over):
		if game_over == 0:
			self.get_user_input()
			self.constrain_movement()
			self.handle_animation()
			self.apply_gravity()
			self.check_for_collision()
			game_over = self.check_for_death(game_over)
			game_over = self.check_level_complete(game_over)
			self.check_for_collision_with_platform()
			self.update_player_coordinates()
		elif game_over == -1:
			self.dead_animation()

		#draw player on screen
		self.draw()
		return game_over

	def update_player_coordinates(self):
		self.rect.x += self.dx
		self.rect.y += self.dy

	def get_user_input(self):
		key = pygame.key.get_pressed()
		self.dx, self.dy = 0, 0 
		
		if key[pygame.K_LEFT]:
			self.dx -= 5
			self.counter += 1
			self.direction = -1
		if key[pygame.K_RIGHT]:
			self.dx += 5
			self.counter += 1
			self.direction = 1
		if key[pygame.K_SPACE] and not self.jumped and not self.in_air:
			jump_sound.play()
			self.velocity_y = -15
			self.jumped = True
		if not key[pygame.K_SPACE]:
			self.jumped = False
		if not key[pygame.K_LEFT] and not key[pygame.K_RIGHT]:
			self.counter = 0
			self.index = 0
			if self.direction == 1:
				self.image = self.images_right[self.index]
			if self.direction == -1:
				self.image = self.images_left[self.index]

	def handle_animation(self):
		if self.counter > self.walk_cooldown:
			self.counter = 0
			self.index += 1
			if self.index >= len(self.images_right):
				self.index = 0
			if self.direction == 1:
				self.image = self.images_right[self.index]
			if self.direction == -1:
				self.image = self.images_left[self.index]

	def dead_animation(self):
		self.image = self.dead_image
		if self.rect.y > tile_size:
			self.rect.y -= 5 

		draw_text("GAME OVER", font, red, (screen_width//2) - 200, screen_height//2 - 170)

	def apply_gravity(self):
		self.velocity_y += 1
		if self.velocity_y > 10: #nikogas ne odi povekje od 10
			self.velocity_y = 10
		self.dy += self.velocity_y

	def check_for_collision(self):
		self.in_air = True 

		for tile in world.tile_list:
			if tile[1].colliderect(self.rect.x + self.dx, self.rect.y, self.width, self.height):
				self.dx = 0  # Stop moving
			
			#check for collision in y direction
			if tile[1].colliderect(self.rect.x, self.rect.y + self.dy, self.width, self.height):
			#collision in the y direction -> + dy
			#check if below the ground aka jumping
				if self.velocity_y < 0:
					#si ja mava glavata vo block above, restricts movement samo do block
					self.dy = tile[1].bottom - self.rect.top
					self.velocity_y = 0
				elif self.velocity_y >= 0:
					#mora else if bc ili pagja ili skoka
					#he's falling, he needs to land on sth
					#this is what we need to prove he's on the ground
					self.dy = tile[1].top - self.rect.bottom
					self.velocity_y = 0
					self.in_air = False

	#the player dies if they touch the enemies, lava, or if they fall off screen
	def check_for_death(self, game_over):
		if pygame.sprite.spritecollide(self, enemy_group, False) or pygame.sprite.spritecollide(self, lava_group, False) or self.rect.bottom > screen_height:
			game_over_sound.play()
			return -1
		return game_over

	def check_level_complete(self, game_over):
		#ako e true it'll delete the sprites:
		if pygame.sprite.spritecollide(self, exit_group, False):
			level_clear_sound.play()
			return 1
		return game_over

	#separate from regular tile collision bc they are dynamic
	def check_for_collision_with_platform(self):
		for platform in platform_group:

			#check for collision in x direction
			if platform.rect.colliderect(self.rect.x + self.dx, self.rect.y, self.width, self.height):
				self.dx = 0

			#collision in y direction
			if platform.rect.colliderect(self.rect.x, self.rect.y + self.dy, self.width, self.height):

				#check if below platform
				if abs(self.rect.top + self.dy - platform.rect.bottom) < self.column_threshold:
					self.velocity_y = 0 
					self.dy = platform.rect.bottom - self.rect.top 

				#check if above platform
				elif abs(self.rect.bottom +self.dy - platform.rect.top) <self.column_threshold:
					self.rect.bottom = platform.rect.top - 1 
					self.dy = 0
					self.in_air = False 

				#move sideways along with the platform
				if platform.move_x != 0: 
					self.rect.x += platform.move_direction
					

	def constrain_movement(self): 
		if self.rect.top < 0:
			self.rect.top = 0
			self.dy = 0
		if self.rect.x > screen_width - self.width:
			self.rect.x = screen_width - self.width
			self.dx = 0
		if self.rect.x < 0:
			self.rect.x = 0
			self.dx = 0

	def draw(self):
		screen.blit(self.image, self.rect)

	def reset(self, x, y):
		self.images_right = []
		self.images_left = []
		self.direction = 0

		self.index = 0
		self.counter = 0 
		self.images_right, self.images_left, self.dead_image = self.get_player_images()

		self.image = self.images_right[self.index]
		self.rect = self.image.get_rect()
		self.rect.x = x 
		self.rect.y = y 

		self.velocity_y = 0 

		self.jumped = False

		self.width = self.image.get_width()
		self.height = self.image.get_height()
		self.in_air = True #if he's in mid air he can't jump
		self.dx, self.dy = 0, 0
		self.walk_cooldown = 7
		self.column_threshold = 20 #for moving platforms to check in y direction


#dynamic items
class MovingItem(pygame.sprite.Sprite):
    def __init__(self, x, y, image_path, move_x=0, move_y=0, scale=None, scale_num = 1):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load(image_path)
        if scale:
            img = pygame.transform.scale(img, scale)

        img = pygame.transform.scale(img, (int(img.get_width() * scale_num), int(img.get_height() * scale_num)))
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_direction = 1
        self.move_counter = 0
        self.move_x = move_x
        self.move_y = move_y

    def update(self):
        self.rect.x += self.move_direction * self.move_x
        self.rect.y += self.move_direction * self.move_y
        self.move_counter += 1
        if abs(self.move_counter) > 30:
            self.move_direction *= -1
            self.move_counter *= -1


class Enemy(MovingItem):
    def __init__(self, x, y):
        super().__init__(x, y, image_path='Graphics/blob.png', move_x = 1, move_y = 0, scale = None, scale_num = 0.8)


class Platform(MovingItem):
    def __init__(self, x, y, move_x, move_y):
        super().__init__(x, y, image_path='Graphics/platform.png', move_x = move_x, move_y = move_y, scale=(tile_size, tile_size // 2))


#static items
class Item(pygame.sprite.Sprite):
    def __init__(self, x, y, image_path, scale_size):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load(image_path)
        self.image = pygame.transform.scale(img, scale_size)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class Lava(Item):
    def __init__(self, x, y):
        super().__init__(x, y, "Graphics/lava.png", (tile_size, tile_size // 2))


class Coin(Item):
    def __init__(self, x, y):
        super().__init__(x, y, "Graphics/coin.png", (tile_size // 2, tile_size // 2))
        self.rect.center = (x, y)  


class Exit(Item):
    def __init__(self, x, y):
        super().__init__(x, y, "Graphics/exit.png", (tile_size, int(tile_size * 1.5)))


#Game
player = Player(player_start_x, player_start_y) 

enemy_group = pygame.sprite.Group() 
platform_group = pygame.sprite.Group() 
lava_group = pygame.sprite.Group()
coin_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

#dummy coin for score
score_coin = Coin(tile_size//2, tile_size//2)
coin_group.add(score_coin)

#load in level data and create world
world = reset_level(level) 

#buttons
restart_button = Button(restart_path, (screen_width //2 - (restart_img.get_width()), screen_height //2 - 50), 2)
start_button = Button(start_path, (screen_width // 2 - start_img.get_width() // 2, screen_height // 2 - start_img.get_height() - 15), 0.8)
exit_button = Button(exit_path, (screen_width // 2 - exit_img.get_width() // 2, screen_height // 2 + 15), 0.8)
exit_button2 = Button(exit_path, (screen_width // 2 - exit_img.get_width()//2 + 12, screen_height // 2 + 45), 0.7)

#high score
high_score = 0

def check_for_high_score(score, high_score):
	if score>high_score:
		high_score = score
		with open("highscore.txt", "w") as file: 
			file.write(str(high_score))


def load_highscore():
	try:
		with open("highscore.txt", "r") as file: 
		#so r za citanje samo
			return int(file.read())
	except FileNotFoundError:
		return 0



while True:
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			pygame.quit()
			sys.exit()

	screen.blit(background_img, (0,0)) 

	if main_menu:
		exit_button.draw()
		start_button.draw()
		if exit_button.is_pressed():
			pygame.quit() 
			sys.exit() 
		if start_button.is_pressed():
			main_menu = False

	else:
		world.draw()
		draw_text('Score: ' + str(score).zfill(4), font_score, white, tile_size, 2)
		draw_text('Level ' + str(level).zfill(3), font_score, white, screen_width - 145, 2)

		#game is running
		if game_over == 0: 
			enemy_group.update()
			platform_group.update()
			coin_collision = pygame.sprite.spritecollide(player, coin_group, True)
			if coin_collision:
				coin_sound.play()
				score += len(coin_collision)
				check_for_high_score(score, high_score)

			

		enemy_group.draw(screen) 
		platform_group.draw(screen)
		lava_group.draw(screen)
		coin_group.draw(screen)
		exit_group.draw(screen)
		#draw_grid()

		game_over = player.update(game_over)

		#if the player has died
		if game_over == -1:
			exit_button2.draw()
			restart_button.draw()
			high_score = load_highscore()
			draw_text("High Score: " + str(high_score).zfill(4), font_score, red, (screen_width//2) - 117, screen_height//2 - 200)
			if exit_button.is_pressed():
				pygame.quit() 
				sys.exit() 
			elif restart_button.is_pressed():
				world_data = []
				world = reset_level(level)
				game_over = 0
				score = 0

		#if the player has completed the level
		if game_over == 1:
			level += 1
			if level <= max_levels:
				world_data = []
				world = reset_level(level)
				game_over = 0
			else:
				#we've beat the game
				#restart game 
				restart_button.draw()
				if restart_button.is_pressed():
					level = 1
					world_data = []
					world = reset_level(level)
					game_over = 0
					score = 0
				draw_text("YOU WIN!", font, black, (screen_width//2)-170, screen_height//2 - 170)

	pygame.display.update()
	clock.tick(fps)

