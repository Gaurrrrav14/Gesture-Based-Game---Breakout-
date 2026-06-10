import pygame
import math
from game_objects import SCREEN_WIDTH, SCREEN_HEIGHT

class TrajectoryPredictor:
    def __init__(self, game_logic):
        self.game_logic = game_logic
        self.max_bounces = 6
        self.max_steps = 800
        self.step_size = 4  # << This was missing!

    def simulate(self, start_pos, direction):
        points = [start_pos]
        px, py = start_pos
        dx, dy = direction
        norm = math.hypot(dx, dy)
        if norm == 0:
            return points

        vx, vy = dx / norm * self.step_size, dy / norm * self.step_size
        bounces = 0
        steps = 0

        while bounces < self.max_bounces and steps < self.max_steps:
            px += vx
            py += vy
            steps += 1

            # Wall bounce
            if px <= 0 or px >= SCREEN_WIDTH:
                vx *= -1
                bounces += 1
            if py <= 0:
                vy *= -1
                bounces += 1

            # ✅ Stop if intersects with a live block
            for block in self.game_logic.blocks:
                if not block.destroyed:
                    if self.collides_with_block((px, py), block):
                        points.append((px, py))
                        return points

            # Only add if far enough from last point
            if len(points) == 0 or math.hypot(px - points[-1][0], py - points[-1][1]) > 5:
                points.append((px, py))

        return points

    def collides_with_block(self, pos, block):
        px, py = pos
        return (block.x <= px <= block.x + block.width) and (block.y <= py <= block.y + block.height)

    def draw(self, screen, points):
        if len(points) < 2:
            return
        for i in range(1, len(points)):
            alpha = 255 * (1 - i / len(points))
            color = (255, 255, int(100 * (i / len(points))))
            pygame.draw.line(screen, color, points[i - 1], points[i], 2)
