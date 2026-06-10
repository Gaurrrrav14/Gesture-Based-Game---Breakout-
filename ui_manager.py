import pygame
import sys
from game_objects import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, BLUE, GREEN, YELLOW, ORANGE, RED, CYAN

#.
#.
#.
#.

class UIManager:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Gesture Block Breaker")
        self.clock = pygame.time.Clock()
        
        # Fonts
        font_path = "assets/fonts/PressStart2P-Regular.ttf"
        self.title_font = pygame.font.Font(font_path, 28)
        self.subtitle_font = pygame.font.Font(font_path, 20)
        self.font = pygame.font.Font(font_path, 18)
        self.small_font = pygame.font.Font(font_path, 12)

        
        # UI States
        self.current_state = "HOME"  # HOME, INSTRUCTIONS, GAME, PAUSE, GAME_OVER
        self.selected_option = 0
        
        # Menu options
        self.home_options = ["PLAY GAME", "HOW TO PLAY", "QUIT"]
        self.pause_options = ["RESUME", "RESTART", "HOME", "QUIT"]
        self.game_over_options = ["PLAY AGAIN", "HOME", "QUIT"]
        self.difficulty_options = ["EASY", "MEDIUM", "HARD", "EXPERT"]

        # Colors for animations
        self.time_offset = 0
        
        # Gesture cursor - Initialize at center
        self.cursor_x = SCREEN_WIDTH // 2
        self.cursor_y = SCREEN_HEIGHT // 2
        self.pinching = False
        self.last_pinch_state = False
        self.cursor_visible = True
        
        # Button rects for home screen
        self.home_button_rects = []
        self.pause_button_rects = []
        self.game_over_button_rects = []
        self.difficulty_button_rects = []
        self.update_button_rects()

    def draw_button(self, screen, rect, text, selected=False):
        bg_color = (34, 40, 49)
        border_color = (255, 255, 255) if selected else (100, 100, 100)
        text_color = (255, 255, 255)

        pygame.draw.rect(screen, bg_color, rect, border_radius=8)
        pygame.draw.rect(screen, border_color, rect, 2, border_radius=8)

        font_surface = self.font.render(text, True, text_color)
        text_rect = font_surface.get_rect(center=rect.center)
        screen.blit(font_surface, text_rect)

    # Add this method to the UIManager class
    def draw_level_info(self, level_name, difficulty):
        """Draw current level information"""
        if hasattr(self, 'current_level_name'):
            level_text = f"Level: {level_name}"
            level_surface = self.small_font.render(level_text, True, CYAN)
            self.screen.blit(level_surface, (20, SCREEN_HEIGHT - 60))
            
            difficulty_text = f"Difficulty: {difficulty}"
            difficulty_surface = self.small_font.render(difficulty_text, True, YELLOW)
            self.screen.blit(difficulty_surface, (20, SCREEN_HEIGHT - 40))




    def update_button_rects(self):
        """Update button rectangles for all menus with consistent placement and size"""
        button_width = 200
        button_height = 45
        spacing = 60
        start_y = 250
        center_x = SCREEN_WIDTH // 2 - button_width // 2

        # Home screen buttons
        self.home_button_rects = []
        for i in range(len(self.home_options)):
            rect = pygame.Rect(center_x, start_y + i * spacing, button_width, button_height)
            self.home_button_rects.append(rect)

        # Pause screen buttons
        self.pause_button_rects = []
        for i in range(len(self.pause_options)):
            rect = pygame.Rect(center_x, start_y + i * spacing, button_width, button_height)
            self.pause_button_rects.append(rect)

        # Game over screen buttons
        self.game_over_button_rects = []
        for i in range(len(self.game_over_options)):
            rect = pygame.Rect(center_x, start_y + i * spacing, button_width, button_height)
            self.game_over_button_rects.append(rect)

        # Difficulty screen buttons
        self.difficulty_button_rects = []
        for i in range(len(self.difficulty_options)):
            rect = pygame.Rect(center_x, start_y + i * spacing, button_width, button_height)
            self.difficulty_button_rects.append(rect)

    
    def update_cursor_from_gesture(self, gesture):
        """Update cursor position based on hand gesture"""
        if gesture and gesture.get('detected', False):
            # Convert normalized coordinates to screen coordinates
            # Flip X coordinate to match natural hand movement
            target_x = int(gesture['hand_x'] * SCREEN_WIDTH)
            target_y = int(gesture['hand_y'] * SCREEN_HEIGHT)
            
            # Smooth cursor movement
            self.cursor_x = int(self.cursor_x * 0.7 + target_x * 0.3)
            self.cursor_y = int(self.cursor_y * 0.7 + target_y * 0.3)
            
            self.pinching = gesture.get('pinch', False)
            self.cursor_visible = True
            
            # Keep cursor within screen bounds
            self.cursor_x = max(10, min(SCREEN_WIDTH - 10, self.cursor_x))
            self.cursor_y = max(10, min(SCREEN_HEIGHT - 10, self.cursor_y))
        else:
            self.cursor_visible = False
    
    def check_button_hover(self, button_rects):
        """Check which button the cursor is hovering over"""
        if not self.cursor_visible:
            return -1
            
        cursor_point = (self.cursor_x, self.cursor_y)
        for i, rect in enumerate(button_rects):
            if rect.collidepoint(cursor_point):
                return i
        return -1
    
    def check_pinch_click(self):
        """Check if a pinch gesture was performed (click)"""
        if self.pinching and not self.last_pinch_state:
            self.last_pinch_state = True
            return True
        elif not self.pinching:
            self.last_pinch_state = False
        return False
    
    def draw_cursor(self):
        """Draw the gesture cursor"""
        if not self.cursor_visible:
            return
            
        # Draw cursor with different colors based on state
        if self.pinching:
            color = RED
            size = 12
        else:
            color = YELLOW
            size = 8
        
        # Draw cursor with glow effect
        for i in range(3, 0, -1):
            alpha_size = size + i * 3
            alpha_color = (color[0] // (i + 1), color[1] // (i + 1), color[2] // (i + 1))
            pygame.draw.circle(self.screen, alpha_color, (self.cursor_x, self.cursor_y), alpha_size)
        
        # Draw main cursor
        pygame.draw.circle(self.screen, color, (self.cursor_x, self.cursor_y), size)
        pygame.draw.circle(self.screen, WHITE, (self.cursor_x, self.cursor_y), size, 2)
        
        # Draw crosshair for precision
        pygame.draw.line(self.screen, WHITE, 
                        (self.cursor_x - size - 5, self.cursor_y), 
                        (self.cursor_x - size, self.cursor_y), 2)
        pygame.draw.line(self.screen, WHITE, 
                        (self.cursor_x + size, self.cursor_y), 
                        (self.cursor_x + size + 5, self.cursor_y), 2)
        pygame.draw.line(self.screen, WHITE, 
                        (self.cursor_x, self.cursor_y - size - 5), 
                        (self.cursor_x, self.cursor_y - size), 2)
        pygame.draw.line(self.screen, WHITE, 
                        (self.cursor_x, self.cursor_y + size), 
                        (self.cursor_x, self.cursor_y + size + 5), 2)
    
    def draw_gesture_status(self):
        """Draw gesture detection status"""
        if self.cursor_visible:
            status_text = "Hand Detected"
            if self.pinching:
                status_text += " - PINCHING"
                color = RED
            else:
                color = GREEN
        else:
            status_text = "No Hand Detected"
            color = ORANGE
        
        status_surface = self.small_font.render(status_text, True, color)
        # Position in top-left, below camera feed area
        self.screen.blit(status_surface, (10, 170))
    
    def draw_static_background(self):
        self.screen.fill((13, 17, 23))  # Deep navy/black — #0d1117

    
    def draw_home_screen(self):
        self.draw_static_background()

        # Title
        title_text = "GESTURE BREAKER"
        title_surface = self.title_font.render(title_text, True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 120))
        self.screen.blit(title_surface, title_rect)

        # Buttons
        for i, option in enumerate(self.home_options):
            self.draw_button(self.screen, self.home_button_rects[i], option, i == self.selected_option)


        # Instructions
        instruction = "🖐️ Move hand to select • 🤏 Pinch to confirm • ESC to quit"
        text = self.small_font.render(instruction, True, (150, 150, 150))
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
        self.screen.blit(text, rect)

        # Draw cursor and gesture feedback
        self.draw_gesture_status()
        self.draw_cursor()

    
    def draw_instructions_screen(self):
        self.draw_static_background()

        title_surface = self.subtitle_font.render("HOW TO PLAY", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH//2, 60))
        self.screen.blit(title_surface, title_rect)

        start_y = 120
        lines = [
            "🖐️ OPEN PALM - Move paddle left/right",
            "✊ FIST - Launch ball / Activate power shot",
            "✌️ PEACE - Activate big paddle (20s cooldown)",
            "🤏 PINCH - Select menu options / Pause game",
            "",
            "POWER-UPS:",
            "🔵 Normal   🔴 Strong   🟢 Extra Ball",
            "🟡 Speed Up   🟣 Big Paddle   🟠 Multi-Hit",
            "",
            "Break all blocks to win. Don't drop the ball!"
        ]

        for i, line in enumerate(lines):
            if line.strip() == "":
                continue
            surface = self.small_font.render(line, True, (200, 200, 200))
            rect = surface.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * 26))
            self.screen.blit(surface, rect)

        back_surface = self.font.render("ESC or PINCH to go back", True, (150, 200, 255))
        back_rect = back_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
        self.screen.blit(back_surface, back_rect)

        self.draw_gesture_status()
        self.draw_cursor()

    
    def draw_pause_screen(self):
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Pause title
        pause_surface = self.subtitle_font.render("PAUSED", True, YELLOW)
        pause_rect = pause_surface.get_rect(center=(SCREEN_WIDTH//2, 200))
        self.screen.blit(pause_surface, pause_rect)
        
        # Menu options
        start_y = 280
        for i, option in enumerate(self.pause_options):  # or game_over_options
            self.draw_button(self.screen, self.pause_button_rects[i], option, i == self.selected_option)
        
        # Draw gesture status and cursor
        self.draw_gesture_status()
        self.draw_cursor()
    
    def draw_game_over_screen(self, score, level):
        self.draw_static_background()
        
        # Game Over title
        game_over_surface = self.subtitle_font.render("GAME OVER", True, RED)
        game_over_rect = game_over_surface.get_rect(center=(SCREEN_WIDTH//2, 150))
        self.screen.blit(game_over_surface, game_over_rect)
        
        # Final stats
        score_surface = self.font.render(f"Final Score: {score}", True, WHITE)
        score_rect = score_surface.get_rect(center=(SCREEN_WIDTH//2, 200))
        self.screen.blit(score_surface, score_rect)
        
        level_surface = self.font.render(f"Level Reached: {level}", True, WHITE)
        level_rect = level_surface.get_rect(center=(SCREEN_WIDTH//2, 240))
        self.screen.blit(level_surface, level_rect)
        
        # Menu options
        start_y = 320
        for i, option in enumerate(self.game_over_options):  # or game_over_options
            self.draw_button(self.screen, self.pause_button_rects[i], option, i == self.selected_option)
        
        # Draw gesture status and cursor
        self.draw_gesture_status()
        self.draw_cursor()

    def draw_difficulty_screen(self):
        self.draw_static_background()

        # Title
        title_surface = self.subtitle_font.render("SELECT DIFFICULTY", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title_surface, title_rect)

        # Difficulty descriptions
        descriptions = {
            "EASY": "Slower ball, more power shots, big paddle",
            "MEDIUM": "Balanced speed and power",
            "HARD": "Faster ball, fewer powers, smaller paddle",
            "EXPERT": "Max speed, no help, tiny paddle"
        }

        # Draw buttons with descriptions above them
        for i, option in enumerate(self.difficulty_options):
            rect = self.difficulty_button_rects[i]
            selected = i == self.selected_option

            # Draw description first — above the button
            desc = descriptions[option]
            desc_surface = self.small_font.render(desc, True, (150, 200, 255))
            desc_rect = desc_surface.get_rect(center=(rect.centerx, rect.top - 8))
            self.screen.blit(desc_surface, desc_rect)

            # Then draw the button on top
            self.draw_button(self.screen, rect, option, selected)

        # Back instruction
        back_text = "ESC to go back"
        back_surface = self.small_font.render(back_text, True, (180, 180, 180))
        back_rect = back_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
        self.screen.blit(back_surface, back_rect)

        self.draw_gesture_status()
        self.draw_cursor()



    def handle_menu_input(self, event, gesture=None):
        """Handle input for menu navigation"""
        # Always update cursor from gesture if available
        if gesture:
            self.update_cursor_from_gesture(gesture)
        
        # Handle gesture input for each screen
        if gesture and gesture.get('detected', False):
            if self.current_state == "HOME":
                hover_index = self.check_button_hover(self.home_button_rects)
                if hover_index >= 0:
                    self.selected_option = hover_index
                
                if self.check_pinch_click() and hover_index >= 0:
                    return self.home_options[hover_index]
            
            elif self.current_state == "PAUSE":
                hover_index = self.check_button_hover(self.pause_button_rects)
                if hover_index >= 0:
                    self.selected_option = hover_index
                
                if self.check_pinch_click() and hover_index >= 0:
                    return self.pause_options[hover_index]
            
            elif self.current_state == "GAME_OVER":
                hover_index = self.check_button_hover(self.game_over_button_rects)
                if hover_index >= 0:
                    self.selected_option = hover_index
                
                if self.check_pinch_click() and hover_index >= 0:
                    return self.game_over_options[hover_index]
            elif self.current_state == "DIFFICULTY":
                hover_index = self.check_button_hover(self.difficulty_button_rects)
                if hover_index >= 0:
                    self.selected_option = hover_index
                
                if self.check_pinch_click() and hover_index >= 0:
                    return self.difficulty_options[hover_index]
            elif self.current_state == "INSTRUCTIONS":
                if self.check_pinch_click():
                    return "HOME"
        
        return None
    
    def handle_keyboard_input(self, event):
        """Handle keyboard input for menu navigation"""
        if event.type == pygame.KEYDOWN:
            current_options = []
            if self.current_state == "HOME":
                current_options = self.home_options
            elif self.current_state == "PAUSE":
                current_options = self.pause_options
            elif self.current_state == "GAME_OVER":
                current_options = self.game_over_options
            elif self.current_state == "INSTRUCTIONS":
                if event.key in [pygame.K_ESCAPE, pygame.K_RETURN]:
                    return "HOME"
                return None
            elif self.current_state == "DIFFICULTY":
                if event.key == pygame.K_ESCAPE:
                    return "HOME"
                elif event.key == pygame.K_UP:
                    self.selected_option = (self.selected_option - 1) % len(self.difficulty_options)
                elif event.key == pygame.K_DOWN:
                    self.selected_option = (self.selected_option + 1) % len(self.difficulty_options)
                elif event.key == pygame.K_RETURN:
                    return self.difficulty_options[self.selected_option]
                return None
            
            if current_options:
                if event.key == pygame.K_UP:
                    self.selected_option = (self.selected_option - 1) % len(current_options)
                elif event.key == pygame.K_DOWN:
                    self.selected_option = (self.selected_option + 1) % len(current_options)
                elif event.key == pygame.K_RETURN:
                    return current_options[self.selected_option]
                elif event.key == pygame.K_ESCAPE:
                    return "QUIT" if self.current_state == "HOME" else "HOME"
    
        return None
    def set_state(self, state):
        """Change the current UI state"""
        self.current_state = state
        self.selected_option = 0
    
    def update(self):
        """Update animations and time-based effects"""
        pass
    
    def get_fonts(self):
        """Return fonts for use in game logic"""
        return self.font, self.small_font