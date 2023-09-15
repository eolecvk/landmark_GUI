import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import Canvas
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import numpy as np
import os

class ImageApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Image Dot Mover')
        self.root.bind("<Control-s>", lambda event=None: self.save_landmarks())

        self.canvas = Canvas(root)
        self.canvas.pack(fill=tk.BOTH, expand=tk.YES)

        self.canvas.bind("<Button-1>", self.place_dot)
        self.canvas.bind("<B1-Motion>", self.move_dot)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        #self.canvas.bind("<Motion>", self.show_index_on_hover)

        menu = tk.Menu(root)
        root.config(menu=menu)

        file_menu = tk.Menu(menu)
        menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open directory...", command=self.open_directory)
        file_menu.add_command(label="Open file...", command=self.open_image)
        file_menu.add_command(label="Save", command=self.save_landmarks)
        file_menu.add_command(label="Exit", command=root.quit)



        self.image_files = []  # To store list of images in a directory
        self.current_image_index = None  # To keep track of which image in the list is currently open

        root.bind('<Left>', self.previous_image)
        root.bind('<Right>', self.next_image)


        self.dot_size = 3
        self.line_size = 1

        self.image_path = None
        self.image = None
        self.photo = None
        self.dots = {}
        self.active_dot = None

        # Create a list of 68 distinct colors
        self.colors = plt.cm.jet(np.linspace(0, 1, 68))

        self.dot_lines = {}  # A dictionary to store lines associated with each dot

        #self.image_path = "/home/eole/Downloads/Chimp_FilmRip_MVP2MostVerticalPrimate.2001.0119_0.png"
        self.open_image()

    # def show_index_on_hover(self, event):
    #     # Get the dot's index from the tag
    #     dot_idx = event.widget.gettags(event.widget.find_withtag("current"))[0]
    #     # Show the index using a label, tooltip, or print
    #     print(dot_idx)
    
    def get_color(self, index, line=False):
        if line:
            color_groups = [
                (range(0, 17), 'red'), # face contour
                (range(17, 22), 'blue'), # left eyebrow
                (range(22, 27), 'blue'), # right eyebrow
                (range(27, 36), 'purple'), # nose
                (range(36, 42), 'yellow'), # left eye
                (range(42, 48), 'yellow'), # right eye
                (range(48, 69), 'magenta') # mouth
            ]
        else:
            color_groups = [
            ((30, 36, 39, 42, 45, 48, 68), 'white'), # special landmarks
            (range(0, 17), 'red'), # face contour
            (range(17, 22), 'blue'), # left eyebrow
            (range(22, 27), 'blue'), # right eyebrow
            (range(27, 36), 'purple'), # nose
            (range(36, 42), 'yellow'), # left eye
            (range(42, 48), 'yellow'), # right eye
            (range(48, 69), 'magenta') # mouth
        ]

        for r, color in color_groups:
            if index in r:
                return color

        return "#000000"  # default color if index is outside defined ranges


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



    def open_directory(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            # Assuming images are in PNG format for this example
            # You can adjust this to handle other image formats or even multiple formats
            images = sorted([os.path.join(dir_path, fname) for fname in os.listdir(dir_path)
                        if any([fname.endswith(valid_extension) for valid_extension in ['.png', '.jpg', '.jpeg']] )])
            if images:
                self.open_image(images[0])
                # Store all images in a list for navigation purposes
                self.image_files = images
                self.current_image_index = 0
            else:
                messagebox.showerror("Error", "No image files found in the selected directory!")
                return


    def previous_image(self, event=None):
        if self.image_files and self.current_image_index > 0:
            self.current_image_index -= 1
            self.open_image(self.image_files[self.current_image_index])

    def next_image(self, event=None):
        if self.image_files and self.current_image_index < len(self.image_files) - 1:
            self.current_image_index += 1
            self.open_image(self.image_files[self.current_image_index])


    def open_image(self, file_path=None):
        
        if file_path is None:
            file_path = filedialog.askopenfilename()

        if not file_path:
            return

        if file_path in self.image_files:
            self.current_image_index = self.image_files.index(file_path)

        self.image_path = file_path

        # Extract the filename from the file_path
        filename = os.path.basename(file_path)
        
        # Update the title of the main window
        self.root.title(f'Image Dot Mover - {filename}')


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

        # Step 1: Create all dots first
        for idx, (x, y) in enumerate(scaled_landmarks):
            dot = self.canvas.create_oval(x - self.dot_size, y - self.dot_size, x + self.dot_size, y + self.dot_size, fill=self.get_color(idx), tags=str(idx))
            center_x = (x + self.dot_size + x - self.dot_size) / 2
            center_y = (y + self.dot_size + y - self.dot_size) / 2
            self.dots[dot] = (center_x, center_y, idx)

        # Step 2: Connect the dots based on the specified groups
        prev_dot = None
        for idx, (x, y) in enumerate(scaled_landmarks):
            dot = list(self.dots.keys())[idx]

            should_connect = any([
                idx-1 in group and idx in group
                for group in [
                    range(0, 17), range(17, 22), range(22, 27), range(27, 36), 
                    range(36, 42), range(42, 48), range(48, 69)
                ]
            ])

            if prev_dot and should_connect:
                prev_dot_center = ((self.canvas.coords(prev_dot)[0] + self.canvas.coords(prev_dot)[2]) / 2, (self.canvas.coords(prev_dot)[1] + self.canvas.coords(prev_dot)[3]) / 2)
                dot_center = ((self.canvas.coords(dot)[0] + self.canvas.coords(dot)[2]) / 2, (self.canvas.coords(dot)[1] + self.canvas.coords(dot)[3]) / 2)
                line = self.canvas.create_line(prev_dot_center, dot_center, fill=self.get_color(idx, line=True), width=self.line_size)

                # Store the line references in the dictionary
                self.dot_lines[prev_dot] = self.dot_lines.get(prev_dot, []) + [line]
                self.dot_lines[dot] = self.dot_lines.get(dot, []) + [line]

            prev_dot = dot

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
            center_x = (event.x + self.dot_size + event.x - self.dot_size) / 2
            center_y = (event.y + self.dot_size + event.y - self.dot_size) / 2
            self.dots[self.active_dot] = (center_x, center_y, idx)


    def on_release(self, event):
        self.active_dot = None

            
    def move_dot(self, event):
        if self.active_dot:
            x, y, idx = self.dots[self.active_dot]
            self.canvas.move(self.active_dot, event.x - x, event.y - y)
            center_x = (event.x + self.dot_size + event.x - self.dot_size) / 2
            center_y = (event.y + self.dot_size + event.y - self.dot_size) / 2
            self.dots[self.active_dot] = (center_x, center_y, idx)

            # Update connected lines for this dot
            if self.active_dot in self.dot_lines:
                for line in self.dot_lines[self.active_dot]:
                    coords = list(self.canvas.coords(line))
                    # Determine which end of the line to update based on proximity
                    center_x, center_y = self.dots[self.active_dot][:2]
                    if self._distance(coords[:2], (x, y)) < self._distance(coords[2:], (x, y)):
                        coords[:2] = [center_x, center_y]
                    else:
                        coords[2:] = [center_x, center_y]
                    self.canvas.coords(line, *coords)

    def _distance(self, point1, point2):
        return ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) ** 0.5


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry('800x800')
    app = ImageApp(root)
    root.mainloop()