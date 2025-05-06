#ifndef READ_MESH_HEADER_FILE
#define READ_MESH_HEADER_FILE

#include <fstream>
#include <vector>
#include <sstream>
#include <iostream>
#include <Eigen/Dense>

using namespace std;
using namespace Eigen;



void readMESH(const std::string& filePath,
              Eigen::MatrixXd& vertices,
              Eigen::MatrixXi& faces,
              Eigen::MatrixXi& tets) {
  
  std::ifstream file(filePath);
  if (!file.is_open()) {
    std::cerr << "Error: Unable to open file " << filePath << std::endl;
    exit(EXIT_FAILURE);
  }
  
  int numVertices, numFaces, numTets;
  std::string header;
  
  for (int i = 0; i < 3; i++) std::getline(file, header);
  file >> numVertices;
  vertices.resize(numVertices, 3);
  for (int i = 0; i < numVertices; i++) {
    int temp;
    file >> vertices(i, 0) >> vertices(i, 1) >> vertices(i, 2) >> temp;
  }
  
  file >> header >> numFaces;
  faces.resize(numFaces, 3);
  for (int i = 0; i < numFaces; i++) {
    int temp;
    file >> faces(i, 0) >> faces(i, 1) >> faces(i, 2) >> temp;
  }
  
  file >> header >> numTets;
  tets.resize(numTets, 4);
  for (int i = 0; i < numTets; i++) {
    int temp;
    file >> tets(i, 0) >> tets(i, 1) >> tets(i, 2) >> tets(i, 3) >> temp;
  }
  
  if (faces.minCoeff() == 1) faces.array() -= 1;
  if (tets.minCoeff() == 1) tets.array() -= 1;
}

#endif
