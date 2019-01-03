![Simple rules](latticeModelMashup/img/top.gif)
# Ultimate Lattice Model Monster Mashup

This app started off as an attempt to visualise different lattice models, and to see what happens when you mix a bunch of them together. It is currently very visually-oriented, though I intend to add some analytics later.

## Getting started
It is built using Python 3 and Qt5. Currently the pip install doesnt work because of pyqt5 (or maybe it does work but it takes forever to download, I'm not sure and I have terrible internet). So for now, if you want to use it to have to install Qt5 using `sudo apt-get install pyqt5-dev-tolls` or equivalent, then clone the repo and run `python3 __init__.py` from the latticeModelMashup folder.

To facilitate rapid testing, there are a few keyboard shortcuts:
* **E** starts a dynamic run. The length is determined by the 'frames' in the bottom right.
* **Esc** interrupts the current run, or closes the app if nothing is running. (Closing is pretty buggy.)
* **Q** clears the screen and adds some noise, determined by the coverage.
* **1** turns the stochastic noise engine on and off
* **2** turns the Life engine on and off
* **Z** steps forward one frame
* **B** paints the background with a cellular automaton
* **WASD** controlls the 'coverage' aka how much noise is added when you clear the scren and 'beta', which determines how noise the simulation is while running.
* **XC** controls the maximum FPS it will operate at. The two FPS values given at the top are the current performance of the two main engines, and the actual FPS is always limited to the lowest of these three values.
* **Alt** brings the focus out of a textbox, so you can use the keyboard shortcuts again after editing something.

A note on the update rules: currently rules of the following sort are permitted,
> a <= NB <= b

where a and b are the maximum and minimum number of neighbours (NB) that a cell can have and survive. So if a=1 and b=8 a cell will always survive. Standard Conway rules say cells survive with 2 or 3 neighbors.

> c <= P <= d

where c and d are the number of cells that, when surrounding an empty cell, will give birth (P -- 'parents') to a new cell. In Conway P=3.

So the standard Conway rule is '2,3,3,3;'.

Liberal parentage (c = 1,2) results in explosive growth. Unbounded parentage (d=6,7,8) results in violently oscillating populations when coupled with normal death rules.

Rules can also be chained, so for example 2,2,3,5;2,3,2,3;2,4,3,5;2,3,4,5; is a rad little combo that will result in a different update rule every frame in a cycle of four frames. Mix it with a good serving of noise at the start.

Turning the Ising model off (**1**) will result in deterministic runs, symmetrical if there was no noise at the start. 

The little area with the letters 'UB, LB, RB, WB, DB' is meant to be a sort of drawing of the screen-- the lines represent the edges. Anyway, here is where you control the boundary conditions. 1 means that boundary is fixed on, 0 fixed off and -1 means it is invisible (so the UB and DB wrap as do LB and RB, while WB ('wolfbound') just paints without interacting).

## About the models
The app is currently based on the following models:
- [x] **Ising Model** nice long-term behaviour when undisturbed by Conway, this model is rather overshadowed by the Life engine and tends only to act as a (very expensive) stochastic noise generator. Turn off conway (**2**) and turn up beta (**D**) and let it run for a while to see Ising at work.
- [x] **Conway's GoL** actually the engine is what they call 'Life-like' and can accept almost arbitrary rulesets. The rules are entered into the green box on the left. Some suggestions are below.
![Conway-style Life](latticeModelMashup/img/conway.gif)
- [x] **Cellular Automata** Wolfram-style cellular automata can be painted on the screen (**B**), and a scroller is also available that will either wipe out all the cells or paint on full cells. Currently there is no meaningful interaction between the 2D automata and the other models, it is largely aesthetic. Lets see what becomes of it.
![Advanced rules make more developed lifeforms](latticeModelMashup/img/advanced.gif)
- [ ] Potts Model is actually in there, or it was, but has been depreceated. This is a nice version of Ising with more states, but currently the models only have 2 states so this is inactive. Might bring it back.


## Features in Version 1
- Ising model
- Life-like automata with time-varying rules
- 'Wolfram' 2D automata painter
- Arbitrary boundary conditions on top, sides and scroller
- Colors!
- Basic recording function (makes gifs, very buggy)

## Features coming in Version 2
- Dynamic update of settings without having to restart
- Fancy shader graphics
- Faster engines, better integrated with one another
- Analytic engine, so you can automatically characterise different update rules
- Easy interaction, can paint different initial conditions onto the canvas
- Good support for exporting videos/ gifs

## Features planned:
- The fanciest graphics
- Automatic monsterfinder (looks for repeating patters with different update rules)
- More models! Including:
- [ ] **Prisoners Dilemma**
- [ ] **Eden Model**

![Here you can see the 'Wolfram' painter in the background](latticeModelMashup/img/bottom.gif)
