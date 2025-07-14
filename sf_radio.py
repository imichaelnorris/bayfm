#!/usr/bin/env python3

import subprocess
import curses
import signal
import os
import sys

class SFRadio:
    def __init__(self):
        self.current_process = None
        self.stations = [
            ("88.1", "KECG - Campus/Variety"),
            ("88.5", "KQED - NPR/Talk"),
            ("89.5", "KPOO - Community/Variety"),
            ("89.7", "KFJC - College/Variety"),
            ("90.1", "KZSU - Stanford College"),
            ("90.3", "KDFC - Classical"),
            ("90.7", "KALX - Berkeley College"),
            ("91.1", "KCSM - Jazz"),
            ("91.7", "KALW - NPR/Talk/Variety"),
            ("92.1", "KKDV - Country"),
            ("92.3", "KSJO - Bollywood"),
            ("93.3", "KRZZ - Regional Mexican"),
            ("94.1", "KPFA - Pacifica Radio"),
            ("95.7", "The Game - Sports"),
            ("96.5", "KOIT - Adult Contemporary"),
            ("97.3", "Alice - Alternative Rock"),
            ("98.1", "Kiss FM - CHR"),
            ("99.7", "Now - Pop"),
            ("100.3", "The Mix - Adult Hits"),
            ("101.3", "Star - Adult Contemporary"),
            ("102.1", "KBLX - Urban AC"),
            ("103.7", "KGO-FM - Classic Hits"),
            ("104.5", "KFOG - Adult Alternative"),
            ("105.3", "The Live - Alternative"),
            ("106.1", "KMEL - Hip Hop/R&B"),
            ("106.9", "KFRC - Classic Hits"),
            ("107.7", "KSAN The Bone - Classic Rock")
        ]
        self.current_station = 0
        self.scroll_offset = 0
        
    def cleanup(self):
        if self.current_process:
            try:
                os.killpg(os.getpgid(self.current_process.pid), signal.SIGTERM)
                self.current_process.wait(timeout=2)
            except:
                pass
            self.current_process = None
            
    def start_station(self, freq):
        self.cleanup()
        cmd = f"rtl_fm -f {freq}M -M wbfm -s 200k -r 48000 2>/dev/null | aplay -r 48000 -f S16_LE 2>/dev/null"
        self.current_process = subprocess.Popen(cmd, shell=True, preexec_fn=os.setsid, 
                                              stdout=subprocess.DEVNULL, 
                                              stderr=subprocess.DEVNULL)
        
    def display_ui(self, stdscr):
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        # Header
        header = "🎵 SF FM Radio - RTL-SDR 🎵"
        stdscr.addstr(0, (width - len(header)) // 2, header, curses.A_BOLD)
        stdscr.addstr(1, 0, "=" * width)
        
        # Calculate scrolling
        available_rows = height - 6
        if self.current_station < self.scroll_offset:
            self.scroll_offset = self.current_station
        elif self.current_station >= self.scroll_offset + available_rows:
            self.scroll_offset = self.current_station - available_rows + 1
            
        # Station list
        for i, (freq, name) in enumerate(self.stations[self.scroll_offset:self.scroll_offset + available_rows]):
            station_idx = i + self.scroll_offset
            y = i + 2
            line = f"[{station_idx+1:2d}] {freq} MHz - {name}"
            
            if len(line) > width - 3:
                line = line[:width-6] + "..."
                
            if station_idx == self.current_station:
                stdscr.addstr(y, 0, f"▶ {line}", curses.A_REVERSE)
            else:
                stdscr.addstr(y, 0, f"  {line}")
        
        # Footer
        stdscr.addstr(height-4, 0, "=" * width)
        status = f"Playing: {self.stations[self.current_station][0]} MHz" if self.current_process else "Stopped"
        stdscr.addstr(height-3, (width - len(status)) // 2, status, curses.A_BOLD)
        controls = "↑/↓:Nav | Enter:Tune | q:Quit"
        stdscr.addstr(height-2, (width - len(controls)) // 2, controls)
        
        stdscr.refresh()
        
    def run(self, stdscr):
        curses.curs_set(0)  # Hide cursor
        stdscr.nodelay(0)   # Blocking input
        
        self.display_ui(stdscr)
        
        while True:
            key = stdscr.getch()
            
            if key == ord('q') or key == ord('Q'):
                break
            elif key == curses.KEY_UP or key == ord('k'):
                self.current_station = (self.current_station - 1) % len(self.stations)
                self.display_ui(stdscr)
            elif key == curses.KEY_DOWN or key == ord('j'):
                self.current_station = (self.current_station + 1) % len(self.stations)
                self.display_ui(stdscr)
            elif key == 10 or key == 13 or key == ord(' '):  # Enter or Space
                freq = self.stations[self.current_station][0]
                self.start_station(freq)
                self.display_ui(stdscr)
            elif key >= ord('1') and key <= ord('9'):
                station_num = key - ord('0')
                if 1 <= station_num <= len(self.stations):
                    self.current_station = station_num - 1
                    freq = self.stations[self.current_station][0]
                    self.start_station(freq)
                    self.display_ui(stdscr)
                    
        self.cleanup()

def main():
    try:
        radio = SFRadio()
        curses.wrapper(radio.run)
    except KeyboardInterrupt:
        pass
    finally:
        if 'radio' in locals():
            radio.cleanup()
        print("\nGoodbye!")

if __name__ == "__main__":
    main()