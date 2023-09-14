import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import Canvas
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import numpy as np

class ImageApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Image Dot Mover')

        self.canvas = Canvas(root)
        self.canvas.pack(fill=tk.BOTH, expand=tk.YES)

        self.canvas.bind("<Button-1>", self.place_dot)
        self.canvas.bind("<B1-Motion>", self.move_dot)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        menu = tk.Menu(root)
        root.config(menu=menu)

        file_menu = tk.Menu(menu)
        menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open...", command=self.open_image)
        file_menu.add_command(label="Save", command=self.save_landmarks)
        file_menu.add_command(label="Exit", command=root.quit)

        self.dot_size = 5
        self.image_path = None
        self.image = None
        self.photo = None
        self.dots = {}
        self.active_dot = None

        # Create a list of 68 distinct colors
        self.colors = plt.cm.jet(np.linspace(0, 1, 68))
    
    def get_color(self, index):
        # Convert RGB from 0-1 to 0-255 range
        r, g, b, a = self.colors[index]
        return "#{:02x}{:02x}{:02x}".format(int(r*255), int(g*255), int(b*255))


    def read_landmarks_from_file(self, img_path):
        filename = img_path.split("/")[-1]
        landmarks_file_path = img_path[:-4] + "_ldmks.txt"
        landmarks = []
        try:
            with open(landmarks_file_path, 'r') as f:
                for line in f:
                    x, y = map(float, line.strip().split())
                    landmarks.append((x, y))
            return landmarks
        except FileNotFoundError:
            print(f"File {landmarks_file_path} not found.")
            return []

    def save_landmarks(self):
        # Get the current positions of the landmarks from the canvas items
        landmarks = [(self.canvas.coords(dot)[0] + self.dot_size, self.canvas.coords(dot)[1] + self.dot_size) for dot in self.dots.keys()]

        # Scale landmarks back to original image dimensions
        scaled_landmarks = [(x / self.width_scale, y / self.height_scale) for x, y in landmarks]

        # Save landmarks
        filename = self.image_path.split("/")[-1]
        with open(self.image_path[:-4] + "_ldmks.txt", "w") as f:
            for x, y in scaled_landmarks:
                f.write("%f %f\n" % (x, y))

    def open_image(self):
        file_path = filedialog.askopenfilename()
        if not file_path:
            return

        self.image_path = file_path
        image = Image.open(file_path)
        self.width_scale = 800 / image.width
        self.height_scale = 800 / image.height

        # Resize the image to fit within 800x800 while maintaining aspect ratio
        aspect_ratio = image.width / image.height
        if image.width > image.height:
            new_width = 800
            new_height = int(new_width / aspect_ratio)
        else:
            new_height = 800
            new_width = int(new_height * aspect_ratio)

        image = image.resize((new_width, new_height))
        
        
        self.photo = ImageTk.PhotoImage(image)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

        # Read and scale landmarks
        landmarks = self.read_landmarks_from_file(file_path)
        scaled_landmarks = [(x*self.width_scale, y*self.height_scale) for x, y in landmarks]

        for idx, (x, y) in enumerate(scaled_landmarks):
            dot = self.canvas.create_oval(x - self.dot_size, y - self.dot_size, x + self.dot_size, y + self.dot_size, fill=self.get_color(idx))
            self.dots[dot] = (x, y, idx)


    def place_dot(self, event):
        self.active_dot = None
        for dot, (x, y, idx) in self.dots.items():
            if x - self.dot_size <= event.x <= x + self.dot_size and y - self.dot_size <= event.y <= y + self.dot_size:
                self.active_dot = dot
                break

    def on_drag(self, event):
        if self.active_dot:
            x, y, idx = self.dots[self.active_dot]  # Use self.active_dot as the key
            self.canvas.move(self.active_dot, event.x - x, event.y - y)
            self.dots[self.active_dot] = (event.x, event.y, idx)


    def on_release(self, event):
        self.active_dot = None

            
    def move_dot(self, event):
        dot = self.canvas.find_closest(event.x, event.y)[0]
        x, y, idx = self.dots[dot]  # Extract all three values
        self.canvas.move(dot, event.x - x, event.y - y)
        self.dots[dot] = (event.x, event.y, idx)  # Store all three values back

    def show_index_on_hover(self, event):
        for dot, (x, y, idx) in self.dots.items():
            if x - self.dot_size <= event.x <= x + self.dot_size and y - self.dot_size <= event.y <= y + self.dot_size:
                self.canvas.create_text(event.x, event.y - 10, text=str(idx), tags="indexTag")
            else:
                self.canvas.delete("indexTag")

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry('800x800')
    app = ImageApp(root)
    root.mainloop()
