# Computer Graphics: Geometry and Simulation---Coursework 2---Simulation

This is the repository for the skeleton code of the entire coursework. To get the repository, write in a terminal:

```
git clone --recurse-submodules https://github.com/avaxman/CGGS-CW2-Simulation.git

```

The PDF for the instructions is included.

In an OSX/Linux environment, you next need to go to the `code` subfolder and write:
```
mkdir build
cd build
cmake ..
make
```

This will compile in Debug mode. To compile in Release mode, do:
```
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
make
```
Alternatively, you can use the `-G` option in `cmake` and create a solution for your chosen C++ IDE (for instance, `-G Xcode`).

In a Windows environment, you'll likely need [CMake-GUI](https://cmake.org/download/), where you load the CMake older, click `configure` twice, and then `generate`. You will need to install an IDE and compiler beforehand, so you may choose it when it prompts you to.

the rest of the instructions can be found in the PDF in the main folder here.
