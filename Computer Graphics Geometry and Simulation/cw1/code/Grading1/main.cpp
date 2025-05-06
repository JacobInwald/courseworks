#include "mesh.h"
#include "scene.h"
#include "serialization.h"
#include <Eigen/Dense>
#include <iostream>
#include <fstream>
#include <random>
#include <chrono>
#include <filesystem>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

using namespace Eigen;
using namespace std;

double tolerance = 1e-5;

namespace fs = std::filesystem;
std::random_device rd;
std::mt19937 gen;

void generate_random_values(Eigen::MatrixXd& mat, double min_val, double max_val) {
  
  std::uniform_real_distribution<double> dis(min_val, max_val);
  
  for (int i = 0; i < mat.rows(); ++i) {
    for (int j = 0; j < mat.cols(); ++j) {
      mat(i, j) = dis(gen);
    }
  }
}

Eigen::MatrixXd random_vectors_in_sphere(double radius, int num_samples) {
  std::uniform_real_distribution<double> theta_dist(0, M_PI);
  std::uniform_real_distribution<double> phi_dist(0, 2 * M_PI);
  std::uniform_real_distribution<double> r_dist(0, 1);
  
  Eigen::MatrixXd samples(num_samples, 3);
  
  for (int i = 0; i < num_samples; ++i) {
    double theta = theta_dist(gen);
    double phi = phi_dist(gen);
    double r = radius * std::cbrt(r_dist(gen)); // cubic root to ensure uniform distribution
    
    double x = r * std::sin(theta) * std::cos(phi);
    double y = r * std::sin(theta) * std::sin(phi);
    double z = r * std::cos(theta);
    
    samples.row(i) << x, y, z;
  }
  
  return samples;
}


