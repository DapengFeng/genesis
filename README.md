# Template Repository

A comprehensive template repository for C++ projects with integrated development tools and best practices.

## Overview

This template provides a ready-to-use foundation for C++ development projects with:

- **Code Quality**: Pre-configured clang-format and cpplint for consistent code styling
- **Pre-commit Hooks**: Automated code quality checks before commits
- **GitHub Integration**: Issue and pull request templates for better project management
- **Multi-language Support**: Configuration for both C++ and Python development
- **Modern C++ Standards**: Configured for C++20 with appropriate linting rules

## Features

- 🔧 **Clang-format**: Comprehensive code formatting configuration
- 📋 **Pre-commit hooks**: Automated checks for code quality, security, and formatting
- 🐛 **CPP Lint**: C++ code linting with customized rules
- 📁 **Gitignore**: Pre-configured for C++, Python, and common IDE files
- 🎯 **GitHub Templates**: Bug report and feature request templates
- 🔍 **Static Analysis**: Integrated cppcheck for code analysis

## Quick Start

1. Use this template to create a new repository
2. Clone your new repository
3. Install pre-commit hooks: `pre-commit install -t commit-msg`
4. Start developing your C++ project

## Coding Agent Support

This repository includes structured issue and pull request templates that are
designed to work well for both humans and coding agents.

- Follow `AGENTS.md` for repository-specific workflow and template usage
  guidance.
- Follow `.github/copilot-instructions.md` for GitHub Copilot-specific
  instructions.
- Run `pre-commit run --all-files` before opening a pull request and include
  the command output in the PR template.

This template helps maintain code quality and consistency across your C++ projects while providing a solid foundation for collaborative development.
