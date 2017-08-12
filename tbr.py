# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------------------------------------------------------------------------------------------
# simple TBR (books to-be-read) list
# coding conventions : 
#   1) underscore separated variables_like_these for local variables in scope only within local functions
#       camelCase for everything else
#   2) class names start in caps

# Todo : 
#   try/catch all SQL
#   scraping description far too slow! Do it at entry/SQL insert stage and save into db instead of fetching every time

#------------------------------------------------------------------------------------------------------------------------------------------------------------------
from Tkinter import *
import webbrowser
import tkMessageBox
import sqlite3
import re
import urllib2
import os
import xml.etree.ElementTree as ET
from PIL import Image, ImageTk

root = Tk()
hover_window = Toplevel(root)
hover_window.state('withdrawn')
#------------------------------------------------------------------------------------------------------------------------------------------------------------------
# our custom Label class, inheriting from the base Tkinter Label class
class BookNameLabel(Label):
    #def __init__(self, master, book_url, author_url, image_url, *args, **kwargs):           
    def __init__(self, master, *args, **kwargs):                # wont work if master isnt included
        Label.__init__(self, master, *args, **kwargs)           # if master isnt included, all new labels will go to a weird phantom zone between the two frames
        # self.master = master
        self.book_name  = self['text'].split(' by ')[0]
        self.author_name  = self['text'].split(' by ')[1]

        self.bind("<Enter>", self.onHover)

#------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # hover on list labels callback
    # sql select to grab data and show it in new window
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
        frame_coverart.pack(side = LEFT)
        frame_details.pack(side = RIGHT)

        # sql prep
        db_conn = sqlite3.connect("Tbr.db")
        db_cursor = db_conn.cursor()

        # grab data. Remember, we already have bookname and authorname, which happen to be primary key, lucky for us. We'll need decsription and coverart path
        print "------------------------------------------------------------------"
        print "DEBUG : self.book_name = %r" % self.book_name
        print "DEBUG : self.author_name = %r" % self.author_name
        print "------------------------------------------------------------------"
        try:
            db_cursor.execute("SELECT BookDescription, ImagePath, BookURL, AuthorURL FROM Tbr WHERE BookName = ? and AuthorName = ?", (self.book_name, self.author_name))
        except sqlite3.Error as e:
            tkMessageBox.showerror("Database Error", e.args[0])

        result_set = db_cursor.fetchone()
        # grab book description (Interesting thought : I could do self.bookdescription and self.coverimage and then we wouldnt have to do the SQL select every time on hover. It'd be automatic for each MyLabel.)
        book_description = result_set[0]
        # print "------------------------------------------------------------------"
        # print "DEBUG : result_set[0] = %r" % result_set[0]
        # print "------------------------------------------------------------------"

        # grab cover image and turn it into a label
        image_path      = result_set[1]
        # print "------------------------------------------------------------------"
        # print "DEBUG : result_set[1] = %r" % result_set[1]
        # print "------------------------------------------------------------------"
        image_data      = Image.open(image_path)
        image_for_tk    = ImageTk.PhotoImage(image_data)

        label_image     = Label(frame_coverart, image = image_for_tk)
        label_image.img = image_for_tk

        # Grab book and author urls
        book_url = result_set[2]
        author_url = result_set[3]

        # make labels out of the rest of the data
        label_book_name     = Label(frame_coverart, font=('Calibri', '11', 'underline'), justify = LEFT, text = self.book_name, fg = 'blue', cursor = 'hand2', wraplength = 200)
        label_author_name   = Label(frame_coverart, font=('Calibri', '11', 'underline'), justify = LEFT, text = self.author_name, fg = 'blue', cursor = 'hand2', wraplength = 200)

        # add the description label
        label_description   = Label(frame_details, font=('Calibri', '11'), justify = LEFT,
            text = book_description, wraplength = 400)

        # pack em all to finish this window off
        label_book_name.grid(row=0,column=0, padx=10, pady=(10,0), sticky = W)
        label_author_name.grid(row=1,column=0, padx=10, pady=(0,10), sticky = W)
        label_description.grid(row=2,column=0, padx=10, pady=10, sticky = N+E+S+W)
        label_image.grid(padx=10, pady=10, sticky = N+E+S+W)
        # label_book_name.pack(side = TOP)
        # label_author_name.pack(side = LEFT)
        # label_description.pack(side = BOTTOM)
        # img_label.pack()

        # set up the link label callbacks
        label_book_name.bind("<Button-1>", lambda event : self.openLink(event, book_url))
        label_author_name.bind("<Button-1>", lambda event : self.openLink(event, author_url))
#------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # callback for link labels
    def openLink(self, event, url):
        webbrowser.open_new(url)

