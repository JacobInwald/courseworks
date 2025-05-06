/*
 * This file is part of CGGS Coursework 1. 
 * author : s2150204
 *
 * This is an implementation of a constraint scheduling algorithm. This  
 * alogrithm makes a constraint map that stores which mesh is affected by
 * which constraints and then resolves them in a depth first manner. 
 * saving processing time. 
 *
 * Usage just requires calling CONSCH::resolve_constraints with a list of 
 * meshes and constraints.
 *
 */

#ifndef CONSCH_HEADER_FILE
#define CONSCH_HEADER_FILE

#include <vector>
#include <complex>
#include <map>
#include "constraints.h"
#include "mesh.h"
using namespace std;
using namespace Eigen;


namespace CONSCH 
{
  
  unsigned int maxDepth = 1; // maximum depth of constraint resolution
  double tolerance=1e-3; // tolerance for constraint resolution
  bool constrained_simulation = true; // whether to use constraint scheduling or not
  
  // defines the map for constraints
  typedef map<int, vector<Constraint>> ConstraintMap;


  /**
   * Makes a constraint map out of a list of constraints, which tells 
   * us which mesh is affected by which constraints.
   *
   * @param constraints list of constraints
   *
   * @return map of constraints
   */
  ConstraintMap make_map(vector<Constraint> constraints)
  {
    ConstraintMap constraintsMap; // initialise
    for (Constraint c : constraints) // add constraint for each mesh
    {
      constraintsMap[c.m1].push_back(c);
      constraintsMap[c.m2].push_back(c);
    }

    if (constraints.size() <= 0) // prevents resolution if no constraints
      maxDepth = -1;

    return constraintsMap;
  }


  /**
   * Resolves a constraint by correcting the position and velocity of the
   * target meshes. Then at the end, resolve all connected constraints.
   *
   * @param meshes list of meshes
   * @param constraint constraint to resolve
   * @param constraints map of constraints
   * @param depth current depth of resolution
   */
  void resolve_constraint(vector<Mesh> &meshes, Constraint constraint, ConstraintMap &constraints, unsigned int depth)
  {
    if (depth >= maxDepth) // Base case
      return;
    depth++;
    
    // initialize values for resolution
    RowVector3d origConstPos1 = meshes[constraint.m1].origV.row(constraint.v1);
    RowVector3d origConstPos2 = meshes[constraint.m2].origV.row(constraint.v2);
      
    RowVector3d currConstPos1 = QRot(origConstPos1, meshes[constraint.m1].orientation)+meshes[constraint.m1].COM;
    RowVector3d currConstPos2 = QRot(origConstPos2, meshes[constraint.m2].orientation)+meshes[constraint.m2].COM;
      
    MatrixXd currCOMPositions(2,3); currCOMPositions<<meshes[constraint.m1].COM, meshes[constraint.m2].COM;
    MatrixXd currConstPositions(2,3); currConstPositions<<currConstPos1, currConstPos2;
    
    // correct position

    MatrixXd correctedCOMPositions;
    bool positionWasValid=constraint.resolve_position_constraint(currCOMPositions, currConstPositions,correctedCOMPositions, tolerance);
    
    if (positionWasValid)
      return;
    
    // update COM without currV to save time    
    meshes[constraint.m1].COM = correctedCOMPositions.row(0);
    meshes[constraint.m2].COM = correctedCOMPositions.row(1);
    
    // Resolve velocity
    
    // Initialize values before resolution
    currConstPos1 = QRot(origConstPos1, meshes[constraint.m1].orientation)+meshes[constraint.m1].COM;
    currConstPos2 = QRot(origConstPos2, meshes[constraint.m2].orientation)+meshes[constraint.m2].COM;
    
    currCOMPositions<<meshes[constraint.m1].COM, meshes[constraint.m2].COM;
    currConstPositions<<currConstPos1, currConstPos2;
    MatrixXd currCOMVelocities(2,3); currCOMVelocities<<meshes[constraint.m1].comVelocity, meshes[constraint.m2].comVelocity;
    MatrixXd currAngVelocities(2,3); currAngVelocities<<meshes[constraint.m1].angVelocity, meshes[constraint.m2].angVelocity;
        
    Matrix3d invInertiaTensor1=meshes[constraint.m1].get_curr_inv_IT();
    Matrix3d invInertiaTensor2=meshes[constraint.m2].get_curr_inv_IT();
    MatrixXd correctedCOMVelocities, correctedAngVelocities;
        
    // correct velocity
    bool velocityWasValid=constraint.resolve_velocity_constraint(currCOMPositions, currConstPositions, currCOMVelocities, currAngVelocities, invInertiaTensor1, invInertiaTensor2, correctedCOMVelocities,correctedAngVelocities, tolerance);
    
    if (velocityWasValid)
      return;
     
    meshes[constraint.m1].comVelocity =correctedCOMVelocities.row(0);
    meshes[constraint.m2].comVelocity =correctedCOMVelocities.row(1);
          
    meshes[constraint.m1].angVelocity =correctedAngVelocities.row(0);
    meshes[constraint.m2].angVelocity =correctedAngVelocities.row(1);
    
    for (Constraint c : constraints[constraint.m1]) 
      resolve_constraint(meshes, c, constraints, depth);

    for (Constraint c : constraints[constraint.m2]) 
      resolve_constraint(meshes, c, constraints, depth);
 
    return;
  }

 
  /**
   * Resolves all constraints in a list of constraints.
   *
   * @param meshes list of meshes
   * @param constraints list of constraints
   */
  void resolve_constraints(vector<Mesh> &meshes, vector<Constraint> constraints)
  {
    ConstraintMap constraintsMap = make_map(constraints); // make map
    
    for (Constraint constraint : constraints) { // resolve all constraints
      unsigned int depth = 0;
      resolve_constraint(meshes, constraint, constraintsMap, depth);
    }
  }

};

#endif
