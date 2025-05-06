#include <polyscope/polyscope.h>
#include <polyscope/surface_mesh.h>
#include <polyscope/volume_mesh.h>
#include <polyscope/curve_network.h>
#include "readOFF.h"
#include "scene.h"
#include <Eigen/Dense>
#include <iostream>
#include <vector>
#include <set>
#include <array>
#include <chrono>
#include <filesystem>

using namespace Eigen;
using namespace std;

bool isAnimating = false;

polyscope::VolumeMesh* pMesh;
polyscope::VolumeMeshVertexVectorQuantity* pVelocityField;

double currTime = 0;
double timeStep = 0.02; //assuming 50 fps
int endStep = 10000000;
int step = 0;
Scene scene;

MatrixXd to_row_positions(const VectorXd& positions){
    MatrixXd rowPositions(positions.size()/3, 3);
    for (int i=0;i<positions.size()/3;i++)
        rowPositions.row(i) = positions.segment(3*i,3).transpose();
    
    //cout<<"rowPositions: "<<rowPositions<<endl;
    
    return rowPositions;
}

void callback_function() {
    ImGui::PushItemWidth(50);
    ImGui::TextUnformatted("Animation Parameters");
    ImGui::Separator();
    bool changed = ImGui::Checkbox("isAnimating", &isAnimating);
    ImGui::PopItemWidth();
    if (!isAnimating)
        return;
    
    if (step++ > endStep) return; 
    
    scene.update_scene(timeStep);
    
    pMesh->updateVertexPositions(to_row_positions(scene.globalPositions));
    pVelocityField->updateData(to_row_positions(scene.globalVelocities));
    //pConstraints->updateNodePositions(scene.currConstVertices);
}


int main(int argc, char *argv[])
{ 
    string sceneFP = "epcot";
    double alpha = 0.1;
    double beta = 0.1;
    if (argc > 1) sceneFP = argv[1];
    if (argc > 2) timeStep = atof(argv[2]); 
    if (argc > 3) alpha = atof(argv[3]);
    if (argc > 4) alpha = atof(argv[4]);
    if (argc > 5) endStep = atoi(argv[5]);

    scene.load_scene(sceneFP + "-scene.txt");
    polyscope::init();
    
    scene.init_scene(timeStep, alpha, beta);
    //scene.update_scene(0.0, CRCoeff, tolerance, maxIterations);
    
    // Visualization
    /*cout<<scene.currV<<endl;
     cout<<scene.meshes[0].F<<endl;
     cout<<scene.meshes[0].T<<endl;*/
    pMesh = polyscope::registerTetMesh("Entire Scene", to_row_positions(scene.globalPositions), scene.globalT);
    pVelocityField = pMesh->addVertexVectorQuantity("Velocity field", to_row_positions(scene.globalVelocities));
    //cout<<"scene.globalPositions: "<<scene.globalPositions<<endl;
    //cout<<"constEdges: "<<scene.constEdges<<endl;
    //cout<<"currConstVertices: "<<scene.currConstVertices<<endl;
    //pConstraints = polyscope::registerCurveNetwork("Constraints", scene.currConstVertices, scene.constEdges);
    //polyscope::state::lengthScale = 1.;
    //polyscope::state::boundingBox =
    //    std::tuple<glm::vec3, glm::vec3>{ {-5., 0., -5.}, {5., 5., 5.} };
    
    //constVertices, constEdges = update_visual_constraints(pMesh, allVertices, allConstEdges)
    //ps_constraints = ps.register_curve_network("Constraints", constVertices, constEdges)
    //ps.set_bounding_box([sceneBBox[1][0], 0, sceneBBox[1][2]], sceneBBox[1])
    //ps.set_ground_plane_height_factor(0.0, False)
    //ps.set_user_callback(callback)
    
    polyscope::options::groundPlaneHeightMode = polyscope::GroundPlaneHeightMode::Manual;
    polyscope::options::groundPlaneHeight = 0.; // in world coordinates along the up axis
    polyscope::state::userCallback = callback_function;
    
    polyscope::show();
    
}

