"""
FLOWSTATE (RIGHTWARD) - A minimalist auto-scrolling platformer
Theme: FLOW - You can only move right. Stay in the flow.
"""

import pygame
import math
import os
import random
import sys
from typing import List, Tuple, Optional

# Initialize Pygame
pygame.init()
music_path = os.path.join(sys._MEIPASS, "Assets", "SFX", "Music", "MainOST.mp3") if hasattr(sys, '_MEIPASS') else "Assets/SFX/Music/MainOST.mp3"
pygame.mixer.music.load(music_path)
pygame.mixer.music.play(-1)

# Constants
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 60

# Color Palette (Blue-only, value-based contrast)
BG_COLOR = (5, 11, 26)          # #050B1A - Background
PLAYER_COLOR = (47, 164, 255)    # #2FA4FF - Player (Slime)
PLATFORM_COLOR = (14, 77, 164)   # #0E4DA4 - Platforms/Terrain
FLOW_COLOR = (27, 110, 220)      # #1B6EDC - Flow Conveyors
GOAL_COLOR = (124, 203, 255)     # #7CCBFF - Goal/Exit
TRAIL_COLOR = (47, 164, 255)     # #2FA4FF - Trail (with alpha)

# Physics - More like Super Mario Bros Wii - ADJUSTED FOR EASIER JUMPS
GRAVITY = 1100  # Reduced for easier jumps
SCROLL_SPEED = 140  # Faster base scroll
JUMP_VELOCITY = -650  # Much higher jumps!
JUMP_HOLD_BOOST = -200  # Stronger variable height control
MAX_FALL_SPEED = 600  # Controlled falling
SLIME_WIDTH = 40
SLIME_HEIGHT = 40
TRAIL_LENGTH = 15

# Power-up durations
POWERUP_DURATION = 8.0  # Seconds
INVINCIBILITY_DURATION = 10.0

# Animation
ANIMATION_SPEED = 0.15  # Time per frame in seconds


class Vec2:
    """Simple 2D vector class for wind forces"""
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    
    def normalized(self):
        length = math.sqrt(self.x ** 2 + self.y ** 2)
        if length == 0:
            return Vec2(0, 0)
        return Vec2(self.x / length, self.y / length)


class AssetManager:
    """Manages loading and caching of game assets"""
    def __init__(self):
        self.slime_idle_frames = []
        self.slime_right_frames = []
        self.enemy_idle_frames = []
        self.enemy_right_frames = []
        self.floor_tile = None
        self.sky_tile = None
        self.tiles = []
        
        self.load_assets()
    
    def load_assets(self):
        """Load all game assets"""
        base_path = os.path.join(sys._MEIPASS, "Assets") if hasattr(sys, '_MEIPASS') else "Assets"
        
        # Load Slime Idle Animation (Idle_01.png to Idle_04.png)
        idle_path = os.path.join(base_path, "Characters", "Slime", "Idle")
        for i in range(1, 5):
            frame_path = os.path.join(idle_path, f"Idle_{i:02d}.png")
            if os.path.exists(frame_path):
                img = pygame.image.load(frame_path).convert_alpha()
                img = pygame.transform.scale(img, (SLIME_WIDTH, SLIME_HEIGHT))
                self.slime_idle_frames.append(img)
            else:
                print(f"Warning: {frame_path} not found, using fallback")
        
        # Load Slime Right Animation (Right_01.png to Right_04.png)
        right_path = os.path.join(base_path, "Characters", "Slime", "Right")
        for i in range(1, 5):
            frame_path = os.path.join(right_path, f"Right_{i:02d}.png")
            if os.path.exists(frame_path):
                img = pygame.image.load(frame_path).convert_alpha()
                img = pygame.transform.scale(img, (SLIME_WIDTH, SLIME_HEIGHT))
                self.slime_right_frames.append(img)
            else:
                print(f"Warning: {frame_path} not found, using fallback")
        
        # Load Enemy Idle Animation
        enemy_idle_path = os.path.join(base_path, "Characters", "Enemy", "Idle")
        for i in range(1, 5):
            frame_path = os.path.join(enemy_idle_path, f"Idle_{i:02d}.png")
            if os.path.exists(frame_path):
                img = pygame.image.load(frame_path).convert_alpha()
                img = pygame.transform.scale(img, (35, 35))
                self.enemy_idle_frames.append(img)
            else:
                print(f"Warning: {frame_path} not found, using fallback")
        
        # Load Enemy Right Animation
        enemy_right_path = os.path.join(base_path, "Characters", "Enemy", "Right")
        for i in range(1, 5):
            frame_path = os.path.join(enemy_right_path, f"Right_{i:02d}.png")
            if os.path.exists(frame_path):
                img = pygame.image.load(frame_path).convert_alpha()
                img = pygame.transform.scale(img, (35, 35))
                self.enemy_right_frames.append(img)
            else:
                print(f"Warning: {frame_path} not found, using fallback")
        
        # Load Floor Tile
        floor_path = os.path.join(base_path, "Tilesets", "Ground", "Floor.png")
        if os.path.exists(floor_path):
            self.floor_tile = pygame.image.load(floor_path).convert()
        else:
            print(f"Warning: {floor_path} not found, using fallback")
        
        # Load Sky Tile
        sky_path = os.path.join(base_path, "Tilesets", "Sky", "Sky.png")
        if os.path.exists(sky_path):
            self.sky_tile = pygame.image.load(sky_path).convert()
        else:
            print(f"Warning: {sky_path} not found, using fallback")
        
        # Load Tiles (Tile_01.png to Tile_05.png)
        tiles_path = os.path.join(base_path, "Tilesets", "Tiles")
        for i in range(1, 6):
            tile_path = os.path.join(tiles_path, f"Tile_{i:02d}.png")
            if os.path.exists(tile_path):
                img = pygame.image.load(tile_path).convert()
                self.tiles.append(img)
            else:
                print(f"Warning: {tile_path} not found, using fallback")
        
        # Create fallback graphics if assets missing
        self._create_fallbacks()
    
    def _create_fallbacks(self):
        """Create simple fallback graphics if assets are missing"""
        # Fallback slime frames (simple circles with squash/stretch)
        if not self.slime_idle_frames:
            for i in range(4):
                surf = pygame.Surface((SLIME_WIDTH, SLIME_HEIGHT), pygame.SRCALPHA)
                pulse = 1 + 0.1 * math.sin(i * math.pi / 2)
                pygame.draw.ellipse(surf, PLAYER_COLOR, 
                                  (5, 5 + (1 - pulse) * 10, 
                                   SLIME_WIDTH - 10, 
                                   (SLIME_HEIGHT - 10) * pulse))
                self.slime_idle_frames.append(surf)
        
        if not self.slime_right_frames:
            for i in range(4):
                surf = pygame.Surface((SLIME_WIDTH, SLIME_HEIGHT), pygame.SRCALPHA)
                offset = 3 * math.sin(i * math.pi / 2)
                pygame.draw.ellipse(surf, PLAYER_COLOR,
                                  (5 + offset, 8, SLIME_WIDTH - 10, SLIME_HEIGHT - 16))
                self.slime_right_frames.append(surf)
        
        # Fallback enemy frames (red tinted)
        if not self.enemy_idle_frames:
            for i in range(4):
                surf = pygame.Surface((35, 35), pygame.SRCALPHA)
                pulse = 1 + 0.1 * math.sin(i * math.pi / 2)
                pygame.draw.ellipse(surf, (200, 80, 100),
                                  (3, 3 + (1 - pulse) * 8, 29, (29) * pulse))
                self.enemy_idle_frames.append(surf)
        
        if not self.enemy_right_frames:
            for i in range(4):
                surf = pygame.Surface((35, 35), pygame.SRCALPHA)
                offset = 2 * math.sin(i * math.pi / 2)
                pygame.draw.ellipse(surf, (200, 80, 100),
                                  (3 + offset, 6, 29, 23))
                self.enemy_right_frames.append(surf)
        
        # Fallback tiles
        if not self.floor_tile:
            self.floor_tile = pygame.Surface((64, 64))
            self.floor_tile.fill(PLATFORM_COLOR)
        
        if not self.sky_tile:
            self.sky_tile = pygame.Surface((64, 64))
            self.sky_tile.fill(BG_COLOR)
        
        if not self.tiles:
            for i in range(5):
                tile = pygame.Surface((64, 64))
                # Create different shades for variety
                shade = PLATFORM_COLOR
                tile.fill(shade)
                self.tiles.append(tile)


