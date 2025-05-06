/*
 * This file is part of CGGS Coursework 1. 
 * author : s2150204
 *
 * This is an implementation of a Broad Phase Space Subdivision (BPSS) algorithm. 
 * This alogrithm divides the world space into cubes of a given side length, and
 * then resolves collisions within those cubes, saving processing time. 
 *
 * Usage just requires calling BSPS::handle_collisions with a list of meshes and 
 * a function to handle collisions.
 *
 */

#ifndef BPSS_HEADER_FILE
#define BPSS_HEADER_FILE

#include <vector>
#include <complex>
#include <set>
#include <map>
using namespace std;
using namespace Eigen;


namespace BPSS 
{
  double cellSize=0; // the side length of the cubes in the BSPS grid
  typedef map<size_t, vector<int>> Grid; // The grid is a map from cell hash to cell


  /**
  * Initialises the BPSS algorithm with a given cell size
   */
  void init(vector<Mesh> meshes) {
    // find the maximum size of the meshes
    for (Mesh m : meshes) {
      RowVector3d vmin=m.currV.colwise().minCoeff();
      RowVector3d vmax=m.currV.colwise().maxCoeff();
      cellSize = max(cellSize, (vmax - vmin).norm());
    }
    cellSize = cellSize*1.5;
  }


  /**
   * Hashes a cell position by iteratively hashing each coordinate
   * @param coords The cell position
   * @return The hash of the cell position
   */
  size_t hash_cell(int x, int y, int z) {
    size_t out = hash<double>()(x) + 0x9e3779b9 + (out << 6) + (out >> 2);
    out ^= hash<double>()(y) + 0x9e3779b9 + (out << 6) + (out >> 2);
    out ^= hash<double>()(z) + 0x9e3779b9 + (out << 6) + (out >> 2);
    return out; 
  }


  /**
   * Adds a mesh to a mesh_id list
   *
   * @param mesh_ids The list of mesh_ids
   * @param id The mesh_id to add
   */
  void add_mesh_to_cell(vector<int>& mesh_ids, int id){
    mesh_ids.push_back(id);
  }


  /**
   * Adds a mesh id to the grid at the given cell position, if there is no cell there, initialises a new one
   *
   * @param grid The grid to add the mesh to
   * @param mesh_id The mesh id to add
   * @param cell_pos The cell position to add the mesh to
   */
  void add(Grid &grid, int mesh_id, size_t hash) {
    
    if (grid.find(hash) != grid.end()) { // checks if cell exists
      grid[hash].push_back(mesh_id);
      return; // job is done 
    }
    
    grid[hash] = vector<int>{mesh_id}; // add new cell to grid
  }
  

  /**
   * Adds a mesh to the grid at all its corresponding cell positions.
   *
   * @param grid The grid to add the mesh to
   * @param m The mesh to add
   * @param m_id Corresponding mesh id
   */
  void add_mesh(Grid &grid, Mesh m, int m_id) {
    // initialise min and maximum positions of mesh
    RowVector3d vmin=m.currV.colwise().minCoeff();
    RowVector3d vmax=m.currV.colwise().maxCoeff();
    
    
    vmin = (vmin / cellSize).array().floor(); // convert to grid positions
    vmax = (vmax / cellSize).array().floor(); // convert to grid positions
    
    
    // iterate through all grid positions inside the mesh and add the mesh's
    //  id to the grid at those points
    for (int x = vmin.x(); x <= vmax.x(); x++)
      for (int y = vmin.y(); y <= vmax.y(); y++)
        for (int z = vmin.z(); z <= vmax.z(); z++) 
          add(grid, m_id, hash_cell(x, y, z));
  }
  
  
  /**
   * Takes a array of meshes and a function to handle collisions, and resolves collisions between meshes using BPSSS
   * 
   * @param meshes The array of meshes to resolve collisions between
   * @param handle The function to handle collisions
   * @param CRCoeff The coefficient of restitution to use in the collision resolution
   */
  void handle_collisions(vector<Mesh> &meshes, 
      function<void(Mesh&, Mesh&, const double&,
                    const RowVector3d&, const RowVector3d&,
                    const double)> handle, 
      const double CRCoeff) {
    // variables used in the collision resolution
    double depth;
    RowVector3d contactNormal, penPosition;
    
    Grid grid; // initialise grid
    for (int i = 0; i < meshes.size(); i++)
      add_mesh(grid, meshes[i], i);
    
    for (const auto& p : grid) // iterate through each cell in the grid
      for (int i = 0; i < p.second.size(); i++)
        for (int j = i+1; j < p.second.size(); j++)
          if (meshes[p.second[i]].is_collide(meshes[p.second[j]],depth, contactNormal, penPosition))
            handle(meshes[p.second[i]], meshes[p.second[j]],depth, contactNormal, penPosition,CRCoeff);
    
  }

};

#endif
