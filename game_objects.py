import pygame
import math
import random

#.
#.
#.
#.

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 100, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
YELLOW = (255, 255, 0)
PURPLE = (150, 0, 255)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)

# Screen constants
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700

class Ball:
    def __init__(self, x, y, vel_x=None, vel_y=None, power_shot=False):
        self.x, self.y = x, y
        self.radius = 8
        self.vel_x = vel_x or random.choice([-6, 6])
        self.vel_y = vel_y or -7
        self.trail = []
        self.active = True
        self.power_shot = power_shot
        self.power_shot_timer = 300 if power_shot else 0
        self.destruction_radius = 60 if power_shot else 0
        
    def update(self, paddle, blocks):
        if not self.active:
            return False
        
        if self.power_shot_timer > 0:
            self.power_shot_timer -= 1
            if self.power_shot_timer <= 0:
                self.power_shot = False
                self.destruction_radius = 0
            
        self.x += self.vel_x
        self.y += self.vel_y
        
        # Speed control
        speed = math.sqrt(self.vel_x**2 + self.vel_y**2)
        if speed < 5:
            factor = 5 / speed
            self.vel_x *= factor
            self.vel_y *= factor
        elif speed > 12:
            factor = 12 / speed
            self.vel_x *= factor
            self.vel_y *= factor
        
        # Trail
        self.trail.append((int(self.x), int(self.y)))
        if len(self.trail) > (10 if self.power_shot else 6):
            self.trail.pop(0)
        
        # Wall collisions
        if self.x <= self.radius or self.x >= SCREEN_WIDTH - self.radius:
            self.vel_x = -self.vel_x
            self.x = max(self.radius + 1, min(SCREEN_WIDTH - self.radius - 1, self.x))
            
        if self.y <= self.radius:
            self.vel_y = -self.vel_y
            self.y = self.radius + 1
        
        return self.check_paddle_collision(paddle) or self.check_block_collisions(blocks)
    
    def check_paddle_collision(self, paddle):
        if (self.y + self.radius >= paddle.y and self.y + self.radius <= paddle.y + paddle.height + 10 and
            self.x + self.radius >= paddle.x and self.x - self.radius <= paddle.x + paddle.width and self.vel_y > 0):
            
            hit_pos = max(0, min(1, (self.x - paddle.x) / paddle.width))
            angle = (hit_pos - 0.5) * math.pi / 2.2
            speed = max(5, math.sqrt(self.vel_x**2 + self.vel_y**2))
            
            self.vel_x = speed * math.sin(angle)
            self.vel_y = -abs(speed * 0.85)
            self.y = paddle.y - self.radius - 2
            return True
        return False
    
    def check_block_collisions(self, blocks):
        hit_blocks = []
        
        for block in blocks:
            if not block.destroyed:
                # Normal collision
                if self.collides_with_block(block):
                    hit_blocks.append(block)
                # Power shot area destruction
                elif self.power_shot and self.destruction_radius > 0:
                    block_center_x = block.x + block.width / 2
                    block_center_y = block.y + block.height / 2
                    distance = math.sqrt((self.x - block_center_x)**2 + (self.y - block_center_y)**2)
                    if distance <= self.destruction_radius:
                        hit_blocks.append(block)
        
        if hit_blocks:
            # Handle collision with first block for physics
            main_block = hit_blocks[0]
            if self.collides_with_block(main_block):
                # Calculate collision direction
                ball_center_x, ball_center_y = self.x, self.y
                block_center_x = main_block.x + main_block.width / 2
                block_center_y = main_block.y + main_block.height / 2
                
                overlap_x = (self.radius + main_block.width / 2) - abs(ball_center_x - block_center_x)
                overlap_y = (self.radius + main_block.height / 2) - abs(ball_center_y - block_center_y)
                
                if overlap_x < overlap_y:
                    self.vel_x = -self.vel_x
                    self.x = main_block.x - self.radius - 1 if ball_center_x < block_center_x else main_block.x + main_block.width + self.radius + 1
                else:
                    self.vel_y = -self.vel_y
                    self.y = main_block.y - self.radius - 1 if ball_center_y < block_center_y else main_block.y + main_block.height + self.radius + 1
            
            # Destroy all hit blocks
            for block in hit_blocks:
                if self.power_shot and block.type != 'multi_hit':
                    block.destroyed = True
                else:
                    block.hit()
            
            return True
        return False
    
    def collides_with_block(self, block):
        closest_x = max(block.x, min(self.x, block.x + block.width))
        closest_y = max(block.y, min(self.y, block.y + block.height))
        distance = math.sqrt((self.x - closest_x)**2 + (self.y - closest_y)**2)
        return distance < self.radius
    
    def is_out_of_bounds(self):
        return self.y > SCREEN_HEIGHT + 50
    
    def draw(self, screen):
        if not self.active:
            return

        ball_color = (242, 242, 242)  # Slightly off-white
        edge_color = (0, 255, 255)

        if self.power_shot:
            pulse = 1 + 0.3 * math.sin(pygame.time.get_ticks() * 0.02)
            radius = int(self.radius * pulse)
            pygame.draw.circle(screen, (255, 56, 96), (int(self.x), int(self.y)), radius)
            pygame.draw.circle(screen, (255, 255, 0), (int(self.x), int(self.y)), radius, 2)
        else:
            pygame.draw.circle(screen, ball_color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, edge_color, (int(self.x), int(self.y)), self.radius, 2)



