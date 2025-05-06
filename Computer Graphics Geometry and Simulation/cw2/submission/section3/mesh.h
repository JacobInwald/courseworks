#ifndef MESH_HEADER_FILE
#define MESH_HEADER_FILE

#include <vector>
#include <fstream>
#include "readMESH.h"
#include "auxfunctions.h"
#include "sparse_block_diagonal.h"
#include <Eigen/Dense>
#include <Eigen/Sparse>

using namespace Eigen;
using namespace std;


//the class the contains each individual rigid objects and their functionality
class Mesh{
public:
    
    //position
    VectorXd origPositions;     //3|V|x1 original vertex positions in xyzxyz format - never change this!
    VectorXd currPositions;     //3|V|x1 current vertex positions in xyzxyz format
    
    //kinematics
    bool isFixed;               //is the object immobile (infinite mass)
    VectorXd currVelocities;    //3|V|x1 velocities per coordinate in xyzxyz format.
    
    double totalInvMass;
    
    MatrixXi T;                 //|T|x4 tetrahdra
    MatrixXi F;                 //|F|x3 boundary faces
    VectorXd invMasses;         //|V|x1 inverse masses of vertices, computed in the beginning as 1.0/(density * vertex voronoi area)
    VectorXd voronoiVolumes;    //|V|x1 the voronoi volume of vertices
    VectorXd tetVolumes;        //|T|x1 tetrahedra volumes
    int globalOffset;           //the global index offset of the of opositions/velocities/impulses from the beginning of the global coordinates array in the containing scene class
    
    VectorXi boundTets;  //just the boundary tets, for collision
    
    double youngModulus, poissonRatio, density, alpha, beta;
    
    SparseMatrix<double> K, M, D;   //The soft-body matrices
    
    //SimplicialLLT<SparseMatrix<double>>* ASolver;   //the solver for the left-hand side matrix constructed for FEM
    
    ~Mesh(){/*if (ASolver!=NULL) delete ASolver;*/}
    
    
    
    bool isNeighborTets(const RowVector4i& tet1, const RowVector4i& tet2){
        for (int i=0;i<4;i++)
            for (int j=0;j<4;j++)
                if (tet1(i)==tet2(j)) //shared vertex
                    return true;
        
        return false;
    }
   
    // Creates the Mass matrix M
    void compute_mass_matrix(SparseMatrix<double>& M) {
      // Initialize M as a sparse matrix with the correct size
      M.resize(currPositions.size(), currPositions.size());
      
      // Create triplets to build the sparse matrix
      std::vector<Triplet<double>> MTriplets;
      MTriplets.reserve(currPositions.size()); // For diagonal mass matrix
      
      // Create diagonal mass matrix using voronoiVolumes already computed
      for (int i = 0; i < voronoiVolumes.size(); i++) {
          // Calculate mass using density and voronoi volume
          double mass = voronoiVolumes(i) * density;
          
          // If this vertex belongs to a fixed mesh, set mass to effectively infinite
          // (or in practice, zero for the inverse mass)
          if (isFixed) {
              mass = std::numeric_limits<double>::max();
          }
          
          // Add diagonal entries for x, y, z components
          for (int d = 0; d < 3; d++) {
              MTriplets.push_back(Triplet<double>(3*i+d, 3*i+d, mass));
          }
      }
      
      // Build the sparse matrix from triplets
      M.setFromTriplets(MTriplets.begin(), MTriplets.end());
    }

