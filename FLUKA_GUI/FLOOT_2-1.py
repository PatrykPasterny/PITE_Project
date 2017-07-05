import ROOT
import matplotlib
import tkMessageBox
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
from Tkinter import *
import tkFileDialog
from sf2rconverter.root2tk import *
from sf2rconverter.sf2r_lib import sf2r_manager, plot_1d, plot_2d, plot_3d
import sf2rconverter.sf2rconverter
from ROOT import TFile
import tkMessageBox
import tkTree as tkt
import os
from os import *
import subprocess as sub




def get_contents(node):
	path=os.path.join(*node.full_id())
	for filename in sorted(os.listdir(path)):
		full=os.path.join(path, filename)
		folder=0
    		if os.path.isdir(full):
			folder=1
		if (folder== 0 and (filename[-4:]==".lis" or filename[-4:]==".dat" or filename[-5:]==".root")) or folder == 1: #
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
		self.menu.add_command(label="PLOT", command=self.PLOT)
		self.menu.add_command(label="CONVERT AND PLOT",command=self.CONVERT_AND_PLOT)
		self.menu.add_command(label="CONVERT ALL DIRECTORY", command=self.CONVERT_ALL_DIRECTORY)
		self.menu.add_command(label="CHANGE DIRECTORY",command=self.FOLDER)
		self.menu.add_command(label="HELP",command=self.HELP)
		self.menu.add_command(label="QUIT",command=self.EXIT)
		self.l1=Label(self.win,text="START")

		# TREES
		self.tree = tkt.Tree(self.win,'./Test/Data','FLUKA_DIR',get_contents_callback=get_contents)

		self.canv_logo = Canvas(self.win,width=400,height=200)
		############################################
		self.grid()
		self.l1.grid(column=0,row=0, sticky=NE+SW)
		self.tree.grid(column = 0, row = 1, rowspan = 3, sticky=NE+SW)
		self.canv_logo.grid(column=0,row=4, rowspan =2, sticky=N+S+W+E)
		self.logo = PhotoImage(file="floot1.gif")
		self.canv_logo.image = self.logo
 

		self.canv_logo.create_image(190,105,image=self.logo)
		#Configuration
		self.win.configure(menu=self.menu)
		self.tree.configure(background='#EEEEEE', relief='sunken',borderwidth=3)
		self.tree.root.expand()

		self.tree.focus_set()
		##############################################
		#FUNCTOINS
	def layouts(self, histo_num):

		self.win.rowconfigure(0, minsize=10)
		self.win.rowconfigure(1, minsize=200)
		self.win.rowconfigure(2, minsize=10)
		self.win.rowconfigure(3, minsize=200)
		self.win.rowconfigure(4, minsize=10)
		self.win.rowconfigure(5, minsize=200)

		self.win.columnconfigure(0, minsize=100)
		self.win.columnconfigure(1, minsize=1300)

		if (histo_num == 1):
			self.canvas[0][0].get_tk_widget().grid(row = 1, column = 1,rowspan = 3)
			self.TOOLBAR.append(NavigationToolbar2TkAgg(self.canvas[0][0], self.win))
			self.TOOLBAR[0].grid(row = 4, column = 1, sticky = N+S)

		elif (histo_num == 2):
			self.canvas[0][0].get_tk_widget().grid(row = 1, column = 1)
			self.canvas[0][1].get_tk_widget().grid(row = 3, column = 1)

			self.TOOLBAR.append(NavigationToolbar2TkAgg(self.canvas[0][0], self.win))
			self.TOOLBAR[0].grid(row = 2, column = 1, sticky = N+S)
			self.TOOLBAR.append(NavigationToolbar2TkAgg(self.canvas[0][1], self.win))
			self.TOOLBAR[1].grid(row = 4, column = 1, sticky = N+S)

		else:
			ERROR="Nie planuje."
			return ERROR
		

	def LOAD(self, plot=True, all=False): # plot True jezeli chcemy dodatkowo plotowac, inaczej False

		if all==True:
			self.STATUS("ALL_DIRECTIORY_CONVERTED")
			string = "python ./sf2rconverter/sf2rconverter.py -p " + self.folder
			print string
			os.system(string)
			print "All files converted."
			tkMessageBox.showinfo("SUCCESS", "All files converted.")
			self.tree.focus_set()

		if(self.file[-4:] == ".lis" or self.file[-4:]==".dat" or self.file[-5:]==".root"):
			self.STATUS("PLOTTING")
			MGR = sf2r_manager( False  , True) #DEBUG = False API = True

			if (self.file[-4:] == ".lis" or self.file[-4:]==".dat"):
				plots = MGR.run_path(self.folder,self.file) # tu wywala TH1F'y
				file = None
				if not os.path.exists( 'fluka2root_one_detector.root' ):
					file = TFile( 'fluka2root_one_detector.root', 'new' )
				else:
					file = TFile( 'fluka2root_one_detector.root', 'recreate' )

				for chart in plots:
					if chart.get_type() == '1DPLOT' or chart.get_type() == '2DPLOT':
						chart.get_histo().Write()
					else:
						histos=chart.get_histo()
						for histo in histos:
							histo.Write()

				file.Close()

			else:
				f = ROOT.TFile.Open(self.file)
				keys = f.GetListOfKeys()
				plots=[]
				p=[]
				for el in keys:
					p.append(f.Get(el.GetName()))
					plots.append(p)

			if plot == False:
				self.STATUS("FILE " +self.file+" ONLY CONVERTED")

			else:
				if self.canvas:
					for i in xrange (len(self.canvas[0])):
						self.canvas[0][i].get_tk_widget().destroy()
						if len(self.TOOLBAR)>0:
							self.TOOLBAR[i].destroy()  
						pass

				self.canvas=[]
				self.TOOLBAR=[]


				if isinstance(plots[0],plot_1d):
					self.canvas.append(plot_1d_2canvas(plots[0],self.win))
				elif isinstance(plots[0],plot_2d):
					self.canvas.append(plot_2d_2canvas(plots[0],self.win))
				elif isinstance(plots[0],plot_3d):
					self.canvas.append(plot_3d_2canvas(plots[0],self.win))
				else:
					output = plot_3d_2canvas(plots[0],self.win)
					if type(output) == str:
						print output
						self.STATUS("ERROR")
						tkMessageBox.showinfo("ERROR", "The amount of histos in .root file should be less than 9.")
					else:
						self.canvas.append(output)#TODO!!!!!  

				if self.file[-4:] == ".lis" or self.file[-4:]==".dat" or type(output)!=str:
					self.number=len(self.canvas[0])
					self.layouts(self.number)
					if self.file[-5:]==".root":
						self.STATUS("FILE " +self.file+" PLOTTED")
					else:
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
		self.file = self.tree.cursor_node().get_label()
		if self.file[-4:]==".lis" or self.file[-4:]==".dat":
			self.LOAD(plot=False)
		else:
			tkMessageBox.showinfo("ERROR", "Option CONVERT converts only .lis and .dat files")
			self.tree.focus_set()

	def PLOT(self):
		self.file = self.tree.cursor_node().get_label()
		if self.file[-5:]==".root":
			self.LOAD(plot=True)
		else:
			tkMessageBox.showinfo("ERROR", "Option PLOT plots only .root files")
		self.tree.focus_set()

	def CONVERT_AND_PLOT(self):
		self.file = self.tree.cursor_node().get_label()
		if self.file[-4:]==".lis" or self.file[-4:]==".dat":
			self.LOAD(plot=True)
		else:
			tkMessageBox.showinfo("ERROR", "Option CONVERT AND PLOT converts and plots only .lis and .dat files")
			self.tree.focus_set()

	def CONVERT_ALL_DIRECTORY(self):
		print "CONVERTING ONLY .lis AND .dat FILES"
		self.LOAD(plot=False,all=True)
		self.tree.focus_set()
	def HELP(self):
		tkMessageBox.showinfo("Help info","Use your arrow keys to choose file\nENTER to confirm your choice\nYou can only convert this file to ROOT format by clicking CONVERT,\n convert it and plot, by clicking CONVERT AND PLOT and plot ROOT files(You can plot maximum 9 ROOT plots on display so make sure that .root file consist less histos than 9). Click CONVERT ALL DIRECTORY to make .root file with histos from all given directory. By clicking CHANGE DIRECTORY you can change folder with data to process.")
		self.tree.focus_set()



if __name__ == "__main__":
	
	root=Tk()

	GUI(root)
	root.mainloop()

