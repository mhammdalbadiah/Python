#!/usr/bin/env python3
# ###############################################
# Terminal Timer - Pro UI
# Author : Mohammed Al-Badiah
# ###############################################

import sys
import time
import os
import shutil


# ###############################################
# ANSI Colors and Styles
# ###############################################
class Color :
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"

    CYAN    = "\033[38;5;51m"
    GREEN   = "\033[38;5;46m"
    YELLOW  = "\033[38;5;226m"
    RED     = "\033[38;5;196m"
    PURPLE  = "\033[38;5;141m"
    GRAY    = "\033[38;5;245m"
    WHITE   = "\033[38;5;255m"


# ###############################################
# Big Digits (ASCII Art for the clock)
# ###############################################
DIGITS = {
    "0" : [" ██████╗ ", "██╔═████╗", "██║██╔██║", "████╔╝██║", "╚██████╔╝", " ╚═════╝ "],
    "1" : ["  ██╗  ", "███║   ", "╚██║   ", " ██║   ", " ██║   ", " ╚═╝   "],
    "2" : ["██████╗ ", "╚════██╗", " █████╔╝", "██╔═══╝ ", "███████╗", "╚══════╝"],
    "3" : ["██████╗ ", "╚════██╗", " █████╔╝", " ╚═══██╗", "██████╔╝", "╚═════╝ "],
    "4" : ["██╗  ██╗", "██║  ██║", "███████║", "╚════██║", "     ██║", "     ╚═╝"],
    "5" : ["███████╗", "██╔════╝", "███████╗", "╚════██║", "███████║", "╚══════╝"],
    "6" : [" ██████╗ ", "██╔════╝ ", "███████╗ ", "██╔═══██╗", "╚██████╔╝", " ╚═════╝ "],
    "7" : ["███████╗", "╚════██║", "    ██╔╝", "   ██╔╝ ", "   ██║  ", "   ╚═╝  "],
    "8" : [" █████╗ ", "██╔══██╗", "╚█████╔╝", "██╔══██╗", "╚█████╔╝", " ╚════╝ "],
    "9" : [" █████╗ ", "██╔══██╗", "╚██████║", " ╚═══██║", " █████╔╝", " ╚════╝ "],
    ":" : ["   ", "██╗", "╚═╝", "██╗", "╚═╝", "   "],
}


# ###############################################
# Helper Functions
# ###############################################
def ClearScreen() :
    os.system("clear" if os.name != "nt" else "cls")


def HideCursor() :
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()


def ShowCursor() :
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()


def GetTerminalWidth() :
    return shutil.get_terminal_size().columns


def CenterText(text , width = None) :
    if width is None :
        width = GetTerminalWidth()
    return text.center(width)


# ###############################################
# Render Big Time
# ###############################################
def RenderBigTime(timeStr , color) :
    lines = ["" , "" , "" , "" , "" , ""]
    for ch in timeStr :
        if ch in DIGITS :
            for i in range(6) :
                lines[i] += DIGITS[ch][i] + " "

    width = GetTerminalWidth()
    output = ""
    for line in lines :
        padding = (width - len(line)) // 2
        output += " " * padding + color + line + Color.RESET + "\n"
    return output


# ###############################################
# Progress Bar
# ###############################################
def RenderProgressBar(elapsed , total , color) :
    barWidth = min(50 , GetTerminalWidth() - 20)
    if total == 0 :
        progress = 1.0
    else :
        progress = elapsed / total

    filled = int(barWidth * progress)
    empty = barWidth - filled

    bar = color + "█" * filled + Color.GRAY + "░" * empty + Color.RESET
    percent = f"{int(progress * 100):3d}%"

    line = f"  {bar}  {Color.BOLD}{percent}{Color.RESET}"
    width = GetTerminalWidth()
    visibleLen = barWidth + 8
    padding = (width - visibleLen) // 2
    return " " * padding + line


# ###############################################
# Header Box
# ###############################################
def RenderHeader(totalSeconds) :
    width = GetTerminalWidth()
    boxWidth = 50
    pad = (width - boxWidth) // 2
    p = " " * pad

    h , m , s = SecondsToHMS(totalSeconds)
    durationStr = f"{h:02d}:{m:02d}:{s:02d}"

    output = "\n"
    output += p + Color.PURPLE + "╔" + "═" * (boxWidth - 2) + "╗" + Color.RESET + "\n"
    title = "TERMINAL TIMER"
    titleLine = title.center(boxWidth - 2)
    output += p + Color.PURPLE + "║" + Color.BOLD + Color.WHITE + titleLine + Color.RESET + Color.PURPLE + "║" + Color.RESET + "\n"
    output += p + Color.PURPLE + "║" + Color.RESET + Color.DIM + f"  Duration : {durationStr}".ljust(boxWidth - 2) + Color.RESET + Color.PURPLE + "║" + Color.RESET + "\n"
    output += p + Color.PURPLE + "╚" + "═" * (boxWidth - 2) + "╝" + Color.RESET + "\n"
    return output


