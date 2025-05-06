#ifndef SCENE_HEADER_FILE
#define SCENE_HEADER_FILE

#include <vector>
#include <fstream>
#include "ccd.h"
#include "volInt.h"
#include "auxfunctions.h"
#include "readMESH.h"
#include "mesh.h"
#include "constraints.h"
#include "bpss.h"
#include "constraint_scheduling.h" 

using namespace Eigen;
using namespace std;


//This class contains the entire scene operations, and the engine time loop.
class Scene{
public:
  double currTime;
  vector<Mesh> meshes;
  vector<Constraint> constraints;
  Mesh groundMesh;
  
  //Mostly for visualization
  MatrixXi allF, constEdges;
  MatrixXd currV, currConstVertices;
  
  
  //adding an objects. You do not need to update this generally
  void add_mesh(const MatrixXd& V, const MatrixXi& F, const MatrixXi& T, const double density, const bool isFixed, const RowVector3d& COM, const RowVector4d& orientation){ 
    Mesh m(V,F, T, density, isFixed, COM, orientation);
    meshes.push_back(m);
    //cout<<"m.origV.row(0): "<<m.origV.row(0)<<endl;
    //cout<<"m.currV.row(0): "<<m.currV.row(0)<<endl;
    
    MatrixXi newAllF(allF.rows()+F.rows(),3);
    newAllF<<allF, (F.array()+currV.rows()).matrix();
    allF = newAllF;
    MatrixXd newCurrV(currV.rows()+V.rows(),3);
    newCurrV<<currV, m.currV;
    currV = newCurrV;
  }
  
  /*********************************************************************
   This function handles a collision between objects ro1 and ro2 when found, by assigning impulses to both objects.
   Input: RigidObjects m1, m2
   depth: the depth of penetration
   contactNormal: the normal of the conact measured m1->m2
   penPosition: a point on m2 such that if m2 <= m2 + depth*contactNormal, then penPosition+depth*contactNormal is the common contact point
   CRCoeff: the coefficient of restitution
   *********************************************************************/
  static void handle_collision(Mesh& m1, Mesh& m2,const double& depth, const RowVector3d& contactNormal,const RowVector3d& penPosition, const double CRCoeff){
    /**************TODO: implement this function**************/

    // Update Position
    double w1 = m1.totalInvMass / (m1.totalInvMass + m2.totalInvMass); // calc w1
    if (m1.isFixed) w1 = 0;
    double w2 = 1-w1;
    if (m2.isFixed) { w2 = 0; w1 = 1;}

    
    m1.COM = m1.COM - w1 * depth * contactNormal; // update COM1
    m2.COM = m2.COM + w2 * depth * contactNormal; // update COM2
    
    // Update Velocity

    // Prep Variables
    RowVector3d p12 = penPosition + w2 * depth * contactNormal; // p12
    RowVector3d r1 = p12 - m1.COM; // r1
    RowVector3d r2 = p12 - m2.COM; // r2
    RowVector3d v1bar = m1.comVelocity + m1.angVelocity.cross(r1); // v1bar
    RowVector3d v2bar = m2.comVelocity + m2.angVelocity.cross(r2); // v1bar
    RowVector3d r1CrossN = r1.cross(contactNormal); // r1 x n_hat
    RowVector3d r2CrossN = r2.cross(contactNormal); // r2 x n_hat
    

    // Compute j
    double j_nom = - (1.0 + CRCoeff) * ((v1bar - v2bar).dot(contactNormal));
    double j_denom = m1.totalInvMass + m2.totalInvMass + \
      (r1CrossN * m1.get_curr_inv_IT() * r1CrossN.transpose()) + \
      (r2CrossN * m2.get_curr_inv_IT() * r2CrossN.transpose());
    double j = j_nom / j_denom;


    // Compute impulse
    RowVector3d impulse = j * contactNormal;
   

    // Update velocities
    m1.comVelocity = m1.comVelocity + impulse * m1.totalInvMass; // update v1
    m2.comVelocity = m2.comVelocity - impulse * m2.totalInvMass; // update v2
    m1.angVelocity = m1.angVelocity + (r1.cross(impulse) * m1.get_curr_inv_IT()); // update w1
    m2.angVelocity = m2.angVelocity - (r2.cross(impulse) * m2.get_curr_inv_IT()); // update w2
    
    // Compute impulse vectors
    // m1.currImpulses.push_back(Impulse(p12, impulse));
    // m2.currImpulses.push_back(Impulse(p12, -impulse));

  }
  
  
  
