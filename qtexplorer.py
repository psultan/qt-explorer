import sys
import os
import shutil
import getpass
import re
import subprocess
import glob
import yaml
from pprint import pprint
import time

'''
import win32com.client
shell = win32com.client.Dispatch("Shell.Application")
folder = shell.NameSpace(21)
folderItem=folder.Self;
folderItem.InvokeVerbEx("Properties")
time.sleep(100)
'''

import ctypes
myappid = u'mycompany.myproduct.subproduct.version' # arbitrary string
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


from PySide2 import QtGui, QtCore, QtWidgets



def splitPath(dir, keepTail=True):
    end=""
    if keepTail:
        if re.search(r"\\$",dir):
            end="\\"
        elif re.search(r"/$", dir):
            end=r"/"
    if dir:
        return list(filter(None, re.split(r"[\\\/]", dir)+[end]))
def joinPath(splits, keepTail=True):
    end=""
    if splits:
        if keepTail and re.search(r"[\\\/]", splits[-1]):
            splits=splits[:-1]
            end=os.sep
        if splits:
            #ignore / \ only paths
            if splits[0].endswith(":"):
                out=os.sep.join(splits)
            else:
                out=os.sep*2+os.sep.join(splits)
            out=out+end
            return out
    return ""
def cleanPath(path):
    path=str(path).lstrip().rstrip()
    if path.startswith("\\\\\\"):
        path=path.replace("\\\\\\","")
    if path==".":
        path=""
    splits=splitPath(path, keepTail=True)
    path=joinPath(splits, keepTail=True)
    if os.path.isfile(path):
        path=os.path.dirname(path)
    
    inpath=path 
    if "bluearc\home\chrlx\\"+getpass.getuser() in path.lower() and ":" not in path:
        inpath="H:"+path[path.find(getpass.getuser())+len(getpass.getuser()):]
    elif "bluearc\gfx" in path.lower() and ":" not in path:
        inpath="G:"+path[13:]

    return path, inpath
def getClipboard():
    '''returns [Path, True(if path is from os copy not text copy)]'''
    import win32clipboard
    '''
    49161 DataObject
    49268 Shell IDList Array
    49519 DataObjectAttributes
    49292 Preferred DropEffect
    49329 Shell Object Offsets
    49158 FileName
    49159 FileNameW
    49171 Ole Private Data
    1     CF_TEXT
    2     CF_BITMAP
    7     CF_OEMTEXT
    13    CF_UNICODETEXT
    15    CF_HDROP
    16    CF_LOCALE
    '''
    win32clipboard.OpenClipboard()
    formats = []
    format  = 0 #0 starts enumeration
    while 1:
        format = win32clipboard.EnumClipboardFormats(format)
        if not format:
            break
        formats.append(format)
    #for format in formats:
    #    print(format, repr(win32clipboard.GetClipboardData(format)), type(win32clipboard.GetClipboardData(format)))

    if 15 in formats and 49422 in formats:
        #windows explorer file [15, 49161, 49422, 49..]
        data = win32clipboard.GetClipboardData(15)
        data=data.split("\n")
    elif 13 in formats:
        #text [1,7,13,16]
        data = win32clipboard.GetClipboardData(13)
        data=data.split("\n")
    win32clipboard.CloseClipboard()
    print("clipboard", data)
    return data

def setClipboard(data):
    import win32clipboard
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(13, data)
    win32clipboard.CloseClipboard()
