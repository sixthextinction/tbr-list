#------------------------------------------------------------------------------------------------------------------------------------------------------------------
# simple TBR (books to-be-read) list
# coding conventions : 
#   1) underscore separated variables_like_these for local variables in scope only within local functions
#       camelCase for everything else
#   2) class names start in caps

# Todo : 
#   scrollbar should move down automatically when an entry goes past initial window
#   prevent duplicate entries (have Name and Author together be primary keys?)
#   try/catch all SQL
#   hover over book name to see cover and description grabbed from internet,
#   click to go to goodreads link in system default browser
#   order SQL-retrieved results by something

#------------------------------------------------------------------------------------------------------------------------------------------------------------------
from Tkinter import *
import tkMessageBox
import sqlite3
import urllib2
import xml.etree.ElementTree as ET
#------------------------------------------------------------------------------------------------------------------------------------------------------------------
# our custom Label class, inheriting from the base Tkinter Label class
class BookNameLabel(Label):
    def __init__(self, master, url, *args, **kwargs):           # wont work if master isnt included
        Label.__init__(self, master, *args, **kwargs)           # if master isnt included, all new labels will go to a weird phantom zone between the two frames
        # self.master = master
        self.url = url
        self.bind("<Enter>", self.onHover)
    def onHover(self,event):
        pass
        #TODO : popup window with pictures and stuff
        # print "TEST: Mouse hovering over %r" % event.widget
        # print "URL =  %r" % event.widget.url
#------------------------------------------------------------------------------------------------------------------------------------------------------------------
class App:

    def __init__(self, master):

        # a 1/0 flip to implement alternating bg/fg (styles) for the todo list
        self.flag           = 1

        # dict of book - author mapping
        self.books_authors = {}

        # hold list of labels.
        self.labels          = []

        # hold list of styles for alternating between
        self.styles         = [{"bg":"#3B653D", "fg":"white"},{"bg":"lightgrey", "fg":"#3B653D"}]


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
        
        # self.testBtn            = Button(self.entryFrame, text = "DEBUG : show self.labels list",  command = self.list_books).pack(side = BOTTOM, fill = X)
        self.bookEntryField     = Text(self.entryFrame, borderwidth = 5, relief = RIDGE, height = 2, width = 200, font = ('Courier','12'))
        self.authorEntryField   = Text(self.entryFrame, borderwidth = 5, relief = RIDGE, height=2, width=200, font=('Courier', '12'))


        # populate gui with books pulled from persistent storage
        # for book in self.labels:
        #     book_added = Label(self.listFrame, text = book, font = ('Courier','14'), bg = choice_of_style["bg"], fg = choice_of_style["fg"]).pack(side = TOP, fill = X)
        
        # pack tkinter widgets
        self.listCanvas.pack(side = TOP, fill = BOTH, expand = 1)
        self.scrollbar.pack(side = RIGHT, fill = Y)

        self.canvas_frame = self.listCanvas.create_window((0,0), window = self.listFrame, anchor = 'n') # this creates a new window inside the canvas with listFrame in it


        self.authorEntryField.pack(padx=10, pady = (0,20), side=BOTTOM, fill=X)
        Label(self.entryFrame, text="Author name here", anchor = 'w').pack(side = BOTTOM, padx = 10, fill=X)
        self.bookEntryField.pack(padx=10, pady = (0,0), side = BOTTOM, fill=X)
        Label(self.entryFrame, text="Book name here", anchor = 'nw').pack(side = BOTTOM, padx = 10, fill=X)
        self.entryFrame.pack(side= BOTTOM, fill = X) 

        # fill default text (NO NEED FOR THESE)
        # self.bookEntryField.insert(1.0,"Book name here")
        # self.authorEntryField.insert(1.0, "Author name here")
        self.bookEntryField.focus_set()
        

        # event handling
        self.authorEntryField.bind("<Return>", self.entry)                  # enter pressed on text entry
        # doesnt work yet self.bookEntryField.bind("<Return>", self.shiftFocus)               # shift focus to author textfield on Return
        self.bookEntryField.bind("<Tab>", self.shiftFocus)                  # shift focus to author textfield on Tab
        self.master.bind("<Configure>", self.dynamicScrollregionAdjust)     # dynamically adjust scrollregion on window resize/expand (needed for scrolling after labels added exceeds windowheight)
        self.listCanvas.bind("<Configure>", self.dynamicWidthAdjust)        # makes labels dynamically expand/shrink to fill out X in canvas without us having to pack the listFrame
        self.master.bind_all("<MouseWheel>", self.mouseWheelScroll)         # mouse wheel scrolling under windows
        self.master.bind_all("<Button-4>", self.mouseWheelScroll)           # mouse wheel scroll up under Linux based
        self.master.bind_all("<Button-5>", self.mouseWheelScroll)           # mouse wheel scroll down under Linux based
        self.bookEntryField.bind("<Button-1>", self.clearTextField)         # clear book entry field when textfield clicked with default text in it
        self.authorEntryField.bind("<Button-1>", self.clearTextField)       # clear author entry field when textfield clicked with default text in it
        #self.master.bind_class("Label", "<Enter>", self.onHover)           # already done in custom Label class


        # db stuff
        self.db_conn = sqlite3.connect("tbr.db")
        self.db_conn.text_factory = str #for ryu murakami and utf-8 characters?
        self.db_cursor = self.db_conn.cursor()
        self.db_conn.execute(
            "CREATE TABLE IF NOT EXISTS Tbr (Name TEXT NOT NULL, Author TEXT NOT NULL, PRIMARY KEY (Name, Author))")
        self.db_cursor.execute("SELECT Name, Author FROM Tbr")
        # name = row[0], author = row[1]
        for row in self.db_cursor:
            self.books_authors[row[0]] = row[1]
        for item in self.books_authors:
            labelText = "%s by %s" % (item, self.books_authors[item])  # when deleted, delete from database by splitting text along " by "
            # create labels out of these
            self.createLabel(labelText)


