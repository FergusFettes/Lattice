# Lattice
## Lattice Model Simulations

The goal is to make a little app for visualising different lattice models. Initially, there won't be any of the good analysis stuff that physicists normally do with these models-- to a computational physicist this work makes basically zero sense. But the analysis is computationally expensive and time-consuming-- to start with this is just a visualisation app.

The models that I will be starting with are:
- [x] **Ising & Potts**
- [x] **Conway's GoL** and cellular automata

> Well that went better than expected! Those three are basically done, couple of upgrades to be done in the GUI (so you can change automata settings and other things) and more options for integrating:

- [x] **Stochastic Game of Life** this is already working actually, GoL with a little bit of Ising thrown in. Actually I think it's the default setting.

Since adding things here seems to make them happen, lets see what happens if I write down the following:

- [ ] **Prisoners Dilemma**

- [ ] **Eden Model**

but actually I would like to make everything I have already harder, better, **faster** and, weather permitting, stronger before I move on. Let's see.

If it works out, I will also be trying to 'gamify' some of the models, or at least make them interactive (so you can paint into them and so forth). We'll see how that goes. And once I have a decent handle on moving pixels around I can perhaps start to experiment with mixtures of models etc. etc.

### To run
You need python3 and pyqt5. Also numpy. Then just run 'python3 latticeEXECUTE.py' in your terminal.
