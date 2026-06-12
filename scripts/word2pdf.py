import os
import glob
from pathlib import Path
from docx2pdf import convert
path = os.getcwd() + '/'
p = Path(path)
FileList=list(p.glob("**/*.docx")) 
for file in FileList:
    
    convert(file,f"{file}.pdf")



