# Program synthesis in the visual programming environment Algot
## General Information
Bachelor Thesis, Spring Semester 2022  
Author: Daniel Nezamabadi  
Supervisors: Prof. Dr. Zhendong Su, Sverrir Thorgeirsson  
Department of Computer Science, ETH Zurich

[Written report (pdf)](documents/written_report.pdf) - 
[Slides (pdf, formatting broke during export)](documents/presentation.pdf)

## Abstract
Programming, especially functional programming, is considered to be difficult. 
One difficulty for beginner programmers is the syntax of “classical” programming 
languages. In this thesis, we develop a prototype of a visual programming 
environment based on Algot and the programming-by-demonstration paradigm 
combined with the style of functional programming to introduce beginner 
programmers to functional programming without them having to learn the syntax 
of a classical functional programming language. To evaluate our prototype,
we conduct a qualitative study with two participants. Our results show
that while the graphical user interface of the prototype requires more
work, the prototype has the potential to become a valuable tool for
introducing students to the key ideas of functional programming.

## Dependencies
* [Python](https://www.python.org/) (at least version 3.10)
* [PyQt5](https://pypi.org/project/PyQt5/)

## Starting the prototype
Run `runner.py` located in the `code` directory using Python:  
```
python runner.py
```
Make sure that you have installed PyQt5 and are using Python 3.10 (or later).
