# gpu-price-tracker

## Summary

This software uses webscraping to monitor prices on NewEgg for a given PC part. When the part drops below a set price threshold, the software will email a target email with the products that it found under that price. The frequency of checks as well as the maximum number of checks can be configured in the software.

## Setup

To use the software, install the following python packages with pip:
- bs4
- requests
- pysimplegui
Before running the software, you must configure the email to send the automated alerts from. It is reccomended to use a gmail account and then go to https://myaccount.google.com/apppasswords to configure an app and app password for python. You can then paste this email and the app password into a file titled email_config.txt (an example is shown in the repo) and these will be automatically read by the program.
The program can then be run by executing the gpu_tracker_gui.py file.