class Slime:
    """The player character - a slime that can only move right"""
    def __init__(self, x: float, y: float, asset_manager: AssetManager):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.width = SLIME_WIDTH
        self.height = SLIME_HEIGHT
        self.on_ground = False
        self.alive = True
        self.jump_held = False
        
        # Animation
        self.asset_manager = asset_manager
        self.animation_timer = 0
        self.current_frame = 0
        self.is_moving = False
        
        # Trail
        self.trail_positions = []
        
        # Squash and stretch
        self.squash_factor = 1.0
        self.stretch_factor = 1.0
        
        # Power-ups (Mario-style!)
        self.active_powerups = {}  # {type: remaining_time}
        self.jumps_remaining = 1  # For double jump
        
        # Attack mechanic
        self.attacking = False
        self.attack_timer = 0
        self.attack_cooldown = 0.5  # Half second between attacks
        self.attack_range = 50  # Attack reach
        
        # Attack system
        self.can_attack = True
        self.attack_cooldown = 0
        self.attack_range = 50
        self.attack_active = False
        self.attack_timer = 0
    
    def update(self, dt: float, keys, scroll_speed: float, platforms: List, wind_zones: List = None):
        if not self.alive:
            return
        
        # Update power-up timers
        expired_powerups = []
        for powerup_type, time_remaining in self.active_powerups.items():
            self.active_powerups[powerup_type] -= dt
            if self.active_powerups[powerup_type] <= 0:
                expired_powerups.append(powerup_type)
        
        for powerup_type in expired_powerups:
            del self.active_powerups[powerup_type]
        
        # Update attack timer
        if self.attack_timer > 0:
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.attacking = False
        
        # Attack input (Q key)
        if keys[pygame.K_q] and self.attack_timer <= 0:
            self.attacking = True
            self.attack_timer = self.attack_cooldown
        
        # Apply gravity (reduced if flow boost active)
        gravity_mult = 0.7 if "flow_boost" in self.active_powerups else 1.0
        self.vy += GRAVITY * dt * gravity_mult
        if self.vy > MAX_FALL_SPEED:
            self.vy = MAX_FALL_SPEED
        
        # Start with base rightward motion
        base_speed = scroll_speed
        if "flow_boost" in self.active_powerups:
            base_speed *= 1.5  # 50% speed boost!
        
        self.vx = base_speed
        
        # Apply wind forces (BEFORE updating position)
        if wind_zones:
            for wind in wind_zones:
                if wind.apply_force(self.x + self.width / 2, self.y + self.height / 2):
                    # Apply wind force directly to velocity
                    self.vx += wind.wind_force.x * dt
                    self.vy += wind.wind_force.y * dt
        
        # Jump logic with double jump support
        if keys[pygame.K_SPACE]:
            if self.on_ground and not self.jump_held:
                self.vy = JUMP_VELOCITY
                self.jump_held = True
                self.jumps_remaining = 2 if "double_jump" in self.active_powerups else 1
            elif not self.on_ground and not self.jump_held and self.jumps_remaining > 0:
                # Double jump!
                if "double_jump" in self.active_powerups:
                    self.vy = JUMP_VELOCITY * 0.85  # Slightly weaker second jump
                    self.jump_held = True
                    self.jumps_remaining -= 1
            elif self.vy < 0 and self.jump_held:  # Hold for higher jump
                self.vy += JUMP_HOLD_BOOST * dt
        else:
            self.jump_held = False
        
        # Update position AFTER all forces are applied
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Check if moving
        self.is_moving = abs(self.vx) > 10
        
        # Update animation
        self.animation_timer += dt
        if self.animation_timer >= ANIMATION_SPEED:
            self.animation_timer = 0
            frames = self.asset_manager.slime_right_frames if self.is_moving else self.asset_manager.slime_idle_frames
            self.current_frame = (self.current_frame + 1) % len(frames)
        
        # Squash and stretch based on velocity
        if self.vy > 100:  # Falling - stretch vertically
            self.stretch_factor = 1.2
            self.squash_factor = 0.9
        elif self.vy < -100:  # Jumping - squash vertically
            self.stretch_factor = 0.85
            self.squash_factor = 1.15
        else:
            self.stretch_factor = 1.0
            self.squash_factor = 1.0
        
        # Collision detection with platforms
        self.on_ground = False
        slime_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        for platform in platforms:
            if platform.rect.colliderect(slime_rect):
                # Only collide from top if falling
                if self.vy > 0 and self.y + self.height - 10 < platform.rect.top + 10:
                    self.y = platform.rect.top - self.height
                    self.vy = 0
                    self.on_ground = True
                    # Reset jump abilities
                    self.jumps_remaining = 2 if "double_jump" in self.active_powerups else 1
                    
                    # Apply platform effects
                    if platform.platform_type == "speed":
                        self.vx *= 1.5
                    elif platform.platform_type == "soft":
                        self.vy *= 0.5
        
        # Update trail
        self.trail_positions.append((self.x + self.width / 2, self.y + self.height / 2))
        if len(self.trail_positions) > TRAIL_LENGTH:
            self.trail_positions.pop(0)
        
        # Death if fall off screen
        if self.y > SCREEN_HEIGHT + 100:
            self.alive = False
    
    def collect_powerup(self, powerup_type: str):
        """Collect a power-up"""
        if powerup_type == "invincible":
            self.active_powerups[powerup_type] = INVINCIBILITY_DURATION
        else:
            self.active_powerups[powerup_type] = POWERUP_DURATION
    
    def is_invincible(self) -> bool:
        """Check if player is invincible"""
        return "invincible" in self.active_powerups
    
    def get_attack_rect(self):
        """Get attack hitbox when attacking"""
        if self.attacking:
            return pygame.Rect(self.x + self.width, self.y, self.attack_range, self.height)
        return None
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def draw(self, screen, camera_offset: float):
        # Draw trail with simple circles (more efficient)
        for i, (tx, ty) in enumerate(self.trail_positions):
            alpha_factor = i / len(self.trail_positions)
            # Use smaller, simpler circles
            if i % 2 == 0:  # Draw every other trail point to reduce draw calls
                radius = int(3 + alpha_factor * 2)
                color_intensity = int(128 + alpha_factor * 127)
                
                # Change trail color based on power-ups
                if "invincible" in self.active_powerups:
                    trail_base = (255, 220, 100)  # Gold
                elif "flow_boost" in self.active_powerups:
                    trail_base = (100, 255, 200)  # Cyan
                else:
                    trail_base = TRAIL_COLOR
                
                trail_color = (
                    int(trail_base[0] * color_intensity / 255),
                    int(trail_base[1] * color_intensity / 255),
                    int(trail_base[2] * color_intensity / 255)
                )
                pygame.draw.circle(screen, trail_color, 
                                 (int(tx - camera_offset), int(ty)), radius)
        
        # Draw slime with current animation frame
        frames = self.asset_manager.slime_right_frames if self.is_moving else self.asset_manager.slime_idle_frames
        current_image = frames[self.current_frame]
        
        # Apply squash and stretch
        squeezed_width = int(self.width * self.squash_factor)
        squeezed_height = int(self.height * self.stretch_factor)
        squeezed_image = pygame.transform.scale(current_image, (squeezed_width, squeezed_height))
        
        # Add power-up visual effects
        if "invincible" in self.active_powerups:
            # Golden glow
            glow_surf = pygame.Surface((squeezed_width + 20, squeezed_height + 20), pygame.SRCALPHA)
            pygame.draw.ellipse(glow_surf, (255, 220, 100, 100), glow_surf.get_rect())
            screen.blit(glow_surf, (int(self.x - camera_offset - 10), int(self.y - 10)))
            # Sparkles
            import time
            for i in range(4):
                angle = (time.time() * 200 + i * 90) % 360
                rad = math.radians(angle)
                spark_x = self.x - camera_offset + self.width/2 + math.cos(rad) * 30
                spark_y = self.y + self.height/2 + math.sin(rad) * 30
                pygame.draw.circle(screen, (255, 255, 150), (int(spark_x), int(spark_y)), 3)
        
        if "flow_boost" in self.active_powerups:
            # Speed lines
            for i in range(3):
                line_x = self.x - camera_offset - 20 - i * 10
                line_y = self.y + self.height/2 + (i - 1) * 10
                pygame.draw.line(screen, (100, 255, 200, 150), 
                               (line_x, line_y), (line_x + 15, line_y), 2)
        
        # Draw attack effect if attacking
        if self.attacking:
            attack_rect = self.get_attack_rect()
            if attack_rect:
                # Draw slash effect
                draw_x = attack_rect.x - camera_offset
                pygame.draw.arc(screen, PLAYER_COLOR,
                              (draw_x - 10, attack_rect.y - 10, 
                               attack_rect.width + 20, attack_rect.height + 20),
                              -0.5, 0.5, 5)
                # Sparkle effect
                for i in range(3):
                    offset = i * 15
                    pygame.draw.circle(screen, GOAL_COLOR,
                                     (int(draw_x + offset), int(attack_rect.y + attack_rect.height/2)),
                                     4)
        
        # Center the squeezed image
        draw_x = int(self.x - camera_offset + (self.width - squeezed_width) / 2)
        draw_y = int(self.y + (self.height - squeezed_height))
        
        screen.blit(squeezed_image, (draw_x, draw_y))


