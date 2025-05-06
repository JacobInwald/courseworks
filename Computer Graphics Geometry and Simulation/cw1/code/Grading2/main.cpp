#include "mesh.h"
#include "scene.h"
#include "constraints.h"
#include "serialization.h"
#include <Eigen/Dense>
#include <iostream>
#include <fstream>
#include <random>
#include <chrono>
#include <filesystem>

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
  gen = std::mt19937(rd());
  Eigen::MatrixXd randomLinVelocities(numSamples, 3);
  Eigen::MatrixXd randomAngVelocities(numSamples, 3);
  Eigen::MatrixXd randomPositions(numSamples, 3);
  Eigen::MatrixXd randomOrientations(numSamples, 4);
  
  generate_random_values(randomLinVelocities, -10, 10);
  generate_random_values(randomAngVelocities, -10, 10);
  generate_random_values(randomPositions, -10, 10);
  generate_random_values(randomOrientations, -10, 10);
  
  double section2Points = 20.0;
  double grade = 0.0;
  MatrixXd V1,V2;
  MatrixXi F1,F2,T1,T2;
  std::string folderPath(DATA_PATH); // Replace with your folder path
  
  std::ifstream ifs(folderPath+"/constraints.data", std::ofstream::binary);
  readMESH(folderPath+"/ellipsoid.mesh", V1,F1, T1);
  MatrixXd VMean = V1.rowwise()-V1.colwise().mean();
  double radius1 = VMean.rowwise().norm().mean();
  readMESH(folderPath+"/ellipsoid.mesh", V2,F2, T2);
  VMean = V2.rowwise()-V2.colwise().mean();
  double radius2 = VMean.rowwise().norm().mean();
  double  mutualRadius = (radius1 + radius2);
  randomPositions = random_vectors_in_sphere(mutualRadius, numSamples);
  generate_random_values(randomLinVelocities, -10, 10);
  generate_random_values(randomAngVelocities, -10, 10);
  generate_random_values(randomOrientations, -10, 10);
  VectorXd refValues = VectorXd::Zero(numSamples);
  MatrixXd correctedPositionsUpper(numSamples,6), correctedPositionsLower(numSamples,6);
  MatrixXd correctedLinVelocities(numSamples,6);
  MatrixXd correctedAngVelocities(numSamples,6);
  VectorXi positionWasValidUpper(numSamples), positionWasValidLower(numSamples), velocityWasValid(numSamples);
  MatrixXd correctedPositionsUpperGT, correctedPositionsLowerGT;
  MatrixXd correctedLinVelocitiesGT;
  MatrixXd correctedAngVelocitiesGT;
  VectorXi positionWasValidUpperGT, positionWasValidLowerGT, velocityWasValidGT;
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
  deserializeVector(positionWasValidUpperGT, ifs);
  deserializeVector(positionWasValidLowerGT, ifs);
  deserializeMatrix(correctedPositionsUpperGT, ifs);
  deserializeMatrix(correctedPositionsLowerGT, ifs);
  deserializeMatrix(correctedLinVelocitiesGT, ifs);
  deserializeMatrix(correctedAngVelocitiesGT, ifs);
  
  for (int i=0;i<numSamples;i++){
    Mesh dummyMesh1(V1, F1, T1, 1.0, false, {0.0,0.0,0.0}, {1.0,0.0,0.0,0.0});
    Mesh dummyMesh2(V2, F2, T2, 1.0, false, randomPositions.row(i), randomOrientations.row(i));
    refValues(i) = (dummyMesh2.origV.row(i) - dummyMesh1.origV.row(0)).norm();
    dummyMesh2.comVelocity = randomLinVelocities.row(i);
    dummyMesh2.angVelocity = randomAngVelocities.row(i);
    double refValueLower = 0.8 * refValues(i);
    double refValueUpper = 1.2 * refValues(i);
    Constraint upperConstraint(DISTANCE, INEQUALITY, true, 0, 0, 1, 0, dummyMesh1.totalInvMass, dummyMesh2.totalInvMass, RowVector3d::Zero(), refValueUpper, 0.0);
    Constraint lowerConstraint(DISTANCE, INEQUALITY, false, 0, 0, 1, 0, dummyMesh1.totalInvMass, dummyMesh2.totalInvMass, RowVector3d::Zero(), refValueLower, 0.0);
    
    MatrixXd currCOMPositions(2,3); currCOMPositions<<dummyMesh1.COM, dummyMesh2.COM;
    MatrixXd currConstPoints(2,3);  currConstPoints<<dummyMesh1.currV.row(0), dummyMesh2.currV.row(0);
    MatrixXd currLinVelocities(2,3); currLinVelocities<<dummyMesh1.comVelocity, dummyMesh2.comVelocity;
    MatrixXd currAngVelocities(2,3); currAngVelocities<<dummyMesh1.angVelocity, dummyMesh2.angVelocity;
    
    Matrix3d invInertiaTensor1 = dummyMesh1.get_curr_inv_IT();
    Matrix3d invInertiaTensor2 = dummyMesh2.get_curr_inv_IT();
    
    //Testing position projection
    MatrixXd correctedCOMPositionUpper, correctedCOMPositionLower;
    positionWasValidUpper(i) = upperConstraint.resolve_position_constraint(currCOMPositions, currConstPoints, correctedCOMPositionUpper, 0.0);
    positionWasValidLower(i) = lowerConstraint.resolve_position_constraint(currCOMPositions, currConstPoints, correctedCOMPositionLower, 0.0);
    correctedPositionsUpper.row(i)<<correctedCOMPositionUpper.row(0), correctedCOMPositionUpper.row(1);
    correctedPositionsLower.row(i)<<correctedCOMPositionLower.row(0), correctedCOMPositionLower.row(1);
    
    MatrixXd correctedLinVelocity, correctedAngVelocity;
    upperConstraint.resolve_velocity_constraint(currCOMPositions, currConstPoints, currLinVelocities, currAngVelocities, invInertiaTensor1, invInertiaTensor2, correctedLinVelocity, correctedAngVelocity, 0.0);
    correctedLinVelocities.row(i)<<correctedLinVelocity.row(0), correctedLinVelocity.row(1);
    correctedAngVelocities.row(i)<<correctedAngVelocity.row(0), correctedAngVelocity.row(1);
  }
  
  int maxRow, maxCol;
  if ((positionWasValidUpperGT-positionWasValidUpper).cwiseAbs().maxCoeff(&maxRow, &maxCol)>tolerance){
    cout<<"positionWasValidUpper differs on sample "<<maxRow<<endl;
    cout<<"GT: "<<positionWasValidUpperGT.row(maxRow)<<endl;
    cout<<"Your result: "<<positionWasValidUpper.row(maxRow)<<endl;
  } else{
    cout<<"PositionWasValidUpper is good! "<<endl;
    grade+=2.0;
  }
  if ((positionWasValidLowerGT-positionWasValidLower).cwiseAbs().maxCoeff(&maxRow, &maxCol)>tolerance){
    cout<<"positionWasValidLower differs on sample "<<maxRow<<endl;
    cout<<"GT: "<<positionWasValidUpperGT.row(maxRow)<<endl;
    cout<<"Your result: "<<positionWasValidUpper.row(maxRow)<<endl;
  } else{
    cout<<"PositionWasValidLower is good! "<<endl;
    grade+=2.0;
  }
  
  if ((correctedPositionsUpperGT-correctedPositionsUpper).cwiseAbs().maxCoeff(&maxRow, &maxCol)>tolerance){
    cout<<"correctedPositionsUpper differs on sample "<<maxRow<<endl;
    cout<<"GT: "<<correctedPositionsUpperGT.row(maxRow)<<endl;
    cout<<"Your result: "<<correctedPositionsUpper.row(maxRow)<<endl;
  } else{
    cout<<"correctedPositionsUpper is good! "<<endl;
    grade+=4.0;
  }
  if ((correctedPositionsLowerGT-correctedPositionsLower).cwiseAbs().maxCoeff(&maxRow, &maxCol)>tolerance){
    cout<<"correctedPositionsUpper differs on sample "<<maxRow<<endl;
    cout<<"GT: "<<correctedPositionsLowerGT.row(maxRow)<<endl;
    cout<<"Your result: "<<correctedPositionsLower.row(maxRow)<<endl;
  } else{
    cout<<"correctedPositionsLower is good! "<<endl;
    grade+=4.0;
  }
  if ((correctedLinVelocitiesGT-correctedLinVelocities).cwiseAbs().maxCoeff(&maxRow, &maxCol)>tolerance){
    cout<<"correctedLinVelocities differs on sample "<<maxRow<<endl;
    cout<<"GT: "<<correctedLinVelocitiesGT.row(maxRow)<<endl;
    cout<<"Your result: "<<correctedLinVelocities.row(maxRow)<<endl;
  } else{
    cout<<"correctedLinVelocities is good! "<<endl;
    grade+=4.0;
  }
  if ((correctedAngVelocitiesGT-correctedAngVelocities).cwiseAbs().maxCoeff(&maxRow, &maxCol)>tolerance){
    cout<<"correctedAngVelocities differs on sample "<<maxRow<<endl;
    cout<<"GT: "<<correctedAngVelocitiesGT.row(maxRow)<<endl;
    cout<<"Your result: "<<correctedAngVelocities.row(maxRow)<<endl;
  } else{
    cout<<"correctedAngVelocities is good! "<<endl;
    grade+=4.0;
  }
  
  cout<<"Your constraints grade: "<<grade<<" / 20"<<endl;
  
}

