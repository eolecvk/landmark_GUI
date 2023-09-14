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

        menu = tk.Menu(root)
        root.config(menu=menu)

        file_menu = tk.Menu(menu)
        menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open...", command=self.open_image)
        file_menu.add_command(label="Save", command=self.save_landmarks)
        file_menu.add_command(label="Exit", command=root.quit)

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
        if not self.image_path or not self.dots:
            messagebox.showwarning("Warning", "No image or landmarks to save!")
            return

        filename = self.image_path.split("/")[-1]
        landmarks_file_path = self.image_path[:-4] + "_ldmks.txt"
        with open(landmarks_file_path, 'w') as f:
            for dot, (x, y) in self.dots.items():
                f.write("%f %f\n" % (x, y))
        messagebox.showinfo("Info", "Landmarks saved successfully!")

    def open_image(self):
        file_path = filedialog.askopenfilename()
        if not file_path:
            return

        self.image_path = file_path

        image = Image.open(file_path)
        self.photo = ImageTk.PhotoImage(image)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

        # Read landmarks
        landmarks = self.read_landmarks_from_file(file_path)
        for idx, (x, y) in enumerate(landmarks):
            dot = self.canvas.create_oval(x - 5, y - 5, x + 5, y + 5, fill=self.get_color(idx))
            self.dots[dot] = (x, y)

    def place_dot(self, event):
        self.active_dot = None
        for dot, (x, y) in self.dots.items():
            if x - 5 <= event.x <= x + 5 and y - 5 <= event.y <= y + 5:
                self.active_dot = dot
                break
        
    def move_dot(self, event):
        if self.active_dot:
            x, y = event.x, event.y
            self.canvas.coords(self.active_dot, x - 5, y - 5, x + 5, y + 5)
            self.dots[self.active_dot] = (x, y)

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry('800x600')
    app = ImageApp(root)
    root.mainloop()
