"""
Greninja runner, a platformer game
Collect and throw water shurikens to defeat Team Rocket

Controls:
---------
Left/Right arrow: move Greninja
Spacebar: jump
f: throw
"""

import pygame
import sys

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)

# Create screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("GRENINJA RUNNER")
clock = pygame.time.Clock()

# Load an image as a pygame surface and scale it to width, height
def load_sprite_surface(file_name, width, height):
    fullres = pygame.image.load(file_name).convert_alpha()
    return pygame.transform.smoothscale(fullres, (width, height))
   
# ===== PLAYER =====
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = load_sprite_surface("greninja-runner/greninja.png", 56, 36)

        # Player location and movement
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y 
        self.vel_y = 0
        self.vel_x = 0
        self.is_jumping = False
        self.gravity = 0.6
        self.jump_power = -15
        self.speed = 5

        # Keeps track of whether player is ready to throw
        self.throwing_cooldown = 0

        # Direction that player is facing for throwing
        # Latches to last movement
        self.looking_forward = True

        # List of all of the shurikens that are collected
        self.shurikens = []
    
    def handle_input(self, keys):
        # Decrement the cooldown timer to be ready to throw
        self.throwing_cooldown = max(0, self.throwing_cooldown - 1)

        # Movement
        if keys[pygame.K_LEFT]:
            self.vel_x = -self.speed
            self.looking_forward = False
        elif keys[pygame.K_RIGHT]:
            self.vel_x = self.speed
            self.looking_forward = True
        else:
            self.vel_x = 0
        if keys[pygame.K_SPACE] and not self.is_jumping:
            self.vel_y = self.jump_power
            self.is_jumping = True
    
        # Throwing if we are ready
        if keys[pygame.K_f]:
            if self.throwing_cooldown == 0:
                self.throwing_cooldown = 10
                if self.shurikens:
                    shuriken = self.shurikens.pop()
                    shuriken.throw(self.rect.x, self.rect.y, self.looking_forward)

    def apply_gravity(self):
        self.vel_y += self.gravity
        self.rect.y += self.vel_y
        
        # Check if player fell off screen
        if self.rect.y > SCREEN_HEIGHT:
            return False
        return True
    
    def update(self, platforms):
        self.rect.x += self.vel_x
        
        # Keep player on screen horizontally
        if self.rect.x < 0:
            self.rect.x = 0
        if self.rect.x > SCREEN_WIDTH - self.rect.width:
            self.rect.x = SCREEN_WIDTH - self.rect.width
        
        # Check collision with platforms
        for platform in platforms:
            if self.vel_y > 0 and self.rect.bottom >= platform.rect.top and self.rect.top < platform.rect.top:
                if self.rect.right > platform.rect.left and self.rect.left < platform.rect.right:
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.is_jumping = False
    
    def draw(self, surface):
        surface.blit(self.image, self.rect)


# ===== PLATFORM =====
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
    
    def draw(self, surface):
        surface.blit(self.image, self.rect)

# ===== HealthBar =====
class HealthBar(object):
    def __init__(self, x, y):
        super().__init__()
        self.width = 40
        self.color = GREEN
        self.background_rect = pygame.Rect(0, 0, self.width, 10)
        self.health_rect = pygame.Rect(0, 0, self.width, 10)
        self.update_position(x,y)
        self.health = 100

    # Update the position of the health rect and background rect
    # at the same time
    def update_position(self, x, y):
        self.background_rect.x = x
        self.background_rect.y = y
        self.health_rect.x = x
        self.health_rect.y = y

    def update_health(self, health):
        # Color based on how low the health is
        if health >= 80:
            self.color = GREEN
        elif health >= 40:
            self.color = YELLOW
        else:
            self.color = RED
        self.health = health

        # Scale the size of the bar with health value
        self.health_rect.width = self.width * health / 100
  
    def draw(self, surface):
        pygame.draw.rect(surface, WHITE, self.background_rect)
        pygame.draw.rect(surface, self.color, self.health_rect)
        


