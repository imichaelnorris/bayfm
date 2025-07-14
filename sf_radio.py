#!/usr/bin/env python3

import subprocess
import curses
import signal
import os
import sys
import math
import time

class SFRadio:
    def __init__(self):
        self.current_process = None
        self.stations = self.load_stations()
        self.current_station = 0
        self.scroll_offset = 0
        
    def load_stations(self):
        """Load stations from stations.txt file with fallback to default stations"""
        default_stations = [
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
        
        try:
            stations = []
            with open('stations.txt', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split(',', 1)
                        if len(parts) == 2:
                            freq, name = parts
                            stations.append((freq.strip(), name.strip()))
            
            return stations if stations else default_stations
        except FileNotFoundError:
            return default_stations
        
    def draw_radio_dial(self, stdscr, y, freq):
        """Draw compact Unicode radio dial on bottom row"""
        height, width = stdscr.getmaxyx()
        
        # FM range: 88.1 - 107.7 MHz
        min_freq = 88.1
        max_freq = 107.7
        
        # Calculate position (0-1) along the dial
        freq_val = float(freq)
        freq_ratio = (freq_val - min_freq) / (max_freq - min_freq)
        
        # Create dial with Unicode block characters
        dial_width = 40
        start_x = (width - dial_width) // 2
        
        try:
            # Draw dial background
            dial_line = "│"
            for i in range(dial_width - 2):
                if i % 8 == 0:  # Tick marks every 8 positions
                    dial_line += "┼"
                else:
                    dial_line += "─"
            dial_line += "│"
            
            stdscr.addstr(y, start_x, dial_line)
            
            # Draw frequency labels below
            freq_labels = " 88   92   96  100  104  108 "
            if len(freq_labels) <= dial_width:
                label_start = start_x + (dial_width - len(freq_labels)) // 2
                stdscr.addstr(y + 1, label_start, freq_labels)
            
            # Draw needle position
            needle_pos = int(1 + freq_ratio * (dial_width - 3))
            needle_pos = max(1, min(dial_width - 2, needle_pos))
            
            # Use different Unicode characters for the needle
            stdscr.addstr(y, start_x + needle_pos, "▲", curses.A_BOLD | curses.A_REVERSE)
            
            # Current frequency display
            freq_display = f" {freq} MHz "
            freq_x = start_x + dial_width + 2
            if freq_x + len(freq_display) < width:
                stdscr.addstr(y, freq_x, freq_display, curses.A_BOLD)
            
        except curses.error:
            pass  # Ignore drawing errors if terminal is too small
        
    def cleanup(self):
        if self.current_process:
            try:
                os.killpg(os.getpgid(self.current_process.pid), signal.SIGTERM)
                self.current_process.wait(timeout=2)
            except:
                pass
            self.current_process = None
            
    def start_station(self, freq):
        # Only cleanup and restart if we're not already playing this frequency
        if not self.current_process or getattr(self, 'current_freq', None) != freq:
            self.cleanup()
            cmd = f"rtl_fm -f {freq}M -M wbfm -s 250k -r 96000 2>/dev/null | aplay -r 96000 -f S16_LE 2>/dev/null"
            self.current_process = subprocess.Popen(cmd, shell=True, preexec_fn=os.setsid, 
                                                  stdout=subprocess.DEVNULL, 
                                                  stderr=subprocess.DEVNULL)
            self.current_freq = freq
        
    def display_ui(self, stdscr):
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        # Header
        header = "🎵 SF FM Radio - RTL-SDR 🎵"
        stdscr.addstr(0, (width - len(header)) // 2, header, curses.A_BOLD)
        stdscr.addstr(1, 0, "=" * width)
        
        current_freq = self.stations[self.current_station][0]
        
        # Calculate scrolling - leave space for dial at bottom
        available_rows = height - 8  # More space for dial
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
        
        # Draw compact radio dial at bottom
        self.draw_radio_dial(stdscr, height - 6, current_freq)
        
        # Footer
        stdscr.addstr(height-4, 0, "=" * width)
        status = f"Playing: {current_freq} MHz" if self.current_process else "Stopped"
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
            elif key == curses.KEY_ENTER or key == 10 or key == 13 or key == ord(' '):  # Enter or Space
                freq = self.stations[self.current_station][0]
                self.start_station(freq)
                self.display_ui(stdscr)
                # Small delay to prevent double-key detection
                time.sleep(0.1)
            elif key >= ord('1') and key <= ord('9'):
                station_num = key - ord('0')
                if 1 <= station_num <= len(self.stations):
                    self.current_station = station_num - 1
                    freq = self.stations[self.current_station][0]
                    self.start_station(freq)
                    self.display_ui(stdscr)
                    
        self.cleanup()

def main():
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--test-dial":
        # Test dial drawing without curses
        radio = SFRadio()
        print("Testing dial positions for different frequencies:")
        for freq in ["88.1", "95.7", "103.7", "107.7"]:
            freq_val = float(freq)
            min_freq = 88.1
            max_freq = 107.7
            freq_ratio = (freq_val - min_freq) / (max_freq - min_freq)
            angle_deg = -60 + (freq_ratio * 120)
            print(f"Freq {freq} MHz -> {angle_deg:.1f}°")
        return
    
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