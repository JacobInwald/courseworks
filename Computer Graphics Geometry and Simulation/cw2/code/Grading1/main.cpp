#include "readOFF.h"
#include "mesh.h"
#include "serialization.h"
#include <Eigen/Dense>
#include <iostream>
#include <fstream>
#include <random>
#include <chrono>
#include <filesystem>

using namespace Eigen;
using namespace std;


double tolerance = 1e-3;

namespace fs = std::filesystem;

double max_sparse(const Eigen::SparseMatrix<double>& mat, int &rowIndex, int &colIndex){
    double maxValue = -1;
    for (int k=0; k<mat.outerSize(); ++k)
        for (SparseMatrix<double>::InnerIterator it(mat,k); it; ++it)
        {
            if (std::isnan(it.value())){
                rowIndex  = it.row();
                colIndex = it.col();
                return std::numeric_limits<double>::quiet_NaN();
            }
                        
            if (abs(it.value())>maxValue){
                maxValue = it.value();
                rowIndex  = it.row();
                colIndex = it.col();
            }
        }
    return maxValue;
}


int main()
{
    double section1Points = 50.0;
    int pointGain=0;
    int pointSum=0;
    double youngModulus=10000;
    double PoissonRatio = 0.3;
    double density=2.5;
    double alpha = 0.1, beta = 0.1, timeStep = 0.02;
    std::string folderPath(DATA_PATH); // Replace with your folder path
    for (const auto& entry : fs::directory_iterator(folderPath)) {
        if (entry.is_regular_file() && entry.path().extension() == ".mesh") {
            cout<<"Working on file "<<entry.path().filename()<<endl;
            std::string dataName = entry.path().string();
            dataName.erase(dataName.size() - 5, 5);
            std::ifstream ifs(dataName+"-section1.data", std::ofstream::binary);
            
            MatrixXd objV;
            MatrixXi objF, objT;
            readMESH(entry.path().string(),objV,objF, objT);
            MatrixXi tempF(objF.rows(),3);
            tempF<<objF.col(2), objF.col(1), objF.col(0);
            objF=tempF;
            
            VectorXd Vxyz(3*objV.rows());
            for (int i=0;i<objV.rows();i++)
                Vxyz.segment(3*i,3)=objV.row(i).transpose();
            
            //cout<<"Vxyz: "<<Vxyz<<endl;
            Mesh m(Vxyz,objF, objT, 0, youngModulus, PoissonRatio, density, false, RowVector3d::Zero(), {1.0,0.0,0.0,0.0});
            
            auto start = std::chrono::high_resolution_clock::now();
            m.create_global_matrices(timeStep, alpha, beta);
            auto end = std::chrono::high_resolution_clock::now();
            auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
            std::cout << "create_global_matrices() took " << (double)(duration.count())/1000.0 << " seconds to execute." << std::endl;
            VectorXd durVector(1); durVector<<(double)(duration.count())/1000.0;
            VectorXd durVectorGT;
            SparseMatrix<double> MGT, KGT, DGT;
            deserializeSparseMatrix(MGT, ifs);
            deserializeSparseMatrix(KGT, ifs);
            deserializeSparseMatrix(DGT, ifs);
            deserializeVector(durVectorGT, ifs);
            
            pointSum+=3;
            if ((durVectorGT(0)*10.0 < (double)(duration.count())/1000.0)&&(durVectorGT(0)>1000.0)){
                cout<<"Running took too long! "<<endl;
            } else {
                 int rowIndex, colIndex;
                double maxValue = max_sparse(MGT-m.M, rowIndex, colIndex);
                if ((maxValue<=tolerance)&&(!std::isnan(maxValue))){
                    cout<<"M is good!"<<endl;
                    pointGain++;
                } else {
                    cout<<"M("<<rowIndex<<","<<colIndex<<")="<<m.M.coeff(rowIndex, colIndex)<<", Ground-truth M("<<rowIndex<<","<<colIndex<<")="<<MGT.coeff(rowIndex, colIndex)<<endl;
                }
                maxValue = max_sparse(KGT-m.K, rowIndex, colIndex);
                if ((maxValue<=tolerance)&&(!std::isnan(maxValue))){
                    cout<<"K is good!"<<endl;
                    pointGain++;
                } else {
                    cout<<"K("<<rowIndex<<","<<colIndex<<")="<<m.K.coeff(rowIndex, colIndex)<<", Ground-truth K("<<rowIndex<<","<<colIndex<<")="<<KGT.coeff(rowIndex, colIndex)<<endl;
                }
                maxValue = max_sparse(DGT-m.D, rowIndex, colIndex);
                if ((maxValue<=tolerance)&&(!std::isnan(maxValue))){
                    cout<<"D is good!"<<endl;
                    pointGain++;
                } else {
                    cout<<"D("<<rowIndex<<","<<colIndex<<")="<<m.D.coeff(rowIndex, colIndex)<<", Ground-truth D("<<rowIndex<<","<<colIndex<<")="<<DGT.coeff(rowIndex, colIndex)<<endl;
                }
            }
        }
    }
    cout<<"Total point gained: "<<pointGain<<"/"<<pointSum<<endl;
    cout<<"Grade for Section 1: "<<round((double)pointGain*section1Points/(double)pointSum)<<endl;
}

