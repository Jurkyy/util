#!/usr/bin/env python3
import os
import argparse
from pathlib import Path


def create_cmake_lists(project_name, path):
    cmake_content = f"""cmake_minimum_required(VERSION 3.10)
project({project_name})

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Add source files
file(GLOB_RECURSE SOURCES src/*.cpp)
file(GLOB_RECURSE HEADERS include/*.hpp)

# Create executable
add_executable(${{PROJECT_NAME}} ${{SOURCES}})

# Include directories
target_include_directories(${{PROJECT_NAME}} PUBLIC include)

# Add testing
enable_testing()
add_subdirectory(tests)
"""
    with open(path / "CMakeLists.txt", "w") as f:
        f.write(cmake_content)


def create_test_cmake(project_name, path):
    test_cmake_content = f"""# Google Test
include(FetchContent)
FetchContent_Declare(
    googletest
    URL https://github.com/google/googletest/archive/release-1.11.0.tar.gz
)
FetchContent_MakeAvailable(googletest)

# Add test files
file(GLOB_RECURSE TEST_SOURCES *.cpp)

add_executable(tests ${{TEST_SOURCES}})
target_link_libraries(tests gtest gtest_main)

add_test(NAME tests COMMAND tests)
"""
    with open(path / "tests" / "CMakeLists.txt", "w") as f:
        f.write(test_cmake_content)


def create_main_cpp(path):
    main_content = """#include <iostream>

int main() {
    std::cout << "Hello, World!" << std::endl;
    return 0;
}
"""
    with open(path / "src" / "main.cpp", "w") as f:
        f.write(main_content)


def create_test_cpp(path):
    test_content = """#include <gtest/gtest.h>

TEST(SampleTest, AssertTrue) {
    ASSERT_TRUE(true);
}
"""
    with open(path / "tests" / "sample_test.cpp", "w") as f:
        f.write(test_content)


def create_gitignore(path):
    gitignore_content = """# Build directory
build/

# IDE specific files
.vscode/
.idea/
*.swp
*.swo

# Compiled files
*.o
*.out
"""
    with open(path / ".gitignore", "w") as f:
        f.write(gitignore_content)


def create_project_structure(project_name):
    # Create project directory
    project_path = Path(project_name)
    project_path.mkdir(exist_ok=True)

    # Create subdirectories
    dirs = ["src", "include", "tests", "build"]
    for dir_name in dirs:
        (project_path / dir_name).mkdir(exist_ok=True)

    # Create files
    create_cmake_lists(project_name, project_path)
    create_test_cmake(project_name, project_path)
    create_main_cpp(project_path)
    create_test_cpp(project_path)
    create_gitignore(project_path)

    print(f"Created C++ project structure for {project_name}")
    print("\nTo build the project:")
    print(f"cd {project_name}")
    print("mkdir -p build && cd build")
    print("cmake ..")
    print("make")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a C++ project structure")
    parser.add_argument("project_name", help="Name of the project")
    args = parser.parse_args()

    create_project_structure(args.project_name)