class Main(QtWidgets.QWidget):
    MainWindow=None
    Windows=[]
    Cuts=[]
    Settings = {}
    YAMLPath = None
    def __init__(self):
        super(Main, self).__init__()
        
        self.setWindowIcon(QtGui.QIcon(r"H:\Windows\Desktop\icons\imageres_1302.ico"))
        Main.MainWindow=self
        Main.Settings={
            "BOOKMARKS":{},
            "UNC":{},
            "paths":[[]],
            "width":500,
            "height":500,
            "x":0,
            "y":0,
        }
        Main.YAMLPath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "qexplorer.yaml")
        if os.path.exists(Main.YAMLPath):
            with open(Main.YAMLPath, 'r') as stream:
                settings=yaml.load(stream)
                if settings:
                    Main.Settings.update(settings)
        self.initUI()
        self.setShortcuts()

    def initUI(self):
        mainLayout = QtWidgets.QHBoxLayout(self)
        self.setLayout(mainLayout)          
        self.setAcceptDrops(True)
        
        self.vbox = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        mainLayout.addWidget(self.vbox)

        if Main.Settings:
            width = Main.Settings["width"]
            height = Main.Settings["height"]
            x = Main.Settings["x"]
            y = Main.Settings["y"]
            
            for i in range(10):
                hbox = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
                self.vbox.addWidget(hbox)
                if len(Main.Settings["paths"])==0:
                    hbox.addWidget(Explorer())
                    break
                if i<len(Main.Settings["paths"]):                   
                    rowPaths=Main.Settings["paths"][i]
                    for path in rowPaths:
                        exp = Explorer()
                        exp.setPath(cleanPath(path)[1])
                        hbox.addWidget(exp)
        else:
            for i in range(10):
                hbox = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
                self.vbox.addWidget(hbox)
                if i==0:
                    hbox.addWidget(Explorer())
        
            desktop = QtWidgets.QApplication.desktop().availableGeometry(1)
            width, height= 1000,700
            x = (desktop.width()-width)/2
            y = (desktop.height()-height)/2
        
        self.resize(width, height)
        self.move(x,y)
        
        self.setWindowTitle('Qt Explorer')    
        self.show()
        
    def setShortcuts(self):
        for i in range(10):
            QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+%d"%i), self, lambda i=i: self.addExplorerY(i))
        for i in range(10):
            QtWidgets.QShortcut(QtGui.QKeySequence("Alt+%d"%i), self, lambda i=i: self.addExplorerY(i))
    def addExplorerY(self, key):
        if key==0:
            key=9
        else:
            key=key-1
        hbox = self.vbox.widget(key)
        hbox.addWidget(Explorer())
    def addExplorerX(self, key):
        if key==0:
            key=9
        else:
            key=key-1
        hbox = self.vbox.widget(key)
        hbox.addWidget(Explorer())
    def dragEnterEvent(self, e):
        e.accept()
    def dropEvent(self, e):
        #position = e.pos()
        #self.btn.move(position)

        #e.setDropAction(QtCore.Qt.MoveAction)
        
        return
        #e.accept()
    
    def closeEvent(self, event):
    
        for window in self.Windows:
            window.close()
        
        
        Main.Settings["height"]=self.frameGeometry().height()
        Main.Settings["width"]=self.frameGeometry().width()
        Main.Settings["x"]=self.frameGeometry().x()
        Main.Settings["y"]=self.frameGeometry().y()
        
        allPaths=[]
        for i in range(10):
            hbox = self.vbox.widget(i)
            rowPaths=[]
            for x in range(hbox.count()):
                explorer = hbox.widget(x)
                if explorer.isVisible():
                    rowPaths.append(str(explorer.model.filePath(explorer.tree.rootIndex())))
            if rowPaths:
                allPaths.append(rowPaths)
        Main.Settings["paths"]=allPaths
        pprint(Main.Settings)
            
        
        with open(Main.YAMLPath, 'w') as stream:
            stream.write(yaml.dump(Main.Settings))       
        self.close()
        
        
        
    def moveEvent(self, event):
        for window in self.Windows:
            window.close()
    def focusOutEvent(self,event):
        for window in self.Windows:
            window.close()        
