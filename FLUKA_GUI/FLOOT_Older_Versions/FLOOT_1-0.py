import matplotlib
import tkMessageBox
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
from Tkinter import *
import tkFileDialog
from sf2rconverter.root2tk import plot_3d_2canvas
from sf2rconverter.sf2r_lib import sf2r_manager
import tkTree as tkt
import os
from os import *


def get_contents(node):
  path=os.path.join(*node.full_id())
  for filename in sorted(os.listdir(path)):
    full=os.path.join(path, filename)
    folder=0
    if os.path.isdir(full):
	folder=1
    if (folder== 0 and filename[-4:]==".lis") or folder == 1: #
        node.widget.add_node(name=filename, id=filename, flag=folder)


class GUI(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, *args, **kwargs)

        #VARIABLES
        self.filelist=[]
        self.file=" "
        self.folder="./Test/Data"
        self.canvas=[]
        self.TOOLBAR=[]
        self.number=3
        ############################## 
        
        self.win = parent
        self.win.geometry("1440x730")
        self.win.title("FLOOT - GUI for FLUKA to ROOT converter")
        #MENU
        self.menu=Menu(self.win)
        self.menu.add_command(label="CONVERT",command=self.CONVERT)
        self.menu.add_command(label="CONVERT AND PLOT",command=self.CONVERT_AND_PLOT)
	self.menu.add_command(label="CHANGE DIRECTORY",command=self.FOLDER)
	self.menu.add_command(label="HELP",command=self.HELP)
	self.menu.add_command(label="QUIT",command=self.EXIT)
        self.l1=Label(self.win,text="START")

        # TREES
        self.tree = tkt.Tree(self.win,'./Test/Data','FLUKA_DIR',get_contents_callback=get_contents)

	self.canv_logo = Canvas(self.win,width=600,height=300)
        ############################################
	self.grid()
	self.l1.grid(column=0,row=0, sticky=NE+SW)
	self.tree.grid(column = 0, row = 1, rowspan = 5, sticky=NE+SW)
	self.canv_logo.grid(column=2,row=3)
	self.logo = PhotoImage(file="floot.gif")
	self.canv_logo.image = self.logo
 

	self.canv_logo.create_image(290,169,image=self.logo)
        #Configuration
        self.win.configure(menu=self.menu)     
        self.tree.configure(background='#EEEEEE', relief='sunken',borderwidth=3)
        self.tree.root.expand()

	self.win.rowconfigure(0, minsize=10)
        self.win.rowconfigure(1, minsize=300)
        self.win.rowconfigure(2, minsize=10)
        self.win.rowconfigure(3, minsize=300)
        self.win.rowconfigure(4, minsize=10)
 
        self.win.columnconfigure(0,minsize=200)
        self.win.columnconfigure(1,minsize =500)
	self.win.columnconfigure(2,minsize=500)
      
	self.tree.focus_set()
     ##############################################
      #FUNCTOINS
    def LOAD(self, plot=True): # plot True jezeli chcemy dodatkowo plotowac, inaczej False

       self.file = self.tree.cursor_node().get_label()
       if(self.file[-4:] == ".lis"):
        self.STATUS("PLOTTING")
        MGR = sf2r_manager( False  , True) #DEBUG = False API = True
        plots = MGR.run_path(self.folder,self.file) # tu wywala TH1F'y
        

        if self.canvas:
	   for i in range (self.number):
               self.canvas[0][i].get_tk_widget().destroy()
               self.TOOLBAR[i].destroy()  
               pass   

                       

        self.canvas=[]
        self.TOOLBAR=[]
       
        if plot == False:
            self.STATUS("FILE " +self.file+" ONLY CONVERTED") 
            return  
	
        self.canvas.append(plot_3d_2canvas(plots[0],self.win))
	self.number=len(self.canvas[0])

        self.canvas[0][0].get_tk_widget().grid(row=1,column=1)
        self.TOOLBAR.append(NavigationToolbar2TkAgg(self.canvas[0][0],self.win))
        self.TOOLBAR[0].grid(row=2,column=1)
  	if(len(self.canvas[0])>1):
         self.canvas[0][1].get_tk_widget().grid(row=3,column=1)
         self.TOOLBAR.append(NavigationToolbar2TkAgg(self.canvas[0][1],self.win))
         self.TOOLBAR[1].grid(row=4,column=1)
        if(len(self.canvas[0])>2):
         self.canvas[0][2].get_tk_widget().grid(row=1,column=2)
         self.TOOLBAR.append(NavigationToolbar2TkAgg(self.canvas[0][2],self.win))
         self.TOOLBAR[2].grid(row=2,column=2)   
        self.tree.focus_set()
       self.STATUS("FILE " +self.file+" CONVERTED AND PLOTTED") 
       self.tree.focus_set()

    def FOLDER(self):
      self.tree.delete(0,END)
      folder=tkFileDialog.askdirectory()
      if(folder!='' and isinstance(folder,str)):
       self.folder=folder
       self.tree = tkt.Tree(self.win,self.folder,"FLUKA_DIR",get_contents_callback=get_contents)
       self.tree.configure(background='#EEEEEE', relief='sunken',borderwidth=3)
       self.tree.grid(column = 0, row = 1, rowspan = 5, sticky=NE+SW)
       self.tree.root.expand()
       self.STATUS("NEW DIRECTORY SELECTED")

    def STATUS(self,string):
        self.l1.configure(text=string)
	self.tree.focus_set()

    def EXIT(self):
        exit()    

    def CONVERT(self):
        self.LOAD(plot=False)
	self.tree.focus_set()

    def CONVERT_AND_PLOT(self):
        self.LOAD(plot=True)
	self.tree.focus_set()
   
    def HELP(self):
	tkMessageBox.showinfo("Help info","Use your arrow keys to choose file\nENTER to confirm your choice\nYou can only convert this file to ROOT format by clicking CONVERT\nOr convert it and plot, by clicking CONVERT AND PLOT")
	self.tree.focus_set()
   


if __name__ == "__main__":
    root=Tk()
    GUI(root)
    root.mainloop()   