class Platform:
    """A platform that the slime can stand on"""
    def __init__(self, x: float, y: float, width: float, height: float, 
                 platform_type: str = "normal", asset_manager: Optional[AssetManager] = None):
        self.rect = pygame.Rect(x, y, width, height)
        self.platform_type = platform_type  # normal, speed, soft, slope
        self.asset_manager = asset_manager
        self._cached_surface = None
        self._cache_platform_surface()
    
    def _cache_platform_surface(self):
        """Pre-render the platform surface for better performance"""
        if self.asset_manager and self.asset_manager.tiles:
            tile = self.asset_manager.tiles[0]
            tile_width = tile.get_width()
            tile_height = tile.get_height()
            
            # Create a surface for this platform
            surf = pygame.Surface((self.rect.width, self.rect.height))
            
            # Choose base color
            if self.platform_type == "speed":
                base_color = FLOW_COLOR
            elif self.platform_type == "soft":
                base_color = GOAL_COLOR
            else:
                base_color = PLATFORM_COLOR
            
            surf.fill(base_color)
            
            # Tile the platform on the cached surface
            for tile_x in range(0, self.rect.width, tile_width):
                for tile_y in range(0, self.rect.height, tile_height):
                    surf.blit(tile, (tile_x, tile_y))
            
            self._cached_surface = surf
        else:
            # Fallback: just use colored rect
            surf = pygame.Surface((self.rect.width, self.rect.height))
            if self.platform_type == "speed":
                surf.fill(FLOW_COLOR)
            elif self.platform_type == "soft":
                surf.fill(GOAL_COLOR)
            else:
                surf.fill(PLATFORM_COLOR)
            self._cached_surface = surf
    
    def draw(self, screen, camera_offset: float):
        draw_x = self.rect.x - camera_offset
        
        # Cull off-screen platforms
        if draw_x + self.rect.width < -100 or draw_x > SCREEN_WIDTH + 100:
            return
        
        # Blit the cached surface
        screen.blit(self._cached_surface, (draw_x, self.rect.y))
        
        # Draw flow lines for speed platforms (simple overlay)
        if self.platform_type == "speed":
            for i in range(3):
                line_x = draw_x + i * 30
                if 0 <= line_x <= SCREEN_WIDTH:
                    pygame.draw.line(screen, PLAYER_COLOR,
                                   (line_x, self.rect.y + 5),
                                   (line_x + 20, self.rect.y + 5), 2)


class Hazard:
    """Deadly obstacles"""
    def __init__(self, x: float, y: float, width: float, height: float):
        self.rect = pygame.Rect(x, y, width, height)
    
    def draw(self, screen, camera_offset: float):
        draw_x = self.rect.x - camera_offset
        
        # Cull off-screen hazards
        if draw_x + self.rect.width < -100 or draw_x > SCREEN_WIDTH + 100:
            return
        
        # Draw spikes as triangles
        num_spikes = max(1, int(self.rect.width / 20))
        spike_width = self.rect.width / num_spikes
        
        for i in range(num_spikes):
            spike_x = draw_x + i * spike_width
            points = [
                (spike_x, self.rect.y + self.rect.height),
                (spike_x + spike_width / 2, self.rect.y),
                (spike_x + spike_width, self.rect.y + self.rect.height)
            ]
            pygame.draw.polygon(screen, PLAYER_COLOR, points)


