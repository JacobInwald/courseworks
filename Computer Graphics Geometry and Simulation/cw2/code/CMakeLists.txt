# Set the project name
cmake_minimum_required(VERSION 3.20)
project(CourseWork2Simulation)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)

# Specify the directories for Eigen and Polyscope
set(EIGEN3_INCLUDE_DIR ${CMAKE_SOURCE_DIR}/../external/eigen)
set(POLYSCOPE_INCLUDE_DIR ${CMAKE_SOURCE_DIR}/../external/polyscope/include)
set(CW0_INCLUDE_DIR ${CMAKE_SOURCE_DIR}/include)

add_subdirectory("${CMAKE_SOURCE_DIR}/../external/polyscope" "polyscope")

add_library(common_includes INTERFACE)
target_include_directories(common_includes INTERFACE
    ${EIGEN3_INCLUDE_DIR}
    ${POLYSCOPE_INCLUDE_DIR}
    ${CW0_INCLUDE_DIR}
)

add_compile_definitions(DATA_PATH="${PROJECT_SOURCE_DIR}/../data")
set(TUTORIAL_DATA_PATH ${PROJECT_SOURCE_DIR}/../data CACHE PATH "location of tutorial data resources")
target_compile_definitions(common_includes INTERFACE "-DTUTORIAL_DATA_PATH=\"${TUTORIAL_DATA_PATH}\"")

# The subprojects
add_subdirectory(Section12)
add_subdirectory(Section3)
add_subdirectory(Grading1)
add_subdirectory(Grading2)