    // Creates Ke for a given tet
    SparseMatrix<double> create_element_stiffness_matrix(const Vector4i &tet) {
        // Compute matrix P
        Matrix4d Pe;
        for (int i = 0; i < 4; i++) {
            Pe(i, 0) = 1.0;
            Pe(i, 1) = origPositions(3 * tet(i) + 0); // x
            Pe(i, 2) = origPositions(3 * tet(i) + 1); // y
            Pe(i, 3) = origPositions(3 * tet(i) + 2); // z
        }

        // Compute gradient matrix G
        Matrix<double,3,4> Ge = Pe.inverse().block<3,4>(1,0);

        // Compute exact volume of the tetrahedron (using determinant of Pe)
        double volume = std::abs(Pe.determinant()) / 6.0;

        // Lamé parameters
        double mu = youngModulus / (2.0 * (1.0 + poissonRatio));
        double lambda = (youngModulus * poissonRatio) / ((1.0 + poissonRatio) * (1.0 - 2.0 * poissonRatio));
        

        // Stiffness Tensor C
        Matrix<double, 6, 6> C = Matrix<double, 6, 6>::Zero();
        C(0,0) = lambda + 2.0*mu;  C(0,1) = lambda;          C(0,2) = lambda;
        C(1,0) = lambda;           C(1,1) = lambda + 2.0*mu; C(1,2) = lambda;
        C(2,0) = lambda;           C(2,1) = lambda;          C(2,2) = lambda + 2.0*mu;
        C(3,3) = 2*mu;
        C(4,4) = 2*mu;
        C(5,5) = 2*mu;

        // Build the matrix B explicitly (D J u) as in Lecture notes
        Matrix<double, 6, 12> B = Matrix<double, 6, 12>::Zero();
        for (int i = 0; i < 4; i++) {
            double dNx = Ge(0, i);
            double dNy = Ge(1, i);
            double dNz = Ge(2, i);
            int col = 3 * i;

            B(0, col + 0) = dNx;
            B(1, col + 1) = dNy;
            B(2, col + 2) = dNz;
            B(3, col + 0) = 0.5 * dNy; B(3, col + 1) = 0.5 * dNx;
            B(4, col + 1) = 0.5 * dNz; B(4, col + 2) = 0.5 * dNy;
            B(5, col + 2) = 0.5 * dNx; B(5, col + 0) = 0.5 * dNz;
        }

        // Compute the element stiffness matrix Ke = B^T * C * B * volume
        Matrix<double, 12, 12> Ke_linear = B.transpose() * C * B * volume;
        
        // ======= Corotational Element ========

        // Construct stacked matrices P and Q
        Matrix<double,3,3> P, Q;

        for (int i = 0; i < 3; i++) {
            // Original undeformed edges
            Vector3d x0 = origPositions.segment<3>(3 * tet(0));   // x1
            Vector3d xi = origPositions.segment<3>(3 * tet(i+1)); // xn
            P.col(i) = x0 - xi; 
           
            // Current deformed edges
            x0 = currPositions.segment<3>(3 * tet(0));   // x1'
            xi = currPositions.segment<3>(3 * tet(i+1)); // xn'
            Q.col(i) = x0 - xi;
        }

        // Compute rotation matrix S and use SVD to get R 
        Matrix3d S = P.transpose() * Q;
        JacobiSVD<Matrix3d> svd(S, ComputeFullU | ComputeFullV);
        Matrix3d R = svd.matrixV() * svd.matrixU().transpose();
        
        // Ensure R is a rotation (det(R) positive)
        if (R.determinant() < 0.0) {
            Matrix3d V = svd.matrixV();
            V.col(2) *= -1.0;
            R = V * svd.matrixU().transpose();
        }

        // Construct the larger rotational element so it applies it to all 
        //  vertices within the tet
        Matrix<double, 12, 12> Re = Matrix<double, 12, 12>::Zero();
        for (int i = 0; i < 4; ++i) {
            Re.block<3,3>(3*i, 3*i) = R;
        }
        // Corotational stiffness matrix (from lecture slides: K' = R*K*R-1)
        // R tranpose is the same as the inverse 
        Matrix<double, 12, 12> Ke_corot = Re * Ke_linear * Re.transpose();

        return Ke_corot.sparseView();
    }


    // Create the permutation matrix Q
    void create_permutation_matrix(SparseMatrix<double> &Q) {
        int T_count = T.rows();                        // number of tetrahedra
        int numVerts = origPositions.size() / 3;         // number of vertices
        int rows = 12 * T_count;                         // local DOF count
        int cols = 3 * numVerts;                         // global DOF count
        
        std::vector<Triplet<double>> triplets;
        triplets.reserve(12 * T_count);
        
        // For each tetrahedron e, for each local vertex i, for each coordinate di:
        // localDOF index = 12*e + 3*i + di, and maps to globalDOF = 3*(T(e,i)) + di.
        for (int e = 0; e < T_count; e++) {
            for (int i = 0; i < 4; i++) {
                int vertexIndex = T(e, i);
                for (int di = 0; di < 3; di++) {
                    int localDOF = 12 * e + 3 * i + di;
                    int globalDOF = 3 * vertexIndex + di;
                    triplets.emplace_back(localDOF, globalDOF, 1.0);
                }
            }
        }
        Q.resize(rows, cols);
        Q.setFromTriplets(triplets.begin(), triplets.end());
    }

    
    // Construct the final K matrix
    void compute_stiffness_matrix(SparseMatrix<double> &K) {
        int T_count = T.rows();  // number of tetrahedra
        int dimKprime = 12 * T_count;
        
        // 1. Build the block-diagonal matrix Kprime by computing each element's stiffness matrix.
        std::vector<SparseMatrix<double>> Kes;
        SparseMatrix<double> Kprime(dimKprime, dimKprime);
        
        for (int e = 0; e < T_count; e++) {
            // Get the tetrahedron's vertex indices.
            Vector4i tet = T.row(e);
            // Compute the element stiffness matrix.
            SparseMatrix<double> Ke = create_element_stiffness_matrix(tet);
            Kes.push_back(Ke);
            
        }
        
        // Stack Matrices 
        sparse_block_diagonal(Kes, Kprime);

        // 2. Build the assembly (permutation) matrix Q.
        SparseMatrix<double> Q;
        create_permutation_matrix(Q);
        
        // 3. Assemble the global stiffness matrix: K = Q^T * Kprime * Q.
        K = Q.transpose() * Kprime * Q;
    }