class WindZone:
    """Wind zones that apply gentle force and show flow particles"""
    def __init__(self, x: float, y: float, width: float, height: float,
                 wind_x: float, wind_y: float):
        self.rect = pygame.Rect(x, y, width, height)
        self.wind_force = Vec2(wind_x, wind_y)
        self.particles = []
        self.particle_timer = 0
        self.animation_offset = 0
        
        # Create initial particles
        self._spawn_particles()
    
    def _spawn_particles(self):
        """Create wind particles"""
        num_particles = int((self.rect.width * self.rect.height) / 5000)
        for _ in range(num_particles):
            x = self.rect.x + random.uniform(0, self.rect.width)
            y = self.rect.y + random.uniform(0, self.rect.height)
            self.particles.append([x, y])
    
    def update(self, dt: float):
        """Update wind particles"""
        self.animation_offset += dt * 50
        self.particle_timer += dt
        
        # Update particle positions based on wind direction
        for particle in self.particles:
            particle[0] += self.wind_force.x * dt * 0.3
            particle[1] += self.wind_force.y * dt * 0.3
            
            # Wrap particles around the zone
            if particle[0] < self.rect.left:
                particle[0] = self.rect.right
            elif particle[0] > self.rect.right:
                particle[0] = self.rect.left
            
            if particle[1] < self.rect.top:
                particle[1] = self.rect.bottom
            elif particle[1] > self.rect.bottom:
                particle[1] = self.rect.top
        
        # Spawn new particles occasionally
        if self.particle_timer > 0.5:
            self.particle_timer = 0
            if len(self.particles) < 20:
                x = self.rect.x + random.uniform(0, self.rect.width)
                y = self.rect.y + random.uniform(0, self.rect.height)
                self.particles.append([x, y])
    
    def apply_force(self, player_x: float, player_y: float) -> bool:
        """Check if player is in wind zone and return True if so"""
        return self.rect.collidepoint(player_x, player_y)
    
    def draw(self, screen, camera_offset: float):
        draw_x = self.rect.x - camera_offset
        
        # Cull off-screen wind zones
        if draw_x + self.rect.width < -100 or draw_x > SCREEN_WIDTH + 100:
            return
        
        # Draw subtle zone background
        zone_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        zone_surf.fill((*FLOW_COLOR, 30))  # Very transparent
        screen.blit(zone_surf, (draw_x, self.rect.y))
        
        # Draw wind particles
        for px, py in self.particles:
            screen_x = px - camera_offset
            if 0 <= screen_x <= SCREEN_WIDTH:
                # Draw particle with trail
                pygame.draw.circle(screen, (*PLAYER_COLOR, 100), 
                                 (int(screen_x), int(py)), 2)
                
                # Draw directional streak
                streak_length = 8
                end_x = screen_x - self.wind_force.x * 0.05 * streak_length
                end_y = py - self.wind_force.y * 0.05 * streak_length
                pygame.draw.line(screen, (*GOAL_COLOR, 80),
                               (int(screen_x), int(py)),
                               (int(end_x), int(end_y)), 1)
        
        # Draw directional arrows
        arrow_spacing = 80
        num_arrows_x = max(1, int(self.rect.width / arrow_spacing))
        num_arrows_y = max(1, int(self.rect.height / arrow_spacing))
        
        wind_dir = self.wind_force.normalized()
        
        for i in range(num_arrows_x):
            for j in range(num_arrows_y):
                arrow_x = draw_x + (i + 0.5) * arrow_spacing
                arrow_y = self.rect.y + (j + 0.5) * (self.rect.height / num_arrows_y)
                
                if 0 <= arrow_x <= SCREEN_WIDTH:
                    # Draw arrow pointing in wind direction
                    arrow_len = 15
                    end_x = arrow_x + wind_dir.x * arrow_len
                    end_y = arrow_y + wind_dir.y * arrow_len
                    
                    # Arrow shaft
                    pygame.draw.line(screen, (*FLOW_COLOR, 150),
                                   (int(arrow_x), int(arrow_y)),
                                   (int(end_x), int(end_y)), 2)
                    
                    # Arrow head
                    angle = math.atan2(wind_dir.y, wind_dir.x)
                    head_size = 5
                    
                    head_points = [
                        (end_x, end_y),
                        (end_x - head_size * math.cos(angle - math.pi/6),
                         end_y - head_size * math.sin(angle - math.pi/6)),
                        (end_x - head_size * math.cos(angle + math.pi/6),
                         end_y - head_size * math.sin(angle + math.pi/6))
                    ]
                    pygame.draw.polygon(screen, (*FLOW_COLOR, 150), head_points)


class Goal:
    """Level exit"""
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.width = 60
        self.height = 100
        self.pulse_timer = 0
    
    def update(self, dt: float):
        self.pulse_timer += dt * 3
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def draw(self, screen, camera_offset: float):
        pulse = 1 + 0.15 * math.sin(self.pulse_timer)
        draw_x = int(self.x - camera_offset)
        draw_y = int(self.y)
        
        # Draw pulsing rectangle
        pulsed_width = int(self.width * pulse)
        pulsed_height = int(self.height * pulse)
        
        offset_x = (self.width - pulsed_width) / 2
        offset_y = (self.height - pulsed_height) / 2
        
        pygame.draw.rect(screen, GOAL_COLOR,
                        (draw_x + offset_x, draw_y + offset_y,
                         pulsed_width, pulsed_height))
        pygame.draw.rect(screen, PLAYER_COLOR,
                        (draw_x + offset_x + 10, draw_y + offset_y + 10,
                         pulsed_width - 20, pulsed_height - 20))


class EnemySlime:
    """Enemy slime that patrols platforms"""
    def __init__(self, x: float, y: float, patrol_range: float, asset_manager: AssetManager):
        self.x = x
        self.y = y
        self.start_x = x
        self.patrol_range = patrol_range
        self.width = 35
        self.height = 35
        self.vx = 80  # Patrol speed
        self.vy = 0
        self.direction = 1  # 1 = right, -1 = left
        self.on_ground = False
        self.asset_manager = asset_manager
        
        # Animation
        self.animation_timer = 0
        self.current_frame = 0
        
        # Make enemy red-tinted (hostile)
        self.color = (200, 80, 100)  # Reddish
    
    def update(self, dt: float, platforms: List):
        # Apply gravity
        self.vy += GRAVITY * dt
        if self.vy > MAX_FALL_SPEED:
            self.vy = MAX_FALL_SPEED
        
        # Patrol movement
        self.x += self.vx * self.direction * dt
        self.y += self.vy * dt
        
        # Turn around at patrol boundaries
        if self.x > self.start_x + self.patrol_range:
            self.direction = -1
            self.x = self.start_x + self.patrol_range
        elif self.x < self.start_x - self.patrol_range:
            self.direction = 1
            self.x = self.start_x - self.patrol_range
        
        # Animation
        self.animation_timer += dt
        if self.animation_timer >= ANIMATION_SPEED:
            self.animation_timer = 0
            if self.asset_manager.slime_right_frames:
                self.current_frame = (self.current_frame + 1) % len(self.asset_manager.slime_right_frames)
        
        # Platform collision
        self.on_ground = False
        enemy_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        for platform in platforms:
            if platform.rect.colliderect(enemy_rect):
                if self.vy > 0 and self.y + self.height - 10 < platform.rect.top + 10:
                    self.y = platform.rect.top - self.height
                    self.vy = 0
                    self.on_ground = True
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def draw(self, screen, camera_offset: float):
        draw_x = self.x - camera_offset
        
        # Cull off-screen enemies
        if draw_x + self.width < -100 or draw_x > SCREEN_WIDTH + 100:
            return
        
        # Draw enemy using loaded assets
        frames = self.asset_manager.enemy_right_frames if abs(self.vx) > 10 else self.asset_manager.enemy_idle_frames
        
        if frames:
            current_image = frames[self.current_frame]
            
            # Flip if moving left
            if self.direction == -1:
                current_image = pygame.transform.flip(current_image, True, False)
            
            screen.blit(current_image, (int(draw_x), int(self.y)))
        else:
            # Fallback: draw red ellipse
            pygame.draw.ellipse(screen, self.color,
                              (int(draw_x), int(self.y), self.width, self.height))


