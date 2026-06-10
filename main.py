import pygame
import sys
import cv2
from ui_manager import UIManager
from game_logic import GameLogic
from gesture_detector import ImprovedGestureDetector
from emotion_detector import EmotionDetector


#.
#.
#.
#.
class MainGame:
    def __init__(self):
        self.ui_manager = UIManager()
        self.gesture_detector = ImprovedGestureDetector()
        self.game_logic = None
        self.running = True
        self.emotion_detector = EmotionDetector()
        self.current_emotion = None
        self.emotion_counter = 0
        self.emotion_interval = 10  

        self.FPS = 60
        self.selected_difficulty = "MEDIUM"

        # Single camera setup - shared between UI and game
        self.camera = cv2.VideoCapture(0)
        self.current_gesture = {'hand_x': 0.5, 'hand_y': 0.5, 'hand_state': 'none', 'detected': False, 'pinch': False}
        self.camera_frame = None
        self.camera_width = 200
        self.camera_height = 150
        # For pause gesture detection
        self.last_pinch_state = False
        
    def run(self):
        try:
            while self.running:
                self.handle_events()
                self.update()
                self.draw()
                self.ui_manager.clock.tick(self.FPS)
            
            self.cleanup()
        except Exception as e:
            print(f"❌ Error: {e}")
            self.cleanup()
            input("Press Enter to exit...")
    
    def update_gesture(self):
        """Update gesture detection - shared between UI and game"""
        ret, frame = self.camera.read()
        if ret:
            frame = cv2.flip(frame, 1)

            # Gesture detection
            gesture, processed_frame = self.gesture_detector.detect_gesture(frame)
            self.current_gesture = gesture

            # Emotion detection only every N frames
            self.emotion_counter += 1
            if self.emotion_counter >= self.emotion_interval:
                emotion_result = self.emotion_detector.detect_emotion(frame)
                if emotion_result:
                    self.current_emotion, score = emotion_result
                else:
                    self.current_emotion = None
                self.emotion_counter = 0

            # Resize frame for display
            self.camera_frame = cv2.resize(processed_frame, (self.camera_width, self.camera_height))
        else:
            self.current_gesture = {'hand_x': 0.5, 'hand_y': 0.5, 'hand_state': 'none', 'detected': False, 'pinch': False}



    
    def check_pause_gesture(self):
        """Check for pinch gesture to pause the game"""
        if self.current_gesture.get('pinch', False) and not self.last_pinch_state:
            self.last_pinch_state = True
            return True
        elif not self.current_gesture.get('pinch', False):
            self.last_pinch_state = False
        return False
    
    def draw_camera_feed(self, screen):
        """Draw camera feed for all screens"""
        if hasattr(self, 'camera_frame') and self.camera_frame is not None:
            
            # Copy the frame
            frame = self.camera_frame.copy()

            # Draw emotion label
            if self.current_emotion:
                cv2.putText(
                    frame,
                    f"Emotion: {self.current_emotion}",
                    (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
            
            if self.ui_manager.current_state == "GAME":
                screen.blit(frame_surface, (screen.get_width() - self.camera_width - 10, 
                                            screen.get_height() - self.camera_height - 10))
            else:
                screen.blit(frame_surface, (screen.get_width() - self.camera_width - 10, 10))


    
    def handle_events(self):
        # Handle UI navigation continuously (not just on events)
        if self.ui_manager.current_state in ["HOME", "INSTRUCTIONS", "DIFFICULTY", "PAUSE", "GAME_OVER"]:    
            action = self.ui_manager.handle_menu_input(None, self.current_gesture)
            if action:
                self.handle_menu_action(action)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            
            # Handle keyboard input for UI navigation
            if self.ui_manager.current_state in ["HOME", "INSTRUCTIONS", "DIFFICULTY", "PAUSE", "GAME_OVER"]:    
                keyboard_action = self.ui_manager.handle_keyboard_input(event)
                if keyboard_action:
                    self.handle_menu_action(keyboard_action)
            
            # Handle in-game events
            elif self.ui_manager.current_state == "GAME":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.ui_manager.set_state("PAUSE")
                    elif event.key == pygame.K_r:
                        self.game_logic.reset_game()
    
    def handle_menu_action(self, action):
        if action == "PLAY GAME":
            self.ui_manager.set_state("DIFFICULTY")
        elif action in ["EASY", "MEDIUM", "HARD", "EXPERT"]:
            self.selected_difficulty = action
            self.start_game()
        elif action == "PLAY AGAIN":
            self.start_game()
        elif action == "HOW TO PLAY":
            self.ui_manager.set_state("INSTRUCTIONS")
        elif action == "HOME":
            self.ui_manager.set_state("HOME")
            if self.game_logic:
                self.game_logic.cleanup()
                self.game_logic = None
        elif action == "RESUME":
            self.ui_manager.set_state("GAME")
        elif action == "RESTART":
            self.start_game()
        elif action == "QUIT":
            self.running = False
    
    def start_game(self):
        if self.game_logic:
            self.game_logic.cleanup()
        # Pass the shared camera and selected difficulty to game logic
        self.game_logic = GameLogic(self.gesture_detector, shared_camera=self.camera, difficulty=self.selected_difficulty)
        self.ui_manager.set_state("GAME")
    
    def update(self):
        # Always update gesture detection with shared camera
        self.update_gesture()
        
        # Update UI animations
        self.ui_manager.update()
        
        # Update game logic if in game
        if self.ui_manager.current_state == "GAME" and self.game_logic:
            # Check for pause gesture during gameplay
            if self.check_pause_gesture():
                self.ui_manager.set_state("PAUSE")
            else:
                # Pass the current gesture to game logic instead of letting it capture separately
                self.game_logic.current_gesture = self.current_gesture
                self.game_logic.camera_frame = self.camera_frame
                
                game_state = self.game_logic.update()
                
                if game_state == "GAME_OVER":
                    # Check if truly game over (no balls and can't launch more)
                    if len(self.game_logic.balls) == 0:
                        self.ui_manager.set_state("GAME_OVER")
    
    def draw(self):
        if self.ui_manager.current_state == "HOME":
            self.ui_manager.draw_home_screen()
            self.draw_camera_feed(self.ui_manager.screen)
        elif self.ui_manager.current_state == "INSTRUCTIONS":
            self.ui_manager.draw_instructions_screen()
            self.draw_camera_feed(self.ui_manager.screen)
        elif self.ui_manager.current_state == "DIFFICULTY":
            self.ui_manager.draw_difficulty_screen()
            self.draw_camera_feed(self.ui_manager.screen)

        elif self.ui_manager.current_state == "GAME":
            if self.game_logic:
                font, small_font = self.ui_manager.get_fonts()
                self.game_logic.draw(self.ui_manager.screen, font, small_font)
                
                # Draw level information
                level_name = getattr(self.game_logic, 'current_level_name', 'Unknown Level')
                self.ui_manager.draw_level_info(level_name, self.selected_difficulty)
                
                # Draw camera feed on top of game
                self.draw_camera_feed(self.ui_manager.screen)

        elif self.ui_manager.current_state == "PAUSE":
            if self.game_logic:
                font, small_font = self.ui_manager.get_fonts()
                self.game_logic.draw(self.ui_manager.screen, font, small_font)
            self.ui_manager.draw_pause_screen()
            self.draw_camera_feed(self.ui_manager.screen)
        elif self.ui_manager.current_state == "GAME_OVER":
            score = self.game_logic.score if self.game_logic else 0
            level = self.game_logic.level if self.game_logic else 1
            self.ui_manager.draw_game_over_screen(score, level)
            self.draw_camera_feed(self.ui_manager.screen)
        
        pygame.display.flip()
    
    def cleanup(self):
        if self.game_logic:
            self.game_logic.cleanup()
        if hasattr(self, 'camera'):
            self.camera.release()
        cv2.destroyAllWindows()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = MainGame()
    game.run()