###################################################################################################################################################################
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
        self.bookEntryField     = Text(self.entryFrame, borderwidth = 5, relief = RIDGE, height = 2, width = 200, font = ('Calibri','12'))
        self.authorEntryField   = Text(self.entryFrame, borderwidth = 5, relief = RIDGE, height=2, width=200, font=('Calibri', '12'))


        # populate gui with books pulled from persistent storage
        # for book in self.labels:
        #     book_added = Label(self.listFrame, text = book, font = ('Courier','14'), bg = choice_of_style["bg"], fg = choice_of_style["fg"]).pack(side = TOP, fill = X)
        
        # pack tkinter widgets
        self.listCanvas.pack(side = TOP, fill = BOTH, expand = 1)
        self.scrollbar.pack(side = RIGHT, fill = Y)

        self.canvas_frame = self.listCanvas.create_window((0,0), window = self.listFrame, anchor = 'n') # this creates a new window inside the canvas with listFrame in it


        self.authorEntryField.pack(padx=10, pady = (0,20), side=BOTTOM, fill=X)
        Label(self.entryFrame, font = 'Calibri',text="Author name here", anchor = 'w').pack(side = BOTTOM, padx = 10, fill=X)
        self.bookEntryField.pack(padx=10, pady = (0,0), side = BOTTOM, fill=X)
        Label(self.entryFrame, font = 'Calibri',text="Book name here", anchor = 'nw').pack(side = BOTTOM, padx = 10, fill=X)
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
            "CREATE TABLE IF NOT EXISTS Tbr (BookName TEXT NOT NULL, BookURL TEXT, AuthorName TEXT NOT NULL, AuthorURL TEXT, ImageURL TEXT, BookDescription TEXT, ImagePath TEXT, CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (BookName, AuthorName))"
            )
        self.db_cursor.execute("SELECT BookName, BookURL, AuthorName, AuthorURL, ImageURL, BookDescription, ImagePath FROM Tbr ORDER BY CreatedAt ASC")
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
            label_image_url             = self.getHighResCover(label_image_url)
            label_book_description      = row[5]
            label_image_path            = row[6]
            # create labels out of these
            # self.createLabel(label_book_and_authorname, label_book_url, label_author_url, label_image_url, label_book_description, label_image_path)
            self.createLabel(label_book_and_authorname) # i.e. just the primary keys


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
            image_url       =   self.getHighResCover(image_url)
            book_description = "" # scrape after book_url is got
            image_path      = os.getcwd() + "\\" + title + ' - ' + author + ".png" # save as png to preemptively avoid format errors

            # get rid of weird characters that windows wont allow SEE TEST.PY FOR SOLUTION
            # regex = r'\\/\"\?<>\*\|' 
            # image_path      = re.sub(regex,'',image_path)

            # Now actually save the image to disk
            image_data      = urllib2.urlopen(image_url)
            image           = Image.open(image_data)
            image           = image.resize((308,475), Image.ANTIALIAS) # resize() returns a new image, so we'll have to store it
            try:
                image.save(image_path, 'PNG') # store image_path in db
            except IOError:
                print " ERROR : Couldn't save image as PNG. image_url = %r" % image_url

            regex_title = r'\w*{}\w*'.format(q_title)
            regex_author = r'\w*{}\w*'.format(q_author)

            # if-else section below is to get book_url and author_url

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
            # overwrite book_name and author_name with Goodreads API returns instead of what was obtaind via .get() from entry fields  
            book_name = title
            author_name = author
        # if NO results were returned
        else:
            # issue statement to console about it
            err_message = "WARNING : Goodreads API search for \'%s by %s\' returned no results." % (book_name, author_name)
            err_message+= "\nUsing entered values as is."
            # N/A values
            book_url = 'N/A'
            author_url = 'N/A'
            image_url = 'N/A'

            tkMessageBox.showwarning("No results", err_message)

        # scrape a bookdescription (obviously wont work if book_results returned nothing)
        page_source         = urllib2.urlopen(book_url)
        page_source         = page_source.read()
        book_description    = self.sanitizeFirstPass(page_source)
        book_description    = self.sanitizeSecondPass(book_description) 
        book_description    = self.sanitizeThirdPass(book_description)  # final thing. We swear.


        # make a label only if both fields have nonzero lengths (no empty book/author names)
        if len(book_name) > 0 and len(author_name) > 0:

            label_text = book_name + " by " + author_name
            # self.createLabel(label_text, book_url, author_url, image_url) # pass over the book URL as well. 
            self.createLabel(label_text) # only the primary key
            # SQL Query to add book_name and author_name to database
            try:
                self.db_cursor.execute("INSERT INTO Tbr(BookName, BookURL, AuthorName, AuthorURL, ImageURL, BookDescription, ImagePath) VALUES (?, ?, ?, ?, ?, ?, ?)", (book_name, book_url, author_name, author_url, image_url, book_description, image_path))  # do it this way instead of directly using raw strings to prevent SQL Injection attacks
                self.db_conn.commit()
            except sqlite3.Error as e:
                if "not unique" in e.args[0]:
                    tkMessageBox.showerror("Database Error", "This book already exists in your TBR.")

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
            try:
                self.db_cursor.execute("DELETE FROM Tbr WHERE BookName = ? AND AuthorName= ?", (book_name, author_name)) # do it this way instead of directly using raw strings to prevent SQL Injection attacks
                self.db_conn.commit()
            except sqlite3.Error as e:
                tkMessageBox.showerror("Database Error", e.args[0])
            # remove the label widget itself
            event.widget.destroy()
            # recolor widgets to preserve alternating color scheme. Works because we saved MyLabel instances in a list and we're retrieving them from there.
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
    #def createLabel(self, labelText, book_url, author_url, image_url, book_description, image_path): # cant add book url's yet; make a column for it in the database
    def createLabel(self, labelText):
        # to alternate color schemes based on flag
        choice_of_style = self.pickColorScheme()
        # add the label. pass bookname, authorname, bookurl, authorurl, imageurl as well
        # book_added = BookNameLabel(self.listFrame, book_url = book_url, author_url = author_url, image_url = image_url, book_description = book_description, image_path = image_path, text=labelText, font=('Calibri', '13'), bg=choice_of_style["bg"],
        #                    fg=choice_of_style["fg"], wraplength = 400)
        book_added = BookNameLabel(self.listFrame, text = labelText, font=('Calibri', '13'), bg=choice_of_style["bg"], fg = choice_of_style["fg"], wraplength = 400)
        book_added.pack(side=TOP, fill=X)
        book_added.bind("<Button-1>", self.delete)
        # store books as MyLabel instances. Needed for color scheming afterwards.
        self.labels.append(book_added)  
        # delete entry field after return is hit
