#ifndef SORTROWS_HEADER_FILE
#define SORTROWS_HEADER_FILE

#include <eigen/dense>
#include <vector>

using namespace Eigen;

void sort_rows(MatrixXi& matrix) {
  for (int i = 0; i < matrix.rows(); i++) {
    std::vector<int> row;
    row.reserve(matrix.cols());
    for (int j = 0; j < matrix.cols(); ++j) {
      row.push_back(matrix(i, j));
    }
    std::sort(row.begin(), row.end());
    for (int j = 0; j < matrix.cols(); ++j) {
      matrix(i, j) = row[j];
    }
  }
}

#endif