# ===== WaterShuriken (Collectible) =====
class WaterShuriken(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = load_sprite_surface("greninja-runner/water_shuriken.png", 24, 24)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vel_x = 0

        # Has been collected by the playre
        self.collected = False

        # Is currently traveling
        self.thrown = False

    # Makes the shuriken move with constant horizontal speed
    # forwards or backwards
    def throw(self, x, y, forward=True):
        self.rect.x = x
        self.rect.y = y
        if forward:
            self.vel_x = 5
        else:
            self.vel_x = -5
        self.thrown = True

    # Update variables that need to be reset when stopped    
    def stop(self):
        self.vel_x = 0
        self.thrown = False
        self.collected = False

    # Update the state of the shuriken at each frame,
    # checking for collisions with platforms and enemies
    def update(self, platforms, enemies):
        score = 0  
        if self.thrown:
            self.rect.x += self.vel_x
            
            # Keep shuriken on screen horizontally
            if self.rect.x < 0:
                self.rect.x = 0
                self.stop()
            if self.rect.x > SCREEN_WIDTH - self.rect.width:
                self.rect.x = SCREEN_WIDTH - self.rect.width
                self.stop()
        
            for platform in platforms:
                if self.rect.colliderect(platform.rect):
                    self.stop()

            # Check collision with enemies, inflicting damage
            for enemy in enemies:
                if self.rect.colliderect(enemy.rect):
                    self.stop()
                    enemy.take_damage()
                    score += 50          
        return score
    
    def draw(self, surface):
        if not self.collected or self.thrown:
            surface.blit(self.image, self.rect)


# ===== ENEMY =====
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = load_sprite_surface("greninja-runner/Team_Rocket_Grunt.png", 42, 65)
        
        # Movement and position
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = 2
        self.direction = 1
        self.left_bound = x - 80
        self.right_bound = x + 80

        # Keep track of the enemy's health with HealthBar
        self.health = HealthBar(x, y - 20)
        
        # When their health goes to 0 they are defeated
        self.defeated = False

    # Update the health bar and check for defeat
    def take_damage(self):
        current_health = self.health.health
        new_health = max(0, current_health -20)
        self.health.update_health(new_health)
        self.defeated = new_health == 0


    def update(self):
        self.rect.x += self.speed * self.direction
        self.health.update_position(self.rect.x, self.rect.y-20)
        
        # Change direction at bounds
        if self.rect.x <= self.left_bound or self.rect.x >= self.right_bound:
            self.direction *= -1
    
    def draw(self, surface):
        if not self.defeated:
            surface.blit(self.image, self.rect)
            self.health.draw(surface)


# ===== GOAL/FINISH AREA =====
class Goal(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = load_sprite_surface("greninja-runner/Premier_Ball.png",50, 50)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
    
    def draw(self, surface):
        surface.blit(self.image, self.rect)


# ===== GAME =====
class Game:
    def __init__(self):
        # Background scene
        self.image = load_sprite_surface("greninja-runner/stadium.jpg", SCREEN_WIDTH, SCREEN_HEIGHT)
        self.image.set_alpha(80)
        self.player = Player(50, 400)
        
        # Create platforms
        self.platforms = [
            Platform(0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40),  # Ground
            Platform(200, 450, 200, 20),
            Platform(500, 380, 100, 20),
            Platform(100, 315, 50, 20),
            Platform(600, 250, 20, 20),
            Platform(50, 200, 50, 20),
        ]
        
        # Create shurikens
        self.shurikens = [
            WaterShuriken(550, 350),
            WaterShuriken(500, 500),
            WaterShuriken(100, 500),
            WaterShuriken(50, 150)
        ]
        
        # Create enemy
        self.enemies = [
            Enemy(300, 380),
            Enemy(200, SCREEN_HEIGHT - 105)
        ]
        
        # Create goal
        self.goal_ready = False # Goal appears after enemies are defeated
        self.goal = Goal(715, 35)
        
        self.score = 0
        self.game_over = False
        self.won = False
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        return True
    
    def update(self):
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)
        
        if not self.player.apply_gravity():
            self.game_over = True
        
        self.player.update(self.platforms)

        for enemy in self.enemies:
            enemy.update()

        for shuriken in self.shurikens:
            score = shuriken.update(self.platforms, self.enemies)
            self.score += score
        
        # Check WaterShuriken collection, filter out already collected
        available_shurikens = [s for s in self.shurikens if not s.collected]
        for shuriken in available_shurikens:
            if self.player.rect.colliderect(shuriken.rect):
                shuriken.collected = True
                self.score += 10
                self.player.shurikens.append(shuriken)
        
        # Check enemy collision (lose condition), filter out defeated
        live_enemies = [e for e in self.enemies if not e.defeated]
        if not live_enemies:
            # Goal appears after enemies defeated
            self.goal_ready = True
        for enemy in live_enemies:
            if self.player.rect.colliderect(enemy.rect):
                self.game_over = True
        
        # Check goal collision (win condition)
        if self.goal_ready and self.player.rect.colliderect(self.goal.rect):
            self.won = True
    
    def draw(self):
        screen.fill(WHITE)
        screen.blit(self.image,(0,0))
        
        # Draw game elements
        for platform in self.platforms:
            platform.draw(screen)
        
        for shuriken in self.shurikens:
            shuriken.draw(screen)

        for enemy in self.enemies:   
            enemy.draw(screen)
        
        if self.goal_ready:
            self.goal.draw(screen)

        # Greninja should disappear into the pokeball
        # when reaching the goal
        if not self.won:
            self.player.draw(screen)
        
        # Draw score
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {self.score}", True, BLACK)
        screen.blit(score_text, (10, 10))
        
        # Draw game state
        if self.game_over:
            game_over_text = font.render("GAME OVER - Press R to Restart", True, RED)
            screen.blit(game_over_text, (200, 250))
        
        if self.won:
            win_text = font.render("YOU WIN! - Press R to Restart", True, GREEN)
            screen.blit(win_text, (200, 250))
        
        pygame.display.flip()
    
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            
            if not self.game_over and not self.won:
                self.update()
            
            # Check for restart
            keys = pygame.key.get_pressed()
            if (self.game_over or self.won) and keys[pygame.K_r]:
                self.__init__()
            
            self.draw()
            clock.tick(60)
        
        pygame.quit()
        sys.exit()


# Run the game
if __name__ == "__main__":
    game = Game()
    game.run()


