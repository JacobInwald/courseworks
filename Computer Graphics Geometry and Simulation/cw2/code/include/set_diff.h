#ifndef SET_DIFF_HEADER_FILE
#define SET_DIFF_HEADER_FILE

#include <Eigen/Dense>
#include <set>

Eigen::VectorXi set_diff(const Eigen::VectorXi& A,
                         const Eigen::VectorXi& B) {
    std::set<int> setB;
    for (int i = 0; i < B.size(); ++i) {
        setB.insert(B[i]);
    }
    
    std::vector<int> result;
    for (int i = 0; i < A.size(); ++i) {
        if (setB.find(A[i]) == setB.end()) {
            result.push_back(A[i]);
        }
    }
    
    // Convert result to Eigen::VectorXi
    Eigen::VectorXi diff(result.size());
    for (size_t i = 0; i < result.size(); ++i) {
        diff[i] = result[i];
    }
    
    return diff;
}

#endif