#------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def clearTextField(self, event):
        if "name here" in event.widget.get(1.0, END):
            event.widget.delete(1.0, END) # Assuming its a text field, so delete method used
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # event handling for return/enter in text entry field
    def entry(self, event):
        # strip() to remove leading and trailing whitespaces
        book_name = self.bookEntryField.get(1.0, END).strip()
        author_name = self.authorEntryField.get(1.0, END).strip()

        #--------------------------------------
        my_api_key = "eogNanr9wqazrV86EAypw"
        url = 'https://www.goodreads.com/search.xml?key=' + my_api_key
        q_title     = book_name
        q_author    = author_name
        q = q_title + " - " + q_author

        final_url = url+"&q="+q.replace(' ','+')
        xml_obj = urllib2.urlopen(final_url)
        tree = ET.parse(xml_obj)
        root = tree.getroot()

        book_results = root.findall('./search/results/work')

        for result in book_results: # WARNING : later sections will cause issues if there are no results returned here i.e. this loop skipped
            book_id         =   result.find('best_book/id')
            title           =   result.find('best_book/title').text.encode("utf-8")             # need explicit encoding for results with non-unicode characters e.g ryu murakami
            author_id       =   result.find('best_book/author/id').text
            author          =   result.find('best_book/author/name').text.encode("utf-8")       # need explicit encoding for results with non-unicode characters e.g ryu murakami
            image_url       =   result.find('best_book/image_url').text

            # if author == "William Gibson" and title == "Neuromancer":
            if author.lower() == q_author.lower() and title.lower() == q_title.lower():
                print "[EXACT MATCH]"
                print("[{}] {} - [{}] {}").format(book_id, title, author_id, author)
                print("https://www.goodreads.com/book/show/{}").format(book_id)
                book_url = "https://www.goodreads.com/book/show/{}".format(book_id) # <-- book url that gets passed. Same string as line above.
                print("https://www.goodreads.com/author/show/{}").format(author_id)
                print("IMAGE URL : {}").format(image_url)
                break
            else:
                tkMessageBox.showwarning("No Exact Match Found", "Using First Match")
                print "[DISPLAYING FIRST MATCH]"
                print("[{}] {} - [{}] {}").format(book_id, title, author_id, author)
                print("https://www.goodreads.com/book/show/{}").format(book_id)
                print("https://www.goodreads.com/author/show/{}").format(author_id)
                print("IMAGE URL : {}").format(image_url)
                break
        #-------------------------------------
        # if results WERE returned via API,
        if book_results:        
            # overwrite book_name and author_name with Goodreads API returns instead    
            book_name = title
            author_name = author
        # if NO results were returned
        else:
            # issue statement to console about it
            print "WARNING : Goodreads API search for \'%s by %s\' returned no results." % (book_name, author_name)
            print "Using entered values as is"
        # make a label only if both fields have nonzero lengths (no empty book/author names)
        if len(book_name) > 0 and len(author_name) > 0:
            label_text = book_name + " by " + author_name
            self.createLabel(label_text) # pass over the book URL as well. CAN'T right now; add column for it in db first.
            # SQL Query to add book_name and author_name to database
            self.db_cursor.execute("INSERT INTO Tbr(Name, Author) VALUES (?, ?)", (book_name, author_name))  # do it this way instead of directly using raw strings to prevent SQL Injection attacks
            self.db_conn.commit()
        # clear out the two fields
        self.bookEntryField.delete(1.0, END)
        self.authorEntryField.delete(1.0, END)