class PowerUpBox:
    """Question mark box that releases power-ups when hit from below (Mario-style!)"""
    def __init__(self, x: float, y: float, powerup_type: str):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 40
        self.powerup_type = powerup_type
        self.hit = False
        self.bounce_timer = 0
        self.bounce_offset = 0
        self.released_powerup = None
        
    def check_hit(self, player_rect: pygame.Rect, player_vy: float, player_attack_rect: Optional[pygame.Rect]) -> Optional['PowerUp']:
        """Check if player hit box from below OR attacked it"""
        if self.hit:
            return None
        
        box_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        # Check attack (Q key)
        if player_attack_rect and player_attack_rect.colliderect(box_rect):
            self.hit = True
            self.bounce_timer = 0.2
            self.released_powerup = PowerUp(self.x + 5, self.y - 35, self.powerup_type)
            return self.released_powerup
        
        # Check if player hit from below (moving upward and hits bottom of box)
        if player_vy < 0 and player_rect.colliderect(box_rect):
            if player_rect.top < box_rect.bottom and player_rect.top > box_rect.top:
                self.hit = True
                self.bounce_timer = 0.2
                # Create power-up above the box
                self.released_powerup = PowerUp(self.x + 5, self.y - 35, self.powerup_type)
                return self.released_powerup
        
        return None
    
    def update(self, dt: float):
        if self.bounce_timer > 0:
            self.bounce_timer -= dt
            self.bounce_offset = math.sin(self.bounce_timer * 20) * 5
        else:
            self.bounce_offset = 0
    
    def draw(self, screen, camera_offset: float):
        draw_x = self.x - camera_offset
        
        # Cull off-screen
        if draw_x + self.width < -100 or draw_x > SCREEN_WIDTH + 100:
            return
        
        draw_y = self.y + self.bounce_offset
        
        # Draw box
        if self.hit:
            # Used box (gray/empty)
            pygame.draw.rect(screen, (80, 100, 120), (draw_x, draw_y, self.width, self.height))
            pygame.draw.rect(screen, (60, 80, 100), (draw_x, draw_y, self.width, self.height), 3)
        else:
            # Active box (blue with glow)
            pygame.draw.rect(screen, FLOW_COLOR, (draw_x, draw_y, self.width, self.height))
            pygame.draw.rect(screen, PLAYER_COLOR, (draw_x, draw_y, self.width, self.height), 3)
            
            # Question mark
            font = pygame.font.Font(None, 32)
            text = font.render("?", True, GOAL_COLOR)
            text_rect = text.get_rect(center=(draw_x + self.width/2, draw_y + self.height/2))
            screen.blit(text, text_rect)
            
            # Subtle glow
            glow_surf = pygame.Surface((self.width + 10, self.height + 10), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*PLAYER_COLOR, 30), glow_surf.get_rect())
            screen.blit(glow_surf, (draw_x - 5, draw_y - 5))


