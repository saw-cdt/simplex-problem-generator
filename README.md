# Simplex Application

A client-server application for generating, classifying, and managing linear programming problems for the Simplex method.

The project was developed as an end-to-end application with a **React** frontend and a **FastAPI** backend. It supports configurable problem generation, problem classification, exam creation, and PDF export.

## Features

- Generate linear programming problems with configurable objective functions and constraints
- Classify generated problems
- Manage problem data through the application interface
- Generate exams from linear programming problems
- Export generated content to PDF
- Client-server communication through a REST API

## Tech Stack

### Frontend
- React
- JavaScript
- Vite

### Backend
- Python
- FastAPI
- Uvicorn

## Architecture

The application is divided into two main components:

```text
React Frontend
      |
      | HTTP / REST
      v
FastAPI Backend
      |
      +-- Problem Generation
      +-- Classification
      +-- Exam Generation
      +-- PDF Export
```

The frontend handles the user interface and application state, while the FastAPI backend exposes the application's functionality through REST endpoints.

## Backend API

The backend is organized into separate routes for the main application features:

- `/api` — problem generation
- `/api` — problem classification
- `/api` — exam generation
- `/api` — PDF export

FastAPI also provides interactive API documentation when the backend is running.

## Running the Project

### Backend

Create and activate a Python virtual environment:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Start the FastAPI development server according to the backend configuration.

### Frontend

Install the frontend dependencies and start the development server:

```bash
cd frontend
npm install
npm run dev
```

Then open the local URL provided by Vite.

## Project Structure

```text
PIA-PILIN/
├── backend/
│   └── app/
│       ├── main.py
│       └── routes/
├── frontend/
│   └── src/
└── README.md
```

## Background

This project was developed as an academic project focused on linear programming and the Simplex method. The implementation covers both the client and server sides of the application, including the user interface, API design, problem-processing logic, and document generation.
