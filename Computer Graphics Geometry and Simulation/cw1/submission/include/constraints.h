#ifndef CONSTRAINTS_HEADER_FILE
#define CONSTRAINTS_HEADER_FILE

using namespace Eigen;
using namespace std;

typedef enum ConstraintType{DISTANCE, COLLISION} ConstraintType;   //You can expand it for more constraints
typedef enum ConstraintEqualityType{EQUALITY, INEQUALITY} ConstraintEqualityType;

//there is such constraints per two variables that are equal. That is, for every attached vertex there are three such constraints for (x,y,z);
class Constraint{
public:
  
  int m1, m2;                     //Two participating meshes (can be the same)  - auxiliary data for users (constraint class shouldn't use that)
  int v1, v2;                     //Two vertices from the respective meshes - auxiliary data for users (constraint class shouldn't use that)
  double invMass1, invMass2;       //inverse masses of two bodies
  double refValue;                //Reference values to use in the constraint, when needed (like distance)
  bool isUpper;                   //in case this is an inequality constraints, whether it's an upper or a lower bound
  RowVector3d refVector;             //Reference vector when needed (like vector)
  double CRCoeff;                 //velocity bias
  ConstraintType constraintType;  //The type of the constraint, and will affect the value and the gradient. This SHOULD NOT change after initialization!
  ConstraintEqualityType constraintEqualityType;  //whether the constraint is an equality or an inequality
  
  Constraint(const ConstraintType _constraintType, const ConstraintEqualityType _constraintEqualityType, const bool _isUpper, const int& _m1, const int& _v1, const int& _m2, const int& _v2, const double& _invMass1, const double& _invMass2, const RowVector3d& _refVector, const double& _refValue, const double& _CRCoeff):constraintType(_constraintType), constraintEqualityType(_constraintEqualityType), isUpper(_isUpper), m1(_m1), v1(_v1), m2(_m2), v2(_v2), invMass1(_invMass1), invMass2(_invMass2),  refValue(_refValue), CRCoeff(_CRCoeff){
    refVector=_refVector;
  }
  
  ~Constraint(){}
  
  
  
  //computes the impulse needed for all particles to resolve the velocity constraint, and corrects the velocities accordingly.
  //The velocities are a vector (vCOM1, w1, vCOM2, w2) in both input and output.
  //returns true if constraint was already valid with "currVelocities", and false otherwise (false means there was a correction done)
  bool resolve_velocity_constraint(const MatrixXd& currCOMPositions, const MatrixXd& currVertexPositions, const MatrixXd& currCOMVelocities, const MatrixXd& currAngVelocities, const Matrix3d& invInertiaTensor1, const Matrix3d& invInertiaTensor2, MatrixXd& correctedCOMVelocities, MatrixXd& correctedAngVelocities, double tolerance){
    
    
    /***************************TODO: implement this function**********************/
    // initialization
    RowVector3d COM1 = currCOMPositions.row(0);
    RowVector3d COM2 = currCOMPositions.row(1);
    RowVector3d v1 = currCOMVelocities.row(0);
    RowVector3d v2 = currCOMVelocities.row(1);
    RowVector3d w1 = currAngVelocities.row(0);
    RowVector3d w2 = currAngVelocities.row(1);
    RowVector3d p1 = currVertexPositions.row(0);
    RowVector3d p2 = currVertexPositions.row(1);

    correctedCOMVelocities=currCOMVelocities;
    correctedAngVelocities=currAngVelocities;
   
   // Converting everything to column vectors cos its easier lol
    
    Eigen::Vector3d unitVector = (p1.transpose() - p2.transpose()).normalized();
    Eigen::Vector3d r1 = p1.transpose() - COM1.transpose();
    Eigen::Vector3d r2 = p2.transpose() - COM2.transpose();

    Eigen::Matrix<double, 1, 12> J;
    J.block<1, 3>(0, 0) = unitVector.transpose();
    J.block<1, 3>(0, 3) = (r1.cross(unitVector)).transpose();
    J.block<1, 3>(0, 6) = -unitVector.transpose();
    J.block<1, 3>(0, 9) = -(r2.cross(unitVector)).transpose();
    
    Vector<double, 12> v;
    v << v1.transpose(), w1.transpose(), v2.transpose(), w2.transpose();

    // Check if the constraint is initially valid
    double Jv = J * v;
    if (abs(Jv) < 1e-5) { // Assuming a small threshold for floating-point precision
        return true; // No correction needed
    }

    // Calculate the effective mass matrix M^-1
    Matrix<double, 12, 12> M_inv;
    M_inv.setZero();
    M_inv.block<3, 3>(0, 0) = invMass1 * Matrix3d::Identity();
    M_inv.block<3, 3>(3, 3) = invInertiaTensor1.transpose();
    M_inv.block<3, 3>(6, 6) = invMass2 * Matrix3d::Identity();
    M_inv.block<3, 3>(9, 9) = invInertiaTensor2.transpose();

    // Calculate the impulse scalar lambda
    double lambda = -Jv / (J * M_inv * J.transpose());

    // Calculate the correction vector ∆v
    Vector<double, 12> delta_v = lambda * M_inv * J.transpose();

    // Update velocities
    correctedCOMVelocities.row(0) += delta_v.segment<3>(0);
    correctedAngVelocities.row(0) += delta_v.segment<3>(3);
    correctedCOMVelocities.row(1) += delta_v.segment<3>(6);
    correctedAngVelocities.row(1) += delta_v.segment<3>(9);
    return false; 
  }
  
  //projects the position unto the constraint
  //returns true if constraint was already good
  bool resolve_position_constraint(const MatrixXd& currCOMPositions, const MatrixXd& currConstPositions, MatrixXd& correctedCOMPositions, double tolerance){
    
    /***************************TODO: implement this function**********************/
    RowVector3d p1 = currConstPositions.row(0);
    RowVector3d p2 = currConstPositions.row(1);
    RowVector3d COM1 = currCOMPositions.row(0);
    RowVector3d COM2 = currCOMPositions.row(1);
    
    correctedCOMPositions=currCOMPositions;

    if (this->constraintEqualityType == EQUALITY) {
      if (abs((p1 - p2).norm()) < this->refValue+tolerance &&
          abs((p1 - p2).norm()) > this->refValue-tolerance) {
          return true;
      }
    }
    else if (this->constraintEqualityType == INEQUALITY &&
      this->isUpper){
      if (abs((p1 - p2).norm()) < this->refValue+tolerance) {
        return true;
      }
    }
    else if (this->constraintEqualityType == INEQUALITY &&
      !this->isUpper){
      if (abs((p1 - p2).norm()) > this->refValue-tolerance) {
        return true;
      }
    }

    RowVector3d n = (p1 - p2).normalized();
    double n_l = (p1 - p2).norm(); 
    double w1 = invMass1 / (invMass1 + invMass2);
    double w2 = 1 - w1;
    
    RowVector3d dp1 = -w1 * (n_l - this->refValue) * n;
    RowVector3d dp2 = w2 * (n_l - this->refValue) * n;

    correctedCOMPositions.row(0) = COM1 + dp1;
    correctedCOMPositions.row(1) = COM2 + dp2;

    //stub implementation
    return false;
  }
  
};



#endif /* constraints_h */
