# Pseudocode & Python

The Pseudocode & Python app runs VCE Maths pseudocode in your browser, shows each step in a trace table, and translates between pseudocode and Python. Nothing is sent anywhere: programs run on your device.

Open it from the Home screen, or go straight to it: <https://cassim-app.pages.dev/#/app/pseudocode>

- [[Pseudocode syntax]]: everything the app accepts, with the Python for each

## Write and run

1. Type a program in the Code pane, or choose one from **Examples** (linear, loops, bisection, GCD and LCM, a prime sieve, dice simulations, Riemann sums, Newton's method).
2. Press **Run**. Output appears below the code. If something goes wrong, the error is shown after the output so far.
3. **Stop** ends a program that runs too long. Loops are also limited to 1,000 passes, so a mistake cannot run forever.

Switch the Code pane between **Pseudocode** and **Python** to see the translation. Comments on their own line are kept in both directions.

## Trace table

The trace table records every change to a variable, in order, as a desk check would.

- **Step**, **First** and **Last** move through the run one row at a time, and the line reached is highlighted in the code.
- Tick the variables you want to see. Drag the line between columns to resize them.
- A `define` line has its own row, where the function is defined.
- **Step steps over a call** to one of your own functions: the whole call runs in one step. Its row has an open button, which opens that call's own trace in a window beside the function's code, with its own Step, First and Last. The window can be moved and resized, and stacks the two parts on a narrow screen.
- Lists show their value at each step.

## Settings

**Number mode** sets how numbers are kept:

- **Approx:** division gives decimals, as in Python.
- **Auto:** whole numbers and fractions stay exact.
- **Exact:** decimals are also read as fractions.

**Angle** is Radian or Degree. **Settings…** also has:

- the code style and symbols the translation writes;
- line numbers;
- the **typing aid**, on by default. It turns `<-` into `←`, `<=` into `≤`, `\pi` into `π`, `x^2` into `x²` and so on, a moment after you stop typing.

## On a phone

The panes stack one above the other. The typing aid is the quickest way to get `←`, `≤`, `≠` and powers.