class PowerUp:
    """Flow-themed power-up that appears from boxes"""
    def __init__(self, x: float, y: float, powerup_type: str):
        self.x = x
        self.y = y
        self.start_y = y
        self.width = 30
        self.height = 30
        self.powerup_type = powerup_type  # "flow_boost", "double_jump", "invincible"
        self.collected = False
        self.float_timer = 0
        self.float_offset = 0
        self.appear_timer = 0.5  # Rise up animation
        
        # Flow-themed colors
        self.colors = {
            "flow_boost": (100, 200, 255),      # Light cyan - WAVE symbol
            "double_jump": (150, 100, 255),     # Purple - SPRING symbol  
            "invincible": (255, 220, 100),      # Gold - STAR symbol
        }
        self.color = self.colors.get(powerup_type, GOAL_COLOR)
    
    def update(self, dt: float):
        # Appear animation (rise up from box)
        if self.appear_timer > 0:
            self.appear_timer -= dt
            rise_progress = 1 - (self.appear_timer / 0.5)
            self.y = self.start_y - (rise_progress * 30)
        else:
            # Floating animation
            self.float_timer += dt * 3
            self.float_offset = math.sin(self.float_timer) * 5
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y + self.float_offset, self.width, self.height)
    
    def draw(self, screen, camera_offset: float):
        if self.collected:
            return
        
        draw_x = self.x - camera_offset
        
        # Cull off-screen
        if draw_x + self.width < -100 or draw_x > SCREEN_WIDTH + 100:
            return
        
        draw_y = self.y + self.float_offset
        
        # Draw outer glow
        glow_size = 40
        glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*self.color, 60), (glow_size // 2, glow_size // 2), glow_size // 2)
        screen.blit(glow_surf, (int(draw_x - 5), int(draw_y - 5)))
        
        # Draw flow-themed icon
        center_x = draw_x + 15
        center_y = draw_y + 15
        
        if self.powerup_type == "flow_boost":
            # WAVE symbol (flowing lines)
            for i in range(3):
                y_off = i * 8 - 8
                wave_y = center_y + y_off + math.sin(self.float_timer + i) * 3
                pygame.draw.line(screen, self.color,
                               (center_x - 10, wave_y),
                               (center_x + 10, wave_y), 3)
        
        elif self.powerup_type == "double_jump":
            # SPRING/BOUNCE symbol (upward coils)
            pygame.draw.circle(screen, self.color, (int(center_x), int(center_y)), 12, 3)
            # Upward arrows
            for i in range(2):
                offset = i * 8 - 4
                points = [
                    (center_x + offset, center_y - 5),
                    (center_x + offset - 4, center_y + 2),
                    (center_x + offset + 4, center_y + 2)
                ]
                pygame.draw.polygon(screen, self.color, points)
        
        elif self.powerup_type == "invincible":
            # STAR symbol (flowing star)
            pygame.draw.circle(screen, self.color, (int(center_x), int(center_y)), 13)
            # Sparkles rotating
            for angle in range(0, 360, 72):
                rad = math.radians(angle + self.float_timer * 80)
                sparkle_x = center_x + math.cos(rad) * 18
                sparkle_y = center_y + math.sin(rad) * 18
                pygame.draw.circle(screen, (255, 255, 200), (int(sparkle_x), int(sparkle_y)), 3)


class Level:
    """A single level with platforms, hazards, and goal"""
    def __init__(self, name: str, scroll_speed: float, asset_manager: AssetManager):
        self.name = name
        self.scroll_speed = scroll_speed
        self.platforms: List[Platform] = []
        self.hazards: List[Hazard] = []
        self.wind_zones: List[WindZone] = []
        self.enemies: List[EnemySlime] = []
        self.powerup_boxes: List[PowerUpBox] = []
        self.powerups: List[PowerUp] = []
        self.goal: Optional[Goal] = None
        self.asset_manager = asset_manager
        self.start_x = 100
        self.start_y = 500
    
    def add_platform(self, x: float, y: float, width: float, height: float, 
                    platform_type: str = "normal"):
        self.platforms.append(Platform(x, y, width, height, platform_type, self.asset_manager))
    
    def add_hazard(self, x: float, y: float, width: float, height: float):
        self.hazards.append(Hazard(x, y, width, height))
    
    def add_wind(self, x: float, y: float, width: float, height: float,
                wind_x: float, wind_y: float):
        self.wind_zones.append(WindZone(x, y, width, height, wind_x, wind_y))
    
    def add_enemy(self, x: float, y: float, patrol_range: float = 100):
        self.enemies.append(EnemySlime(x, y, patrol_range, self.asset_manager))
    
    def add_powerup_box(self, x: float, y: float, powerup_type: str):
        """Add a Mario-style question block"""
        self.powerup_boxes.append(PowerUpBox(x, y, powerup_type))
    
    def set_goal(self, x: float, y: float):
        self.goal = Goal(x, y)


def create_levels(asset_manager: AssetManager) -> List[Level]:
    """Create all 10 levels - Mario-style with power-up boxes, NO wind zones!"""
    levels = []
    
    # Level 1: First Current - EASY tutorial with lots of platforms
    level = Level("First Current", SCROLL_SPEED, asset_manager)
    level.add_platform(0, 600, 400, 120)
    level.add_platform(500, 600, 300, 120)
    level.add_platform(900, 600, 300, 120)
    level.add_powerup_box(1000, 550, "flow_boost")
    level.add_platform(1300, 600, 300, 120)
    level.add_platform(1700, 600, 300, 120)
    level.add_enemy(1800, 550, 120)
    level.add_platform(2100, 600, 300, 120)
    level.add_powerup_box(2200, 550, "double_jump")
    level.add_platform(2500, 600, 300, 120)
    level.add_platform(2900, 600, 300, 120)
    level.add_platform(3300, 600, 300, 120)
    level.add_platform(3700, 600, 300, 120)
    level.add_powerup_box(3800, 550, "invincible")
    level.add_platform(4100, 600, 500, 120)
    level.set_goal(4400, 500)
    levels.append(level)
    
    # Level 2: Soft Steps - More platforms, power-up boxes
    level = Level("Soft Steps", SCROLL_SPEED, asset_manager)
    level.add_platform(0, 600, 500, 120)
    level.add_platform(700, 550, 250, 40)
    level.add_powerup_box(800, 500, "flow_boost")
    level.add_platform(1100, 500, 250, 40)
    level.add_enemy(1150, 450, 100)
    level.add_platform(1500, 450, 250, 40)
    level.add_platform(1850, 500, 250, 40)
    level.add_powerup_box(1950, 450, "double_jump")
    level.add_platform(2200, 550, 300, 40)
    level.add_platform(2650, 600, 800, 120)
    level.add_enemy(2750, 550, 120)
    level.add_powerup_box(2900, 550, "invincible")
    level.set_goal(3300, 500)
    levels.append(level)
    
    # Level 3: Low Flow - Ceiling challenge
    level = Level("Low Flow", SCROLL_SPEED, asset_manager)
    level.add_platform(0, 600, 600, 120)
    level.add_platform(800, 600, 400, 120)
    level.add_powerup_box(950, 550, "flow_boost")
    level.add_platform(1400, 600, 400, 120)
    level.add_platform(2000, 600, 400, 120)
    level.add_powerup_box(2150, 550, "double_jump")
    level.add_platform(2600, 600, 600, 120)
    level.add_platform(3400, 600, 800, 120)
    level.add_platform(800, 350, 1500, 40)  # Ceiling
    level.add_enemy(1000, 550, 150)
    level.add_enemy(2100, 550, 150)
    level.add_powerup_box(3600, 550, "invincible")
    level.set_goal(4000, 500)
    levels.append(level)
    
    # Level 4: Slope Ride - Step platforms
    level = Level("Slope Ride", SCROLL_SPEED, asset_manager)
    level.add_platform(0, 600, 600, 120)
    level.add_platform(800, 550, 200, 40)
    level.add_powerup_box(900, 500, "flow_boost")
    level.add_platform(1100, 450, 200, 40)
    level.add_enemy(1120, 400, 80)
    level.add_platform(1400, 350, 200, 40)
    level.add_platform(1700, 400, 250, 40)
    level.add_platform(2050, 450, 250, 40)
    level.add_enemy(2100, 400, 100)
    level.add_powerup_box(2200, 400, "double_jump")
    level.add_platform(2400, 500, 250, 40)
    level.add_platform(2750, 550, 250, 40)
    level.add_platform(3100, 600, 800, 120)
    level.add_powerup_box(3300, 550, "invincible")
    level.set_goal(3700, 500)
    levels.append(level)
    
    # Level 5: Gap Rhythm - Timed jumps
    level = Level("Gap Rhythm", SCROLL_SPEED * 1.05, asset_manager)
    level.add_platform(0, 600, 400, 120)
    level.add_powerup_box(200, 550, "double_jump")
    for i in range(7):
        x_pos = 400 + i * 500
        level.add_platform(x_pos, 600, 250, 120)
        if i % 2 == 1 and i < 6:
            level.add_enemy(x_pos + 50, 550, 120)
        if i == 3:
            level.add_powerup_box(x_pos + 100, 550, "flow_boost")
        if i == 5:
            level.add_powerup_box(x_pos + 100, 550, "invincible")
    level.add_platform(3750, 600, 200, 120)  # Added platform to fix gap
    level.set_goal(4000, 500)
    levels.append(level)
    
    # Level 6: Speed Drift - Speed platforms
    level = Level("Speed Drift", SCROLL_SPEED * 1.15, asset_manager)
    level.add_platform(0, 600, 800, 120)
    level.add_powerup_box(400, 550, "flow_boost")
    level.add_platform(1000, 600, 400, 120)
    level.add_enemy(1100, 550, 150)
    level.add_platform(1600, 550, 300, 40, "speed")
    level.add_powerup_box(1700, 500, "double_jump")
    level.add_platform(2050, 600, 300, 40)
    level.add_platform(2500, 600, 400, 120)
    level.add_enemy(2600, 550, 120)
    level.add_platform(3100, 600, 600, 120)
    level.add_powerup_box(3300, 550, "invincible")
    level.add_platform(3850, 600, 600, 120)
    level.set_goal(4200, 500)
    levels.append(level)
    
    # Level 7: Stability Test - Soft platforms
    level = Level("Stability Test", SCROLL_SPEED, asset_manager)
    level.add_platform(0, 600, 400, 120)
    level.add_powerup_box(200, 550, "double_jump")
    for i in range(6):
        x_pos = 400 + i * 450
        level.add_platform(x_pos, 550, 250, 40, "soft")
        if i % 2 == 0 and i < 5:
            level.add_enemy(x_pos + 50, 500, 100)
        if i == 2:
            level.add_powerup_box(x_pos + 100, 500, "flow_boost")
        if i == 4:
            level.add_powerup_box(x_pos + 100, 500, "invincible")
    level.add_platform(3100, 600, 1000, 120)
    level.add_enemy(3300, 550, 200)
    level.set_goal(3900, 500)
    levels.append(level)
    
    # Level 8: Pressure Run - Hazards and enemies
    level = Level("Pressure Run", SCROLL_SPEED * 1.15, asset_manager)
    level.add_platform(0, 600, 500, 120)
    level.add_powerup_box(250, 550, "flow_boost")
    level.add_platform(700, 550, 400, 40)
    level.add_enemy(800, 500, 150)
    level.add_hazard(1000, 560, 100, 40)
    level.add_platform(1300, 500, 400, 40)
    level.add_powerup_box(1450, 450, "double_jump")
    level.add_platform(1850, 550, 350, 40)
    level.add_enemy(1900, 500, 120)
    level.add_platform(2350, 550, 400, 40)
    level.add_hazard(2650, 560, 100, 40)
    level.add_powerup_box(2700, 500, "invincible")
    level.add_platform(2950, 600, 600, 120)
    level.add_platform(3700, 600, 600, 120)
    level.add_enemy(3850, 550, 150)
    level.set_goal(4100, 500)
    levels.append(level)
    
    # Level 9: False Panic - Many hazards but safe with power-ups
    level = Level("False Panic", SCROLL_SPEED, asset_manager)
    level.add_platform(0, 600, 600, 120)
    level.add_powerup_box(300, 550, "invincible")
    level.add_platform(800, 600, 500, 120)
    level.add_platform(1500, 600, 500, 120)
    level.add_powerup_box(1700, 550, "double_jump")
    level.add_platform(2200, 600, 500, 120)
    level.add_platform(2900, 600, 500, 120)
    level.add_powerup_box(3100, 550, "flow_boost")
    level.add_platform(3600, 600, 900, 120)
    level.add_hazard(700, 560, 80, 40)
    level.add_enemy(900, 550, 120)
    level.add_hazard(1200, 560, 80, 40)
    level.add_hazard(1550, 560, 80, 40)
    level.add_enemy(1700, 550, 150)
    level.add_hazard(2100, 560, 80, 40)
    level.add_enemy(2400, 550, 130)
    level.add_powerup_box(3800, 550, "invincible")
    level.set_goal(4300, 500)
    levels.append(level)
    
    # Level 10: Pure Flow - Epic finale with everything!
    level = Level("Pure Flow", SCROLL_SPEED * 1.1, asset_manager)
    level.add_platform(0, 600, 500, 120)
    level.add_powerup_box(250, 550, "flow_boost")
    level.add_platform(700, 550, 300, 40, "speed")
    level.add_enemy(800, 500, 120)
    level.add_powerup_box(1000, 500, "double_jump")
    level.add_platform(1200, 500, 250, 40)
    level.add_platform(1550, 450, 250, 40)
    level.add_enemy(1600, 400, 100)
    level.add_platform(1900, 500, 300, 40, "soft")
    level.add_powerup_box(2000, 450, "invincible")
    level.add_platform(2300, 550, 300, 40)
    level.add_enemy(2350, 500, 120)
    level.add_platform(2750, 550, 350, 40)
    level.add_hazard(3000, 560, 120, 40)
    level.add_platform(3300, 500, 350, 40)
    level.add_enemy(3400, 450, 140)
    level.add_powerup_box(3500, 450, "flow_boost")
    level.add_platform(3800, 550, 350, 40, "speed")
    level.add_powerup_box(4000, 500, "double_jump")
    level.add_platform(4300, 600, 400, 120)
    level.add_platform(4850, 550, 350, 40)
    level.add_platform(5300, 600, 800, 120)
    level.add_platform(5400, 400, 600, 40)  # Ceiling
    level.add_enemy(5500, 550, 180)
    level.add_powerup_box(5600, 550, "invincible")
    level.set_goal(5900, 500)
    levels.append(level)
    
    return levels
class Camera:
    """Auto-scrolling camera that moves right"""
    def __init__(self):
        self.x = 0
        self.shake_amount = 0
        self.shake_timer = 0
    
    def update(self, dt: float, scroll_speed: float, player_x: float):
        # Constant rightward scroll
        self.x += scroll_speed * dt
        
        # Keep player in view (don't let them fall behind)
        if player_x < self.x + 100:
            self.x = player_x - 100
        
        # Update shake
        if self.shake_timer > 0:
            self.shake_timer -= dt
            if self.shake_timer <= 0:
                self.shake_amount = 0
    
    def shake(self, amount: float = 5, duration: float = 0.2):
        self.shake_amount = amount
        self.shake_timer = duration
    
    def get_offset(self) -> float:
        if self.shake_timer > 0:
            import random
            return self.x + random.uniform(-self.shake_amount, self.shake_amount)
        return self.x


class Game:
    """Main game class"""
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("FLOWSTATE (Rightward)")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Asset management
        self.asset_manager = AssetManager()
        
        # Game state
        self.levels = create_levels(self.asset_manager)
        self.current_level_index = 0
        self.player: Optional[Slime] = None
        self.camera = Camera()
        self.game_state = "MENU"  # MENU, PLAYING, COMPLETE
        
        # UI
        self.font = pygame.font.Font(None, 74)
        self.small_font = pygame.font.Font(None, 36)
        
        # Background
        self.bg_scroll = 0
        self._cached_background = None
        self._create_background_cache()
    
    def _create_background_cache(self):
        """Create a cached background surface for better performance"""
        if self.asset_manager.sky_tile:
            tile = self.asset_manager.sky_tile
            tile_width = tile.get_width()
            tile_height = tile.get_height()
            
            # Create a background larger than screen for scrolling
            bg_width = SCREEN_WIDTH + tile_width * 2
            bg_height = SCREEN_HEIGHT
            
            self._cached_background = pygame.Surface((bg_width, bg_height))
            
            # Tile it once
            for x in range(0, bg_width, tile_width):
                for y in range(0, bg_height, tile_height):
                    self._cached_background.blit(tile, (x, y))
        else:
            # Just use solid color
            self._cached_background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self._cached_background.fill(BG_COLOR)
    
    def load_level(self, index: int):
        """Load a specific level"""
        if index >= len(self.levels):
            self.game_state = "COMPLETE"
            return
        
        level = self.levels[index]
        self.player = Slime(level.start_x, level.start_y, self.asset_manager)
        self.camera = Camera()
        self.current_level_index = index
    
    def reset_level(self):
        """Restart current level"""
        self.load_level(self.current_level_index)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.KEYDOWN:
                if self.game_state == "MENU":
                    self.game_state = "PLAYING"
                    self.load_level(0)
                elif self.game_state == "COMPLETE":
                    self.game_state = "MENU"
                    self.current_level_index = 0
                elif self.game_state == "PLAYING":
                    if event.key == pygame.K_r:
                        self.reset_level()
    
    def update(self, dt: float):
        if self.game_state != "PLAYING":
            return
        
        level = self.levels[self.current_level_index]
        keys = pygame.key.get_pressed()
        
        # Update wind zones
        for wind in level.wind_zones:
            wind.update(dt)
        
        # Update enemies
        for enemy in level.enemies:
            enemy.update(dt, level.platforms)
        
        # Update power-ups
        for powerup in level.powerups:
            powerup.update(dt)
        
        # Update powerup boxes
        for box in level.powerup_boxes:
            box.update(dt)
        
        # Update player
        if self.player:
            self.player.update(dt, keys, level.scroll_speed, level.platforms, level.wind_zones)
            
            player_rect = self.player.get_rect()
            player_attack_rect = self.player.get_attack_rect()
            
            # Check powerup box hits (from below OR attack)
            for box in level.powerup_boxes:
                released_powerup = box.check_hit(player_rect, self.player.vy, player_attack_rect)
                if released_powerup:
                    level.powerups.append(released_powerup)
            
            # Check if player fell behind screen
            if self.player.x < self.camera.x - 100:
                self.player.alive = False
            
            # Check power-up collection
            for powerup in level.powerups:
                if not powerup.collected and powerup.get_rect().colliderect(player_rect):
                    powerup.collected = True
                    self.player.collect_powerup(powerup.powerup_type)
            
            # Check hazard collisions (unless invincible!)
            for hazard in level.hazards:
                if hazard.rect.colliderect(player_rect):
                    if not self.player.is_invincible():
                        self.player.alive = False
                        self.camera.shake()
            
            # Check enemy collisions (unless invincible!)
            for enemy in level.enemies:
                if enemy.get_rect().colliderect(player_rect):
                    if not self.player.is_invincible():
                        self.player.alive = False
                        self.camera.shake()
            
            # Check goal
            if level.goal and level.goal.get_rect().colliderect(player_rect):
                self.load_level(self.current_level_index + 1)
            
            # Death - restart
            if not self.player.alive:
                self.reset_level()
        
        # Update camera
        if self.player:
            self.camera.update(dt, level.scroll_speed, self.player.x)
        
        # Update goal animation
        if level.goal:
            level.goal.update(dt)
        
        # Update background scroll
        self.bg_scroll += level.scroll_speed * dt * 0.3
    
    def draw_background(self):
        """Draw scrolling background using cached surface"""
        if self._cached_background:
            if self.asset_manager.sky_tile:
                tile_width = self.asset_manager.sky_tile.get_width()
                offset = int(self.bg_scroll) % tile_width
                self.screen.blit(self._cached_background, (-offset, 0))
            else:
                self.screen.blit(self._cached_background, (0, 0))
        else:
            self.screen.fill(BG_COLOR)
    
    def draw(self):
        self.draw_background()
        
        if self.game_state == "MENU":
            title = self.font.render("FLOWSTATE", True, PLAYER_COLOR)
            subtitle = self.small_font.render("Rightward", True, GOAL_COLOR)
            instruction = self.small_font.render("Press any key to start", True, PLATFORM_COLOR)
            
            title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
            subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
            instruction_rect = instruction.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
            
            self.screen.blit(title, title_rect)
            self.screen.blit(subtitle, subtitle_rect)
            self.screen.blit(instruction, instruction_rect)
            
            controls = self.small_font.render("SPACE: Jump | Q: Attack Boxes | Only move RIGHT", True, FLOW_COLOR)
            controls_rect = controls.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120))
            self.screen.blit(controls, controls_rect)
        
        elif self.game_state == "COMPLETE":
            title = self.font.render("PURE FLOW", True, GOAL_COLOR)
            subtitle = self.small_font.render("You stayed in the flow", True, PLAYER_COLOR)
            restart = self.small_font.render("Press any key to restart", True, PLATFORM_COLOR)
            
            title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
            subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            restart_rect = restart.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
            
            self.screen.blit(title, title_rect)
            self.screen.blit(subtitle, subtitle_rect)
            self.screen.blit(restart, restart_rect)
        
        elif self.game_state == "PLAYING":
            level = self.levels[self.current_level_index]
            camera_offset = self.camera.get_offset()
            
            # Draw wind zones first (behind everything) - removed for Level 1
            for wind in level.wind_zones:
                wind.draw(self.screen, camera_offset)
            
            # Draw platforms
            for platform in level.platforms:
                platform.draw(self.screen, camera_offset)
            
            # Draw powerup boxes
            for box in level.powerup_boxes:
                box.draw(self.screen, camera_offset)
            
            # Draw power-ups
            for powerup in level.powerups:
                powerup.draw(self.screen, camera_offset)
            
            # Draw hazards
            for hazard in level.hazards:
                hazard.draw(self.screen, camera_offset)
            
            # Draw enemies
            for enemy in level.enemies:
                enemy.draw(self.screen, camera_offset)
            
            # Draw goal
            if level.goal:
                level.goal.draw(self.screen, camera_offset)
            
            # Draw player (on top)
            if self.player:
                self.player.draw(self.screen, camera_offset)
            
            # === GUI OVERLAY ===
            self.draw_gui(level)
        
        pygame.display.flip()
    
    def draw_gui(self, level):
        """Draw GUI elements - power-ups, level name, controls"""
        # Semi-transparent background for GUI
        gui_bg = pygame.Surface((SCREEN_WIDTH, 100), pygame.SRCALPHA)
        gui_bg.fill((5, 11, 26, 180))
        self.screen.blit(gui_bg, (0, 0))
        
        # Level name
        level_text = self.small_font.render(f"Level {self.current_level_index + 1}: {level.name}", 
                                           True, GOAL_COLOR)
        self.screen.blit(level_text, (10, 10))
        
        # Controls
        controls = self.small_font.render("SPACE: Jump | Q: Attack | R: Restart", 
                                         True, PLATFORM_COLOR)
        self.screen.blit(controls, (10, 35))
        
        # Active Power-ups
        if self.player and self.player.active_powerups:
            powerup_y = 60
            powerup_text = self.small_font.render("Active Power-ups:", True, PLAYER_COLOR)
            self.screen.blit(powerup_text, (10, powerup_y))
            
            x_offset = 180
            for powerup_type, time_remaining in self.player.active_powerups.items():
                # Power-up icon colors
                colors = {
                    "flow_boost": (100, 200, 255),
                    "double_jump": (150, 100, 255),
                    "invincible": (255, 220, 100)
                }
                color = colors.get(powerup_type, GOAL_COLOR)
                
                # Draw power-up box
                box_rect = pygame.Rect(x_offset, powerup_y, 40, 30)
                pygame.draw.rect(self.screen, color, box_rect)
                pygame.draw.rect(self.screen, PLAYER_COLOR, box_rect, 2)
                
                # Draw icon symbol
                center_x = x_offset + 20
                center_y = powerup_y + 15
                
                if powerup_type == "flow_boost":
                    # Wave lines
                    for i in range(3):
                        y = center_y - 8 + i * 6
                        pygame.draw.line(self.screen, (255, 255, 255),
                                       (center_x - 12, y), (center_x + 12, y), 2)
                elif powerup_type == "double_jump":
                    # Up arrows
                    pygame.draw.polygon(self.screen, (255, 255, 255),
                                      [(center_x - 8, center_y), 
                                       (center_x, center_y - 8),
                                       (center_x + 8, center_y)])
                    pygame.draw.polygon(self.screen, (255, 255, 255),
                                      [(center_x - 8, center_y + 8), 
                                       (center_x, center_y),
                                       (center_x + 8, center_y + 8)])
                elif powerup_type == "invincible":
                    # Star
                    pygame.draw.circle(self.screen, (255, 255, 255), 
                                     (center_x, center_y), 10)
                
                # Timer
                timer_text = self.small_font.render(f"{int(time_remaining)}s", 
                                                    True, (255, 255, 255))
                self.screen.blit(timer_text, (x_offset + 5, powerup_y + 32))
                
                x_offset += 100
        
        # Optional FPS counter (for debugging)
        # Uncomment to see frame rate
        # fps_text = self.small_font.render(f"FPS: {int(self.clock.get_fps())}", True, GOAL_COLOR)
        # self.screen.blit(fps_text, (SCREEN_WIDTH - 80, 10))
    
    def run(self):
        """Main game loop"""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            
            self.handle_events()
            self.update(dt)
            self.draw()
        
        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()