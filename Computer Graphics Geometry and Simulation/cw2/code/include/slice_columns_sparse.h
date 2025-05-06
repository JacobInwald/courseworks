#ifndef SLICE_COLUMNS_SPARSE_HEADER_FILE
#define SLICE_COLUMNS_SPARSE_HEADER_FILE

#include <Eigen/Dense>


Eigen::SparseMatrix<double> slice_columns_sparse(const Eigen::SparseMatrix<double>& mat,
                                                 const Eigen::VectorXi& colIndices)
{
    // Number of rows in the original matrix
    int numRows = mat.rows();
    
    // Create the resulting sparse matrix
    Eigen::SparseMatrix<double> result(numRows, colIndices.size());
    std::vector<Eigen::Triplet<double>> triplets;
    
    // Iterate over selected columns and populate the result
    for (size_t i = 0; i < colIndices.size(); ++i) {
        int col = colIndices(i);
        for (Eigen::SparseMatrix<double>::InnerIterator it(mat, col); it; ++it) {
            triplets.emplace_back(it.row(), i, it.value());
        }
    }
    
    // Build the resulting matrix from triplets
    result.setFromTriplets(triplets.begin(), triplets.end());
    return result;
}


#endif