class Block:
    def __init__(self, x, y, block_type='normal'):
        self.x, self.y = x, y
        self.width, self.height = 80, 30
        self.type = block_type
        self.destroyed = False
        self.hits = 0
        self.max_hits = {'normal': 1, 'strong': 2, 'extra_ball': 1, 'speed_up': 1, 'big_paddle': 1, 'multi_hit': 3}[block_type]
        self.color = {'normal': BLUE, 'strong': RED, 'extra_ball': GREEN, 'speed_up': YELLOW, 'big_paddle': PURPLE, 'multi_hit': ORANGE}[block_type]
    
    @classmethod
    def from_dict(cls, block_data):
        """Create a Block instance from a dictionary (JSON data)"""
        block_type = block_data.get('type', 'normal')
        x = block_data.get('x', 0)
        y = block_data.get('y', 0)
        
        # Create the block with the specified type
        block = cls(x, y, block_type)
        
        # Override max_hits if specified in JSON (for custom hit counts)
        if 'hits' in block_data:
            block.max_hits = block_data['hits']  # Set max hits from JSON
            # block.hits stays at 0 (no hits taken yet)
        
        return block
    
    def hit(self):
        self.hits += 1
        if self.hits >= self.max_hits:
            self.destroyed = True
            return self.type
        return None
    
    
    
    def draw(self, screen):
        if self.destroyed:
            return

        # Flat color style
        base_color = self.color
        intensity = 1 - (self.hits / self.max_hits)
        def clamp_color(val):
            return max(0, min(255, int(val)))
        color = tuple(clamp_color(c * intensity + 30) for c in base_color)

        # Rounded block with border
        block_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(screen, color, block_rect, border_radius=6)
        pygame.draw.rect(screen, (255, 255, 255), block_rect, width=2, border_radius=6)

        # Subtle text indicator
        if self.type != 'normal':
            font = pygame.font.Font(None, 20)
            text_map = {
                'strong': 'S',
                'extra_ball': '+',
                'speed_up': '>>',
                'big_paddle': '=',
                'multi_hit': str(self.max_hits - self.hits)
            }
            label = text_map.get(self.type, '?')
            text = font.render(label, True, (255, 255, 255))
            text_rect = text.get_rect(center=block_rect.center)
            screen.blit(text, text_rect)

    


class Paddle:
    def __init__(self):
        self.width, self.height = 100, 15
        self.x = SCREEN_WIDTH // 2 - self.width // 2
        self.y = SCREEN_HEIGHT - 40
        self.speed = 8
        self.target_x = self.x
        self.power_ups = {}
        self.fist_action_cooldown = 0
        self.peace_cooldown = 0
        
    def update(self, gesture):
        if not gesture['detected']:
            return
        
        # Update cooldowns
        if self.fist_action_cooldown > 0:
            self.fist_action_cooldown -= 1
        if self.peace_cooldown > 0:
            self.peace_cooldown -= 1
            
        # Movement
        target_ratio = gesture['hand_x']
        self.target_x = (SCREEN_WIDTH - self.width) * target_ratio
        diff = self.target_x - self.x
        self.x += diff * 0.4
        self.x = max(0, min(SCREEN_WIDTH - self.width, self.x))
        
        # Peace gesture for big paddle (with cooldown)
        if gesture['hand_state'] == 'peace' and self.peace_cooldown <= 0 and 'big_paddle' not in self.power_ups:
            self.activate_power_up('big_paddle')
            self.peace_cooldown = 1200  # 20 second cooldown
        
        # Update power-up timers
        for power_up in list(self.power_ups.keys()):
            self.power_ups[power_up] -= 1
            if self.power_ups[power_up] <= 0:
                self.deactivate_power_up(power_up)
    
    def can_perform_fist_action(self):
        return self.fist_action_cooldown <= 0
    
    def perform_fist_action(self):
        if self.can_perform_fist_action():
            self.fist_action_cooldown = 30
            return True
        return False
    
    def activate_power_up(self, power_type):
        if power_type == 'big_paddle':
            self.power_ups['big_paddle'] = 600  # 10 seconds
            old_width = self.width
            self.width = 150
            self.x -= (self.width - old_width) / 2
            self.x = max(0, min(SCREEN_WIDTH - self.width, self.x))
        elif power_type == 'speed_up':
            self.power_ups['speed_up'] = 600
            self.speed = 12
    
    def deactivate_power_up(self, power_type):
        if power_type == 'big_paddle':
            old_width = self.width
            self.width = 100
            self.x += (old_width - self.width) / 2
            self.x = max(0, min(SCREEN_WIDTH - self.width, self.x))
        elif power_type == 'speed_up':
            self.speed = 8
        del self.power_ups[power_type]
    
    def draw(self, screen):
        # Paddle glow if power-up active
        glow = 'big_paddle' in self.power_ups
        paddle_rect = pygame.Rect(int(self.x), int(self.y), self.width, self.height)
        
        if glow:
            glow_color = (131, 56, 236)
            pygame.draw.rect(screen, glow_color, paddle_rect.inflate(10, 4), border_radius=8)
        
        pygame.draw.rect(screen, (0, 255, 225), paddle_rect, border_radius=8)
        pygame.draw.rect(screen, (255, 255, 255), paddle_rect, 2, border_radius=8)