    //Computing the K, M, D matrices per mesh.
    void create_global_matrices(const double timeStep, const double _alpha, const double _beta)
    {
      compute_stiffness_matrix(K);
      compute_mass_matrix(M); 
      D = _alpha*M + _beta*K;
    }


    //returns center of mass
    Vector3d initializeVolumesAndMasses()
    {
        tetVolumes.conservativeResize(T.rows());
        voronoiVolumes.conservativeResize(origPositions.size()/3);
        voronoiVolumes.setZero();
        invMasses.conservativeResize(origPositions.size()/3);
        Vector3d COM; COM.setZero();
        for (int i=0;i<T.rows();i++){
            Vector3d e01=origPositions.segment(3*T(i,1),3)-origPositions.segment(3*T(i,0),3);
            Vector3d e02=origPositions.segment(3*T(i,2),3)-origPositions.segment(3*T(i,0),3);
            Vector3d e03=origPositions.segment(3*T(i,3),3)-origPositions.segment(3*T(i,0),3);
            Vector3d tetCentroid=(origPositions.segment(3*T(i,0),3)+origPositions.segment(3*T(i,1),3)+origPositions.segment(3*T(i,2),3)+origPositions.segment(3*T(i,3),3))/4.0;
            tetVolumes(i)=std::abs(e01.dot(e02.cross(e03)))/6.0;
            for (int j=0;j<4;j++)
                voronoiVolumes(T(i,j))+=tetVolumes(i)/4.0;
            
            COM+=tetVolumes(i)*tetCentroid;
        }
        
        COM.array()/=tetVolumes.sum();
        totalInvMass=0.0;
        for (int i=0;i<origPositions.size()/3;i++){
            invMasses(i)=1.0/(voronoiVolumes(i)*density);
            totalInvMass+=voronoiVolumes(i)*density;
        }
        totalInvMass = 1.0/totalInvMass;
        
        return COM;
        
    }
    
    Mesh(const VectorXd& _origPositions, const MatrixXi& boundF, const MatrixXi& _T, const int _globalOffset, const double _youngModulus, const double _poissonRatio, const double _density, const bool _isFixed, const RowVector3d& userCOM, const RowVector4d& userOrientation){
        origPositions=_origPositions;
        //cout<<"original origPositions: "<<origPositions<<endl;
        T=_T;
        F=boundF;
        isFixed=_isFixed;
        globalOffset=_globalOffset;
        density=_density;
        poissonRatio=_poissonRatio;
        youngModulus=_youngModulus;
        currVelocities=VectorXd::Zero(origPositions.rows());
        
        VectorXd naturalCOM=initializeVolumesAndMasses();
        //cout<<"naturalCOM: "<<naturalCOM<<endl;
        
        
        origPositions-= naturalCOM.replicate(origPositions.rows()/3,1);  //removing the natural COM of the OFF file (natural COM is never used again)
        //cout<<"after natrualCOM origPositions: "<<origPositions<<endl;
        
        for (int i=0;i<origPositions.size();i+=3)
            origPositions.segment(i,3) = (QRot(origPositions.segment(i,3).transpose(), userOrientation)+userCOM).transpose();
        
        currPositions=origPositions;
        
        if (isFixed)
            invMasses.setZero();
        
        //finding boundary tets
        VectorXi boundVMask(origPositions.rows()/3);
        boundVMask.setZero();
        for (int i=0;i<boundF.rows();i++)
            for (int j=0;j<3;j++)
                boundVMask(boundF(i,j))=1;
        
        //cout<<"boundVMask.sum(): "<<boundVMask.sum()<<endl;
        
        vector<int> boundTList;
        for (int i=0;i<T.rows();i++){
            int incidence=0;
            for (int j=0;j<4;j++)
                incidence+=boundVMask(T(i,j));
            if (incidence>2)
                boundTList.push_back(i);
        }
        
        boundTets.resize(boundTList.size());
        for (int i=0;i<boundTets.size();i++)
            boundTets(i)=boundTList[i];
        
    }
    
};





#endif
