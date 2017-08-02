#------------------------------------------------------------------------------------------------------------------------------------------------------------------
# simple TBR (books to-be-read) list
# coding conventions : 
#   1) underscore separated variables_like_these for local variables in scope only within local functions
#       camelCase for everything else
#   2) class names start in caps

# Todo : 
#   click to delete
#   prevent duplicate entries
#   author name how? (possible solution : have 2 entry fields for book name and author respectively, dont accept final entry without both)
#   hover over book name to see cover and description grabed from internet, 
#   click to go to goodreads link in system default browser

#------------------------------------------------------------------------------------------------------------------------------------------------------------------
from Tkinter import *
import tkMessageBox

class App:
#------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def __init__(self, master):

        # a 1/0 flip to implement alternating bg/fg (styles) for the todo list
        self.flag           = 1

        # hold list of books. 
        self.books          = []

        # hold list of styles for alternating between
        self.styles         = [{"bg":"lightgrey", "fg":"black"},{"bg":"black", "fg":"white"}]

        # window stuff
        self.master         = master
        self.master.title("TBR")
        self.master.geometry("480x640")
        

        # create widgets needed
        self.listCanvas     = Canvas(self.master)

        self.listFrame      = Frame(self.listCanvas)
        self.entryFrame     = Frame(self.master)

        self.scrollbar      = Scrollbar(self.listCanvas, orient = 'vertical')
        self.listCanvas.configure(yscrollcommand = self.scrollbar.set)
        self.scrollbar.configure(command = self.listCanvas.yview)
        
        self.testBtn        = Button(self.entryFrame, text = "DEBUG : show self.books list",  command = self.list_books).pack(side = BOTTOM, fill = X)
        self.entryField     = Text(self.entryFrame, height = 2, width = 200, font = ('Courier','12'))


        # add a dummy book
        #dummy_book = self.books.append("DUMMY_BOOK")


        # populate gui with books pulled from persistent storage
        # for book in self.books:
        #     book_added = Label(self.listFrame, text = book, font = ('Courier','14'), bg = choice_of_style["bg"], fg = choice_of_style["fg"]).pack(side = TOP, fill = X)
        
        # pack tkinter widgets
        self.listCanvas.pack(side = TOP, fill = BOTH, expand = 1)
        self.scrollbar.pack(side = RIGHT, fill = Y)

        self.canvas_frame = self.listCanvas.create_window((0,0), window = self.listFrame, anchor = 'n') # this creates a new window inside the canvas with listFrame in it

        self.entryField.pack(padx=10, pady=20, side = BOTTOM, fill = X)
        self.entryFrame.pack(side= BOTTOM, fill = X) 
       
        self.entryField.focus_set()
        

        # event handling
        self.entryField.bind("<Return>", self.entry)                        # enter pressed on text entry
        self.master.bind("<Configure>", self.dynamicScrollregionAdjust)     # dynamically adjust scrollregion on window resize/expand (needed for scrolling after labels added exceeds windowheight)
        self.listCanvas.bind("<Configure>", self.dynamicWidthAdjust)        # makes labels dynamically expand/shrink to fill out X in canvas without us having to pack the listFrame
        self.master.bind_all("<MouseWheel>", self.mouseWheelScroll)         # mouse wheel scrolling under windows
        self.master.bind_all("<Button-4>", self.mouseWheelScroll)            # mouse wheel scroll up under Linux based
        self.master.bind_all("<Button-5>", self.mouseWheelScroll)            # mouse wheel scroll down under Linux based
#------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # event handling for return/enter in text entry field
    def entry(self, event):

        # to alternate color schemes based on flag
        choice_of_style = self.pickColorScheme()
        # strip() to remove leading and trailing whitespaces
        text_entered = self.entryField.get(1.0, END).strip()
        if len(text_entered) > 0:
            # add the label, pack it too
            book_added = Label(self.listFrame, text = text_entered, font = ('Courier','14'), bg = choice_of_style["bg"], fg = choice_of_style["fg"])
            book_added.pack(side = TOP, fill = X)
            book_added.bind("<Button-1>", self.delete)
            # store books
            self.books.append(book_added) # append book_added if need to store in list as Label instances instead
            # delete entry field after return is hit
            self.entryField.delete(1.0, END)
#------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def dynamicScrollregionAdjust(self,event):
        self.listCanvas.configure(scrollregion = self.listCanvas.bbox("all"))
#------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # handles click to delete a book from TBR
    def delete(self, event):
        user_choice = tkMessageBox.askyesno("Delete", "Delete this book from TBR?") # todo: display book name instead
        if user_choice: # "Yes" = True
            self.books.remove(event.widget)
            event.widget.destroy()
            # recolor widgets to preserve alternating color scheme
            self.recolor_labels()

#------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # entry point, holds binding
    def start(self):
        self.entryField.bind("<Return>", self.entry)
#------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # recolors labels to preserve alternating color scheme 
    def recolor_labels(self):
        for index, book in enumerate(self.books): #remember that self.books holds only label widget instances
            if (index%2) == 0:
                # color this label 
                choice_of_style = self.styles[1]
                self.flag = 0
            else:
                choice_of_style = self.styles[0]
                self.flag = 1
            book.configure(bg = choice_of_style["bg"], fg = choice_of_style["fg"])
#------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # dynamically adjust canvas_frame width to make sure stuff in that frame (our labels) always fill X
    def dynamicWidthAdjust(self, event):
        canvas_width = event.width      # width of window at this point in time
        self.listCanvas.itemconfig(self.canvas_frame, width = canvas_width)
#------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # For debug. Prints to console members of self.books list, if needed
    def list_books(self):
        print "------------------------"
        for book in self.books:
            print book
#------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # pick a color scheme to preserve alternating color scheme
    def pickColorScheme(self):
        if self.flag == 1:
            choice_of_style = self.styles[1]
            self.flag = 0
        else:
            choice_of_style = self.styles[0]
            self.flag = 1
        return choice_of_style
#------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # handle scrolling via mousewheel for windows and linux
    def mouseWheelScroll(self, event):
        if event.delta: # for windows, 120 = 1 unit
            self.listCanvas.yview_scroll(int(-1 * (event.delta/120)), "units")
        else:           # linux based, already in units, no such calculation needed
            if event.num == 5: # mouse-5 = scroll down
                scroll = -1
            else: # event.num == 4 (mouse-4), scroll up
                scroll = 1
            self.listCanvas.yview_scroll(scroll * "units")
#------------------------------------------------------------------------------------------------------------------------------------------------------------------


root = Tk()
app = App(root)
app.start()
root.mainloop()