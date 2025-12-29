import pygame
import random
import time
from enum import Enum

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
DRAWING_SCALE = 8
AI_MOVE_INTERVAL = 0.25
MAZE_OFFSET = (80, 50)
MAZE_COLOR = (189, 252, 201)  # Mint color
KEY_COOLDOWN = 0.1
GAME_FONT = "Consolas"

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)
YELLOW = (255, 255, 0)
BEIGE = (245, 245, 220)
MINT = (189, 252, 201)

class CellPath(Enum):
    NORTH = 1
    EAST = 2
    SOUTH = 4
    WEST = 8
    VISITED = 16

class GameState(Enum):
    TITLE = 0
    WARMUP = 1
    PLAYING = 2
    PAUSED = 3
    RESULT = 4

class Vec2I:
    def __init__(self, x: int, y: int) -> None:
        self.x: int = x
        self.y: int = y
    
    def __add__(self, other: "Vec2I") -> "Vec2I":
        return Vec2I(self.x + other.x, self.y + other.y)
    
    def __eq__(self, other: "Vec2I") -> bool:
        return self.x == other.x and self.y == other.y
    
    def __hash__(self) -> int:
        return hash((self.x, self.y))
    
    def __str__(self) -> str:
        return f"({self.x}, {self.y})"

class PathNode:
    def __init__(self, position: Vec2I) -> None:
        self.position: Vec2I = position
        self.parent: PathNode | None = None
        self.g_cost: int = 0
        self.h_cost: int = 0
    
    @property
    def f_cost(self) -> int:
        return self.g_cost + self.h_cost

