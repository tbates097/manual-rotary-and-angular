This is a program intially built to pull in data from the Autocollimator via the RS232 port and use that to perform a manual rotary calibration using the Ultradex.

Seeing as though the RS232 connection scheme is a dependency, I added another tab to the UI to capture angular errors on a linear stage.

Run MetrologyTestInterface.py to initialize the UI and enter test parameters and stage data. 

The program will provide a live plot, live results, and outputs an Aerotech data file and PDF.

The program works with the A1 API.

It can be used to calibrate and verify.