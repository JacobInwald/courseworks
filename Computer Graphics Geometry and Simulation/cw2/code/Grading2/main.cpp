#include "scene.h"
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


int main()
{
    double section1Points = 10.0;
    int pointGain=0;
    int pointSum=0;
    double youngModulus=10000;
    double PoissonRatio = 0.3;
    double density=2.5;
    double alpha = 0.1, beta = 0.1, timeStep = 0.02;
    
    std::string folderPath(DATA_PATH); // Replace with your folder path
    std::ifstream ifs(DATA_PATH "/section2.data", std::ofstream::binary);
    
    Scene scene;
    scene.load_scene("fertility-scene.txt");
    scene.init_scene(timeStep, 0.1, 0.1);
    auto start = std::chrono::high_resolution_clock::now();
    for (int i=0;i<5;i++)
        scene.update_scene(timeStep);
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "update_scene() took " << (double)(duration.count())/1000.0 << " seconds to execute." << std::endl;
    VectorXd durVector(1); durVector<<(double)(duration.count())/1000.0;
    VectorXd durVectorGT;
    VectorXd globalVelocitiesGT, globalPositionsGT;
    deserializeVector(globalVelocitiesGT, ifs);
    deserializeVector(globalPositionsGT, ifs);
    deserializeVector(durVectorGT, ifs);
    
    pointSum+=2;
    if ((durVectorGT(0)*10.0 < (double)(duration.count())/1000.0)&&(durVectorGT(0)>1000.0)){
        cout<<"Running took too long! "<<endl;
    } else {
        int where;
        if ((globalVelocitiesGT-scene.globalVelocities).cwiseAbs().maxCoeff(&where)<=tolerance){
            cout<<"globalVelocities is good!"<<endl;
            pointGain++;
        } else {
            cout<<"globalVelocities("<<where<<")="<<scene.globalVelocities(where)<<", Ground-truth globalVelocities("<<where<<")="<<globalVelocitiesGT(where)<<endl;
        }
        if ((globalPositionsGT-scene.globalPositions).cwiseAbs().maxCoeff(&where)<=tolerance){
            cout<<"globalPositions is good!"<<endl;
            pointGain++;
        } else {
            cout<<"globalPositions("<<where<<")="<<scene.globalVelocities(where)<<", Ground-truth globalPositions("<<where<<")="<<globalVelocitiesGT(where)<<endl;
        }
    }
    cout<<"Total point gained: "<<pointGain<<"/"<<pointSum<<endl;
    cout<<"Grade for Section 2: "<<round((double)pointGain*section1Points/(double)pointSum)<<endl;
    
}

