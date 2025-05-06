#ifndef SPARSE_BLOCK_H
#define SPARSE_BLOCK_H
#include <Eigen/Core>
#include <Eigen/Sparse>
#include <string>
#include <vector>
#include <cstdio>
#include <set>



void sparse_block(const Eigen::MatrixXi& blockIndices,
                  const std::vector<Eigen::SparseMatrix<double>>& blockMats,
                  Eigen::SparseMatrix<double>& result){
    
    //assessing dimensions
    Eigen::VectorXi blockRowOffsets=Eigen::VectorXi::Zero(blockIndices.rows());
    Eigen::VectorXi blockColOffsets=Eigen::VectorXi::Zero(blockIndices.cols());
    for (int i=1;i<blockIndices.rows();i++)
        blockRowOffsets(i)=blockRowOffsets(i-1)+ blockMats[blockIndices(i-1,0)].rows();
    
    for (int i=1;i<blockIndices.cols();i++)
        blockColOffsets(i)=blockColOffsets(i-1)+ blockMats[blockIndices(0,i-1)].cols();
    
    int rowSize=blockRowOffsets(blockIndices.rows()-1)+ blockMats[blockIndices(blockIndices.rows()-1,0)].rows();
    int colSize=blockColOffsets(blockIndices.cols()-1)+ blockMats[blockIndices(0,blockIndices.cols()-1)].cols();
    
    result.conservativeResize(rowSize, colSize);
    std::vector<Eigen::Triplet<double>> resultTriplets;
    
    for (int i=0;i<blockIndices.rows();i++){
        for (int j=0;j<blockIndices.cols();j++){
            int currMat = blockIndices(i,j);
            for (int k=0; k<blockMats[currMat].outerSize(); ++k)
                for (typename Eigen::SparseMatrix<double>::InnerIterator it(blockMats[currMat],k); it; ++it)
                    resultTriplets.push_back(Eigen::Triplet<double>(blockRowOffsets(i)+it.row(),blockColOffsets(j)+it.col(),it.value()));
        }
    }
    
    result.setFromTriplets(resultTriplets.begin(), resultTriplets.end());
    
}

#endif