#------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # on enter or tab on book textfield, shift focus to author textfield
    def shiftFocus(self, event):
        self.authorEntryField.focus_set()
        return "break"
#------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # destroy the side toplevel window when anything but its label is hovered over
    def killHoverWindow(self, event):
        global hover_window
        hover_window.destroy()
#------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # get higher res image if possible. Returns imageurl unchanged if not
    def getHighResCover(self, url):
        string = url
        new_url = ''
        words = string.split('/')
        for word in words:
            if word[-1:] == 'm' and word[-3:] != 'com':
                new_url = new_url + word[:-1] + 'l'
            else:
                new_url = new_url + word
            new_url = new_url + '/'
        new_url = new_url[:-1] #ditch the last /
        return new_url
#------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # count words
    def wordCount(self, string):
        count = 0
        for character in string:
            if character == ' ':
                count += 1
        return count
#------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # strips span tag id's
    def sanitizeFirstPass(self, string):
        regex = r'<span id=\"freeText[0-9]*\".*</span>'
        return_str = re.findall(regex, string)[0]
        # make sure we arent fetching a review instead
        if self.wordCount(return_str) > 300:
            regex = r'<span id=\"freeTextContainer[0-9]*\".*</span>'
            return_str = re.findall(regex, string)[0]

        print "DEBUG : FIRST_PASS = %r" % return_str
        print "########################################################"
        return return_str
    # gets thing inside > < tags
    def sanitizeSecondPass(self, string):
        regex = r'>\".*\<'
        return_str = re.findall(regex, string)
        if not return_str:
            regex = r'>.*<'
            return_str = re.findall(regex, string)[0] # the[0] is just to make sure we're passing a string
        else:
            return_str = return_str[0]
        print "DEBUG : SECOND_PASS = %r" % return_str
        print "########################################################"
        return return_str 
    # replaces html tags and non-ascii symbols with more sensible counterparts
    def sanitizeThirdPass(self, string):
         # html tags
        # regex will get reused a whole lot, bear with me.
        regex = r'<.*?>' # clean anything inside <>
        new_string = re.sub(regex, '', string)
        # stray brackets
        new_string = new_string.replace('<','')
        new_string = new_string.replace('>','')
        # non-ascii characters
        #new_string = new_string.replace('’','\'')
        #new_string = new_string.replace('”','\"')
        #new_string = new_string.replace('“','\"')
        regex = r'[^\x00-\x7F]'
        new_string = re.sub(regex,'', new_string)
        print "DEBUG : THIRD_PASS = %s" % new_string
        print "########################################################"
        return new_string
#------------------------------------------------------------------------------------------------------------------------------------------------------------------

app = App(root)
app.start()
root.mainloop()