class BetterTree(QtWidgets.QTreeView):
    def __init__(self, parent):
        super(BetterTree, self).__init__(parent)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.openMenu)

        self.setDragEnabled(True);
        self.setAnimated(False)
        self.setIndentation(20)
        self.setSortingEnabled(True)
        self.setAcceptDrops(True);
        self.viewport().setAcceptDrops(True);
        self.setDropIndicatorShown(True);
        #self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove);
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection);
        self.sortByColumn(0, QtCore.Qt.AscendingOrder)
        #seld.selectionModel().currentChanged.connect(self.keySelectionChanged)
        
        self.expanded.connect(self.expandAlt)
    def expandAlt(self, index):
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.AltModifier:
            self.expandRecursive(index)
    def expandRecursive(self, index):
        children = index.model().rowCount(index)
        for i in range(children):
            child=index.child(i,0)
            if "." not in child.data(QtCore.Qt.DisplayRole):
                self.expand(child)
    def openMenu(self, position):
        indexes = self.selectedIndexes()
        menu = QtWidgets.QMenu()
        
        newFolder = QtWidgets.QAction("New Folder", self)                
        newFolder.triggered.connect(self.newFolder)
        newFile = QtWidgets.QAction("New File", self)                
        newFile.triggered.connect(self.newFile)
        explorer = QtWidgets.QAction("Open command window here", self)                
        menu.addAction(newFolder)
        menu.addAction(newFile)
        menu.exec_(self.viewport().mapToGlobal(position))
    def focusInEvent(self, event):
        self.parent().lineEdit.completer.hide()
        
        self.setTabOrder(self, self.parent().filterEdit)
        super(BetterTree,self).focusInEvent(event)   
    def newFolder(self):
        indexes = self.selectedIndexes()
        if not indexes:
            destination=self.model().fileInfo(self.rootIndex()).absoluteFilePath()
        else:
            destination=self.model().fileInfo(indexes[0]).absoluteFilePath()
        i=1
        newpath=os.path.join(destination, "New folder")
        while os.path.exists(newpath):
            newpath=os.path.join(destination, "New folder (%d)"%i)
            i+=1
        print("new", newpath)
        os.mkdir(newpath)
        self.edit(self.model().index(newpath))
    def newFile(self):
        indexes = self.selectedIndexes()
        if not indexes:
            destination=self.model().fileInfo(self.rootIndex()).absoluteFilePath()
        else:
            destination=self.model().fileInfo(indexes[0]).absoluteFilePath()
            if os.path.isfile(destination):
                destination=os.path.dirname(destination)
        i=1
        newpath=os.path.join(destination, "New Text Document")
        while os.path.exists(newpath+".txt"):
            newpath=os.path.join(destination, "New Text Document (%d)"%i)
            i+=1
        newpath=newpath+".txt"
        print("new", newpath)
        open(newpath, 'a').close()
        self.edit(self.model().index(newpath))
    def mouseDoubleClickEvent(self, event):
        print("dbl clicked")
    def keyPressEvent(self, event):
        if event.key()==QtCore.Qt.Key_Enter or event.key()==QtCore.Qt.Key_Return:
            if self.selectedIndexes():
                path=str(self.model().filePath(self.selectedIndexes()[0]))
                if os.path.isfile(path):
                    os.system(path)
                else:
                    self.parent().setPath(path)
        elif event.key()==QtCore.Qt.Key_Asterisk:
            for item in self.selectedIndexes():
                self.expand(item)
                self.expandRecursive(item)

        elif event.key()==QtCore.Qt.Key_Left and event.modifiers()==QtCore.Qt.AltModifier:
            self.parent().back()
        elif event.key()==QtCore.Qt.Key_Right and event.modifiers()==QtCore.Qt.AltModifier:
            self.parent().forward()
        elif event.key()==QtCore.Qt.Key_Right or event.key()==QtCore.Qt.Key_Plus:
            for item in self.selectedIndexes():
                self.expand(item)
        elif event.key()==QtCore.Qt.Key_Left or event.key()==QtCore.Qt.Key_Minus:
            for item in self.selectedIndexes():
                self.collapse(item)
        elif event.key()==QtCore.Qt.Key_Up and event.modifiers()==QtCore.Qt.AltModifier:
            self.parent().upClicked()
        elif event.key()==QtCore.Qt.Key_C and event.modifiers()==QtCore.Qt.ControlModifier:
            paths=[]
            for item in self.selectedIndexes():
                #col 0 = name
                if item.column()==0:
                    paths.append(str(self.parent().model.filePath(item)))
            setClipboard("\n".join(paths))
        elif event.key()==QtCore.Qt.Key_X and event.modifiers()==QtCore.Qt.ControlModifier:
            paths=[]
            for item in self.selectedIndexes():
                #col 0 = name
                if item.column()==0:
                    paths.append(str(self.parent().model.filePath(item)))
            setClipboard(paths)
            Main.Cuts = paths
        elif event.key()==QtCore.Qt.Key_V and event.modifiers()==QtCore.Qt.ControlModifier:
            self.paste()
            Main.Cuts = []
        elif event.key()==QtCore.Qt.Key_V and event.modifiers()==(QtCore.Qt.ControlModifier|QtCore.Qt.ShiftModifier):            
            self.paste(move=True)
            Main.Cuts = []
        elif event.key()==QtCore.Qt.Key_Delete:
            for item in self.selectedIndexes():
                if item.column()==0:
                    path=str(self.parent().model.filePath(item))
                    if os.path.isfile(path):
                        print("delete file", path, self.model().remove(item))
                    else:
                        print("delete folder", path, shutil.rmtree(path))
        elif event.key()==QtCore.Qt.Key_F5:
            print("refresh")
            self.model().setRootPath("");
            self.model().setRootPath(self.model().fileInfo(self.rootIndex()).absoluteFilePath());
        else:
            super(BetterTree,self).keyPressEvent(event)   
    def dragMoveEvent(self, event):

        super(BetterTree,self).dragMoveEvent(event)   
    def paste(self, move=False):  
        print("paste", move)
        if self.selectedIndexes():
           destination=str(self.model().filePath(self.selectedIndexes()[0]))
        else:
            destination=self.model().filePath(self.rootIndex())
        if os.path.isfile(destination):
            destination=os.path.dirname(destination)       
        print("cuts",Main.Cuts)
        if Main.Cuts:
            #handle internal cuts before clipboard
            for item in Main.cuts:
                self.copy(item, destination, True)
        else:        
            data = getClipboard()
            for path in data:
                oldpath=joinPath(splitPath(path, keepTail=True), keepTail=True)
                if os.path.exists(oldpath):
                    self.copy(oldpath, destination, move)


    def copy(self, sourcePath, destinationFolder, move=False):
        newpath=os.path.join(destinationFolder, os.path.basename(sourcePath))
        while os.path.exists(newpath):
            newpath=newpath+"Copy"
        print(newpath)
        if not move:
            print("paste: copy", sourcePath, newpath)
            if os.path.isfile(sourcePath):
                shutil.copyfile(sourcePath,newpath)
            else:
                shutil.copytree(sourcePath, newpath)
        else:
            print("paste: move", sourcePath, newpath)
            shutil.move(sourcePath, newpath)
                
    def mouseDoubleClickEvent(self, event):
        if self.selectedIndexes():
            path=str(self.model().filePath(self.selectedIndexes()[0]))
            if os.path.isfile(path):
                os.startfile(path)
            else:
                self.parent().setPath(path)
        else:
            super(BetterTree,self).mouseDoubleClickEvent(event)
    def mousePressEvent(self, event):
        self.parent().lineEdit.completer.close()
        super(BetterTree,self).mousePressEvent(event) 
