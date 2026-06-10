import pygame
import cv2
import random
import json
import os
import math
from game_objects import Ball, Block, Paddle, SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, YELLOW, GREEN, ORANGE, RED
from trajectory_predictor import TrajectoryPredictor

class GameLogic:
    def __init__(self, gesture_detector, shared_camera=None, difficulty="MEDIUM"):    
        self.gesture_detector = gesture_detector
        self.paddle = Paddle()
        self.balls = []
        self.blocks = []
        self.score = 0
        self.level = 1
        self.last_gesture_state = 'none'
        self.power_shots_remaining = 2
        self.difficulty = difficulty
        self.apply_difficulty_settings()
        self.aim_mode = False
        self.aim_vector = (0, -1)
        self.smooth_aim_vector = (0, -1)  # Used for smoothing

        self.trajectory_points = []
        self.max_trajectory_length = 500    # max steps to simulate
        self.trajectory_bounces    = 3      # max wall bounces
        self.trajectory_predictor = TrajectoryPredictor(self)



        # Use shared camera or create own (for backwards compatibility)
        if shared_camera is not None:
            self.cap = shared_camera
            self.owns_camera = False  # Don't release shared camera
        else:
            self.cap = cv2.VideoCapture(0)
            self.owns_camera = True
        
        self.camera_width = 200
        self.camera_height = 150
        
        self.load_level(difficulty)
        self.current_gesture = {'hand_x': 0.5, 'hand_state': 'none', 'detected': False}
        self.camera_frame = None
    
    # Add this method to replace generate_blocks()
    def load_level(self, difficulty="MEDIUM", level=1):
        """Load level from JSON file based on difficulty and level number"""
        self.blocks = []
        self.current_level_name = f"{difficulty} Level {level}"
        level_file = os.path.join("levels", f"{difficulty}_{level}.json")

        if not os.path.exists(level_file):
            print(f"⚠️ Level file {level_file} not found, using fallback")
            self.generate_blocks_fallback()
            return

        try:
            with open(level_file, 'r') as f:
                level_data = json.load(f)
            
            self.current_level_name = level_data.get('level_name', f"{difficulty} Level {level}")
            level_description = level_data.get('description', '')

            blocks_data = level_data.get('blocks', [])
            for block_data in blocks_data:
                block = Block.from_dict(block_data)
                self.blocks.append(block)

            print(f"✅ Loaded {len(self.blocks)} blocks from {level_file}")
            if level_description:
                print(f"📝 {level_description}")
        except Exception as e:
            print(f"❌ Error loading {level_file}: {e}")
            self.generate_blocks_fallback()


    # Keep the old generate_blocks as a fallback
    def generate_blocks_fallback(self):
        """Fallback procedural block generation (original method)"""
        self.blocks = []
        for row in range(6):
            for col in range(10):
                x, y = col * 90 + 50, row * 40 + 80
                if row == 0:
                    block_type = 'multi_hit'
                elif row == 1:
                    block_type = 'strong'
                elif col % 4 == 0:
                    block_type = random.choice(['extra_ball', 'speed_up', 'big_paddle'])
                else:
                    block_type = 'normal'
                self.blocks.append(Block(x, y, block_type))
