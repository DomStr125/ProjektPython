import sys
import tkinter as tk
from tkinter import messagebox
import random
import time
from collections import deque
import pickle

class Desert:
    #Poziomy trudności
    DIFFICULTY = {
        "easy": {
            "width": 30,
            "height": 15,
            "vision": 5,
            "enemies": 5,
            "enemy_speed": 1,
            "enemy_vision": 3,
            "day_turns": 20,
            "night_turns": 0,
            "shift": 10,
            "quick_sand": 0.1
        },
        "medium": {
            "width": 40,
            "height": 20,
            "vision": 4,
            "enemies": 10,
            "enemy_speed": 1,
            "enemy_vision": 5,
            "day_turns": 15,
            "night_turns": 10,
            "shift": 8,
            "quick_sand": 0.2
        },
        "hard": {
            "width": 50,
            "height": 25,
            "vision": 3,
            "enemies": 15,
            "enemy_speed": 2,
            "enemy_vision": 5,
            "day_turns": 10,
            "night_turns": 15,
            "shift": 6,
            "quick_sand": 0.3
        }
    }

    def __init__(self, root, hearts, difficulty): # Inicjalizacja gry
        self.root = root
        self.hearts = hearts
        self.difficulty = difficulty
        self.in_quick_sand = False
        self.settings = self.DIFFICULTY[difficulty]
        self.width = self.settings["width"]
        self.height = self.settings["height"]
        self.vision = self.settings["vision"]
        self.enemies = self.settings["enemies"]
        self.cell_size = 32
        self.turns = 0
        
        self.points = 5000
        self.start_time = time.time()
        self.game_time = 0
        self.is_game_active = True
        self.last_player_cell = 0
        self.has_torch = False
        self.has_sandals = False

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        max_cell_width = screen_width // self.width
        max_cell_height = (screen_height - 50) // self.height
        self.cell_size = min(self.cell_size, max_cell_width, max_cell_height)
        #ramki
        self.frame_points = tk.Frame(root, bg='#f0f0f0')
        self.frame_points.pack(side=tk.TOP, fill=tk.X)

        self.label_points = tk.Label(self.frame_points, text="Points: 0", font=('Arial', 10, 'bold'), fg="white", bg="#34495e")   
        self.label_points.pack(side=tk.LEFT, padx=10)

        self.label_time = tk.Label(self.frame_points, text="Time: 0s", font=('Arial', 10, 'bold'), fg="white", bg="#34495e")
        self.label_time.pack(side=tk.LEFT)

        self.label_hearts = tk.Label(self.frame_points, text=f"Hearts: {self.hearts}", font=('Arial', 10, 'bold'), fg="white", bg="#34495e")
        self.label_hearts.pack(side=tk.LEFT, padx=10)

        self.setup_scores()

        self._is_day = True
        self.day_turns = self.settings["day_turns"]
        self.night_turns = self.settings["night_turns"]
        self.day_night_counter = 0

        self.textures = self.load_textures()

        self.generate_labirynth()
        self.draw_labirynth()

        self.root.bind("<KeyPress>", self.on_key_press)

    def load_textures(self): # Ładowanie tekstur
        textures = {
            "sand": tk.PhotoImage(file="grafika/desert/sand.png"),
            "wall": tk.PhotoImage(file="grafika/desert/rock.png"),
            "player": tk.PhotoImage(file="grafika/knight.png"),
            "enemy": tk.PhotoImage(file="grafika/desert/vulture.png"),
            "sandals": tk.PhotoImage(file="grafika/desert/sandals.png"),
            "darkness": tk.PhotoImage(file="grafika/desert/darkness.png"),
            "quick_sand": tk.PhotoImage(file="grafika/desert/quick_sand.png"),
            "tornado": tk.PhotoImage(file="grafika/desert/tornado.png"),
            "exit": tk.PhotoImage(file="grafika/exit.png"),
            "torch": tk.PhotoImage(file="grafika/forest/torch.png")
        }
        return textures

    def setup_scores(self): # Ustawianie punktów i czasu gry
        if self.is_game_active:
            self.game_time = int(time.time() - self.start_time)
            self.points = max(0, 5000 - self.game_time * 10)
            self.label_points.config(text=f"Punkty: {self.points}")
            self.label_time.config(text=f"Czas: {self.game_time}s")
            self.root.after(1000, self.setup_scores)
    
    def generate_labirynth(self): # Generowanie labiryntu
        labirynth = [[1 for _ in range(self.width)] for _ in range(self.height)]

        def carve(x, y):
            dirs = [(2,0), (-2,0), (0,2), (0,-2)]
            random.shuffle(dirs)
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                if 1 <= nx < self.width-1 and 1 <= ny < self.height-1 and labirynth[ny][nx] == 1:
                    labirynth[ny][nx] = 0
                    labirynth[y + dy//2][x + dx//2] = 0
                    carve(nx, ny)

        for y in range(1, self.height-1):
            for x in range(1, self.width-1):
                labirynth[y][x] = 1

        labirynth[1][1] = 0 
        carve(1, 1)

        ex, ey = self.width-2, self.height-2
        if labirynth[ey][ex] != 0:
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                nx, ny = ex+dx, ey+dy
                if 1 <= nx < self.width-1 and 1 <= ny < self.height-1 and labirynth[ny][nx] == 0:
                    labirynth[ey][ex] = 0
                    break
            else:
                labirynth[ey][ex] = 0
                labirynth[ey][ex-1] = 0

        for y in range(1, self.height-1):
            for x in range(1, self.width-1):
                if labirynth[y][x] == 1:
                    labirynth[y][x] = 2

        self.player_x, self.player_y = 1, 1
        self.exit_x, self.exit_y = ex, ey
        labirynth[self.player_y][self.player_x] = "P"
        labirynth[self.exit_y][self.exit_x] = "E"
        
        num_quick_sand = int(self.settings["quick_sand"] * self.width * self.height) # Procent szybkiego piasku
        placed = 0
        while placed < num_quick_sand:
            x = random.randint(1, self.width - 2)
            y = random.randint(1, self.height - 2)
            if labirynth[y][x] == 0 and (x, y) not in [(self.player_x, self.player_y), (self.exit_x, self.exit_y)]:
                labirynth[y][x] = 3
                placed += 1
        # Generowanie wrogów
        self.vultures = []
        placed = 0
        min_dist = self.settings["enemy_vision"] + 2
        while placed < self.enemies:
            x = random.randint(1, self.width - 2)
            y = random.randint(1, self.height - 2)
            if (labirynth[y][x] == 0 and
                (x, y) not in [(self.player_x, self.player_y), (self.exit_x, self.exit_y)] and
                all(abs(x - vx) + abs(y - vy) >= min_dist for vx, vy, *_ in self.vultures)):
                self.vultures.append([x, y, x, y])
                placed += 1

        while True:
            x = random.randint(1, self.width - 2)
            y = random.randint(1, self.height - 2)
            if (labirynth[y][x] == 0 and
                (x, y) not in [(self.player_x, self.player_y), (self.exit_x, self.exit_y)] and
                all((x, y) != (vx, vy) for vx, vy, *_ in self.vultures)):
                self.torch_pos = (x, y)
                break

        while True:
            x = random.randint(1, self.width - 2)
            y = random.randint(1, self.height - 2)
            if (labirynth[y][x] == 0 and
                (x, y) not in [(self.player_x, self.player_y), (self.exit_x, self.exit_y)] and
                (not hasattr(self, "torch_pos") or (x, y) != self.torch_pos) and
                all((x, y) != (vx, vy) for vx, vy, *_ in self.vultures)):
                self.sandals_pos = (x, y)
                break

        self.labirynth = labirynth

    def tornado_shift(self): # Przesuwanie tornada
        path = self.find_shortest_path()
        if not path:
            return

        labirynth = [[1 for _ in range(self.width)] for _ in range(self.height)]
        def carve(x, y):
            dirs = [(2,0), (-2,0), (0,2), (0,-2)]
            random.shuffle(dirs)
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                if 1 <= nx < self.width-1 and 1 <= ny < self.height-1 and labirynth[ny][nx] == 1:
                    labirynth[ny][nx] = 0
                    labirynth[y + dy//2][x + dx//2] = 0
                    carve(nx, ny)
        for y in range(1, self.height-1):
            for x in range(1, self.width-1):
                labirynth[y][x] = 1
        carve(self.player_x, self.player_y)
        ex, ey = self.exit_x, self.exit_y
        if labirynth[ey][ex] != 0:
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                nx, ny = ex+dx, ey+dy
                if 1 <= nx < self.width-1 and 1 <= ny < self.height-1 and labirynth[ny][nx] == 0:
                    labirynth[ey][ex] = 0
                    break
            else:
                labirynth[ey][ex] = 0
                labirynth[ey][ex-1] = 0
        for y in range(1, self.height-1):
            for x in range(1, self.width-1):
                if labirynth[y][x] == 1:
                    labirynth[y][x] = 2
        labirynth[self.player_y][self.player_x] = "P"
        labirynth[self.exit_y][self.exit_x] = "E"

        num_quick_sand = int(self.settings["quick_sand"] * self.width * self.height)
        placed = 0
        while placed < num_quick_sand:
            x = random.randint(1, self.width - 2)
            y = random.randint(1, self.height - 2)
            if labirynth[y][x] == 0 and (x, y) not in [(self.player_x, self.player_y), (self.exit_x, self.exit_y)]:
                labirynth[y][x] = 3
                placed += 1

        self.labirynth = labirynth

    def next_turn(self): # Przechodzenie do następnej tury
        self.turns += 1
        self.day_night_counter += 1
        if self.is_day and self.day_night_counter >= self.day_turns:
            self.is_day = False
            self.day_night_counter = 0
        elif not self.is_day and self.day_night_counter >= self.night_turns:
            self.is_day = True
            self.day_night_counter = 0

        if self.turns % self.settings["shift"] == 0:
            self.tornado_shift()
            self.draw_labirynth()
    
    def draw_labirynth(self): # Rysowanie labiryntu
        if not hasattr(self, "canvas") or self.canvas is None:
            self.canvas = tk.Canvas(self.root, width=self.width * self.cell_size, height=self.height * self.cell_size, bg="white")
            self.canvas.pack(expand=True, fill=tk.BOTH)

        self.canvas.delete("all")

        if not self.is_day:
            vision = self.vision + (2 if self.has_torch else 0)
        else:
            vision = max(self.width, self.height)

        for y in range(self.height):
            for x in range(self.width):
                cell = self.labirynth[y][x]
                px, py = x * self.cell_size, y * self.cell_size

                if cell == 1:
                    self.canvas.create_image(px, py, anchor=tk.NW, image=self.textures["wall"])
                elif cell == 2:
                    self.canvas.create_image(px, py, anchor=tk.NW, image=self.textures["tornado"])
                elif cell == 3:
                    self.canvas.create_image(px, py, anchor=tk.NW, image=self.textures["quick_sand"])
                elif cell == 0:
                    self.canvas.create_image(px, py, anchor=tk.NW, image=self.textures["sand"])
                elif cell == "P":
                    self.canvas.create_image(px, py, anchor=tk.NW, image=self.textures["sand"])
                    self.canvas.create_image(px, py, anchor=tk.NW, image=self.textures["player"])
                elif cell == "E":
                    self.canvas.create_image(px, py, anchor=tk.NW, image=self.textures["sand"])
                    exit_img = self.textures.get("exit", self.textures["enemy"])
                    self.canvas.create_image(px, py, anchor=tk.NW, image=exit_img)

                if not self.is_day:
                    if abs(x - self.player_x) + abs(y - self.player_y) > vision:
                        self.canvas.create_image(px, py, anchor=tk.NW, image=self.textures["darkness"])

        for vulture in self.vultures:
            vx, vy, _, _ = vulture
            if self.is_day or abs(vx - self.player_x) + abs(vy - self.player_y) <= vision:
                self.canvas.create_image(vx * self.cell_size, vy * self.cell_size, anchor=tk.NW, image=self.textures["enemy"])

        if hasattr(self, "torch_pos") and self.torch_pos and not self.has_torch:
            tx, ty = self.torch_pos
            if self.is_day or abs(tx - self.player_x) + abs(ty - self.player_y) <= vision:
                self.canvas.create_image(tx * self.cell_size, ty * self.cell_size, anchor=tk.NW, image=self.textures["torch"])

        if hasattr(self, "sandals_pos") and self.sandals_pos and not self.has_sandals:
            sx, sy = self.sandals_pos
            if self.is_day or abs(sx - self.player_x) + abs(sy - self.player_y) <= vision:
                self.canvas.create_image(sx * self.cell_size, sy * self.cell_size, anchor=tk.NW, image=self.textures["sandals"])

    def on_key_press(self, event): # Obsługa klawiszy
        if event.keysym.lower() == "e":
            equipment = []
            if self.has_torch:
                equipment.append("Torch")
            if self.has_sandals:
                equipment.append("Sandals")
            equipment_display = ", ".join(equipment) if equipment else "None"
            messagebox.showinfo("Equipment", f"Collected equipment: {equipment_display}")
            return
        
        if event.keysym.lower() == "p":
            self.save_game()
            return

        if self.in_quick_sand:
            self.in_quick_sand = False
            self.next_turn()
            self.draw_labirynth()
            return

        dx, dy = 0, 0
        if event.keysym == "Up":
            dy = -1
        elif event.keysym == "Down":
            dy = 1
        elif event.keysym == "Left":
            dx = -1
        elif event.keysym == "Right":
            dx = 1
        else:
            return

        new_x = self.player_x + dx
        new_y = self.player_y + dy

        if (0 < new_x < self.width - 1 and 0 < new_y < self.height - 1 and
            self.labirynth[new_y][new_x] != 1 and self.labirynth[new_y][new_x] != 2):
            stepping_on_quicksand = self.labirynth[new_y][new_x] == 3 and not self.has_sandals

            leaving_quicksand = False
            if self.labirynth[self.player_y][self.player_x] == "P":
                if hasattr(self, "last_player_cell") and self.last_player_cell == 3:
                    leaving_quicksand = True

            if leaving_quicksand:
                self.labirynth[self.player_y][self.player_x] = 3
            else:
                self.labirynth[self.player_y][self.player_x] = 0

            self.last_player_cell = self.labirynth[new_y][new_x]

            self.player_x, self.player_y = new_x, new_y
            self.labirynth[self.player_y][self.player_x] = "P"
            self.next_turn()
            self.draw_labirynth()

            if stepping_on_quicksand:
                self.in_quick_sand = True

            if (self.player_x, self.player_y) == (self.exit_x, self.exit_y):
                self.is_game_active = False
                final_time = int(time.time() - self.start_time)
                self.points += self.hearts * 250
                messagebox.showinfo("Congratulations!", f"You've reached the exit in {final_time}s \n Your score: {self.points}")
                self.root.after(100, self.root.destroy)

        for vx, vy, *_ in self.vultures:
            if (vx, vy) == (self.player_x, self.player_y):
                self.hearts -= 1
                self.label_hearts.config(text=f"Hearts: {self.hearts}")
                if self.hearts <= 0:
                    messagebox.showinfo("Game Over", "You were caught by a vulture!")
                    self.root.after(100, self.root.destroy)
                break

        if hasattr(self, "torch_pos") and (self.player_x, self.player_y) == self.torch_pos and not self.has_torch:
            self.has_torch = True
            self.torch_pos = None
            self.points += 1000
            self.label_points.config(text=f"Punkty: {self.points}")

        if hasattr(self, "sandals_pos") and (self.player_x, self.player_y) == self.sandals_pos and not self.has_sandals:
            self.has_sandals = True
            self.sandals_pos = None
            self.points += 1000
            self.label_points.config(text=f"Punkty: {self.points}")

        self.move_vultures()
        self.draw_labirynth()

    def find_shortest_path(self): # Znajdowanie najkrótszej ścieżki do wyjścia
        queue = deque()
        queue.append((self.player_x, self.player_y))
        visited = [[False]*self.width for _ in range(self.height)]
        prev = [[None]*self.width for _ in range(self.height)]
        visited[self.player_y][self.player_x] = True

        while queue:
            x, y = queue.popleft()
            if (x, y) == (self.exit_x, self.exit_y):
                path = []
                while (x, y) != (self.player_x, self.player_y):
                    path.append((x, y))
                    x, y = prev[y][x]
                path.append((self.player_x, self.player_y))
                path.reverse()
                return path
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                nx, ny = x+dx, y+dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if not visited[ny][nx] and self.labirynth[ny][nx] not in (1,2):
                        visited[ny][nx] = True
                        prev[ny][nx] = (x, y)
                        queue.append((nx, ny))
        return None
    
    def is_in_vulture_vision(self, vulture): # Sprawdzanie, czy gracz jest w zasięgu wzroku wroga
        _, _, cx, cy = vulture
        vision = self.settings["enemy_vision"]
        if not self.is_day:
            vision = max(1, vision - 2)
        return abs(self.player_x - cx) <= vision and abs(self.player_y - cy) <= vision

    def move_vultures(self): # Ruch wrogów
        for vulture in self.vultures:
            vx, vy, cx, cy = vulture
            vision = self.settings["enemy_vision"]
            speed = self.settings["enemy_speed"]
            if not self.is_day:
                vision = max(1, vision - 2)
            for _ in range(speed):
                vx, vy = vulture[0], vulture[1]
                if abs(self.player_x - cx) <= vision and abs(self.player_y - cy) <= vision:
                    best_dx = 0
                    best_dy = 0
                    if self.player_x > vx:
                        best_dx = 1
                    elif self.player_x < vx:
                        best_dx = -1
                    if self.player_y > vy:
                        best_dy = 1
                    elif self.player_y < vy:
                        best_dy = -1
                    moved = False
                    for dx, dy in [(best_dx, 0), (0, best_dy)]:
                        nx, ny = vx + dx, vy + dy
                        if (abs(nx - cx) <= vision and
                            abs(ny - cy) <= vision and
                            self.labirynth[ny][nx] in (0, 3) and
                            (nx, ny) != (self.player_x, self.player_y) and
                            all((nx, ny) != (ovx, ovy) for ovx, ovy, *_ in self.vultures)):
                            vulture[0], vulture[1] = nx, ny
                            vx, vy = nx, ny
                            moved = True
                            break
                    if not moved:
                        break
                else:
                    if (vx, vy) != (cx, cy):
                        dx = 1 if cx > vx else -1 if cx < vx else 0
                        dy = 1 if cy > vy else -1 if cy < vy else 0
                        moved = False
                        for ddx, ddy in [(dx, 0), (0, dy)]:
                            nx, ny = vx + ddx, vy + ddy
                            if (abs(nx - cx) <= vision and
                                abs(ny - cy) <= vision and
                                self.labirynth[ny][nx] in (0, 3) and
                                (nx, ny) != (self.player_x, self.player_y) and
                                all((nx, ny) != (ovx, ovy) for ovx, ovy, *_ in self.vultures)):
                                vulture[0], vulture[1] = nx, ny
                                vx, vy = nx, ny
                                moved = True
                                break
                        if not moved:
                            break

    def save_game(self, filename="savegame.pkl"): # zapisywanie stanu gry
        state = {
            "level": "desert",
            "difficulty": self.difficulty,
            "player_x": self.player_x,
            "player_y": self.player_y,
            "exit_x": self.exit_x,
            "exit_y": self.exit_y,
            "labirynth": self.labirynth,
            "vultures": self.vultures,
            "has_torch": self.has_torch,
            "has_sandals": self.has_sandals,
            "hearts": self.hearts,
            "points": self.points,
            "turns": self.turns,
            "is_day": self.is_day,
            "day_night_counter": self.day_night_counter,
            "start_time": self.start_time
        }
        with open(filename, "wb") as f:
            pickle.dump(state, f)
        messagebox.showinfo("Game Saved", "Your game has been saved!")

    @property # Właściwość do sprawdzania, czy jest dzień
    def is_day(self):
        return self._is_day

    @is_day.setter # Właściwość do ustawiania dnia/nocy
    def is_day(self, value):
        self._is_day = value

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        hearts = int(sys.argv[1])
        difficulty = sys.argv[2]
    else:
        hearts = 5
        difficulty = "hard"
    root = tk.Tk()
    Desert(root, hearts, difficulty)
    root.mainloop()