class BetterLineEdit(QtWidgets.QLineEdit):
    def __init__(self, parent):
        super(BetterLineEdit, self).__init__(parent)
        self.setAcceptDrops(True)
        
        self.completer = Completer(self)
        
        self.returnPressed.connect(self.parent().setPath)
        self.returnPressed.connect(self.completer.updateCompleter)
        self.textEdited.connect(self.completer.showCompleter)

        self.setFocusPolicy(QtCore.Qt.StrongFocus)
            


    def dropEvent(self, event):
        self.parent().setPath(event.mimeData().urls()[0].toString().replace("file:",""))
        event.accept()
    def dragEnterEvent(self, event):
        event.accept()
    def keyPressEvent(self, event):
        if event.key()==QtCore.Qt.Key_Down:
           self.completer.down()
        elif event.key()==QtCore.Qt.Key_Up and event.modifiers()==QtCore.Qt.AltModifier:
            self.parent().upClicked()
        elif event.key()==QtCore.Qt.Key_Up:
           self.completer.up()
        elif event.key()==QtCore.Qt.Key_Escape:
           self.completer.hide()
        elif event.key()==QtCore.Qt.Key_Return or event.key()==QtCore.Qt.Key_Enter:
            self.completer.hide()
            if self.text() in Main.Settings["BOOKMARKS"]["hidden"]:
                self.setText(Main.Settings["BOOKMARKS"]["hidden"][str(self.text())])
            super(BetterLineEdit,self).keyPressEvent(event)
            #data = getClipboard()
            #path=joinPath(splitPath(data, keepTail=True), keepTail=True)
            #if os.path.exists(path):
            #    self.parent().setPath(path)
            #else:
            #    self.setText(data)
        else:
            super(BetterLineEdit,self).keyPressEvent(event)
    
    def focusInEvent(self, event):     
        self.setTabOrder(self, self.parent().tree)
        super(BetterLineEdit,self).focusInEvent(event)   

    '''
    def event(self, event):
        if hasattr(event,"type"):
            if (event.type()==QtCore.QEvent.KeyPress) and (event.key()==QtCore.Qt.Key_Tab):
                self.completer.tabSelected()
                return True
            return super(BetterLineEdit,self).event(event)

    '''
