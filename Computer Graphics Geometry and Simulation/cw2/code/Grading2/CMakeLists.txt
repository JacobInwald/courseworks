# Set the project name
cmake_minimum_required(VERSION 3.20)
project(Grading2)

# Add the executable
file(GLOB CODE_SOURCES ../include/*.c)
add_executable(${PROJECT_NAME} main.cpp ${CODE_SOURCES})

target_link_libraries(${PROJECT_NAME} common_includes polyscope)

