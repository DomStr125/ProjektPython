import sys
import tkinter as tk
import random
import time

class Desert:

    DIFFICULTY = {
        "easy": {
            "width": 30,
            "height": 15,
            "vision": 5,
            "enemies": 5,
            "day_turns": 20,
            "night_turns": 0,
            "shift": 10
        },
        "medium": {
            "width": 40,
            "height": 20,
            "vision": 4,
            "enemies": 10,
            "day_turns": 15,
            "night_turns": 5,
            "shift": 8
        },
        "hard": {
            "width": 50,
            "height": 25,
            "vision": 3,
            "enemies": 15,
            "day_turns": 10,
            "night_turns": 10,
            "shift": 6
        }
    }

    def __init__(self, root, hearts, difficulty):
        self.root = root
        self.hearts = hearts
        self.difficulty = difficulty
        self.settings = self.DIFFICULTY[difficulty]
        self.width = self.settings["width"]
        self.height = self.settings["height"]
        self.vision = self.settings["vision"]
        self.enemies = self.settings["enemies"]
        self.cell_size = 20
        self.turns = 0
        
        self.points = 5000
        self.start_time = time.time()
        self.game_time = 0
        self.is_game_active = True

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        max_cell_width = screen_width // self.width
        max_cell_height = (screen_height - 50) // self.height
        self.cell_size = min(self.cell_size, max_cell_width, max_cell_height)


        self.frame_points = tk.Frame(root, bg='#f0f0f0')
        self.frame_points.pack(side=tk.TOP, fill=tk.X)

        self.label_points = tk.Label(self.frame_points, text="Points: 0", font=('Arial', 10, 'bold'), fg="white", bg="#34495e")   
        self.label_points.pack(side=tk.LEFT, padx=10)

        self.label_time = tk.Label(self.frame_points, text="Time: 0s", font=('Arial', 10, 'bold'), fg="white", bg="#34495e")
        self.label_time.pack(side=tk.LEFT)

        self.label_hearts = tk.Label(self.frame_points, text=f"Hearts: {self.hearts}", font=('Arial', 10, 'bold'), fg="white", bg="#34495e")
        self.label_hearts.pack(side=tk.LEFT, padx=10)

        self.setup_scores()

        self.textures = self.load_textures()

        self.generate_labirynth()  # Generate the labyrinth on startup

    def load_textures(self):
        textures = {
            "sand": tk.PhotoImage(file="grafika/desert/sand.png"),
            "wall": tk.PhotoImage(file="grafika/desert/rock.png"),
            "player": tk.PhotoImage(file="grafika/knight.png"),
            "enemy": tk.PhotoImage(file="grafika/desert/vulture.png"),
            "sandals": tk.PhotoImage(file="grafika/desert/sandals.png"),
            "darkness": tk.PhotoImage(file="grafika/desert/darkness.png"),
            "quick_sand": tk.PhotoImage(file="grafika/desert/quick_sand.png"),
            "tornado": tk.PhotoImage(file="grafika/desert/tornado.png")
        }
        return textures

    def setup_scores(self): # aktualizacja punktów i czasu         
            if self.is_game_active:
                self.game_time = int(time.time() - self.start_time)
                self.points = max(0, 5000 - self.game_time * 10)

                self.label_points.config(text=f"Punkty: {self.points}")
                self.label_time.config(text=f"Czas: {self.game_time}s")

                self.root.after(1000, self.setup_scores)
    
    def generate_labirynth(self): # generowanie labiryntu
        # 1 = wall, 0 = sand
        labirynth = [[1 for _ in range(self.width)] for _ in range(self.height)]

        # Set interior to sand
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                labirynth[y][x] = 0

        # Place player in top-right (not on the border)
        self.player_x, self.player_y = self.width - 2, 1
        labirynth[self.player_y][self.player_x] = "P"

        # Place exit in bottom-left (not on the border)
        self.exit_x, self.exit_y = 1, self.height - 2
        labirynth[self.exit_y][self.exit_x] = "E"

        # Optionally: randomly add some walls inside (not on player or exit)
        for _ in range((self.width * self.height) // 6):  # adjust density as needed
            x = random.randint(1, self.width - 2)
            y = random.randint(1, self.height - 2)
            if (x, y) not in [(self.player_x, self.player_y), (self.exit_x, self.exit_y)]:
                labirynth[y][x] = 1

        self.labirynth = labirynth

    def tornado_shift(self):
        # Randomize interior walls (not border, not player, not exit)
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if (x, y) not in [(self.player_x, self.player_y), (self.exit_x, self.exit_y)]:
                    self.labirynth[y][x] = 1 if random.random() < 0.18 else 0  # 18% wall, adjust as needed

    def next_turn(self):
        # Call this every player move
        self.turns += 1
        if self.turns % self.settings["shift"] == 0:
            self.tornado_shift()
            self.draw_labirynth()
    
    def draw_labirynth(self):
        self.canvas = getattr(self, "canvas", None)
        if self.canvas is None:
            self.canvas = tk.Canvas(self.root, width=self.width * self.cell_size, height=self.height * self.cell_size, bg="white")
            self.canvas.pack(expand=True, fill=tk.BOTH)
            self.canvas.lower()  # keep under UI

        self.canvas.delete("all")
        for y in range(self.height):
            for x in range(self.width):
                cell = self.labirynth[y][x]
                px, py = x * self.cell_size, y * self.cell_size
                if cell == 1:
                    self.canvas.create_image(px, py, anchor=tk.NW, image=self.textures["wall"])
                elif cell == 0:
                    self.canvas.create_image(px, py, anchor=tk.NW, image=self.textures["sand"])
                elif cell == "P":
                    self.canvas.create_image(px, py, anchor=tk.NW, image=self.textures["sand"])
                    self.canvas.create_image(px, py, anchor=tk.NW, image=self.textures["player"])
                elif cell == "E":
                    self.canvas.create_image(px, py, anchor=tk.NW, image=self.textures["sand"])
                    self.canvas.create_image(px, py, anchor=tk.NW, image=self.textures["enemy"])  # or use exit texture if you have one

        # Optionally: draw other objects (enemies, items, etc.) here


if __name__ == "__main__":
    # zbierz argumenty z linii poleceń
    if len(sys.argv) < 3:
        print("Usage: python level2.py <hearts> <difficulty>")
        sys.exit(1)
    hearts = int(sys.argv[1])
    difficulty = sys.argv[2]
    root = tk.Tk()
    Desert(root, hearts, difficulty)
    root.mainloop()