class Completer(QtWidgets.QWidget):
    def __init__(self, lineEdit):
        super(Completer, self).__init__(lineEdit)
        Main.Windows.append(self)
        self.lineEdit=lineEdit
        self.setWindowFlags(QtCore.Qt.ToolTip)
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating);

            
        self.mainLayout = QtWidgets.QVBoxLayout(self)
                
        pal = QtGui.QPalette()
        pal.setColor(QtGui.QPalette.Background, QtCore.Qt.lightGray);
        self.setPalette(pal)
                
        self.index=-1
        self.savedText=""
        self.bookmarks=[]
        print(Main.Settings)
        print(Main.Settings["BOOKMARKS"])
        if "visible" in Main.Settings["BOOKMARKS"]:
            self.bookmarks=list(Main.Settings["BOOKMARKS"]["visible"].keys())
        self.localDirs=[]
         
        self.mainLayout.setSpacing(0)
        self.setLayout(self.mainLayout)

    def down(self):
        if self.isVisible()==False:
            self.showCompleter()
        self.index+=1
        if self.index!=0:
            self.mainLayout.itemAt(self.index-1).widget().setStyleSheet("QPushButton:hover{background-color:rgb(51,153,255); border-style:inset; color:white; text-align:left} QPushButton{text-align:left; border-style:inset;}")
        else:
            self.mainLayout.itemAt(self.mainLayout.count()-1).widget().setStyleSheet("QPushButton:hover{background-color:rgb(51,153,255); border-style:inset; color:white; text-align:left} QPushButton{text-align:left; border-style:inset;}")
        self.mainLayout.itemAt(self.index).widget().setStyleSheet("background-color:rgb(51,153,255); color:white; text-align:left; border-style:inset;")
        self.lineEdit.setText(self.mainLayout.itemAt(self.index).widget().text())
            
    def up(self):
        self.index-=1
        if self.index>=0:
            self.mainLayout.itemAt(self.index+1).widget().setStyleSheet("QPushButton:hover{background-color:rgb(51,153,255); border-style:inset; color:white; text-align:left} QPushButton{text-align:left; border-style:inset;}")               
            self.mainLayout.itemAt(self.index).widget().setStyleSheet("background-color:rgb(51,153,255); color:white; text-align:left; border-style:inset;")
            self.lineEdit.setText(self.mainLayout.itemAt(self.index).widget().text())
        else:
            self.lineEdit.setText(self.savedText)            
    @property
    def index(self):
        return self.__index
    @index.setter
    def index(self, index):
        if index < -1:
            pass
        elif index > self.mainLayout.count()-1:
            self.__index = 0
        else:
            self.__index = index
    
    def updateCompleter(self):
        self.index=-1
        path, inpath=cleanPath(self.lineEdit.text())
        dir,name=os.path.split(path)
        self.savedText=path
        
        if os.path.exists(dir):
            if not re.search("[\\\/]$", path):
                paths=os.listdir(dir)
                self.localDirs= [os.path.join(dir,s) for s in paths if name!="" and os.path.isdir(os.path.join(dir,s)) and os.path.basename(s).lower().startswith(name.lower())]
            else:
                self.localDirs=[os.path.join(dir,o) for o in os.listdir(dir) if os.path.isdir(os.path.join(dir,o)) and name.lower() in o.lower()]
        else:
            self.localDirs=[]
        if self.localDirs:
            folders=self.localDirs+[""]+self.bookmarks
        else:
            folders=self.localDirs+self.bookmarks
        for i in reversed(range(self.mainLayout.count())): 
            self.mainLayout.itemAt(i).widget().setParent(None)
        for folder in folders:
            test = QtWidgets.QPushButton(folder)
            test.setMinimumHeight(16);
            test.pressed.connect(self.buttonClicked)
            test.setStyleSheet("QPushButton:hover{background-color:rgb(51,153,255); border-style:inset; color:white; text-align:left} QPushButton{text-align:left; border-style:inset;}")
            test.setFlat(True)
            self.mainLayout.addWidget(test)
    def showCompleter(self):
        self.updateCompleter()
        self.show()
        self.adjustSize()
        point = self.lineEdit.rect().bottomLeft()
        global_point = self.lineEdit.mapToGlobal(point)
        self.move(global_point)
    def tabSelected(self):
        widget=self.mainLayout.itemAt(self.index)
        if widget:
            widget.widget().clicked.emit()
    def buttonClicked(self):
        path=str(self.sender().text())
        if path in Main.Settings["BOOKMARKS"]["visible"]:
            path=Main.Settings["BOOKMARKS"]["visible"][path]
        path=path+"\\"
        self.lineEdit.setText(path)
        self.lineEdit.returnPressed.emit()
        self.close()