int main()
{
  int numSamples = 100;
  double CRCoeff = 0.5;
  gen = std::mt19937(rd());
  Eigen::MatrixXd randomLinVelocities(numSamples, 3);
  Eigen::MatrixXd randomAngVelocities(numSamples, 3);
  Eigen::MatrixXd randomPositions(numSamples, 3);
  Eigen::MatrixXd randomOrientations(numSamples, 4);
  
  generate_random_values(randomLinVelocities, -10, 10);
  generate_random_values(randomAngVelocities, -10, 10);
  generate_random_values(randomPositions, -10, 10);
  generate_random_values(randomOrientations, -10, 10);
  
  Eigen::MatrixXd resultLinVelocities = Eigen::MatrixXd::Zero(numSamples, 3);
  Eigen::MatrixXd resultAngVelocities = Eigen::MatrixXd::Zero(numSamples, 3);
  Eigen::MatrixXd resultPositions = Eigen::MatrixXd::Zero(numSamples, 3);
  Eigen::MatrixXd resultOrientations = Eigen::MatrixXd::Zero(numSamples, 4);
  double section1Points = 20.0;
  double integrationGrade=0.0, collisionGrade = 0.0;
  MatrixXd V1,V2;
  MatrixXi F1,F2,T1,T2;
  
  /******************Testing integration***************************/
  cout<<"Testing Integration"<<endl;
  std::string folderPath(DATA_PATH); // Replace with your folder path
  std::ifstream ifs(folderPath+"/integration.data", std::ofstream::binary);
  deserializeMatrix(randomPositions,ifs);
  deserializeMatrix(randomOrientations,ifs);
  deserializeMatrix(randomLinVelocities,ifs);
  deserializeMatrix(randomAngVelocities,ifs);
  Eigen::MatrixXd resultLinVelocitiesGT, resultAngVelocitiesGT;
  Eigen::MatrixXd resultPositionsGT, resultOrientationsGT;
  deserializeMatrix(resultPositionsGT,ifs);
  deserializeMatrix(resultOrientationsGT,ifs);
  deserializeMatrix(resultLinVelocitiesGT,ifs);
  deserializeMatrix(resultAngVelocitiesGT,ifs);
  for (int i=0;i<randomPositions.rows();i++){
    Mesh dummyMesh(MatrixXd::Zero(0,3), MatrixXi::Zero(0,3), MatrixXi::Zero(0,4), 1.0, false, randomPositions.row(i), randomOrientations.row(i));
    dummyMesh.comVelocity=randomLinVelocities.row(i);
    dummyMesh.angVelocity=randomAngVelocities.row(i);
    dummyMesh.integrate(0.5);
    resultLinVelocities.row(i)=dummyMesh.comVelocity;
    resultAngVelocities.row(i)=dummyMesh.angVelocity;
    resultPositions.row(i)=dummyMesh.COM;
    resultOrientations.row(i)=dummyMesh.orientation;
  }
  ifs.close();
  int maxRow, maxCol;
  
  if ((resultPositionsGT-resultPositions).cwiseAbs().maxCoeff(&maxRow, &maxCol)>tolerance){
    cout<<"COM result differs on sample "<<maxRow<<endl;
    cout<<"GT: "<<resultPositionsGT.row(maxRow)<<endl;
    cout<<"Your result: "<<resultPositions.row(maxRow)<<endl;
  } else{
    cout<<"COM result is good! "<<endl;
    integrationGrade+=2.5;
  }
  if ((resultOrientationsGT-resultOrientations).cwiseAbs().maxCoeff(&maxRow, &maxCol)>tolerance){
    cout<<"COM result differs on sample "<<maxRow<<endl;
    cout<<"GT: "<<resultOrientationsGT.row(maxRow)<<endl;
    cout<<"Your result: "<<resultOrientations.row(maxRow)<<endl;
  } else{
    cout<<"Orientation result is good! "<<endl;
    integrationGrade+=2.5;
  }
  if ((resultLinVelocitiesGT-resultLinVelocities).cwiseAbs().maxCoeff(&maxRow, &maxCol)>tolerance){
    cout<<"COM velocity result differs on sample "<<maxRow<<endl;
    cout<<"GT: "<<resultLinVelocitiesGT.row(maxRow)<<endl;
    cout<<"Your result: "<<resultLinVelocities.row(maxRow)<<endl;
  } else{
    cout<<"COM velocity result is good! "<<endl;
    integrationGrade+=2.5;
  }
  if ((resultAngVelocitiesGT-resultAngVelocities).cwiseAbs().maxCoeff(&maxRow, &maxCol)>tolerance){
    cout<<"COM velocity result differs on sample "<<maxRow<<endl;
    cout<<"GT: "<<resultAngVelocitiesGT.row(maxRow)<<endl;
    cout<<"Your result: "<<resultAngVelocities.row(maxRow)<<endl;
  } else{
    cout<<"Angular velocity result is good! "<<endl;
    integrationGrade+=2.5;
  }
  cout<<"Grade for integration: "<<integrationGrade<<" / 10"<<endl;
  
  
  /*********************Testing collisions***************************************/
  cout<<endl<<endl<<"Testing collision"<<endl;
  ifs = std::ifstream (folderPath+"/collision.data", std::ofstream::binary);
  MatrixXd resultPositions1(numSamples,3),resultPositions2(numSamples,3);
  MatrixXd resultOrientations1(numSamples,4), resultOrientations2(numSamples,4);
  MatrixXd resultLinVelocities1(numSamples,3), resultLinVelocities2(numSamples,3);
  MatrixXd resultAngVelocities1(numSamples,3), resultAngVelocities2(numSamples,3);
  MatrixXd intNormals=MatrixXd::Zero(numSamples, 3);
  MatrixXd intPositions=MatrixXd::Zero(numSamples, 3);
  VectorXd depths = VectorXd::Zero(numSamples);
  VectorXi isCollision = VectorXi::Zero(numSamples);
  deserializeMatrix(V1,ifs);
  deserializeMatrix(F1,ifs);
  deserializeMatrix(T1,ifs);
  deserializeMatrix(V2,ifs);
  deserializeMatrix(F2,ifs);
  deserializeMatrix(T2,ifs);
  deserializeMatrix(randomPositions,ifs);
  deserializeMatrix(randomOrientations,ifs);
  deserializeMatrix(randomLinVelocities,ifs);
  deserializeMatrix(randomAngVelocities,ifs);
  deserializeVector(isCollision,ifs);
  deserializeVector(depths,ifs);
  deserializeMatrix(intNormals,ifs);
  deserializeMatrix(intPositions,ifs);
  Eigen::MatrixXd resultLinVelocities1GT, resultAngVelocities1GT, resultLinVelocities2GT, resultAngVelocities2GT;
  Eigen::MatrixXd resultPositions1GT, resultOrientations1GT, resultPositions2GT, resultOrientations2GT;
  deserializeMatrix(resultPositions1GT,ifs);
  deserializeMatrix(resultPositions2GT,ifs);
  deserializeMatrix(resultOrientations1GT,ifs);
  deserializeMatrix(resultOrientations2GT,ifs);
  deserializeMatrix(resultLinVelocities1GT,ifs);
  deserializeMatrix(resultLinVelocities2GT,ifs);
  deserializeMatrix(resultAngVelocities1GT,ifs);
  deserializeMatrix(resultAngVelocities2GT,ifs);
  
  for (int i=0;i<isCollision.size();i++){
    if (!isCollision[i])
      continue;
    Mesh dummyMesh1(V1, F1, T1, 1.0, false, {0.0,0.0,0.0}, {1.0,0.0,0.0,0.0});
    Mesh dummyMesh2(V2, F2, T2, 1.0, false, randomPositions.row(i), randomOrientations.row(i));
    
    dummyMesh2.comVelocity=randomLinVelocities.row(i);
    dummyMesh2.angVelocity=randomAngVelocities.row(i);
    Scene scene;
    scene.meshes.push_back(dummyMesh1);
    scene.meshes.push_back(dummyMesh2);
    scene.handle_collision(dummyMesh1, dummyMesh2, depths(i), intNormals.row(i), intPositions.row(i), CRCoeff);
    
    resultPositions1.row(i) = dummyMesh1.COM;
    resultPositions2.row(i) = dummyMesh2.COM;
    resultOrientations1.row(i) = dummyMesh1.orientation;
    resultOrientations2.row(i) = dummyMesh2.orientation;
    resultLinVelocities1.row(i) = dummyMesh1.comVelocity;
    resultLinVelocities2.row(i) = dummyMesh2.comVelocity;
    resultAngVelocities1.row(i) = dummyMesh1.angVelocity;
    resultAngVelocities2.row(i) = dummyMesh2.angVelocity;
  }
  
  if ((resultPositions1GT-resultPositions1).cwiseAbs().maxCoeff(&maxRow, &maxCol)>tolerance){
    cout<<"COM result for mesh 1 differs on sample "<<maxRow<<endl;
    cout<<"GT: "<<resultPositions1GT.row(maxRow)<<endl;
    cout<<"Your result: "<<resultPositions1.row(maxRow)<<endl;
  } else{
    cout<<"COM result for mesh 1 is good! "<<endl;
    collisionGrade+=1.25;
  }
  if ((resultPositions2GT-resultPositions2).cwiseAbs().maxCoeff(&maxRow, &maxCol)>tolerance){
    cout<<"COM result for mesh 2 differs on sample "<<maxRow<<endl;
    cout<<"GT: "<<resultPositions2GT.row(maxRow)<<endl;
    cout<<"Your result: "<<resultPositions2.row(maxRow)<<endl;
  } else{
    cout<<"COM result for mesh 2 is good! "<<endl;
    collisionGrade+=1.25;
  }
  
  if ((resultOrientations1GT-resultOrientations1).cwiseAbs().maxCoeff(&maxRow, &maxCol)>tolerance){
    cout<<"Orientation result for mesh 1 differs on sample "<<maxRow<<endl;
    cout<<"GT: "<<resultOrientations1GT.row(maxRow)<<endl;
    cout<<"Your result: "<<resultOrientations1.row(maxRow)<<endl;
  } else{
    cout<<"Orientation result for mesh 1 is good! "<<endl;
    collisionGrade+=1.25;
  }
  if ((resultOrientations2GT-resultOrientations2).cwiseAbs().maxCoeff(&maxRow, &maxCol)>tolerance){
    cout<<"Orientation result for mesh 2 differs on sample "<<maxRow<<endl;
    cout<<"GT: "<<resultOrientations2GT.row(maxRow)<<endl;
    cout<<"Your result: "<<resultOrientations2.row(maxRow)<<endl;
  } else{
    cout<<"Orientation result for mesh 2 is good! "<<endl;
    collisionGrade+=1.25;
  }
  
  if ((resultLinVelocities1GT-resultLinVelocities1).cwiseAbs().maxCoeff(&maxRow, &maxCol)>tolerance){
    cout<<"COM velocity result form mesh 1 differs on sample "<<maxRow<<endl;
    cout<<"GT: "<<resultLinVelocities1GT.row(maxRow)<<endl;
    cout<<"Your result: "<<resultLinVelocities1.row(maxRow)<<endl;
  } else{
    cout<<"COM velocity for mesh 1 result is good! "<<endl;
    collisionGrade+=1.25;
  }
  if ((resultLinVelocities2GT-resultLinVelocities2).cwiseAbs().maxCoeff(&maxRow, &maxCol)>tolerance){
    cout<<"COM velocity result for mesh 2 differs on sample "<<maxRow<<endl;
    cout<<"GT: "<<resultLinVelocities2GT.row(maxRow)<<endl;
    cout<<"Your result: "<<resultLinVelocities2.row(maxRow)<<endl;
  } else{
    cout<<"COM velocity for mesh 2 result is good! "<<endl;
    collisionGrade+=1.25;
  }
  
  if ((resultAngVelocities1GT-resultAngVelocities1).cwiseAbs().maxCoeff(&maxRow, &maxCol)>tolerance){
    cout<<"Angular velocity for mesh 1 result differs on sample "<<maxRow<<endl;
    cout<<"GT: "<<resultAngVelocities1GT.row(maxRow)<<endl;
    cout<<"Your result: "<<resultAngVelocities1.row(maxRow)<<endl;
  } else{
    cout<<"Angular velocity for mesh 1 result is good! "<<endl;
    collisionGrade+=1.25;
  }
  if ((resultAngVelocities2GT-resultAngVelocities2).cwiseAbs().maxCoeff(&maxRow, &maxCol)>tolerance){
    cout<<"Angular velocity for mesh 2 result differs on sample "<<maxRow<<endl;
    cout<<"GT: "<<resultAngVelocities2GT.row(maxRow)<<endl;
    cout<<"Your result: "<<resultAngVelocities2.row(maxRow)<<endl;
  } else{
    cout<<"Angular velocity for mesh 2 result is good! "<<endl;
    collisionGrade+=1.25;
  }
  
  cout<<"Your collision grade: "<<collisionGrade<<" / 10"<<endl;
  cout<<"Your total grade: "<<integrationGrade+collisionGrade<<" /20"<<endl;
  
}

