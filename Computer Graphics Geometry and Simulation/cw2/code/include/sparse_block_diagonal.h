#ifndef SPARSE_BLOCK_DIAGONAL_H
#define SPARSE_BLOCK_DIAGONAL_H
#include <iostream>
#include <vector>
#include <Eigen/Sparse>

// Function to create a block diagonal sparse matrix
void sparse_block_diagonal(const std::vector<Eigen::SparseMatrix<double>>& matrices, Eigen::SparseMatrix<double>& result) {
    using namespace Eigen;
    
    // Compute the total dimensions of the output matrix
    int totalRows = 0, totalCols = 0;
    for (const auto& mat : matrices) {
        totalRows += mat.rows();
        totalCols += mat.cols();
    }

    result.resize(totalRows, totalCols);
    result.setZero();  // Ensure the matrix is empty before inserting elements

    std::vector<Triplet<double>> triplets;

    // Place each matrix at the correct block diagonal position
    int rowOffset = 0, colOffset = 0;
    for (const auto& mat : matrices) {
        for (int k = 0; k < mat.outerSize(); ++k) {
            for (SparseMatrix<double>::InnerIterator it(mat, k); it; ++it) {
                triplets.emplace_back(it.row() + rowOffset, it.col() + colOffset, it.value());
            }
        }
        rowOffset += mat.rows();
        colOffset += mat.cols();
    }

    // Build the sparse matrix from triplets
    result.setFromTriplets(triplets.begin(), triplets.end());
}




#endif