class FilterEdit(QtWidgets.QLineEdit):
    def __init__(self, parent):
        super(FilterEdit, self).__init__(parent)
    def focusInEvent(self, event):
        self.setTabOrder(self, self.parent().lineEdit)
        super(FilterEdit, self).focusInEvent(event)
class Explorer(QtWidgets.QWidget):
    def __init__(self):
        super(Explorer, self).__init__()
        self.layout()
        mainLayout = QtWidgets.QVBoxLayout(self)
        
        headerLayout = QtWidgets.QHBoxLayout()
        self.lineEdit = BetterLineEdit(self)
        

        self.upButton = QtWidgets.QPushButton("^", self) 
        self.upButton.setMaximumSize(20,20)
        self.upButton.setFlat(True)
        self.upButton.clicked.connect(self.upClicked)
        self.upButton.setFocusPolicy(QtCore.Qt.NoFocus)

        self.closeButton = QtWidgets.QPushButton("x", self)
        self.closeButton.setMaximumSize(20,20)
        self.closeButton.setFlat(True)
        self.closeButton.clicked.connect(self.closeClicked)
        self.closeButton.setFocusPolicy(QtCore.Qt.NoFocus)
        
        self.model = QtWidgets.QFileSystemModel()
        self.model.directoryLoaded.connect(self.directoryLoaded)
        self.model.setFilter(QtCore.QDir.NoDotAndDotDot)
        self.model.setReadOnly(False)
        self.model.setRootPath("")
        self.model.setFilter(QtCore.QDir.AllEntries)
        self.model.setNameFilterDisables(False)

        self.tree = BetterTree(self)       
        self.tree.setModel(self.model)
        self.tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents);
        self.tree.header().setStretchLastSection(True);
        
        filterLayout = QtWidgets.QHBoxLayout()
        self.filterEdit =FilterEdit(self)
        self.filterEdit.textChanged.connect(self.setFilter)
        self.filterCheck = QtWidgets.QCheckBox()
        self.filterCheck.clicked.connect(self.setFilter)
        filterLayout.addWidget(self.filterEdit)
        filterLayout.addWidget(self.filterCheck)
        
        headerLayout.addWidget(self.lineEdit)
        headerLayout.addWidget(self.upButton)
        headerLayout.addWidget(self.closeButton)
        mainLayout.addLayout(headerLayout)
        mainLayout.addWidget(self.tree)
        mainLayout.addLayout(filterLayout)
        
        
        
        self.setTabOrder(self.tree, self.filterEdit)
        self.setTabOrder(self.filterEdit, self.lineEdit)
        
        self.history=[]
        self.future=[]
        
        self.setLayout(mainLayout)  
        
    def directoryLoaded(self, path):
        '''triggered when there is an os change or the user navigates to a new folder'''
        index = self.model.index(path)
        children = self.model.rowCount(index)
        
        for i in range(children):
            child=index.child(i,0)
            if child.data(QtCore.Qt.DisplayRole)=="." or child.data(QtCore.Qt.DisplayRole)=="..":
                self.tree.setRowHidden(i, index, True)
        if QtWidgets.QApplication.keyboardModifiers()==QtCore.Qt.AltModifier:
            if cleanPath(path)[0] not in cleanPath(self.history[-2])[0]:
                #don't expand if newpath is a parent of the past path(catches alt+up)
                self.tree.expandAlt(self.model.index(path))
    def loaded(self):
        self.tree.collapseAll()
        self.filterEdit.setText("")
    def setFilter(self):
        text=self.filterEdit.text().lower()
        root=self.tree.rootIndex()
        children = self.model.rowCount(root)
        
        for i in range(children):
            child=root.child(i,0)
            self.tree.setRowHidden(i, root, False)
            if child.data(QtCore.Qt.DisplayRole)=="." or child.data(QtCore.Qt.DisplayRole)=="..":
                self.tree.setRowHidden(i, root, True)
        
        if self.filterCheck.isChecked():
            if text:
                self.model.setNameFilters(["*{0}*".format(text)])
            else:
                self.model.setNameFilters([])
        else:
            for i in range(children):
                child=root.child(i,0)
                if text not in child.data(QtCore.Qt.DisplayRole).lower():
                    self.tree.setRowHidden(i, root, True)

    def keySelectionChanged(self, modelIndex):
        self.tree.selectionModel().setCurrentIndex(modelIndex, QtWidgets.QItemSelectionModel.SelectCurrent)
    def setPath(self, path=None):   
        if path==None:
            path = self.lineEdit.text()
        path, inpath = cleanPath(path)
        self.lineEdit.setText(path)
        self.tree.setRootIndex(self.model.index(inpath))
        self.tree.resizeColumnToContents(0)
        self.tree.collapseAll()
        self.history.append(path)
        self.filterEdit.setText("")
               
        basename = os.path.basename(path).lower()
        if basename=="desktop":
            Main.MainWindow.setWindowIcon(QtGui.QIcon(r"H:\Windows\Desktop\icons\imageres_110.ico"))
        elif basename=="music":
            Main.MainWindow.setWindowIcon(QtGui.QIcon(r"H:\Windows\Desktop\icons\imageres_137.ico"))
        else:
            Main.MainWindow.setWindowIcon(QtGui.QIcon(r"H:\Windows\Desktop\icons\imageres_1302.ico"))

        if self.lineEdit.text():
            if self.lineEdit.text()[-1].isalpha() or self.lineEdit.text()[-1]==":":
                self.lineEdit.setText(self.lineEdit.text()+"\\")
    def back(self):
        print(self.history)
        print(self.future)
        if self.history:
            self.future.append(self.history.pop())
        if self.history:
            self.setPath(self.history.pop())
    def forward(self):
        print(self.history)
        print(self.future)
        if self.future:
            self.setPath(self.future.pop())
    def upClicked(self):
        path=str(self.lineEdit.text()).rstrip("\\")
        newpath=os.path.dirname(path)
        if path==newpath:
            newpath=""
        self.setPath(newpath)
    def closeClicked(self):
        self.close()

      
app = QtWidgets.QApplication(sys.argv)
ex = Main()
sys.exit(app.exec_())