#.
#.
#.
#.
    def apply_difficulty_settings(self):
        """Apply difficulty-specific settings"""
        if self.difficulty == "EASY":
            self.power_shots_remaining = 3
            self.ball_speed_multiplier = 0.7
            self.paddle_size_multiplier = 1.3
        elif self.difficulty == "MEDIUM":
            self.power_shots_remaining = 2
            self.ball_speed_multiplier = 1.0
            self.paddle_size_multiplier = 1.0
        elif self.difficulty == "HARD":
            self.power_shots_remaining = 1
            self.ball_speed_multiplier = 1.3
            self.paddle_size_multiplier = 0.8
        elif self.difficulty == "EXPERT":
            self.power_shots_remaining = 0
            self.ball_speed_multiplier = 1.6
            self.paddle_size_multiplier = 0.6
        
        # Apply paddle size immediately if paddle exists
        if hasattr(self, 'paddle'):
            base_width = 100
            self.paddle.width = int(base_width * self.paddle_size_multiplier)

    def reset_game(self):
        self.score, self.level = 0, 1
        self.balls = []
        self.load_level(self.difficulty, level=1)
        self.paddle.power_ups = {}
        self.paddle.peace_cooldown = 0
        self.aim_mode = False
        self.aim_vector = (0, -1)
        self.trajectory_points = []
        self.apply_difficulty_settings()

    
    def update_gesture(self):
        """Only used if we have our own camera (backwards compatibility)"""
        if self.owns_camera:
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                gesture, processed_frame = self.gesture_detector.detect_gesture(frame)
                self.current_gesture = gesture
                self.camera_frame = cv2.resize(processed_frame, (self.camera_width, self.camera_height))
    
    def handle_fist_gesture(self):
        # Triggered when a new “fist” is detected and paddle is ready
        if (self.current_gesture['hand_state'] == 'fist'
                and self.last_gesture_state != 'fist'
                and self.paddle.can_perform_fist_action()):
            
            # ===== Aim-and-Launch Mode =====
            if len(self.balls) == 0:
                if not self.aim_mode:
                    # First fist: enter aim mode (show trajectory)
                    self.aim_mode = True
                    self.paddle.perform_fist_action()
                    return "AIM_MODE"
                else:
                    # Second fist: fire along the selected aim_vector
                    self.launch_ball_with_aim()
                    self.aim_mode = False
                    self.trajectory_points = []
                    self.paddle.perform_fist_action()
                    return "LAUNCH"
            
            # ===== Existing Power-Shot Logic =====
            elif self.power_shots_remaining > 0:
                self.activate_power_shots()
                self.power_shots_remaining -= 1
                self.paddle.perform_fist_action()
                return "POWER_SHOT"

        return None
    
    def launch_ball(self):
        base_vel_x = random.choice([-5, 5])
        base_vel_y = -8
        vel_x = base_vel_x * self.ball_speed_multiplier
        vel_y = base_vel_y * self.ball_speed_multiplier
        new_ball = Ball(self.paddle.x + self.paddle.width // 2, self.paddle.y - 20, vel_x, vel_y)
        self.balls.append(new_ball)
    
    def activate_power_shots(self):
        for ball in self.balls:
            ball.power_shot = True
            ball.power_shot_timer = 100
            ball.destruction_radius = 40
    
    def update(self):
        # Only update gesture if we own the camera
        if self.owns_camera:
            self.update_gesture()
        
        self.handle_fist_gesture()
        self.last_gesture_state = self.current_gesture['hand_state']
        
        self.paddle.update(self.current_gesture)
        if self.aim_mode and self.current_gesture.get('detected'):
            cx = int(self.current_gesture['hand_x'] * SCREEN_WIDTH)
            cy = int(self.current_gesture['hand_y'] * SCREEN_HEIGHT)
            self.update_aim_direction(cx, cy)
        # Update balls
        for ball in self.balls[:]:
            if ball.update(self.paddle, self.blocks):
                self.score += 5
            if ball.is_out_of_bounds():
                self.balls.remove(ball)
        
        # Handle power-ups
        for block in self.blocks:
            if block.destroyed and block.type in ['extra_ball', 'speed_up', 'big_paddle']:
                if block.type == 'extra_ball':
                    base_vel_x = random.choice([-4, 4])
                    base_vel_y = -6
                    vel_x = base_vel_x * self.ball_speed_multiplier
                    vel_y = base_vel_y * self.ball_speed_multiplier
                    new_ball = Ball(self.paddle.x + self.paddle.width // 2, self.paddle.y - 20, vel_x, vel_y)
                    self.balls.append(new_ball)
                elif block.type == 'speed_up':
                    self.paddle.activate_power_up('speed_up')
                elif block.type == 'big_paddle':
                    self.paddle.activate_power_up('big_paddle')
                block.type = 'normal'
        
        # In the update() method, replace this section:
        # Check win conditions
        if all(block.destroyed for block in self.blocks):
            self.level += 1
            self.load_level(self.difficulty, self.level)
            self.balls = []
            return "LEVEL_COMPLETE"
        
        # Check lose condition (no balls and no way to launch)
        if len(self.balls) == 0 and not any(not block.destroyed for block in self.blocks):
            return "GAME_OVER"
        
        return "PLAYING"
    
    def draw_background(self, screen):
        screen.fill((13, 17, 23))  # Same dark navy as UI

    
    def draw_ui(self, screen, font, small_font):
        stats = [
            f"Score: {self.score}",
            f"Level: {self.level}",
            f"Balls: {len(self.balls)}",
            f"Power Shots: {self.power_shots_remaining}"
        ]
        
        for i, text in enumerate(stats):
            surface = small_font.render(text, True, (255, 255, 255))
            screen.blit(surface, (20, 20 + i * 25))

        # Gesture status
        gesture = self.current_gesture
        gesture_text = "Hand: " + gesture['hand_state'].upper() if gesture['detected'] else "No Hand"
        gesture_color = (0, 255, 0) if gesture['detected'] else (255, 64, 64)
        gesture_surface = small_font.render(gesture_text, True, gesture_color)
        screen.blit(gesture_surface, (20, 140))

        if len(self.balls) == 0:
            text = font.render("FIST TO LAUNCH!", True, (255, 255, 0))
            screen.blit(text, text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2)))

    
    def draw_camera_feed(self, screen):
        """Draw camera feed - only if we own the camera (backwards compatibility)"""
        if self.owns_camera and hasattr(self, 'camera_frame') and self.camera_frame is not None:
            frame_rgb = cv2.cvtColor(self.camera_frame, cv2.COLOR_BGR2RGB)
            frame_surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
            screen.blit(frame_surface, (SCREEN_WIDTH - self.camera_width - 10, SCREEN_HEIGHT - self.camera_height - 10))
    
    def draw(self, screen, font, small_font):
        self.draw_background(screen)
        for block in self.blocks:
            block.draw(screen)
        for ball in self.balls:
            ball.draw(screen)
        self.paddle.draw(screen)
        self.draw_ui(screen, font, small_font)
        self.draw_aim_overlay(screen)

        # Only draw camera feed if we own the camera
        if self.owns_camera:
            self.draw_camera_feed(screen)
    
    def cleanup(self):
        # Only release camera if we own it
        if self.owns_camera and hasattr(self, 'cap'):
            self.cap.release()
        cv2.destroyAllWindows()

    def launch_ball_with_aim(self):
            base_speed = 8
            vx = self.aim_vector[0] * base_speed * self.ball_speed_multiplier
            vy = self.aim_vector[1] * base_speed * self.ball_speed_multiplier
            b = Ball(self.paddle.x + self.paddle.width // 2,
                    self.paddle.y - 20, vx, vy)
            self.balls.append(b)

    def update_aim_direction(self, cursor_x, cursor_y):
        px = self.paddle.x + self.paddle.width // 2
        py = self.paddle.y

        dx = cursor_x - px
        dy = cursor_y - py

        dx *= 1.8  # sensitivity tweak

        dist = math.hypot(dx, dy)
        if dist > 0:
            aim_y = min(-0.15, dy / dist)
            new_aim = (dx / dist, aim_y)

            alpha = 0.25
            self.smooth_aim_vector = (
                (1 - alpha) * self.smooth_aim_vector[0] + alpha * new_aim[0],
                (1 - alpha) * self.smooth_aim_vector[1] + alpha * new_aim[1]
            )

            norm = math.hypot(*self.smooth_aim_vector)
            if norm > 0:
                self.aim_vector = (self.smooth_aim_vector[0] / norm, self.smooth_aim_vector[1] / norm)

            # 🧠 Update trajectory
            self.trajectory_points = self.trajectory_predictor.simulate((px, py), self.aim_vector)



    def draw_aim_overlay(self, screen):
        if self.aim_mode and self.trajectory_points:
            self.trajectory_predictor.draw(screen, self.trajectory_points)