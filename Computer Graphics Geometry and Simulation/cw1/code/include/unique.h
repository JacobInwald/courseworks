#ifndef UNIQUE_HEADER_FILE
#define UNIQUE_HEADER_FILE

#include <Eigen/Dense>
#include <map>
#include <vector>


void unique(const Eigen::MatrixXi& matrix,
            std::vector<int>& uniqueIndices,
            std::vector<int>& counts,
            std::vector<int>& inverse) {
  // Clear output vectors to ensure a fresh start
  uniqueIndices.clear();
  counts.clear();
  inverse.clear();
  
  // Use a map to track unique rows
  std::map<std::vector<int>, int> rowToIndex;  // Maps row (as a vector) to its first occurrence index
  std::vector<std::vector<int>> uniqueRows;   // To store unique rows for counting purposes
  
  for (int i = 0; i < matrix.rows(); ++i) {
    // Convert the current row to a std::vector for comparison
    std::vector<int> row;
    row.reserve(matrix.cols());
    for (int j = 0; j < matrix.cols(); ++j) {
      row.push_back(matrix(i, j));  // Access each element directly
    }
    if (rowToIndex.find(row) == rowToIndex.end()) {
      // If the row is not yet recorded, record its first occurrence
      rowToIndex[row] = uniqueIndices.size();
      uniqueIndices.push_back(i);       // Store the index of first appearance
      uniqueRows.push_back(row);       // Add to unique rows
    }
    // Map the original row index to its unique row index
    inverse.push_back(rowToIndex[row]);
  }
  
  // Compute counts of each unique row
  counts.resize(uniqueRows.size(), 0);  // Initialize counts to 0
  for (int i = 0; i < matrix.rows(); ++i) {
    std::vector<int> row;
    row.reserve(matrix.cols());
    for (int j = 0; j < matrix.cols(); ++j) {
      row.push_back(matrix(i, j));  // Access each element directly
    }
    counts[rowToIndex[row]]++;
  }
}


#endif
