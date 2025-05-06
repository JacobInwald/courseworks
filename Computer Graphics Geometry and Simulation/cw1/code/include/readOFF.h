#ifndef READ_OFF_H
#define READ_OFF_H
#include <cmath>
#include <Eigen/Core>
#include <string>
#include <sys/types.h>
#include <sys/stat.h>
#include <fstream>
#include <cassert>
#include <iostream>


//wraps around libigl readOFF to return a mesh object.
bool inline readOFF(const std::string off_file_name,
                    Eigen::MatrixXd& V,
                    Eigen::MatrixXi& F){
    
    std::ifstream file(off_file_name);
    if (!file.is_open()) {
        std::cout << "Failed to open OFF file" << std::endl;
        return false;
    }
    
    std::string line;
    int numVertices, numFaces;
    file >> line >> numVertices >> numFaces;
    std::getline(file, line); // Skip remaining characters on first line
    
    V.resize(numVertices, 3);
    for (int i = 0; i < numVertices; ++i)
        file >> V(i,0) >> V(i,1) >> V(i,2);
    
    F.resize(numFaces,3);
    for (int i = 0; i < numFaces; ++i) {
        int numVerticesPerFace;
        file >> numVerticesPerFace;
        assert(numVerticesPerFace==3 && "readOFF() is only intended for triangle meshes.");
        file >> F(i,0) >> F(i,1) >> F(i,2);
    }
    return true;
}


#endif