# ###############################################
# Time Conversion
# ###############################################
def SecondsToHMS(totalSeconds) :
    h = totalSeconds // 3600
    m = (totalSeconds % 3600) // 60
    s = totalSeconds % 60
    return h , m , s


def FormatTime(totalSeconds) :
    h , m , s = SecondsToHMS(totalSeconds)
    return f"{h:02d}:{m:02d}:{s:02d}"


# ###############################################
# Get User Input
# ###############################################
def GetUserInput() :
    ClearScreen()
    width = GetTerminalWidth()
    pad = " " * ((width - 50) // 2)

    print()
    print(pad + Color.PURPLE + Color.BOLD + "╔" + "═" * 48 + "╗" + Color.RESET)
    print(pad + Color.PURPLE + Color.BOLD + "║" + Color.WHITE + "          ⏱  TERMINAL TIMER  ⏱            ".center(48) + Color.PURPLE + "║" + Color.RESET)
    print(pad + Color.PURPLE + Color.BOLD + "╚" + "═" * 48 + "╝" + Color.RESET)
    print()
    print(pad + Color.GRAY + "  Set your timer below " + Color.RESET)
    print()

    while True :
        try :
            print(pad + Color.CYAN + "  Hours    : " + Color.RESET , end = "")
            hours = input().strip()
            hours = int(hours) if hours else 0

            print(pad + Color.CYAN + "  Minutes  : " + Color.RESET , end = "")
            minutes = input().strip()
            minutes = int(minutes) if minutes else 0

            print(pad + Color.CYAN + "  Seconds  : " + Color.RESET , end = "")
            seconds = input().strip()
            seconds = int(seconds) if seconds else 0

            total = hours * 3600 + minutes * 60 + seconds

            if total <= 0 :
                print()
                print(pad + Color.RED + "  ✗ Please enter a value greater than 0 " + Color.RESET)
                print()
                continue

            return total

        except ValueError :
            print()
            print(pad + Color.RED + "  ✗ Invalid number , try again " + Color.RESET)
            print()
        except KeyboardInterrupt :
            print("\n")
            print(pad + Color.YELLOW + "  Cancelled " + Color.RESET)
            sys.exit(0)


# ###############################################
# Pick Color Based on Remaining Time
# ###############################################
def PickColor(remaining , total) :
    ratio = remaining / total if total > 0 else 0
    if ratio > 0.5 :
        return Color.GREEN
    elif ratio > 0.2 :
        return Color.YELLOW
    else :
        return Color.RED


# ###############################################
# Run the Countdown
# ###############################################
def RunTimer(totalSeconds) :
    HideCursor()
    startTime = time.time()
    endTime = startTime + totalSeconds

    try :
        while True :
            now = time.time()
            remaining = int(round(endTime - now))

            if remaining < 0 :
                remaining = 0

            elapsed = totalSeconds - remaining
            color = PickColor(remaining , totalSeconds)
            timeStr = FormatTime(remaining)

            ClearScreen()
            print(RenderHeader(totalSeconds))
            print()
            print(RenderBigTime(timeStr , color))
            print()
            print(RenderProgressBar(elapsed , totalSeconds , color))
            print()

            width = GetTerminalWidth()
            hint = Color.DIM + "Press Ctrl+C to cancel" + Color.RESET
            print(hint.center(width + len(Color.DIM) + len(Color.RESET)))

            if remaining == 0 :
                break

            time.sleep(1)

        # ###############################################
        # Timer Done
        # ###############################################
        TimerFinished()

    except KeyboardInterrupt :
        ClearScreen()
        width = GetTerminalWidth()
        print()
        print(Color.YELLOW + "  ⏸  Timer cancelled by user".center(width) + Color.RESET)
        print()
    finally :
        ShowCursor()


# ###############################################
# Finish Animation
# ###############################################
def TimerFinished() :
    width = GetTerminalWidth()

    for i in range(6) :
        ClearScreen()
        c = Color.GREEN if i % 2 == 0 else Color.YELLOW
        print()
        print()
        msg = c + Color.BOLD + "✓  TIME'S UP !".center(width) + Color.RESET
        print(msg)
        print()
        # Terminal bell
        sys.stdout.write("\a")
        sys.stdout.flush()
        time.sleep(0.4)

    print()
    print(Color.GRAY + "  Timer finished successfully ".center(width) + Color.RESET)
    print()


# ###############################################
# Main
# ###############################################
def Main() :
    try :
        totalSeconds = GetUserInput()
        RunTimer(totalSeconds)
    except KeyboardInterrupt :
        ShowCursor()
        print("\n")
        sys.exit(0)


if __name__ == "__main__" :
    Main()
