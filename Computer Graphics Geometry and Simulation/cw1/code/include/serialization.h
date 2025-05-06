#ifndef SERIALIZATION_HEADER_FILE
#define SERIALIZATION_HEADER_FILE

#include <Eigen/Dense>
#include <vector>
#include <iostream>
#include <fstream>


template<typename Scalar>
void serializeMatrix(const Eigen::Matrix<Scalar, Eigen::Dynamic, Eigen::Dynamic>& mat, std::ofstream& ofs) {
  
  // Write rows and columns
  int rows = mat.rows();
  int cols = mat.cols();
  ofs.write(reinterpret_cast<const char*>(&rows), sizeof(rows));
  ofs.write(reinterpret_cast<const char*>(&cols), sizeof(cols));
  
  // Write elements row by row
  for (int i = 0; i < rows; i++) {
    for (int j = 0; j < cols; j++) {
      Scalar value = mat(i, j);
      ofs.write(reinterpret_cast<const char*>(&value), sizeof(value));
    }
  }
}

template<typename Scalar>
void serializeVector(const Eigen::Matrix<Scalar, Eigen::Dynamic, 1>& vec, std::ofstream& ofs) {
  
  // Write rows and columns
  int size = vec.size();
  ofs.write(reinterpret_cast<const char*>(&size), sizeof(size));
  
  // Write elements row by row
  for (int i = 0; i < size; i++) {
    Scalar value = vec(i);
    ofs.write(reinterpret_cast<const char*>(&value), sizeof(value));
  }
}

// Function to deserialize a MatrixXd
template<typename Scalar>
void deserializeMatrix(Eigen::Matrix<Scalar, Eigen::Dynamic, Eigen::Dynamic>& mat, std::ifstream& ifs) {
  
  // Read rows and columns
  int rows, cols;
  ifs.read(reinterpret_cast<char*>(&rows), sizeof(rows));
  ifs.read(reinterpret_cast<char*>(&cols), sizeof(cols));
  
  if (rows <= 0 || cols <= 0) {
    throw std::runtime_error("Invalid matrix dimensions in file.");
  }
  
  // Resize the matrix
  mat.resize(rows, cols);
  
  // Read elements row by row
  for (int i = 0; i < rows; i++) {
    for (int j = 0; j < cols; j++) {
      Scalar value;
      ifs.read(reinterpret_cast<char*>(&value), sizeof(value));
      mat(i, j) = value;
    }
  }
}

template<typename Scalar>
void deserializeVector(Eigen::Matrix<Scalar, Eigen::Dynamic, 1>& vec, std::ifstream& ifs) {
  
  // Read rows and columns
  int size;
  ifs.read(reinterpret_cast<char*>(&size), sizeof(size));
  
  if (size <= 0) {
    throw std::runtime_error("Invalid vector dimensions in file.");
  }
  
  // Resize the matrix
  vec.resize(size);
  
  // Read elements row by row
  for (int i = 0; i < size; i++) {
    Scalar value;
    ifs.read(reinterpret_cast<char*>(&value), sizeof(value));
    vec(i) = value;
  }
}

#endif
