"""Optional local OS chooser, isolated from server lifetime. Paths also editable."""
import sys
import tkinter as tk
from tkinter import filedialog
root=tk.Tk();root.withdraw();root.attributes('-topmost',True)
try:
    result=filedialog.askdirectory(title='MPAP simulation folder') if sys.argv[1]=='folder' else filedialog.askopenfilename(title='MPAP G-code configuration',filetypes=[('G-code','*.mpf *.nc *.gcode *.tap *.txt'),('All files','*')])
    print(result)
finally:root.destroy()
