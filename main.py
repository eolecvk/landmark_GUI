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

        self.canvas.bind("<Control-Button-1>", self.place_dots)
        self.canvas.bind("<Button-1>", self.place_dot)
        self.canvas.bind("<B1-Motion>", self.on_b1_motion)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Motion>", self.show_index_on_hover) # debug : check landmark indices
        self.prev_dot_idx = None

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
        self.group_drag = False

        # Create a list of 68 distinct colors
        self.colors = plt.cm.jet(np.linspace(0, 1, 68))

        self.dot_lines = {}  # A dictionary to store lines associated with each dot
 
        self.color_groups = [
                (range(0, 17), 'red'), # face contour
                (range(17, 22), 'blue'), # left eyebrow
                (range(22, 27), 'blue'), # right eyebrow
                (range(27, 36), 'purple'), # nose
                (range(36, 42), 'yellow'), # left eye
                (range(42, 48), 'yellow'), # right eye
                (range(48, 69), 'magenta') # mouth
            ]

        self.connection_groups = [rng for rng, _ in self.color_groups]
        self.open_image('/home/eole/Downloads/Chimp_FilmRip_MVP2MostVerticalPrimate.2001.0119_0.png')

    def show_index_on_hover(self, event):
        # Get the dot's index from the tag
        dot_idx = event.widget.gettags(event.widget.find_withtag("current"))[0]
        
        if 'current' in dot_idx:
            return  # Ignore 'current' or if no tags found
        
        # Show the index using a label, tooltip, or print
        if dot_idx != self.prev_dot_idx:
            print(int(dot_idx))
            self.prev_dot_idx = dot_idx
    
    def get_color(self, index, line=False):
        color_groups = self.color_groups
        if not line:
            special_landmarks = ((30, 36, 39, 42, 45, 48, 68), 'white')
            color_groups.insert(0, special_landmarks)

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

        # Clear previous landmarks and their connecting lines
        for dot in self.dots.keys():
            self.canvas.delete(dot)
            if dot in self.dot_lines:
                for line in self.dot_lines[dot]:
                    self.canvas.delete(line)
        self.dots = {}
        self.dot_lines = {}

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
                idx-1 in group and idx in group for group in self.connection_groups
            ])

            if prev_dot and should_connect:
                prev_dot_center = ((self.canvas.coords(prev_dot)[0] + self.canvas.coords(prev_dot)[2]) / 2, (self.canvas.coords(prev_dot)[1] + self.canvas.coords(prev_dot)[3]) / 2)
                dot_center = ((self.canvas.coords(dot)[0] + self.canvas.coords(dot)[2]) / 2, (self.canvas.coords(dot)[1] + self.canvas.coords(dot)[3]) / 2)
                line = self.canvas.create_line(prev_dot_center, dot_center, fill=self.get_color(idx, line=True), width=self.line_size)

                # Store the line references in the dictionary
                self.dot_lines[prev_dot] = self.dot_lines.get(prev_dot, []) + [line]
                self.dot_lines[dot] = self.dot_lines.get(dot, []) + [line]

            prev_dot = dot
        
        # Special case for loops (for example, mouth and eyes)
        loops = [(59, 48), (67, 60), (41, 36), (42, 47)]
        for start, end in loops:
            start_dot = list(self.dots.keys())[start]
            end_dot = list(self.dots.keys())[end]
            start_center = ((self.canvas.coords(start_dot)[0] + self.canvas.coords(start_dot)[2]) / 2, (self.canvas.coords(start_dot)[1] + self.canvas.coords(start_dot)[3]) / 2)
            end_center = ((self.canvas.coords(end_dot)[0] + self.canvas.coords(end_dot)[2]) / 2, (self.canvas.coords(end_dot)[1] + self.canvas.coords(end_dot)[3]) / 2)
            line = self.canvas.create_line(start_center, end_center, fill=self.get_color(start, line=True), width=self.line_size)
            self.dot_lines[start_dot] = self.dot_lines.get(start_dot, []) + [line]
            self.dot_lines[end_dot] = self.dot_lines.get(end_dot, []) + [line]


    def place_dot(self, event):
        self.active_dot = None
        for dot, (x, y, idx) in self.dots.items():
            if x - self.dot_size <= event.x <= x + self.dot_size and y - self.dot_size <= event.y <= y + self.dot_size:
                self.active_dot = dot
                break
    
    def place_dots(self, event):
        self.active_dots = None
        self.group_drag = True
        self.place_dot(event)
        self.active_dots = self.find_active_dots()

    def find_active_dots(self):
        if self.active_dot is None:
            return []
        if self.active_dot and not self.active_dots:
            self.active_dots = self.find_all_connected_dots(self.dots[self.active_dot][2])
            #self.active_dots.add(self.active_dot)
        
        return list(self.active_dots)

        
    def on_release(self, event):
        self.active_dot = None
        self.group_drag = False


    def on_b1_motion(self, event):
        if self.active_dot:
            x, y, idx = self.dots[self.active_dot]
            dx, dy = event.x - x, event.y - y
            
            # Move active dot and update its position
            self.canvas.move(self.active_dot, dx, dy)
            self.dots[self.active_dot] = (event.x, event.y, idx)
            
            # Move and update positions for dots connected to active dot
            if self.group_drag:
                for dot in self.active_dots:
                    if dot != self.active_dot:  # We've already moved the active_dot
                        x, y, idx = self.dots[dot]
                        self.canvas.move(dot, dx, dy)
                        self.dots[dot] = (x + dx, y + dy, idx)
            
            # Update the lines
            self.update_lines()




    def update_lines(self):
        for dot, lines in self.dot_lines.items():
            x, y, idx = self.dots[dot]
            for line in lines:
                coords = self.canvas.coords(line)
                if (coords[0], coords[1]) == (x, y):
                    self.canvas.coords(line, x, y, coords[2], coords[3])
                else:
                    self.canvas.coords(line, coords[0], coords[1], x, y)


    def get_connected_dots(self, index):
        for group in self.connection_groups:
            if index in group:
                return set(group)
        return set()


    def find_all_connected_dots(self, index):
        visited_dots = set()
        to_visit = self.get_connected_dots(index)
        all_connected_dots_idx = set(to_visit)
        
        while to_visit:
            dot = to_visit.pop()
            visited_dots.add(dot)

            for group in self.connection_groups:
                if dot in group:
                    group_set = set(group)
                    new_connections = group_set - visited_dots
                    all_connected_dots_idx.update(new_connections)
                    to_visit.update(new_connections)

        # Return dot, not just idx
        all_connected_dots = set([dot for dot in self.dots.keys() if self.dots[dot][2] in all_connected_dots_idx])    
        return all_connected_dots


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry('800x800')
    app = ImageApp(root)
    root.mainloop()