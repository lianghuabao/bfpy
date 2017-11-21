# -*- utf-8 -*-
#creat by Bingdian(QQ:251859269)
import ctypes

STD_INPUT_HANDLE = -10
STD_OUTPUT_HANDLE= -11
STD_ERROR_HANDLE = -12

FOREGROUND_BLACK = 0x0
FOREGROUND_BLUE = 0x01 # text color contains blue.
FOREGROUND_GREEN= 0x02 # text color contains green.
FOREGROUND_RED = 0x04 # text color contains red.
FOREGROUND_INTENSITY = 0x08 # text color is intensified.

BACKGROUND_BLUE = 0x10 # background color contains blue.
BACKGROUND_GREEN= 0x20 # background color contains green.
BACKGROUND_RED = 0x40 # background color contains red.
BACKGROUND_INTENSITY = 0x80 # background color is intensified.

class Color:
    ''' See http://msdn.microsoft.com/library/default.asp?url=/library/en-us/winprog/winprog/windows_api_reference.asp
    for information on Windows APIs.'''
    std_out_handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
    
    def set_cmd_color(self, color, handle=std_out_handle):
        """(color) -> bit
        Example: set_cmd_color(FOREGROUND_RED | FOREGROUND_GREEN | FOREGROUND_BLUE | FOREGROUND_INTENSITY)
        """
        bool = ctypes.windll.kernel32.SetConsoleTextAttribute(handle, color)
        return bool
    
    def reset_color(self):
        self.set_cmd_color(FOREGROUND_RED | FOREGROUND_GREEN | FOREGROUND_BLUE)
    
    def print_red_text(self, *print_text):
        self.set_cmd_color(FOREGROUND_RED | FOREGROUND_INTENSITY)
        #print print_text[0].encode("GBK")
        print print_text
        self.reset_color()
    def print_red_text_oneline(self, print_text):
        self.set_cmd_color(FOREGROUND_RED | FOREGROUND_INTENSITY)
        #print print_text[0].encode("GBK")
        print print_text,
        self.reset_color()
        
    def print_green_text(self, *print_text):
        self.set_cmd_color(FOREGROUND_GREEN | FOREGROUND_INTENSITY)
        print print_text
        self.reset_color()
    def print_green_text_oneline(self, print_text):
        self.set_cmd_color(FOREGROUND_GREEN | FOREGROUND_INTENSITY)
        print print_text,
        self.reset_color()
    
    def print_blue_text(self, *print_text): 
        self.set_cmd_color(FOREGROUND_BLUE | FOREGROUND_INTENSITY)
        print print_text
        self.reset_color()
          
    def print_red_text_with_blue_bg(self, *print_text):
        self.set_cmd_color(FOREGROUND_RED | FOREGROUND_INTENSITY| BACKGROUND_BLUE | BACKGROUND_INTENSITY)
        print print_text
        self.reset_color()    
def inred( s ):
    return"%s[31;2m%s%s[0m"%(chr(27), s, chr(27))

if __name__ == "__main__":
    print('5+%d'%5)
    clr = Color()
    clr.print_red_text(*u'红色')
    clr.print_green_text(u'绿色')
    clr.print_blue_text('blue')
    clr.print_red_text_with_blue_bg('blue',5)
    
    print'this is a very '+inred('important')+' thing'
    

