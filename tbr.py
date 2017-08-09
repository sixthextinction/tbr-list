#------------------------------------------------------------------------------------------------------------------------------------------------------------------
# simple TBR (books to-be-read) list
# coding conventions : 
#   1) underscore separated variables_like_these for local variables in scope only within local functions
#       camelCase for everything else
#   2) class names start in caps

# Todo : 
#   try/catch all SQL
#   hover over book name to see cover and description grabbed from internet,
#   order SQL-retrieved results by date added

#------------------------------------------------------------------------------------------------------------------------------------------------------------------
from Tkinter import *
import webbrowser
import tkMessageBox
import sqlite3
import re
import urllib2
import xml.etree.ElementTree as ET
from PIL import Image, ImageTk

root = Tk()
hover_window = Toplevel(root)
hover_window.state('withdrawn')
#------------------------------------------------------------------------------------------------------------------------------------------------------------------
# our custom Label class, inheriting from the base Tkinter Label class
class BookNameLabel(Label):
    def __init__(self, master, book_url, author_url, image_url, *args, **kwargs):           # wont work if master isnt included
        Label.__init__(self, master, *args, **kwargs)           # if master isnt included, all new labels will go to a weird phantom zone between the two frames
        # self.master = master
        self.book_name  = self['text'].split(' by ')[0]
        self.author_name  = self['text'].split(' by ')[1]
        self.book_url   = book_url
        self.author_url = author_url
        self.image_url  = image_url
        self.bind("<Enter>", self.onHover)


    # hover on list labels callback
    def onHover(self,event):
        # fetch global var hover_window and destroy it, to avoid duplicate hover_windows for what were gonna do
        global hover_window
        hover_window.destroy()

        # then create a new one
        global root
        hover_window = Toplevel(root)
        offset_x = root.winfo_rootx() + root.winfo_width()
        offset_y = root.winfo_rooty()
        hover_window.geometry("+%d+%d" % (offset_x, offset_y - 31)) # x always off by 8 pixels, y a;lways off by 30-32. Dont know why.

        # create two frames for this new window
        frame_coverart  = Frame(hover_window)
        frame_details   = Frame(hover_window)
        # pack em
        frame_coverart.grid(row = 0, column = 0)
        frame_details.grid(row = 0, column = 1)

        # grab cover image and turn it into a label
        image_data      = urllib2.urlopen(self.image_url)
        image           = Image.open(image_data)
        image.thumbnail((512,512))
        image_for_tk    = ImageTk.PhotoImage(image)
        img_label       = Label(frame_coverart, image = image_for_tk)
        img_label.img   = image_for_tk       

        # make hyperlink labels out of the rest of the data
        label_book_name     = Label(frame_details, text = self.book_name, fg = 'blue', cursor = 'hand2')
        label_author_name   = Label(frame_details, text = self.author_name, fg = 'blue', cursor = 'hand2')
        #book_description will go here too once scraped

        # pack em all to finish this window off
        label_book_name.grid()
        label_author_name.grid()
        img_label.grid()

        # set up the link label callbacks
        label_book_name.bind("<Button-1>", lambda event : self.openLink(event, self.book_url))
        label_author_name.bind("<Button-1>", lambda event : self.openLink(event, self.author_url))

    # callback for link labels
    def openLink(self, event, url):
        webbrowser.open_new(url)

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
        self.listCanvas.bind("<Enter>", self.killHoverWindow)               # destroy hover_window if mouse pointer enters anywhere but labels
        self.entryFrame.bind("<Enter>", self.killHoverWindow)               # destroy hover_window if mouse pointer enters anywhere but labels


        # db stuff
        self.db_conn = sqlite3.connect("tbr.db")
        self.db_conn.text_factory = str #for ryu murakami and utf-8 characters?
        self.db_cursor = self.db_conn.cursor()
        self.db_conn.execute(
            "CREATE TABLE IF NOT EXISTS Tbr (BookName TEXT NOT NULL, BookURL TEXT, AuthorName TEXT NOT NULL, AuthorURL TEXT, ImageURL TEXT, PRIMARY KEY (BookName, AuthorName))")
        self.db_cursor.execute("SELECT BookName, BookURL, AuthorName, AuthorURL, ImageURL FROM Tbr")
        # name = row[0], url = row[1], and so on
        # for row in self.db_cursor:
        #     self.books_authors[row[0]] = row[1]
        # for item in self.books_authors:
        for row in self.db_cursor:
            # labelText = "%s by %s" % (item, self.books_authors[item])  # when deleted, delete from database by splitting text along " by "
            label_book_and_authorname   = "%s by %s" % (row[0], row[2])
            label_book_url              = row[1]
            label_author_url            = row[3]
            label_image_url             = row[4]
            # create labels out of these
            self.createLabel(label_book_and_authorname, label_book_url, label_author_url, label_image_url)


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
            book_id         =   result.find('best_book/id').text
            title           =   result.find('best_book/title').text.encode("utf-8")             # need explicit encoding for results with non-unicode characters e.g ryu murakami
            author_id       =   result.find('best_book/author/id').text
            author          =   result.find('best_book/author/name').text.encode("utf-8")       # need explicit encoding for results with non-unicode characters e.g ryu murakami
            image_url       =   result.find('best_book/image_url').text

            regex_title = r'\w*{}\w*'.format(q_title)
            regex_author = r'\w*{}\w*'.format(q_author)

            # if author == "William Gibson" and title == "Neuromancer":
            if author.lower() == q_author.lower() and title.lower() == q_title.lower(): #cant convert to lowercase for non unicode characters; will fail every time for those
                print "[EXACT MATCH]"
                print("[{}] {} - [{}] {}").format(book_id, title, author_id, author)
                # print("https://www.goodreads.com/book/show/{}").format(book_id)
                book_url = "https://www.goodreads.com/book/show/{}".format(book_id) # <-- book url that gets passed. Same string as line above.
                print book_url
                # print("https://www.goodreads.com/author/show/{}").format(author_id)
                author_url = "https://www.goodreads.com/author/show/{}".format(author_id)
                # print("IMAGE URL : {}").format(image_url)
                break
            # elif with re goes here
            elif (re.findall(regex_title, title)) or (re.findall(regex_author,author)):
                tkMessageBox.showwarning("Partial Match Found", "Using Best Match.")
                print "[DISPLAYING BEST MATCH]"
                print("[{}] {} - [{}] {}").format(book_id, title, author_id, author)
                # print("https://www.goodreads.com/book/show/{}").format(book_id)
                book_url = "https://www.goodreads.com/book/show/{}".format(book_id) # <-- book url that gets passed. Same string as line above.
                print book_url
                # print("https://www.goodreads.com/author/show/{}").format(author_id)
                author_url = "https://www.goodreads.com/author/show/{}".format(author_id)
                # print("IMAGE URL : {}").format(image_url)
                break
            # Edge cases (mostly due to goodreads screwing up /eyeroll)
            else:
                tkMessageBox.showerror("No Match Of Note Found", "Using First Match.")
                print "[DISPLAYING FIRST MATCH]"
                print("[{}] {} - [{}] {}").format(book_id, title, author_id, author)
                # print("https://www.goodreads.com/book/show/{}").format(book_id)
                book_url = "https://www.goodreads.com/book/show/{}".format(book_id) # <-- book url that gets passed. Same string as line above.
                print book_url
                # print("https://www.goodreads.com/author/show/{}").format(author_id)
                author_url = "https://www.goodreads.com/author/show/{}".format(author_id)
                # print("IMAGE URL : {}").format(image_url)
                break
        #-------------------------------------
        # if results WERE returned via API,
        if book_results:        
            # overwrite book_name and author_name with Goodreads API returns instead    
            book_name = title
            author_name = author
        # if NO results were returne
        else:
            # issue statement to console about it
            err_message = "WARNING : Goodreads API search for \'%s by %s\' returned no results." % (book_name, author_name)
            err_message+= "\nUsing entered values as is."

            tkMessageBox.showwarning("No results", err_message)

        # make a label only if both fields have nonzero lengths (no empty book/author names)
        if len(book_name) > 0 and len(author_name) > 0:
            label_text = book_name + " by " + author_name
            self.createLabel(label_text, book_url, author_url, image_url) # pass over the book URL as well. CAN'T right now; add column for it in db first.
            # SQL Query to add book_name and author_name to database
            self.db_cursor.execute("INSERT INTO Tbr(BookName, BookURL, AuthorName, AuthorURL, ImageURL) VALUES (?, ?, ?, ?, ?)", (book_name, book_url, author_name, author_url, image_url))  # do it this way instead of directly using raw strings to prevent SQL Injection attacks
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
            self.db_cursor.execute("DELETE FROM Tbr WHERE BookName = ? AND AuthorName= ?", (book_name, author_name)) # do it this way instead of directly using raw strings to prevent SQL Injection attacks
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
    def createLabel(self, labelText, book_url, author_url, image_url): # cant add book url's yet; make a column for it in the database
        # to alternate color schemes based on flag
        choice_of_style = self.pickColorScheme()
        # add the label. pass bookname, authorname, bookurl, authorurl, imageurl as well
        book_added = BookNameLabel(self.listFrame, book_url = book_url, author_url = author_url, image_url = image_url, text=labelText, font=('Courier', '14'), bg=choice_of_style["bg"],
                           fg=choice_of_style["fg"], wraplength = 400)
        book_added.pack(side=TOP, fill=X)
        book_added.bind("<Button-1>", self.delete)
        # store books as MyLabel instances
        self.labels.append(book_added)  
        # delete entry field after return is hit
#------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # on enter or tab on book textfield, shift focus to author textfield
    def shiftFocus(self, event):
        self.authorEntryField.focus_set()
        return "break"
#------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def killHoverWindow(self, event):
        global hover_window
        hover_window.destroy()
#------------------------------------------------------------------------------------------------------------------------------------------------------------------

app = App(root)
app.start()
root.mainloop()