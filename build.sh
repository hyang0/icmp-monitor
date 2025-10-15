#!/bin/bash

pyinstaller --collect-all PyQt5 \
	--collect-all scapy \
	--onefile gui_icmp_monitor.py

