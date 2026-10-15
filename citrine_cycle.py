#!/usr/bin/env python3
"""Citrine Cycle — neon light-cycle arcade for ElbowOS. Python 3 + pygame."""
import math
import os
import random
import subprocess
import sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv

if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/workspace/artifacts/CITRINE_CYCLE_ElbowOS.mp4")
TITLE, HANDLE = "CITRINE CYCLE", "x.com/ElbowOS"

# Neon palette
BG = (8, 4, 18)
CYAN = (0, 255, 255)
MAG = (255, 0, 180)
YEL = (255, 220, 0)
GOLD = (255, 180, 40)
WHITE = (240, 240, 255)
TRAIL = (255, 140, 0)

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            self.screen = pygame.display.set_mode((W, H), pygame.HIDDEN)
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.font_lg = pygame.font.SysFont("monospace", 72, bold=True)
        self.font_md = pygame.font.SysFont("monospace", 48, bold=True)
        self.font_sm = pygame.font.SysFont("monospace", 36, bold=True)
        self.reset()

    def reset(self):
        self.x = W // 2
        self.y = H - 300
        self.angle = -math.pi / 2  # up
        self.speed = 8.0
        self.trail = [(self.x, self.y)]
        self.score = 0
        self.orbs = []
        self.frame = 0
        self.alive = True
        self.spawn_orb()

    def spawn_orb(self):
        if len(self.orbs) < 4:
            ox = random.randint(100, W - 100)
            oy = random.randint(200, H - 400)
            self.orbs.append([ox, oy, random.randint(18, 28)])

    def step_auto(self):
        # Simple AI: look ahead, turn if blocked
        if not self.alive:
            return
        look = 60
        fx = self.x + math.cos(self.angle) * look
        fy = self.y + math.sin(self.angle) * look
        blocked = (fx < 40 or fx > W - 40 or fy < 40 or fy > H - 40)
        if not blocked:
            for tx, ty in self.trail[-80:]:
                if (fx - tx) ** 2 + (fy - ty) ** 2 < 30 ** 2:
                    blocked = True
                    break
        if blocked and self.frame % 8 == 0:
            self.angle += random.choice([-math.pi / 2, math.pi / 2])

    def update(self, turn=0):
        if not self.alive:
            if self.frame % 90 == 0:
                self.reset()
            return
        if turn:
            self.angle += turn * (math.pi / 2)
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.trail.append((self.x, self.y))
        if len(self.trail) > 400:
            self.trail.pop(0)
        # bounds
        if self.x < 30 or self.x > W - 30 or self.y < 30 or self.y > H - 30:
            self.alive = False
            return
        # trail collision (skip recent)
        for tx, ty in self.trail[:-12]:
            if (self.x - tx) ** 2 + (self.y - ty) ** 2 < 18 ** 2:
                self.alive = False
                return
        # orbs
        for o in self.orbs[:]:
            if (self.x - o[0]) ** 2 + (self.y - o[1]) ** 2 < (o[2] + 12) ** 2:
                self.score += 10
                self.orbs.remove(o)
                self.speed = min(14, self.speed + 0.3)
        if self.frame % 45 == 0:
            self.spawn_orb()
        self.frame += 1

    def draw(self):
        self.screen.fill(BG)
        # grid lines
        for i in range(0, W, 90):
            pygame.draw.line(self.screen, (30, 20, 50), (i, 0), (i, H), 1)
        for i in range(0, H, 90):
            pygame.draw.line(self.screen, (30, 20, 50), (0, i), (W, i), 1)
        # trail
        if len(self.trail) > 1:
            pygame.draw.lines(self.screen, TRAIL, False, [(int(p[0]), int(p[1])) for p in self.trail], 10)
            pygame.draw.lines(self.screen, YEL, False, [(int(p[0]), int(p[1])) for p in self.trail], 4)
        # bike
        bx, by = int(self.x), int(self.y)
        pygame.draw.circle(self.screen, GOLD, (bx, by), 16)
        pygame.draw.circle(self.screen, YEL, (bx, by), 10)
        # direction arrow
        ex = bx + int(math.cos(self.angle) * 28)
        ey = by + int(math.sin(self.angle) * 28)
        pygame.draw.line(self.screen, WHITE, (bx, by), (ex, ey), 4)
        # orbs
        for ox, oy, r in self.orbs:
            pygame.draw.circle(self.screen, MAG, (int(ox), int(oy)), r)
            pygame.draw.circle(self.screen, CYAN, (int(ox), int(oy)), r // 2)
        # UI overlay
        title = self.font_lg.render(TITLE, True, YEL)
        self.screen.blit(title, (W // 2 - title.get_width() // 2, 60))
        sc = self.font_md.render(f"SCORE  {self.score}", True, CYAN)
        self.screen.blit(sc, (40, 160))
        handle = self.font_sm.render(HANDLE, True, MAG)
        self.screen.blit(handle, (W // 2 - handle.get_width() // 2, H - 80))
        if not self.alive:
            dead = self.font_md.render("CRASH!", True, MAG)
            self.screen.blit(dead, (W // 2 - dead.get_width() // 2, H // 2))

    def record(self):
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
            "-preset", "fast", "-movflags", "+faststart",
            OUT
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        total = FPS * SECS
        for i in range(total):
            self.step_auto()
            self.update()
            self.draw()
            frame = pygame.surfarray.array3d(self.screen)
            frame = frame.transpose(1, 0, 2)
            proc.stdin.write(frame.tobytes())
            if i % 60 == 0:
                print(f"frame {i}/{total}")
        proc.stdin.close()
        proc.wait()
        print("Wrote", OUT)

    def play(self):
        running = True
        while running:
            turn = 0
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                if e.type == pygame.KEYDOWN:
                    if e.key in (pygame.K_LEFT, pygame.K_a):
                        turn = -1
                    if e.key in (pygame.K_RIGHT, pygame.K_d):
                        turn = 1
                    if e.key == pygame.K_SPACE:
                        self.reset()
            self.update(turn)
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

if __name__ == "__main__":
    g = Game()
    if RECORD:
        g.record()
    else:
        g.play()
