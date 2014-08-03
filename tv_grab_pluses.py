#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright 2014 Oscar Curero
This code is free software; you can redistribute it and/or modify it
under the terms of the GPL 3 license (see the file
COPYING.txt included with the distribution).
"""

from __future__ import print_function
from ConfigParser import ConfigParser
from datetime import datetime, timedelta
import getopt
import os
import time
import uuid
import sys
import xmltv
import libmhw

def usage():
    print("""tv_grab_pluses usage:\t
    --description: This grabber\t
    --capabilities: show capabilities\t
    --quiet: supress informational messages, show only errors\t
    --output: write data to file\t
    --days: fetch data for X days\t
    --offset: fetch data for X days in future\t
    --config-file: parameters file for configure tv_grab_pluses\t
    -h,--help: Show this help""")
    
def main():
    # Safe defaults
    no_info = False
    maxdays = 30
    offset = -1
    output_file = "/tmp/" + str(uuid.uuid4())
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help", "description", "capabilities", "quiet" ,\
        "output=","days=","offset=","config-file="])
    except getopt.GetoptError, err:
        # print help information and exit:
        #print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("--description"):
          print("plus.es (MHWv2)")
        elif o in ("--capabilities"):
          print("baseline")
          sys.exit()
        elif o in ("--quiet"):
          no_info = True
        elif o in ("--output"):
          output_file = a
          new_file = True
        elif o in ("--days"):
          maxdays = a
        elif o in ("--offset"):
          offset = a
        elif o in ("--config-file"):
          config_file = a
        elif o in ("-h", "--help"):
          usage()
          sys.exit()    
    # No more BS, let's have some fun :)
    config = ConfigParser()
    try:
        config.read(config_file)
    except UnboundLocalError:
        print("ERROR: configuration file not specified", file=sys.stderr)
        sys.exit(1)
    try:   
        device = config.get("General", "device")
    except:
        print("ERROR: configuration file not found or syntax invalid", file=sys.stderr)
        sys.exit(2)
    if no_info == False:
        print("INFO: Fetching data from device %s" % (device,))
    # Get the data!
    data = libmhw.MHW(device)
    try:
        data.scan_stream()
    except libmhw.NoMHWStreamFoundError:
        print("ERROR: No EPG data found on the current tune", file=sys.stderr)
        sys.exit(3)
    if no_info == False: 
        print("INFO: Processing data (found %d programmes)" % (len(data.programs)))
    # Process data
    xmlfile = xmltv.Writer(date = str(datetime.today()), source_info_url = "http://www.plus.es")
    channel_count = 1
    channels = []
    channelid_list = {}
    filtered_channels = []
    # Filter programmes (maxdays and offset)
    for program in data.programs:
            # If the program is within the limits of maxdays and offset, add it to the list
            if datetime.now() + timedelta(maxdays) >= program.airtime and\
            datetime.now() + timedelta(offset) <= program.airtime:
                filtered_channels.append(program)
                if program.channel not in channels:
                    # New channel detected, add it to the list
                    channels.append(program.channel)
            else:
                print(program)
  
    # Read channels and build their channelID, add them to xmltv
    for channel in channels:
            channel_id = "tv." + str(channel_count) + "-" + channel.replace(" ", "_") + ".plus.es"
            channelid_list[channel] = channel_id
            xmlfile.addChannel({"id": channel_id, "display-name": [(channel, "es")]})
            channel_count += 1
    if no_info == False:
        print("INFO: %d channels written" % (len(channels),))
        
    # Read channels and add them to xmltv
    if time.daylight == 1:
        gmt_offset = "+0100"
    else:
        gmt_offset = "+0200"
    for program in filtered_channels:
        data={}
        data["title"] = [(program.title, "")]
        data["category"] = [(program.category, 'es'), (program.subcategory, 'es')]
        data["length"] = {"units": "minutes", "length": str(program.length)}
        data["channel"] = channelid_list[program.channel]
        data["start"] = program.airtime.strftime("%Y%m%d%H%M") + " " + gmt_offset
        data["desc"] = [(program.summary, '')]
        xmlfile.addProgramme(data)
    if no_info == False:
        print("INFO: %d programmes written" % (len(filtered_channels),))
        
    xmlfile.write(output_file)
    if not locals().has_key("new_file"):
        print(open(output_file, "r").read())
        os.remove(output_file)
    
if __name__ == "__main__":
    # Run tv_grab_pluses
    main()