#------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def dynamicScrollregionAdjust(self,event):
        self.listCanvas.configure(scrollregion = self.listCanvas.bbox("all"))
        self.listCanvas.yview_moveto(1.0)  # auto-scroll to bottom of screen # bad solution. You dont want to scroll down when the user has scrolled up...
#------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # handles click to delete a book from TBR
    def delete(self, event):
        user_choice = tkMessageBox.askyesno("Delete", "Delete this book from your TBR?") # todo: display book name instead
        if user_choice: # "Yes" = True
            self.labels.remove(event.widget)
            # get text, split in two to use in SQL query
            text = event.widget['text']
            book_name = text.split(" by ")[0]
            author_name = text.split(" by ")[1]
            # sql query to delete this
            self.db_cursor.execute("DELETE FROM Tbr WHERE Name = ? AND Author = ?", (book_name, author_name)) # do it this way instead of directly using raw strings to prevent SQL Injection attacks
            self.db_conn.commit()
            # remove the label widget itself
            event.widget.destroy()
            # recolor widgets to preserve alternating color scheme
            self.recolor_labels()

#------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # entry point, holds binding
    def start(self):
        self.bookEntryField.bind("<Return>", self.entry)
#------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # recolors labels to preserve alternating color scheme 
    def recolor_labels(self):
        for index, book in enumerate(self.labels):  # remember that self.labels holds only label widget instances
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
    # For debug. Prints to console members of self.labels list, if needed
    def list_books(self):
        print "------------------------"
        for book in self.labels:
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
    def createLabel(self, labelText, book_url= None): # cant add book url's yet; make a column for it in the database
        # to alternate color schemes based on flag
        choice_of_style = self.pickColorScheme()
        # add the label, pack it too
        book_added = BookNameLabel(self.listFrame, url = book_url, text=labelText, font=('Courier', '14'), bg=choice_of_style["bg"],
                           fg=choice_of_style["fg"], wraplength = 400)
        book_added.pack(side=TOP, fill=X)
        book_added.bind("<Button-1>", self.delete)
        # store books
        self.labels.append(book_added)  # append book_added if need to store in list as Label instances instead
        # delete entry field after return is hit
#------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # on enter or tab on book textfield, shift focus to author textfield
    def shiftFocus(self, event):
        self.authorEntryField.focus_set()
        return "break"
#------------------------------------------------------------------------------------------------------------------------------------------------------------------

root = Tk()
app = App(root)
app.start()
root.mainloop()