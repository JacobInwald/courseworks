#ifndef COMPUTE_AREAS_NORMALS_HEADER_FILE
#define COMPUTE_AREAS_NORMALS_HEADER_FILE

#include <Eigen/Dense>

void compute_areas_normals(const Eigen::MatrixXd& V,
                           const Eigen::MatrixXi& F,
                           Eigen::VectorXd& areas,
                           Eigen::MatrixXd& normals){
  using namespace Eigen;
  areas.resize(F.rows());
  normals.resize(F.rows(),3);
  for (int i=0;i<F.rows();i++){
    RowVector3d v1 = V.row(F(i,0));
    RowVector3d v2 = V.row(F(i,1));
    RowVector3d v3 = V.row(F(i,2));
    normals.row(i)<<(v2-v1).cross(v3-v1);
    areas(i) = normals.row(i).norm()*0.5;
    normals.row(i).normalize();
  }
}


#endif