class AmazingMaze:
    def __init__(self) -> None:
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Amazing Maze Remake")
        self.clock = pygame.time.Clock()
        self.font_tiny = pygame.font.SysFont(GAME_FONT, 12, True)
        self.font_small = pygame.font.SysFont(GAME_FONT, 24, True)
        self.font_medium = pygame.font.SysFont(GAME_FONT, 36, True)
        self.font_large = pygame.font.SysFont(GAME_FONT, 48, True)
        
        # Maze parameters
        self.maze_width = 20
        self.maze_height = 15
        self.path_width = 3
        self.maze = []
        
        # Game state
        self.game_state = GameState.TITLE
        self.visited_cells = 0
        self.stack = []
        
        # Player and AI variables
        self.player1_pos = Vec2I(0, 0)
        self.player2_pos = Vec2I(0, 0)
        self.player1_start = Vec2I(0, 0)
        self.player2_start = Vec2I(0, 0)
        self.player1_target = Vec2I(0, 0)
        self.player2_target = Vec2I(0, 0)
        self.player1_finished = False
        self.player2_finished = False
        self.game_timer = 0.0
        self.warmup_timer = 0.0
        self.ai_move_timer = 0.0
        self.ai_path = None
        self.player1_key_timer = 0.0
        self.player2_key_timer = 0.0
        self.pause_pressed = False
        
        # Game mode
        self.two_player_mode = False
        
        # Colors
        self.player1_color = CYAN
        self.player2_color = GREEN
        self.ai_color = YELLOW
        
        self.generate_maze()
        self.setup_game()
    
    def generate_maze(self) -> None:
        # Initialize maze
        self.maze = [0] * (self.maze_width * self.maze_height)
        self.visited_cells = 0
        self.stack: list[Vec2I] = []
        
        # Choose a starting cell
        x = random.randint(0, self.maze_width - 1)
        y = random.randint(0, self.maze_height - 1)
        self.stack.append(Vec2I(x, y))
        self.maze[y * self.maze_width + x] = CellPath.VISITED.value
        self.visited_cells = 1
        
        # Generate maze using depth-first search
        while self.visited_cells < self.maze_width * self.maze_height:
            def offset(xo, yo):
                new_x = self.stack[-1].x + xo
                new_y = self.stack[-1].y + yo
                if new_x < 0 or new_x >= self.maze_width or new_y < 0 or new_y >= self.maze_height:
                    return -1
                return new_y * self.maze_width + new_x
            
            # Create a set of unvisited neighbours
            neighbours = []
            
            # Check all four directions
            if self.stack[-1].y > 0 and (self.maze[offset(0, -1)] & CellPath.VISITED.value) == 0:
                neighbours.append(0)
            if self.stack[-1].x < self.maze_width - 1 and (self.maze[offset(1, 0)] & CellPath.VISITED.value) == 0:
                neighbours.append(1)
            if self.stack[-1].y < self.maze_height - 1 and (self.maze[offset(0, 1)] & CellPath.VISITED.value) == 0:
                neighbours.append(2)
            if self.stack[-1].x > 0 and (self.maze[offset(-1, 0)] & CellPath.VISITED.value) == 0:
                neighbours.append(3)
            
            if neighbours:
                # Choose random neighbor
                next_dir = random.choice(neighbours)
                
                if next_dir == 0:  # North
                    self.maze[offset(0, -1)] = self.maze[offset(0, -1)] | CellPath.VISITED.value | CellPath.SOUTH.value
                    self.maze[offset(0, 0)] = self.maze[offset(0, 0)] | CellPath.NORTH.value
                    self.stack.append(Vec2I(self.stack[-1].x, self.stack[-1].y - 1))
                elif next_dir == 1:  # East
                    self.maze[offset(1, 0)] = self.maze[offset(1, 0)] | CellPath.VISITED.value | CellPath.WEST.value
                    self.maze[offset(0, 0)] = self.maze[offset(0, 0)] | CellPath.EAST.value
                    self.stack.append(Vec2I(self.stack[-1].x + 1, self.stack[-1].y))
                elif next_dir == 2:  # South
                    self.maze[offset(0, 1)] = self.maze[offset(0, 1)] | CellPath.VISITED.value | CellPath.NORTH.value
                    self.maze[offset(0, 0)] = self.maze[offset(0, 0)] | CellPath.SOUTH.value
                    self.stack.append(Vec2I(self.stack[-1].x, self.stack[-1].y + 1))
                elif next_dir == 3:  # West
                    self.maze[offset(-1, 0)] = self.maze[offset(-1, 0)] | CellPath.VISITED.value | CellPath.EAST.value
                    self.maze[offset(0, 0)] = self.maze[offset(0, 0)] | CellPath.WEST.value
                    self.stack.append(Vec2I(self.stack[-1].x - 1, self.stack[-1].y))
                
                self.visited_cells += 1
            else:
                self.stack.pop()
    
    def setup_game(self) -> None:
        # Set up entrances and player positions
        # Randomly choose entrance positions on left and right sides
        left_entrance_y = random.randint(1, self.maze_height - 2)
        right_entrance_y = random.randint(1, self.maze_height - 2)
        
        # Create openings at entrances
        self.maze[left_entrance_y * self.maze_width] |= CellPath.WEST.value
        self.maze[right_entrance_y * self.maze_width + (self.maze_width - 1)] |= CellPath.EAST.value
        
        # Set player starting positions
        self.player1_pos = Vec2I(0, left_entrance_y)
        self.player2_pos = Vec2I(self.maze_width - 1, right_entrance_y)
        
        self.player1_start = Vec2I(0, left_entrance_y)
        self.player2_start = Vec2I(self.maze_width - 1, right_entrance_y)
        
        # Set targets (opposite sides)
        self.player1_target = Vec2I(self.maze_width - 1, right_entrance_y)
        self.player2_target = Vec2I(0, left_entrance_y)
        
        self.player1_finished = False
        self.player2_finished = False
        self.game_timer = 0.0
        self.warmup_timer = 0.0
        self.ai_move_timer = 0.0
        self.ai_path = None
    
    def can_move(self, from_pos: Vec2I, direction: Vec2I) -> bool:
        to_pos = from_pos + direction
        if to_pos.x < 0 or to_pos.x >= self.maze_width or to_pos.y < 0 or to_pos.y >= self.maze_height:
            return False
        
        cell = self.maze[from_pos.y * self.maze_width + from_pos.x]
        
        # Check if there's a path in the desired direction
        if direction.x == -1 and (cell & CellPath.WEST.value) != 0:
            return True  # Moving left
        if direction.x == 1 and (cell & CellPath.EAST.value) != 0:
            return True  # Moving right
        if direction.y == -1 and (cell & CellPath.NORTH.value) != 0:
            return True  # Moving up
        if direction.y == 1 and (cell & CellPath.SOUTH.value) != 0:
            return True  # Moving down
        return False
    
    def move_player(self, player: int, direction: Vec2I) -> None:
        current_pos = self.player1_pos if player == 1 else self.player2_pos
        
        if self.can_move(current_pos, direction):
            new_pos = current_pos + direction
            
            # Check if player reached target
            if player == 1 and new_pos == self.player1_target:
                self.player1_finished = True
            elif player == 2 and new_pos == self.player2_target:
                self.player2_finished = True
            
            if player == 1:
                self.player1_pos = new_pos
            else:
                self.player2_pos = new_pos
    
    def get_distance(self, pos_a: Vec2I, pos_b: Vec2I) -> int:
        return abs(pos_a.x - pos_b.x) + abs(pos_a.y - pos_b.y)
    
    def find_path(self, start: Vec2I, target: Vec2I) -> list[Vec2I]:
        open_set: list[PathNode] = []
        closed_set: set[Vec2I] = set()
        
        start_node = PathNode(start)
        start_node.g_cost = 0
        start_node.h_cost = self.get_distance(start, target)
        open_set.append(start_node)
        
        while open_set:
            current_node = open_set[0]
            for i in range(1, len(open_set)):
                if (open_set[i].f_cost < current_node.f_cost or 
                    (open_set[i].f_cost == current_node.f_cost and open_set[i].h_cost < current_node.h_cost)):
                    current_node = open_set[i]
            
            open_set.remove(current_node)
            closed_set.add(current_node.position)
            
            # If we reached the target
            if current_node.position == target:
                path = []
                node = current_node
                
                while node is not None and node != start_node:
                    path.append(node.position)
                    node = node.parent
                
                path.reverse()
                return path
            
            # Check all neighbors
            for direction in [Vec2I(0, -1), Vec2I(1, 0), Vec2I(0, 1), Vec2I(-1, 0)]:
                if self.can_move(current_node.position, direction):
                    neighbor_pos = current_node.position + direction
                    
                    if neighbor_pos in closed_set:
                        continue
                    
                    move_cost_to_neighbor = current_node.g_cost + self.get_distance(current_node.position, neighbor_pos)
                    neighbor_node = next((n for n in open_set if n.position == neighbor_pos), None)
                    
                    if neighbor_node is None:
                        neighbor_node = PathNode(neighbor_pos)
                        neighbor_node.g_cost = move_cost_to_neighbor
                        neighbor_node.h_cost = self.get_distance(neighbor_pos, target)
                        neighbor_node.parent = current_node
                        open_set.append(neighbor_node)
                    elif move_cost_to_neighbor < neighbor_node.g_cost:
                        neighbor_node.g_cost = move_cost_to_neighbor
                        neighbor_node.parent = current_node
        
        # No path found
        return []
    
    def move_ai(self) -> None:
        if self.ai_path is None or (len(self.ai_path) > 0 and self.player2_pos != self.ai_path[0]):
            self.ai_path = self.find_path(self.player2_pos, self.player2_target)
        
        if self.ai_path:
            try:
                next_pos = self.ai_path[0]
                direction = Vec2I(next_pos.x - self.player2_pos.x, next_pos.y - self.player2_pos.y)
                
                if self.can_move(self.player2_pos, direction):
                    self.player2_pos = next_pos
                    self.ai_path.pop(0)
                    
                    if self.player2_pos == self.player2_target:
                        self.player2_finished = True
                        self.ai_path = None
                else:
                    self.ai_path = None
            except (IndexError, ValueError):
                self.ai_path = None
        else:
            target = self.player2_target
            current_pos = self.player2_pos
            possible_moves = []
            toward_target_moves = []
            
            for move in [Vec2I(-1, 0), Vec2I(1, 0), Vec2I(0, -1), Vec2I(0, 1)]:
                if self.can_move(current_pos, move):
                    possible_moves.append(move)
            
            if not possible_moves:
                return
            
            for move in possible_moves:
                new_pos: Vec2I = current_pos + move
                dist_before = abs(current_pos.x - target.x) + abs(current_pos.y - target.y)
                dist_after = abs(new_pos.x - target.x) + abs(new_pos.y - target.y)
                
                if dist_after < dist_before:
                    toward_target_moves.append(move)
            
            if toward_target_moves:
                best_move = random.choice(toward_target_moves)
            else:
                best_move = random.choice(possible_moves)
            
            new_ai_pos = current_pos + best_move
            if new_ai_pos == target:
                self.player2_finished = True
            self.player2_pos = new_ai_pos
    
    def update_title_screen(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    self.two_player_mode = False
                    self.generate_maze()
                    self.setup_game()
                    self.game_state = GameState.WARMUP
                elif event.key == pygame.K_2:
                    self.two_player_mode = True
                    self.generate_maze()
                    self.setup_game()
                    self.game_state = GameState.WARMUP
        
        self.screen.fill(BLACK)
        
        # Draw title
        title_text = self.font_large.render("AMAZING MAZE REMAKE", True, self.player1_color)
        self.screen.blit(title_text, (100, 150))
        
        single_text = self.font_medium.render('* PRESS "1" FOR SINGLE PLAYER', True, self.ai_color)
        self.screen.blit(single_text, (50, 240))
        
        two_text = self.font_medium.render('* PRESS "2" FOR TWO PLAYERS', True, self.player2_color)
        self.screen.blit(two_text, (50, 300))
        
        p1_text = self.font_medium.render("Player 1 moves with arrow keys", True, WHITE)
        self.screen.blit(p1_text, (50, 400))
        
        p2_text = self.font_medium.render("Player 2 moves with W,A,S,D", True, WHITE)
        self.screen.blit(p2_text, (50, 450))
        
        pygame.display.flip()
        return True
    
    def update_game(self, dt: float) -> bool:
        self.pause_pressed = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                # Handle pause based on event
                if event.key == pygame.K_p:
                    self.pause_pressed = True
                elif event.key == pygame.K_ESCAPE:
                    return False
        
        if self.pause_pressed:
            self.game_state = GameState.PAUSED
        
        # Check if still in warm-up phase
        if self.game_state == GameState.WARMUP:
            self.warmup_timer += dt
            if self.warmup_timer >= 3.0:
                self.game_state = GameState.PLAYING
        else:
            self.game_timer += dt
            # Only allow movement if not in warm-up
            self.player1_key_timer += dt
            self.player2_key_timer += dt
            
            # Player 1's movement with cooldown
            if self.player1_key_timer > KEY_COOLDOWN:
                keys = pygame.key.get_pressed()
                moved = False
                if keys[pygame.K_LEFT]:
                    self.move_player(1, Vec2I(-1, 0))
                    moved = True
                if keys[pygame.K_RIGHT]:
                    self.move_player(1, Vec2I(1, 0))
                    moved = True
                if keys[pygame.K_UP]:
                    self.move_player(1, Vec2I(0, -1))
                    moved = True
                if keys[pygame.K_DOWN]:
                    self.move_player(1, Vec2I(0, 1))
                    moved = True
                
                if moved:
                    self.player1_key_timer = 0.0  # Reset cooldown timer
            
            if self.two_player_mode:
                # Player 2's movement with cooldown
                if self.player2_key_timer > KEY_COOLDOWN:
                    keys = pygame.key.get_pressed()
                    moved = False
                    if keys[pygame.K_a]:
                        self.move_player(2, Vec2I(-1, 0))
                        moved = True
                    if keys[pygame.K_d]:
                        self.move_player(2, Vec2I(1, 0))
                        moved = True
                    if keys[pygame.K_w]:
                        self.move_player(2, Vec2I(0, -1))
                        moved = True
                    if keys[pygame.K_s]:
                        self.move_player(2, Vec2I(0, 1))
                        moved = True
                    
                    if moved:
                        self.player2_key_timer = 0.0  # Reset cooldown timer
            else:
                # AI movement
                self.ai_move_timer += dt
                if self.ai_move_timer > AI_MOVE_INTERVAL:
                    self.move_ai()
                    self.ai_move_timer = 0.0
        
        # Check game over
        if self.player1_finished or self.player2_finished:
            self.game_state = GameState.RESULT
        
        self.draw_game()
        return True
    
    def update_paused_screen(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    self.game_state = GameState.PLAYING
        
        # Draw pause overlay
        pygame.draw.rect(self.screen, BLACK, (245, 250, 350, 125))
        pause_text = self.font_medium.render("GAME PAUSED", True, BEIGE)
        self.screen.blit(pause_text, (290, 280))
        
        continue_text = self.font_small.render('PRESS "P" TO CONTINUE', True, WHITE)
        self.screen.blit(continue_text, (250, 340))
        
        pygame.display.flip()
        return True
    
    def update_result_screen(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.game_state = GameState.TITLE
        
        # Determine result
        if self.player1_finished and self.player2_finished:
            result_text = "IT'S A DRAW!"
            color = BEIGE
        elif self.player1_finished:
            result_text = "PLAYER 1 WINS!"
            color = self.player1_color
        else:
            result_text = "PLAYER 2 WINS!" if self.two_player_mode else "COMPUTER WINS!"
            color = self.player2_color if self.two_player_mode else self.ai_color
        
        # Draw result overlay
        pygame.draw.rect(self.screen, BLACK, (240, 250, 400, 150))
        result_surface = self.font_medium.render(result_text, True, color)
        self.screen.blit(result_surface, (250, 270))
        
        time_text = self.font_small.render(f"TIME: {self.game_timer:.1f}s", True, WHITE)
        self.screen.blit(time_text, (270, 330))
        
        continue_text = self.font_small.render("PRESS ENTER TO CONTINUE", True, WHITE)
        self.screen.blit(continue_text, (250, 370))
        
        pygame.display.flip()
        return True
    
    def draw_game(self) -> None:
        self.screen.fill(BLACK)
        
        # Draw Maze
        cell_size = self.path_width * DRAWING_SCALE
        max_cell_x = MAZE_OFFSET[0] + self.maze_width * (self.path_width + 1) * DRAWING_SCALE
        max_cell_y = MAZE_OFFSET[1] + self.maze_height * (self.path_width + 1) * DRAWING_SCALE
        
        # Draw maze background
        pygame.draw.rect(self.screen, MAZE_COLOR, 
                        (MAZE_OFFSET[0] - self.path_width * 2, 
                         MAZE_OFFSET[1] - self.path_width * 2,
                         max_cell_x + self.path_width - MAZE_OFFSET[0],
                         max_cell_y + self.path_width - MAZE_OFFSET[1]))
        
        for x in range(self.maze_width):
            for y in range(self.maze_height):
                cell_x = MAZE_OFFSET[0] + x * (self.path_width + 1) * DRAWING_SCALE
                cell_y = MAZE_OFFSET[1] + y * (self.path_width + 1) * DRAWING_SCALE
                
                # Draw cell background
                pygame.draw.rect(self.screen, BLACK, (cell_x, cell_y, cell_size, cell_size))
                
                # Draw passageways between cells
                if self.maze[y * self.maze_width + x] & CellPath.SOUTH.value:
                    pygame.draw.rect(self.screen, BLACK, (cell_x, cell_y + cell_size, cell_size, DRAWING_SCALE))
                if self.maze[y * self.maze_width + x] & CellPath.EAST.value:
                    pygame.draw.rect(self.screen, BLACK, (cell_x + cell_size, cell_y, DRAWING_SCALE, cell_size))
        
        # Draw entrance openings
        pygame.draw.rect(self.screen, BLACK, 
                        (MAZE_OFFSET[0] - self.path_width * 2,
                         MAZE_OFFSET[1] + self.player1_start.y * (self.path_width + 1) * DRAWING_SCALE,
                         DRAWING_SCALE, cell_size))
        
        # Draw exit markers
        self.draw_exit_markers(self.player1_start, True)
        self.draw_exit_markers(self.player2_start, False)
        
        # Draw players
        self.draw_player(self.player1_pos, self.player1_color, "P1")
        if self.two_player_mode:
            self.draw_player(self.player2_pos, self.player2_color, "P2")
        else:
            self.draw_player(self.player2_pos, self.ai_color, "AI")
        
        # Draw UI
        time_text = self.font_small.render(f"TIME: {self.game_timer:.1f}s", True, WHITE)
        self.screen.blit(time_text, (30, 10))
        
        p1_status = "FINISHED!" if self.player1_finished else "MOVING..."
        p1_text = self.font_small.render(f"Player 1: {p1_status}", True, self.player1_color)
        self.screen.blit(p1_text, (75, 550))
        
        if self.two_player_mode:
            p2_status = "FINISHED!" if self.player2_finished else "MOVING..."
            p2_text = self.font_small.render(f"Player 2: {p2_status}", True, self.player2_color)
        else:
            p2_status = "FINISHED!" if self.player2_finished else "MOVING..."
            p2_text = self.font_small.render(f"Computer: {p2_status}", True, self.ai_color)
        
        self.screen.blit(p2_text, (425, 550))
        
        # Draw warm-up countdown if in warm-up phase
        if self.game_state == GameState.WARMUP:
            countdown = max(0, 3 - int(self.warmup_timer))
            warmup_text = self.font_medium.render(f"GET READY! {countdown}", True, MINT)
            self.screen.blit(warmup_text, (SCREEN_WIDTH-300, 10))
        elif self.game_state == GameState.PLAYING:
            pause_text = self.font_small.render('Press "P" to pause', True, WHITE)
            self.screen.blit(pause_text, (SCREEN_WIDTH-275, 10))
        
        pygame.display.flip()
    
    def draw_exit_markers(self, pos: Vec2I, is_left_side: bool) -> None:
        left_color = self.player2_color if self.two_player_mode else self.ai_color
        right_color = self.player1_color
        
        base_x = MAZE_OFFSET[0] + pos.x * (self.path_width + 1) * DRAWING_SCALE
        base_y = MAZE_OFFSET[1] + pos.y * (self.path_width + 1) * DRAWING_SCALE + (self.path_width * DRAWING_SCALE) // 2
        
        tip_size = 10
        
        if is_left_side:
            mk_base_x = base_x - 5 * DRAWING_SCALE
            mk_tip_x = base_x - 2 * DRAWING_SCALE
            pygame.draw.polygon(self.screen, left_color, [
                (mk_base_x, base_y),
                (mk_tip_x, base_y - tip_size),
                (mk_tip_x, base_y + tip_size)
            ])
        else:
            mk_base_x = base_x + (self.path_width + 5) * DRAWING_SCALE
            mk_tip_x = base_x + (self.path_width + 2) * DRAWING_SCALE
            pygame.draw.polygon(self.screen, right_color, [
                (mk_base_x, base_y),
                (mk_tip_x, base_y - tip_size),
                (mk_tip_x, base_y + tip_size)
            ])
    
    def draw_player(self, pos: Vec2I, color: tuple, label: str) -> None:
        x = MAZE_OFFSET[0] + (pos.x * (self.path_width + 1) + self.path_width // 2) * DRAWING_SCALE
        y = MAZE_OFFSET[1] + (pos.y * (self.path_width + 1) + self.path_width // 2) * DRAWING_SCALE
        radius = (self.path_width // 2) * (DRAWING_SCALE + self.path_width)
        
        # Draw player as filled circle
        pygame.draw.circle(self.screen, color, (x + self.path_width, y + self.path_width), radius)
        
        # Draw player label
        label_text = self.font_tiny.render(label, True, BLACK)
        self.screen.blit(label_text, (x - 5, y))
    
    def run(self) -> None:
        running = True
        last_time = time.time()
        
        while running:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            if self.game_state == GameState.TITLE:
                running = self.update_title_screen()
            elif self.game_state == GameState.WARMUP or self.game_state == GameState.PLAYING:
                running = self.update_game(dt)
            elif self.game_state == GameState.PAUSED:
                running = self.update_paused_screen()
            elif self.game_state == GameState.RESULT:
                running = self.update_result_screen()
            
            self.clock.tick(60)
        
        pygame.quit()

if __name__ == "__main__":
    AmazingMaze().run()