  /*********************************************************************
   This function handles a single time step by:
   1. Integrating velocities, positions, and orientations by the timeStep
   2. detecting and handling collisions with the coefficient of restitutation CRCoeff
   3. updating the visual scene in fullV and fullT
   *********************************************************************/
  void update_scene(double timeStep, double CRCoeff, int maxIterations, double tolerance){
    
    //integrating velocity, position and orientation from forces and previous states
    for (int i=0;i<meshes.size();i++)
      meshes[i].integrate(timeStep);
    
    //detecting and handling collisions when found
    //This is done exhaustively: checking every two objects in the scene.

    BPSS::handle_collisions(meshes, this->handle_collision, CRCoeff);
    
    //colliding with the pseudo-mesh of the ground
    for (int i=0;i<meshes.size();i++){
      int minyIndex;
      double minY = meshes[i].currV.col(1).minCoeff(&minyIndex);
      //linear resolution
      if (minY<=0.0)
        handle_collision(meshes[i], groundMesh, minY, {0.0,1.0,0.0},meshes[i].currV.row(minyIndex),CRCoeff);
    }
    
    // Resolving constraints
    CONSCH::resolve_constraints(meshes, constraints);

    currTime+=timeStep;
    
    //updating meshes and visualization
    for (int i=0;i<meshes.size();i++)
      for (int j=0;j<meshes[i].currV.rows();j++)
        meshes[i].currV.row(j)<<QRot(meshes[i].origV.row(j), meshes[i].orientation)+meshes[i].COM;
    
    int currVOffset=0;
    for (int i=0;i<meshes.size();i++){
      currV.block(currVOffset, 0, meshes[i].currV.rows(), 3) = meshes[i].currV;
      currVOffset+=meshes[i].currV.rows();
    }
    for (int i=0;i<constraints.size();i+=2){   //jumping bc we have constraint pairs
      currConstVertices.row(i) = meshes[constraints[i].m1].currV.row(constraints[i].v1);
      currConstVertices.row(i+1) = meshes[constraints[i].m2].currV.row(constraints[i].v2);
    }
  }
  
  //loading a scene from the scene .txt files
  //you do not need to update this function
  bool load_scene(const std::string sceneFileName, const std::string constraintFileName){
    
    ifstream sceneFileHandle, constraintFileHandle;
    sceneFileHandle.open(DATA_PATH "/" + sceneFileName);
    if (!sceneFileHandle.is_open())
      return false;
    int numofObjects;
    
    currTime=0;
    sceneFileHandle>>numofObjects;
    for (int i=0;i<numofObjects;i++){
      MatrixXi objT, objF;
      MatrixXd objV;
      std::string MESHFileName;
      bool isFixed;
      double density;
      RowVector3d userCOM;
      RowVector4d userOrientation;
      sceneFileHandle>>MESHFileName>>density>>isFixed>>userCOM(0)>>userCOM(1)>>userCOM(2)>>userOrientation(0)>>userOrientation(1)>>userOrientation(2)>>userOrientation(3);
      userOrientation.normalize();
      readMESH(DATA_PATH "/" + MESHFileName,objV,objF, objT);
      
      //fixing weird orientation problem
      MatrixXi tempF(objF.rows(),3);
      tempF<<objF.col(2), objF.col(1), objF.col(0);
      objF=tempF;
      
      add_mesh(objV,objF, objT,density, isFixed, userCOM, userOrientation);
      cout << "COM: " << userCOM <<endl;
      cout << "orientation: " << userOrientation <<endl;
    }
    
    // initialise BPSS
    BPSS::init(meshes);

    //adding ground mesh artifically
    groundMesh = Mesh(MatrixXd(0,3), MatrixXi(0,3), MatrixXi(0,4), 0.0, true, RowVector3d::Zero(), RowVector4d::Zero());
    
    //Loading constraints
    int numofConstraints;
    constraintFileHandle.open(DATA_PATH "/" + constraintFileName);
    if (!constraintFileHandle.is_open())
      return false;
    constraintFileHandle>>numofConstraints;
    currConstVertices.resize(numofConstraints*2,3);
    constEdges.resize(numofConstraints,2);
    for (int i=0;i<numofConstraints;i++){
      int attachM1, attachM2, attachV1, attachV2;
      double lowerBound, upperBound;
      constraintFileHandle>>attachM1>>attachV1>>attachM2>>attachV2>>lowerBound>>upperBound;
      //cout<<"Constraints: "<<attachM1<<","<<attachV1<<","<<attachM2<<","<<attachV2<<","<<lowerBound<<","<<upperBound<<endl;
      
      double initDist=(meshes[attachM1].currV.row(attachV1)-meshes[attachM2].currV.row(attachV2)).norm();
      //cout<<"initDist: "<<initDist<<endl;
      double invMass1 = (meshes[attachM1].isFixed ? 0.0 : meshes[attachM1].totalInvMass);  //fixed meshes have infinite mass
      double invMass2 = (meshes[attachM2].isFixed ? 0.0 : meshes[attachM2].totalInvMass);
      constraints.push_back(Constraint(DISTANCE, INEQUALITY,false, attachM1, attachV1, attachM2, attachV2, invMass1,invMass2,RowVector3d::Zero(), lowerBound*initDist, 0.0));
      constraints.push_back(Constraint(DISTANCE, INEQUALITY,true, attachM1, attachV1, attachM2, attachV2, invMass1,invMass2,RowVector3d::Zero(), upperBound*initDist, 0.0));
      currConstVertices.row(2*i) = meshes[attachM1].currV.row(attachV1);
      currConstVertices.row(2*i+1) = meshes[attachM2].currV.row(attachV2);
      constEdges.row(i)<<2*i, 2*i+1;
    }
    
    return true;
  }
  
  
  Scene(){allF.resize(0,3); currV.resize(0,3);}
  ~Scene(){}
};



#endif
